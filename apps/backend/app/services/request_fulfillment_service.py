from __future__ import annotations

import json
import logging
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from datetime import datetime
from time import sleep
from typing import Any, Protocol

from app.repositories.feature_request_repository import PENDING_STATUS, FeatureRequestRepository
from app.services.fitbit_anchoring import FitbitAnchorContext, build_anchor_context
from app.services.fitbit_feature_builder import build_feature_payload
from app.services.weather_context_client import WeatherContextClient
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_BACKOFF_SECONDS = (0.25, 0.5, 1.0)
DEFAULT_FEATURE_SOURCE = "fitbit-pipeline"
DEFAULT_REQUEST_RETRY_BACKOFF_BASE_SECONDS = 30.0


class FitbitClientProtocol(Protocol):
    def fetch_user_data(self, *, user_id: str) -> dict[str, Any]: ...


class FitbitTimeoutError(Exception):
    pass


@dataclass
class FulfillmentRunStats:
    processed: int = 0
    fulfilled: int = 0
    skipped: int = 0
    failed: int = 0


class RequestFulfillmentService:
    def __init__(
        self,
        repository: FeatureRequestRepository,
        fitbit_client: FitbitClientProtocol,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        backoff_seconds: tuple[float, float, float] = DEFAULT_BACKOFF_SECONDS,
        feature_source: str = DEFAULT_FEATURE_SOURCE,
        sleep_func: Callable[[float], None] = sleep,
        weather_client: WeatherContextClient | None = None,
        request_retry_backoff_base_seconds: float = DEFAULT_REQUEST_RETRY_BACKOFF_BASE_SECONDS,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._fitbit_client = fitbit_client
        self._timeout_seconds = timeout_seconds
        self._backoff_seconds = backoff_seconds
        self._feature_source = feature_source
        self._sleep = sleep_func
        self._weather_client = weather_client or WeatherContextClient()
        self._request_retry_backoff_base_seconds = request_retry_backoff_base_seconds
        self._settings = settings or get_settings()

    def process_pending_requests(self, *, limit: int = 100) -> FulfillmentRunStats:
        return self._process_requests(self._repository.list_pending_requests(limit=limit))

    def process_pending_requests_for_user(
        self,
        *,
        user_id: str,
        limit: int = 100,
    ) -> FulfillmentRunStats:
        return self._process_requests(
            self._repository.list_pending_requests_by_user(
                user_id=user_id,
                limit=limit,
            )
        )

    def _process_requests(self, requests) -> FulfillmentRunStats:
        stats = FulfillmentRunStats()
        fetched_data_by_user_date: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        latest_exercise_by_anchor: dict[tuple[str, str], dict[str, Any]] = {}
        for request in requests:
            stats.processed += 1
            client_features = self._extract_client_features(request)
            anchor_context = self._request_anchor_context(
                request=request,
                client_features=client_features,
            )
            try:
                date_iso = anchor_context.local_date_iso
                night_date_iso = anchor_context.night_anchor_date_iso
                cache_key = (
                    request.user_id,
                    date_iso,
                    night_date_iso,
                    anchor_context.source_timezone,
                )
                prefetched_fitbit_data = fetched_data_by_user_date.get(cache_key)
                if prefetched_fitbit_data is None:
                    prefetched_fitbit_data = self._fetch_fitbit_data_with_retry(
                        user_id=request.user_id,
                        request_id=request.id,
                        date_iso=date_iso,
                        night_date_iso=night_date_iso,
                        source_timezone=anchor_context.source_timezone,
                    )
                    fetched_data_by_user_date[cache_key] = prefetched_fitbit_data
                    self._log_missing_signal_blobs(
                        user_id=request.user_id,
                        date_iso=date_iso,
                        raw_fitbit_data=prefetched_fitbit_data,
                    )

                request_fitbit_data = dict(prefetched_fitbit_data)
                latest_exercise_blob = self._fetch_latest_exercise_for_request(
                    user_id=request.user_id,
                    anchor_context=anchor_context,
                    cache=latest_exercise_by_anchor,
                )
                if isinstance(latest_exercise_blob, dict):
                    request_fitbit_data["latest_exercise"] = latest_exercise_blob

                outcome = self.process_request(
                    request.id,
                    prefetched_fitbit_data=request_fitbit_data,
                    request_context=anchor_context,
                )
            except Exception as exc:
                logger.exception("Failed to process request %s.", request.id)
                self._schedule_request_retry(request=request, exc=exc)
                outcome = "failed"
            if outcome == "fulfilled":
                stats.fulfilled += 1
            elif outcome == "skipped":
                stats.skipped += 1
            else:
                stats.failed += 1
        return stats

    def process_request(
        self,
        request_id: str,
        *,
        prefetched_fitbit_data: dict[str, Any] | None = None,
        request_context: FitbitAnchorContext | None = None,
    ) -> str:
        request = self._repository.get_request_by_id(request_id=request_id)
        if request is None:
            logger.warning("Skipping missing request %s.", request_id)
            return "skipped"

        if request.status != PENDING_STATUS or request.feature_id is not None:
            logger.info(
                "Skipping request %s because status=%s featureId=%s.",
                request.id,
                request.status,
                request.feature_id,
            )
            return "skipped"

        try:
            client_features = self._extract_client_features(request)
            anchor_ctx = request_context or self._request_anchor_context(
                request=request,
                client_features=client_features,
            )
            raw_fitbit_data = prefetched_fitbit_data
            if raw_fitbit_data is None:
                raw_fitbit_data = self._fetch_fitbit_data_with_retry(
                    user_id=request.user_id,
                    request_id=request.id,
                    date_iso=anchor_ctx.local_date_iso,
                    night_date_iso=anchor_ctx.night_anchor_date_iso,
                    source_timezone=anchor_ctx.source_timezone,
                )
                latest_exercise_blob = self._fetch_latest_exercise_for_request(
                    user_id=request.user_id,
                    anchor_context=anchor_ctx,
                    cache={},
                )
                if isinstance(latest_exercise_blob, dict):
                    raw_fitbit_data = dict(raw_fitbit_data)
                    raw_fitbit_data["latest_exercise"] = latest_exercise_blob

            feature_payload = self._extract_feature_payload(
                raw_fitbit_data=raw_fitbit_data,
                request_id=request.id,
                request=request,
                client_features=client_features,
                request_context=anchor_ctx,
            )
            feature_id = self._repository.fulfill_request_if_pending(
                request_id=request.id,
                user_id=request.user_id,
                feature_source=self._feature_source,
                feature_payload=feature_payload,
                source_timezone=anchor_ctx.source_timezone,
                window_start=anchor_ctx.night_window_start_utc,
                window_end=anchor_ctx.night_window_end_utc,
            )
            if feature_id is None:
                logger.info(
                    "Skipping request %s because it was already fulfilled by another worker.",
                    request.id,
                )
                return "skipped"

            logger.info(
                "Successfully fulfilled request %s with feature %s.",
                request.id,
                feature_id,
            )
            return "fulfilled"
        except Exception as exc:
            logger.exception("Failed to fulfill request %s.", request.id)
            self._schedule_request_retry(request=request, exc=exc)
            return "failed"

    def _fetch_fitbit_data_with_retry(
        self,
        *,
        user_id: str,
        request_id: str,
        date_iso: str,
        night_date_iso: str,
        source_timezone: str,
    ) -> dict[str, Any]:
        max_retries = len(self._backoff_seconds)
        attempt = 0
        while True:
            attempt += 1
            try:
                return self._call_fitbit_with_timeout(
                    user_id=user_id,
                    date_iso=date_iso,
                    night_date_iso=night_date_iso,
                    source_timezone=source_timezone,
                )
            except Exception as exc:
                is_retryable = self._is_retryable_fitbit_error(exc)
                if not is_retryable or attempt > max_retries:
                    logger.error(
                        "Fitbit fetch failed for request %s after %s attempts: %s",
                        request_id,
                        attempt,
                        exc,
                    )
                    raise

                retry_after_delay = _to_float(getattr(exc, "retry_after_seconds", None))
                if retry_after_delay is not None and retry_after_delay > 0:
                    delay = retry_after_delay
                else:
                    delay = self._backoff_seconds[attempt - 1]
                logger.warning(
                    "Retrying Fitbit fetch for request %s (attempt %s/%s) in %.3fs after error: %s",
                    request_id,
                    attempt,
                    max_retries + 1,
                    delay,
                    exc,
                )
                self._sleep(delay)

    def _call_fitbit_with_timeout(
        self,
        *,
        user_id: str,
        date_iso: str,
        night_date_iso: str,
        source_timezone: str,
    ) -> dict[str, Any]:
        executor: ThreadPoolExecutor | None = None
        timed_out = False
        try:
            executor = ThreadPoolExecutor(max_workers=1)
            fetch_for_date = getattr(self._fitbit_client, "fetch_user_data_for_date", None)
            if callable(fetch_for_date):
                future: Future[dict[str, Any]] = executor.submit(
                    self._call_fetch_for_date_compat,
                    fetch_for_date=fetch_for_date,
                    user_id=user_id,
                    date_iso=date_iso,
                    night_date_iso=night_date_iso,
                    source_timezone=source_timezone,
                )
            else:
                future = executor.submit(
                    self._fitbit_client.fetch_user_data,
                    user_id=user_id,
                )
            return future.result(timeout=self._timeout_seconds)
        except FuturesTimeoutError as exc:
            timed_out = True
            if executor is not None:
                executor.shutdown(wait=False, cancel_futures=True)
            raise FitbitTimeoutError(
                f"Timed out while fetching Fitbit data for user {user_id}."
            ) from exc
        finally:
            if executor is not None and not timed_out:
                executor.shutdown(wait=True, cancel_futures=False)

    def _extract_feature_payload(
        self,
        *,
        raw_fitbit_data: dict[str, Any],
        request_id: str,
        request,
        client_features: dict[str, Any],
        request_context: FitbitAnchorContext,
    ) -> dict[str, Any]:
        weather_context = self._fetch_weather_context(
            client_features=client_features,
            anchor_datetime=request_context.anchor_local,
            request_id=request_id,
        )

        if not isinstance(raw_fitbit_data, dict):
            logger.warning(
                "Fitbit payload for request %s is not an object; storing empty feature object.",
                request_id,
            )
            return build_feature_payload(
                raw_fitbit_data={},
                anchor_datetime=request_context.anchor_local,
                client_features=client_features,
                weather_context=weather_context,
            )

        if not raw_fitbit_data:
            logger.warning(
                "Fitbit payload for request %s is empty; storing empty feature object.",
                request_id,
            )
            return build_feature_payload(
                raw_fitbit_data={},
                anchor_datetime=request_context.anchor_local,
                client_features=client_features,
                weather_context=weather_context,
            )

        payload = build_feature_payload(
            raw_fitbit_data=raw_fitbit_data,
            anchor_datetime=request_context.anchor_local,
            client_features=client_features,
            weather_context=weather_context,
        )
        payload = self._attach_feature_window_metadata(
            payload=payload,
            request_context=request_context,
        )
        notes = payload.get("notes")
        if isinstance(notes, list):
            missing_or_partial = [
                note
                for note in notes
                if isinstance(note, str)
                and (note.startswith("missing_") or note.startswith("partial_"))
            ]
            if missing_or_partial:
                logger.info(
                    "Feature payload contains missing/partial Fitbit signals for request %s: %s",
                    request_id,
                    ", ".join(missing_or_partial),
                )
        return payload

    @staticmethod
    def _is_retryable_fitbit_error(exc: Exception) -> bool:
        if isinstance(exc, ConnectionError | TimeoutError | FitbitTimeoutError):
            return True

        status_code = getattr(exc, "status_code", None)
        return isinstance(status_code, int) and (status_code == 429 or 500 <= status_code < 600)

    @staticmethod
    def _extract_client_features(request) -> dict[str, Any]:
        client_features_raw = getattr(request, "client_features_json", None)
        if not isinstance(client_features_raw, str) or not client_features_raw.strip():
            return {}
        try:
            parsed = json.loads(client_features_raw)
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        return parsed

    def _fetch_weather_context(
        self,
        *,
        client_features: dict[str, Any],
        anchor_datetime: datetime,
        request_id: str,
    ) -> dict[str, Any]:
        lat = _to_float(client_features.get("lat"))
        lon = _to_float(client_features.get("lon"))
        try:
            return self._weather_client.fetch_context(
                lat=lat,
                lon=lon,
                date_iso=anchor_datetime.date().isoformat(),
            )
        except Exception:
            logger.exception("Failed to fetch weather context for request %s.", request_id)
            missing = {
                "__missing": True,
                "reason": "request_error",
                "raw_status": None,
                "payload": {},
            }
            return {"weather": missing, "air_quality": missing}

    def _request_anchor_context(
        self,
        *,
        request: Any,
        client_features: dict[str, Any],
    ) -> FitbitAnchorContext:
        return build_anchor_context(
            created_at=getattr(request, "created_at", None),
            client_features=client_features,
            fallback_timezone=self._settings.FITBIT_DEFAULT_TIMEZONE,
            night_anchor_start_hour=self._settings.NIGHT_ANCHOR_START_HOUR,
            night_anchor_end_hour=self._settings.NIGHT_ANCHOR_END_HOUR,
        )

    @staticmethod
    def _attach_feature_window_metadata(
        *,
        payload: dict[str, Any],
        request_context: FitbitAnchorContext,
    ) -> dict[str, Any]:
        payload_copy = dict(payload)
        meta = payload_copy.get("meta")
        if not isinstance(meta, dict):
            meta = {}
        else:
            meta = dict(meta)
        meta.update(
            {
                "source_timezone": request_context.source_timezone,
                "window_start": request_context.night_window_start_utc.isoformat(),
                "window_end": request_context.night_window_end_utc.isoformat(),
                "local_date": request_context.local_date_iso,
                "night_anchor_date": request_context.night_anchor_date_iso,
            }
        )
        payload_copy["meta"] = meta
        return payload_copy

    @staticmethod
    def _log_missing_signal_blobs(
        *,
        user_id: str,
        date_iso: str,
        raw_fitbit_data: dict[str, Any],
    ) -> None:
        missing_signals: list[str] = []
        for signal_name, signal_blob in raw_fitbit_data.items():
            if not isinstance(signal_blob, dict):
                continue
            if not signal_blob.get("__missing", False):
                continue
            reason = signal_blob.get("reason")
            if isinstance(reason, str) and reason:
                missing_signals.append(f"{signal_name}:{reason}")
            else:
                missing_signals.append(signal_name)

        if missing_signals:
            logger.info(
                "Missing Fitbit signal blobs for user %s date %s: %s",
                user_id,
                date_iso,
                ", ".join(sorted(missing_signals)),
            )

    @staticmethod
    def _call_fetch_for_date_compat(
        *,
        fetch_for_date,
        user_id: str,
        date_iso: str,
        night_date_iso: str,
        source_timezone: str,
    ) -> dict[str, Any]:
        try:
            return fetch_for_date(
                user_id=user_id,
                date_iso=date_iso,
                night_date_iso=night_date_iso,
                source_timezone=source_timezone,
            )
        except TypeError:
            return fetch_for_date(
                user_id=user_id,
                date_iso=date_iso,
            )

    def _fetch_latest_exercise_for_request(
        self,
        *,
        user_id: str,
        anchor_context: FitbitAnchorContext,
        cache: dict[tuple[str, str], dict[str, Any]],
    ) -> dict[str, Any] | None:
        fetch_latest = getattr(self._fitbit_client, "fetch_latest_activity_for_anchor", None)
        if not callable(fetch_latest):
            return None

        before_timestamp_iso = anchor_context.anchor_local.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        cache_key = (user_id, before_timestamp_iso)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            latest_blob = fetch_latest(
                user_id=user_id,
                before_timestamp_iso=before_timestamp_iso,
            )
        except Exception:
            logger.exception(
                "Failed to fetch latest exercise for user %s at anchor %s.",
                user_id,
                before_timestamp_iso,
            )
            latest_blob = {
                "__missing": True,
                "reason": "request_error",
                "raw_status": None,
                "payload": {},
            }
        cache[cache_key] = latest_blob
        return latest_blob

    def _schedule_request_retry(self, *, request: Any, exc: Exception) -> None:
        schedule_retry = getattr(self._repository, "schedule_retry_if_pending", None)
        if not callable(schedule_retry):
            return

        attempts = _to_int(getattr(request, "attempts", None)) or 0
        delay_seconds = self._request_retry_backoff_base_seconds * (2**attempts)
        error_code = _to_int(getattr(exc, "status_code", None))
        error_signal = _to_str(getattr(exc, "signal_name", None)) or exc.__class__.__name__
        try:
            scheduled = schedule_retry(
                request_id=request.id,
                user_id=request.user_id,
                delay_seconds=delay_seconds,
                error_code=error_code,
                error_signal=error_signal,
            )
        except Exception:
            logger.exception("Failed to schedule retry for request %s.", request.id)
            return

        if scheduled:
            logger.info(
                "Scheduled retry for request %s after %.1f seconds (attempt %s).",
                request.id,
                delay_seconds,
                attempts + 1,
            )


def _to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_str(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return None
