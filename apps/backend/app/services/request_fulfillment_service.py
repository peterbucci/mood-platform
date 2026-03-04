from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from time import sleep
from typing import Any, Protocol

from app.repositories.feature_request_repository import PENDING_STATUS, FeatureRequestRepository

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_BACKOFF_SECONDS = (0.25, 0.5, 1.0)
DEFAULT_FEATURE_SOURCE = "fitbit-pipeline"
FITBIT_SECTIONS = (
    "sleep",
    "steps",
    "exercise",
    "heart_rate",
    "resting_heart_rate",
    "calories",
)


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
    ) -> None:
        self._repository = repository
        self._fitbit_client = fitbit_client
        self._timeout_seconds = timeout_seconds
        self._backoff_seconds = backoff_seconds
        self._feature_source = feature_source
        self._sleep = sleep_func

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
        for request in requests:
            stats.processed += 1
            outcome = self.process_request(request.id)
            if outcome == "fulfilled":
                stats.fulfilled += 1
            elif outcome == "skipped":
                stats.skipped += 1
            else:
                stats.failed += 1
        return stats

    def process_request(self, request_id: str) -> str:
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
            raw_fitbit_data = self._fetch_fitbit_data_with_retry(
                user_id=request.user_id,
                request_id=request.id,
            )
            feature_payload = self._extract_feature_payload(
                raw_fitbit_data=raw_fitbit_data,
                request_id=request.id,
            )
            feature_id = self._repository.fulfill_request_if_pending(
                request_id=request.id,
                user_id=request.user_id,
                feature_source=self._feature_source,
                feature_payload=feature_payload,
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
        except Exception:
            logger.exception("Failed to fulfill request %s.", request.id)
            return "failed"

    def _fetch_fitbit_data_with_retry(self, *, user_id: str, request_id: str) -> dict[str, Any]:
        max_retries = len(self._backoff_seconds)
        attempt = 0
        while True:
            attempt += 1
            try:
                return self._call_fitbit_with_timeout(user_id=user_id)
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

    def _call_fitbit_with_timeout(self, *, user_id: str) -> dict[str, Any]:
        executor: ThreadPoolExecutor | None = None
        timed_out = False
        try:
            executor = ThreadPoolExecutor(max_workers=1)
            future: Future[dict[str, Any]] = executor.submit(
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
    ) -> dict[str, Any]:
        if not isinstance(raw_fitbit_data, dict):
            logger.warning(
                "Fitbit payload for request %s is not an object; storing empty feature object.",
                request_id,
            )
            return {}

        if not raw_fitbit_data:
            logger.warning(
                "Fitbit payload for request %s is empty; storing empty feature object.",
                request_id,
            )
            return {}

        feature_payload: dict[str, Any] = {}
        for section in FITBIT_SECTIONS:
            section_payload = raw_fitbit_data.get(section)
            if section_payload is None:
                logger.warning("Request %s is missing Fitbit section '%s'.", request_id, section)
                continue
            feature_payload[section] = section_payload

        if not feature_payload:
            logger.warning(
                "Fitbit payload for request %s had no expected sections; persisting raw payload.",
                request_id,
            )
            return dict(raw_fitbit_data)

        return feature_payload

    @staticmethod
    def _is_retryable_fitbit_error(exc: Exception) -> bool:
        if isinstance(exc, ConnectionError | TimeoutError | FitbitTimeoutError):
            return True

        status_code = getattr(exc, "status_code", None)
        return isinstance(status_code, int) and 500 <= status_code < 600
