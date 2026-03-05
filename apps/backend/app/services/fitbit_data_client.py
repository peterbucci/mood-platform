from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy.orm import Session, sessionmaker

from app.repositories.fitbit_token_repository import FitbitTokenRepository
from app.services.fitbit_api_client import FitbitApiClient
from app.services.fitbit_token_service import FitbitTokenService
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class FitbitAuthorizationError(Exception):
    def __init__(self, *, status_code: int, signal_name: str) -> None:
        super().__init__(f"Fitbit auth failure for signal {signal_name} (status={status_code}).")
        self.status_code = status_code
        self.signal_name = signal_name


class FitbitRateLimitError(Exception):
    def __init__(self, *, signal_name: str, retry_after_seconds: float | None) -> None:
        super().__init__(f"Fitbit rate limited for signal {signal_name}.")
        self.status_code = 429
        self.signal_name = signal_name
        self.retry_after_seconds = retry_after_seconds


class StaticFitbitPayloadClient:
    def __init__(self) -> None:
        raw_payload = os.getenv("FITBIT_STATIC_PAYLOAD", "").strip()
        self._uses_static_payload = bool(raw_payload)
        if not self._uses_static_payload:
            self._payload: dict[str, Any] = {}
            return

        try:
            parsed_payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            logger.warning("Invalid FITBIT_STATIC_PAYLOAD JSON; using empty payload.")
            self._payload = {}
            return

        if not isinstance(parsed_payload, dict):
            logger.warning(
                "FITBIT_STATIC_PAYLOAD must deserialize to an object; using empty payload."
            )
            self._payload = {}
            return

        self._payload = parsed_payload

    @property
    def is_configured(self) -> bool:
        return self._uses_static_payload

    def fetch_user_data(self, *, user_id: str) -> dict[str, Any]:
        del user_id
        return dict(self._payload)

    def fetch_user_data_for_date(self, *, user_id: str, date_iso: str) -> dict[str, Any]:
        del user_id, date_iso
        return dict(self._payload)

    def fetch_latest_activity_for_anchor(
        self,
        *,
        user_id: str,
        before_timestamp_iso: str,
    ) -> dict[str, Any]:
        del user_id, before_timestamp_iso
        return _missing_signal(reason="not_supported")


