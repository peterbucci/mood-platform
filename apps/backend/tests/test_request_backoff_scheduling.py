from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.services.request_fulfillment_service import RequestFulfillmentService


@dataclass
class _Request:
    id: str
    user_id: str
    created_at: int
    status: str
    feature_id: str | None = None
    attempts: int = 0
    next_attempt_at: int | None = None
    last_error_code: int | None = None
    last_error_signal: str | None = None


class _FailingFitbitClient:
    def fetch_user_data(self, *, user_id: str) -> dict[str, Any]:
        del user_id
        raise ConnectionError("network")


class _RateLimitedError(Exception):
    def __init__(self) -> None:
        super().__init__("rate limited")
        self.status_code = 429
        self.signal_name = "activity_summary"


class _RateLimitedFitbitClient:
    def fetch_user_data(self, *, user_id: str) -> dict[str, Any]:
        del user_id
        raise _RateLimitedError()


class _RetryAwareRepository:
    def __init__(self, request: _Request) -> None:
        self._request = request

    def list_pending_requests(self, *, limit: int = 100) -> list[_Request]:  # noqa: ARG002
        if self._request.status != "pending" or self._request.feature_id is not None:
            return []
        now_ts = int(datetime.now(tz=UTC).timestamp())
        if self._request.next_attempt_at is not None and self._request.next_attempt_at > now_ts:
            return []
        return [self._request]

    def list_pending_requests_by_user(
        self,
        *,
        user_id: str,
        limit: int = 100,  # noqa: ARG002
    ) -> list[_Request]:
        if self._request.user_id != user_id:
            return []
        return self.list_pending_requests()

    def get_request_by_id(self, *, request_id: str) -> _Request | None:
        if self._request.id == request_id:
            return self._request
        return None

    def fulfill_request_if_pending(
        self,
        *,
        request_id: str,  # noqa: ARG002
        user_id: str,  # noqa: ARG002
        feature_source: str,  # noqa: ARG002
        feature_payload: dict[str, Any],  # noqa: ARG002
    ) -> str | None:
        return None

    def schedule_retry_if_pending(
        self,
        *,
        request_id: str,
        user_id: str,
        delay_seconds: float,
        error_code: int | None,
        error_signal: str | None,
    ) -> bool:
        if self._request.id != request_id or self._request.user_id != user_id:
            return False
        now_ts = int(datetime.now(tz=UTC).timestamp())
        self._request.attempts += 1
        self._request.next_attempt_at = now_ts + int(delay_seconds)
        self._request.last_error_code = error_code
        self._request.last_error_signal = error_signal
        return True


def test_failed_request_is_scheduled_and_not_immediately_retried() -> None:
    request = _Request(
        id="req-retry-1",
        user_id="00000000-0000-0000-0000-00000000ba01",
        created_at=1772684306,
        status="pending",
    )
    repository = _RetryAwareRepository(request=request)
    service = RequestFulfillmentService(
        repository=repository,  # type: ignore[arg-type]
        fitbit_client=_FailingFitbitClient(),  # type: ignore[arg-type]
        request_retry_backoff_base_seconds=60.0,
        backoff_seconds=(),
    )

    first_stats = service.process_pending_requests()
    second_stats = service.process_pending_requests()

    assert first_stats.processed == 1
    assert first_stats.failed == 1
    assert request.attempts == 1
    assert request.next_attempt_at is not None
    assert request.next_attempt_at > int(datetime.now(tz=UTC).timestamp())
    assert second_stats.processed == 0


def test_rate_limited_request_is_scheduled_and_not_immediately_retried() -> None:
    request = _Request(
        id="req-retry-429-1",
        user_id="00000000-0000-0000-0000-00000000ba02",
        created_at=1772684306,
        status="pending",
    )
    repository = _RetryAwareRepository(request=request)
    service = RequestFulfillmentService(
        repository=repository,  # type: ignore[arg-type]
        fitbit_client=_RateLimitedFitbitClient(),  # type: ignore[arg-type]
        request_retry_backoff_base_seconds=45.0,
        backoff_seconds=(),
    )

    first_stats = service.process_pending_requests()
    second_stats = service.process_pending_requests()

    assert first_stats.processed == 1
    assert first_stats.failed == 1
    assert request.attempts == 1
    assert request.last_error_signal == "activity_summary"
    assert request.next_attempt_at is not None
    assert second_stats.processed == 0
