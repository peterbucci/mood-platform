from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.fitbit_data_client import build_fitbit_client
from app.services.request_fulfillment_service import RequestFulfillmentService


@dataclass
class _Request:
    id: str
    user_id: str
    created_at: int
    status: str
    feature_id: str | None = None
    client_features_json: str | None = None


class _InMemoryRepository:
    def __init__(self, request: _Request) -> None:
        self.request = request
        self.saved_payload: dict[str, Any] | None = None

    def list_pending_requests(self, *, limit: int = 100) -> list[_Request]:  # noqa: ARG002
        if self.request.status == "pending" and self.request.feature_id is None:
            return [self.request]
        return []

    def list_pending_requests_by_user(
        self,
        *,
        user_id: str,
        limit: int = 100,  # noqa: ARG002
    ) -> list[_Request]:
        if (
            self.request.user_id == user_id
            and self.request.status == "pending"
            and self.request.feature_id is None
        ):
            return [self.request]
        return []

    def get_request_by_id(self, *, request_id: str) -> _Request | None:
        if self.request.id == request_id:
            return self.request
        return None

    def fulfill_request_if_pending(
        self,
        *,
        request_id: str,
        user_id: str,
        feature_source: str,  # noqa: ARG002
        feature_payload: dict[str, Any],
        source_timezone: str | None = None,  # noqa: ARG002
        window_start=None,  # noqa: ANN001, ARG002
        window_end=None,  # noqa: ANN001, ARG002
    ) -> str | None:
        if (
            self.request.id != request_id
            or self.request.user_id != user_id
            or self.request.status != "pending"
            or self.request.feature_id is not None
        ):
            return None

        self.saved_payload = feature_payload
        self.request.status = "fulfilled"
        self.request.feature_id = "feature-1"
        return self.request.feature_id


class _UnusedSessionFactory:
    def __call__(self):  # noqa: ANN204
        raise RuntimeError("Session factory should not be used in static payload mode.")


def test_request_fulfillment_uses_static_fitbit_payload(monkeypatch) -> None:
    monkeypatch.setenv("FITBIT_STATIC_PAYLOAD", '{"steps":{"count":4321}}')
    request = _Request(
        id="req-static-1",
        user_id="00000000-0000-0000-0000-00000000ab01",
        created_at=1772684306,
        status="pending",
    )
    repository = _InMemoryRepository(request)
    fitbit_client = build_fitbit_client(session_factory=_UnusedSessionFactory())  # type: ignore[arg-type]

    service = RequestFulfillmentService(
        repository=repository,  # type: ignore[arg-type]
        fitbit_client=fitbit_client,  # type: ignore[arg-type]
    )

    stats = service.process_pending_requests()

    assert stats.processed == 1
    assert stats.fulfilled == 1
    assert repository.saved_payload is not None
    assert repository.saved_payload["steps"] == {"count": 4321}


class _ForbiddenBreathingFitbitClient:
    def fetch_user_data(self, *, user_id: str) -> dict[str, Any]:
        del user_id
        return {
            "steps": {"count": 1200},
            "breathing_rate": {
                "__missing": True,
                "reason": "forbidden_scope",
                "raw_status": 403,
                "payload": {},
            },
        }


def test_request_fulfillment_succeeds_with_forbidden_breathing_rate() -> None:
    request = _Request(
        id="req-forbidden-br-1",
        user_id="00000000-0000-0000-0000-00000000ab02",
        created_at=1772684306,
        status="pending",
    )
    repository = _InMemoryRepository(request)
    service = RequestFulfillmentService(
        repository=repository,  # type: ignore[arg-type]
        fitbit_client=_ForbiddenBreathingFitbitClient(),  # type: ignore[arg-type]
    )

    stats = service.process_pending_requests()

    assert stats.processed == 1
    assert stats.fulfilled == 1
    assert repository.saved_payload is not None
    assert "missing_breathing_rate_forbidden" in repository.saved_payload["notes"]