class FitbitSignalPullClient:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        settings: Settings | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings or get_settings()

    def fetch_user_data(self, *, user_id: str) -> dict[str, Any]:
        date_iso = datetime.now(tz=UTC).date().isoformat()
        return self.fetch_user_data_for_date(user_id=user_id, date_iso=date_iso)

    def fetch_user_data_for_date(
        self,
        *,
        user_id: str,
        date_iso: str,
        night_date_iso: str | None = None,
        source_timezone: str | None = None,
    ) -> dict[str, Any]:
        del source_timezone
        user_uuid = uuid.UUID(user_id)
        day_anchor_date = _parse_iso_date(date_iso)
        night_anchor_date = _parse_iso_date(night_date_iso) if night_date_iso else day_anchor_date
        range_start_date = night_anchor_date - timedelta(days=6)
        range_start_iso = range_start_date.isoformat()
        night_anchor_iso = night_anchor_date.isoformat()
        with self._session_factory() as session:
            with httpx.Client(timeout=10) as http_client:
                token_service = FitbitTokenService(
                    repository=FitbitTokenRepository(session=session),
                    settings=self._settings,
                    http_client=http_client,
                )
                api_client = FitbitApiClient(
                    token_service=token_service,
                    http_client=http_client,
                    min_fetch_interval_seconds=self._settings.FITBIT_MIN_FETCH_INTERVAL_SECONDS,
                )

                if token_service.is_reauth_required(user_id=user_uuid):
                    logger.warning(
                        "Skipping Fitbit fetch for user %s because reauth is required.",
                        user_id,
                    )
                    return _needs_reauth_signal_payload()

                def fetch_signal(*, signal_name: str, fetch_fn) -> dict[str, Any]:
                    return self._fetch_signal(
                        signal_name=signal_name,
                        fetch_fn=fetch_fn,
                        token_service=token_service,
                        user_id=user_uuid,
                    )

                activity_summary = fetch_signal(
                    signal_name="activity_summary",
                    fetch_fn=lambda: api_client.fetch_activity_summary(
                        user_id=user_uuid,
                        date_iso=date_iso,
                    ),
                )
                steps_intraday = fetch_signal(
                    signal_name="steps_intraday",
                    fetch_fn=lambda: api_client.fetch_intraday_steps(
                        user_id=user_uuid,
                        date_iso=date_iso,
                    ),
                )
                calories_intraday = fetch_signal(
                    signal_name="calories_intraday",
                    fetch_fn=lambda: api_client.fetch_intraday_calories(
                        user_id=user_uuid,
                        date_iso=date_iso,
                    ),
                )
                azm_intraday = fetch_signal(
                    signal_name="azm_intraday",
                    fetch_fn=lambda: api_client.fetch_intraday_active_zone_minutes(
                        user_id=user_uuid,
                        date_iso=date_iso,
                    ),
                )
                heart_intraday = fetch_signal(
                    signal_name="heart_intraday",
                    fetch_fn=lambda: api_client.fetch_intraday_heart_rate(
                        user_id=user_uuid,
                        date_iso=date_iso,
                    ),
                )
                steps_7d = fetch_signal(
                    signal_name="steps_7d",
                    fetch_fn=lambda: api_client.fetch_steps_7d(
                        user_id=user_uuid,
                        date_iso=date_iso,
                    ),
                )
                heart_7d = fetch_signal(
                    signal_name="heart_7d",
                    fetch_fn=lambda: api_client.fetch_heart_rate_7d(
                        user_id=user_uuid,
                        date_iso=date_iso,
                    ),
                )
                hrv_range = fetch_signal(
                    signal_name="hrv_range",
                    fetch_fn=lambda: api_client.fetch_hrv_range(
                        user_id=user_uuid,
                        start_date_iso=range_start_iso,
                        end_date_iso=night_anchor_iso,
                    ),
                )
                hrv_all = fetch_signal(
                    signal_name="hrv_all",
                    fetch_fn=lambda: api_client.fetch_hrv_all(
                        user_id=user_uuid,
                        date_iso=night_anchor_iso,
                    ),
                )
                hrv = fetch_signal(
                    signal_name="hrv",
                    fetch_fn=lambda: api_client.fetch_hrv(
                        user_id=user_uuid,
                        date_iso=night_anchor_iso,
                    ),
                )
                sleep_range = fetch_signal(
                    signal_name="sleep_range",
                    fetch_fn=lambda: api_client.fetch_sleep_range(
                        user_id=user_uuid,
                        start_date_iso=range_start_iso,
                        end_date_iso=night_anchor_iso,
                    ),
                )
                breathing_rate = fetch_signal(
                    signal_name="breathing_rate",
                    fetch_fn=lambda: api_client.fetch_breathing_rate(
                        user_id=user_uuid,
                        date_iso=night_anchor_iso,
                    ),
                )
                breathing_rate_range = fetch_signal(
                    signal_name="breathing_rate_range",
                    fetch_fn=lambda: api_client.fetch_breathing_rate_range(
                        user_id=user_uuid,
                        start_date_iso=range_start_iso,
                        end_date_iso=night_anchor_iso,
                    ),
                )
                breathing_rate_all = fetch_signal(
                    signal_name="breathing_rate_all",
                    fetch_fn=lambda: api_client.fetch_breathing_rate_all(
                        user_id=user_uuid,
                        date_iso=night_anchor_iso,
                    ),
                )
                spo2_range = fetch_signal(
                    signal_name="spo2_range",
                    fetch_fn=lambda: api_client.fetch_spo2_range(
                        user_id=user_uuid,
                        start_date_iso=range_start_iso,
                        end_date_iso=night_anchor_iso,
                    ),
                )
                temp_range = fetch_signal(
                    signal_name="temp_range",
                    fetch_fn=lambda: api_client.fetch_skin_temperature_range(
                        user_id=user_uuid,
                        start_date_iso=range_start_iso,
                        end_date_iso=night_anchor_iso,
                    ),
                )
                spo2 = fetch_signal(
                    signal_name="spo2",
                    fetch_fn=lambda: api_client.fetch_spo2(
                        user_id=user_uuid,
                        date_iso=night_anchor_iso,
                    ),
                )
                temp = fetch_signal(
                    signal_name="temp",
                    fetch_fn=lambda: api_client.fetch_skin_temperature(
                        user_id=user_uuid,
                        date_iso=night_anchor_iso,
                    ),
                )
                nutrition = fetch_signal(
                    signal_name="nutrition",
                    fetch_fn=lambda: api_client.fetch_nutrition(
                        user_id=user_uuid,
                        date_iso=date_iso,
                    ),
                )
                water = fetch_signal(
                    signal_name="water",
                    fetch_fn=lambda: api_client.fetch_water_logs(
                        user_id=user_uuid,
                        date_iso=date_iso,
                    ),
                )

        return {
            "activity_summary": activity_summary,
            "heart": heart_7d,
            "sleep": sleep_range,
            "hrv": hrv,
            "breathing_rate": breathing_rate,
            "spo2": spo2,
            "temp": temp,
            "nutrition": nutrition,
            "water": water,
            "steps_intraday": steps_intraday,
            "calories_intraday": calories_intraday,
            "azm_intraday": azm_intraday,
            "heart_intraday": heart_intraday,
            "steps_7d": steps_7d,
            "heart_7d": heart_7d,
            "hrv_range": hrv_range,
            "hrv_all": hrv_all,
            "sleep_range": sleep_range,
            "breathing_rate_all": breathing_rate_all,
            "breathing_rate_range": breathing_rate_range,
            "spo2_range": spo2_range,
            "temp_range": temp_range,
        }

    def fetch_latest_activity_for_anchor(
        self,
        *,
        user_id: str,
        before_timestamp_iso: str,
    ) -> dict[str, Any]:
        user_uuid = uuid.UUID(user_id)
        with self._session_factory() as session:
            with httpx.Client(timeout=10) as http_client:
                token_service = FitbitTokenService(
                    repository=FitbitTokenRepository(session=session),
                    settings=self._settings,
                    http_client=http_client,
                )
                api_client = FitbitApiClient(
                    token_service=token_service,
                    http_client=http_client,
                    min_fetch_interval_seconds=self._settings.FITBIT_MIN_FETCH_INTERVAL_SECONDS,
                )
                if token_service.is_reauth_required(user_id=user_uuid):
                    return _missing_signal(reason="needs_reauth")
                return self._fetch_signal(
                    signal_name="latest_exercise",
                    fetch_fn=lambda: api_client.fetch_latest_activity(
                        user_id=user_uuid,
                        before_date_iso=before_timestamp_iso,
                    ),
                    token_service=token_service,
                    user_id=user_uuid,
                )

    def _fetch_signal(
        self,
        *,
        signal_name: str,
        fetch_fn,
        token_service: FitbitTokenService | None = None,
        user_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        response: httpx.Response | None = None
        for attempt in range(2):
            try:
                response = fetch_fn()
                break
            except httpx.ReadTimeout:
                if attempt == 0:
                    logger.warning(
                        "Retrying Fitbit signal %s after read timeout (attempt %s).",
                        signal_name,
                        attempt + 2,
                    )
                    continue
                logger.exception("Fitbit request timed out for signal %s.", signal_name)
                return _missing_signal(reason="request_error")
            except httpx.RequestError:
                logger.exception("Fitbit request failed for signal %s.", signal_name)
                return _missing_signal(reason="request_error")

        if response is None:
            return _missing_signal(reason="request_error")

        status_code = response.status_code
        if status_code == 401:
            raise FitbitAuthorizationError(status_code=status_code, signal_name=signal_name)
        if status_code == 403:
            reason = "forbidden"
            if _is_missing_scope_response(response):
                reason = "forbidden_scope"
                if token_service is not None and user_id is not None:
                    token_service.mark_needs_reauth(user_id=user_id, required=True)
                    scope = None
                    try:
                        stored_token = token_service.get_stored_token(user_id=user_id)
                    except Exception:
                        stored_token = None
                    if stored_token is not None:
                        scope = getattr(stored_token, "scope", None)
                    logger.warning(
                        (
                            "Detected insufficient Fitbit scope for signal %s (user=%s). "
                            "Marking needs_reauth=true. Stored scope=%s"
                        ),
                        signal_name,
                        user_id,
                        scope,
                    )
            return _missing_signal(reason=reason, raw_status=status_code)
        if status_code == 404:
            return _missing_signal(reason="not_found", raw_status=status_code)
        if status_code == 429:
            raise FitbitRateLimitError(
                signal_name=signal_name,
                retry_after_seconds=_retry_after_seconds(response),
            )
        if 500 <= status_code < 600:
            return _missing_signal(reason="upstream_error", raw_status=status_code)
        if not 200 <= status_code < 300:
            return _missing_signal(reason="unexpected_status", raw_status=status_code)

        try:
            payload = response.json()
        except ValueError:
            return _missing_signal(reason="malformed_json", raw_status=status_code)

        if isinstance(payload, dict):
            parsed_payload = payload
        elif isinstance(payload, list):
            parsed_payload = {"items": payload}
        else:
            parsed_payload = {"value": payload}
        return _present_signal(payload=parsed_payload, raw_status=status_code)


def build_fitbit_client(*, session_factory: sessionmaker[Session]) -> object:
    static_client = StaticFitbitPayloadClient()
    if static_client.is_configured:
        logger.info("Using static Fitbit payload client.")
        return static_client

    return FitbitSignalPullClient(session_factory=session_factory)


def _present_signal(*, payload: dict[str, Any], raw_status: int) -> dict[str, Any]:
    return {
        "__missing": False,
        "reason": None,
        "raw_status": raw_status,
        "payload": payload,
    }


def _missing_signal(*, reason: str, raw_status: int | None = None) -> dict[str, Any]:
    return {
        "__missing": True,
        "reason": reason,
        "raw_status": raw_status,
        "payload": {},
    }


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return datetime.now(tz=UTC).date()


def _is_missing_scope_response(response: httpx.Response) -> bool:
    try:
        payload = response.json()
    except ValueError:
        return False
    if not isinstance(payload, dict):
        return False

    errors = payload.get("errors")
    if not isinstance(errors, list):
        return False

    for error in errors:
        if not isinstance(error, dict):
            continue
        candidates = [
            error.get("errorType"),
            error.get("message"),
            error.get("fieldName"),
        ]
        normalized = " ".join(
            value.lower() for value in candidates if isinstance(value, str) and value.strip()
        )
        if "scope" in normalized or "permission" in normalized:
            return True
    return False


def _needs_reauth_signal_payload() -> dict[str, Any]:
    return {
        "activity_summary": _missing_signal(reason="needs_reauth"),
        "heart": _missing_signal(reason="needs_reauth"),
        "sleep": _missing_signal(reason="needs_reauth"),
        "hrv": _missing_signal(reason="needs_reauth"),
        "breathing_rate": _missing_signal(reason="needs_reauth"),
        "spo2": _missing_signal(reason="needs_reauth"),
        "temp": _missing_signal(reason="needs_reauth"),
        "nutrition": _missing_signal(reason="needs_reauth"),
        "water": _missing_signal(reason="needs_reauth"),
        "steps_intraday": _missing_signal(reason="needs_reauth"),
        "calories_intraday": _missing_signal(reason="needs_reauth"),
        "azm_intraday": _missing_signal(reason="needs_reauth"),
        "heart_intraday": _missing_signal(reason="needs_reauth"),
        "steps_7d": _missing_signal(reason="needs_reauth"),
        "heart_7d": _missing_signal(reason="needs_reauth"),
        "hrv_range": _missing_signal(reason="needs_reauth"),
        "hrv_all": _missing_signal(reason="needs_reauth"),
        "sleep_range": _missing_signal(reason="needs_reauth"),
        "breathing_rate_all": _missing_signal(reason="needs_reauth"),
        "breathing_rate_range": _missing_signal(reason="needs_reauth"),
        "spo2_range": _missing_signal(reason="needs_reauth"),
        "temp_range": _missing_signal(reason="needs_reauth"),
    }


def _retry_after_seconds(response: httpx.Response) -> float | None:
    header_value = response.headers.get("Retry-After")
    if not header_value:
        return None
    try:
        return max(0.0, float(header_value.strip()))
    except ValueError:
        return None
