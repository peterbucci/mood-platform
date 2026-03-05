from __future__ import annotations

import json
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


class _MultiRequestInMemoryRepository:
    def __init__(self, requests: list[_Request]) -> None:
        self.requests = requests
        self.saved_payloads_by_request: dict[str, dict[str, Any]] = {}

    def list_pending_requests(self, *, limit: int = 100) -> list[_Request]:  # noqa: ARG002
        return [
            request
            for request in self.requests
            if request.status == "pending" and request.feature_id is None
        ]

    def list_pending_requests_by_user(
        self,
        *,
        user_id: str,
        limit: int = 100,  # noqa: ARG002
    ) -> list[_Request]:
        return [
            request
            for request in self.requests
            if request.user_id == user_id
            and request.status == "pending"
            and request.feature_id is None
        ]

    def get_request_by_id(self, *, request_id: str) -> _Request | None:
        return next((request for request in self.requests if request.id == request_id), None)

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
        request = self.get_request_by_id(request_id=request_id)
        if request is None:
            return None
        if (
            request.user_id != user_id
            or request.status != "pending"
            or request.feature_id is not None
        ):
            return None
        self.saved_payloads_by_request[request_id] = feature_payload
        request.status = "fulfilled"
        request.feature_id = f"feature-{request_id}"
        return request.feature_id


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


class _TimezoneAwareFitbitClient:
    def __init__(
        self,
        *,
        timezone_blob: dict[str, Any],
        fitbit_payload: dict[str, Any] | None = None,
    ) -> None:
        self._timezone_blob = timezone_blob
        self._fitbit_payload = fitbit_payload or {"steps": {"count": 500}}
        self.fetch_user_timezone_calls = 0
        self.fetch_user_data_for_date_calls: list[dict[str, str]] = []

    def fetch_user_timezone(self, *, user_id: str) -> dict[str, Any]:
        self.fetch_user_timezone_calls += 1
        _ = user_id
        return dict(self._timezone_blob)

    def fetch_user_data_for_date(
        self,
        *,
        user_id: str,
        date_iso: str,
        night_date_iso: str,
        source_timezone: str,
    ) -> dict[str, Any]:
        self.fetch_user_data_for_date_calls.append(
            {
                "user_id": user_id,
                "date_iso": date_iso,
                "night_date_iso": night_date_iso,
                "source_timezone": source_timezone,
            }
        )
        return dict(self._fitbit_payload)


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


def test_request_fulfillment_prefers_fitbit_timezone_over_client_timezone() -> None:
    request = _Request(
        id="req-fitbit-timezone-1",
        user_id="00000000-0000-0000-0000-00000000ab03",
        created_at=1772721000,
        status="pending",
        client_features_json=json.dumps({"timezone": "UTC"}),
    )
    repository = _InMemoryRepository(request)
    fitbit_client = _TimezoneAwareFitbitClient(
        timezone_blob={
            "__missing": False,
            "reason": None,
            "raw_status": 200,
            "payload": {"timezone": "America/Los_Angeles"},
        }
    )
    service = RequestFulfillmentService(
        repository=repository,  # type: ignore[arg-type]
        fitbit_client=fitbit_client,  # type: ignore[arg-type]
    )

    stats = service.process_pending_requests()

    assert stats.fulfilled == 1
    assert fitbit_client.fetch_user_timezone_calls == 1
    assert (
        fitbit_client.fetch_user_data_for_date_calls[0]["source_timezone"] == "America/Los_Angeles"
    )
    assert repository.saved_payload is not None
    assert repository.saved_payload["meta"]["source_timezone"] == "America/Los_Angeles"
    assert "timezone_fallback_to_client" not in repository.saved_payload["notes"]


def test_falls_back_to_client_timezone_with_notes_when_fitbit_unavailable() -> None:
    request = _Request(
        id="req-fitbit-timezone-2",
        user_id="00000000-0000-0000-0000-00000000ab04",
        created_at=1772721000,
        status="pending",
        client_features_json=json.dumps({"timezone": "America/New_York"}),
    )
    repository = _InMemoryRepository(request)
    fitbit_client = _TimezoneAwareFitbitClient(
        timezone_blob={
            "__missing": True,
            "reason": "timezone_unavailable",
            "raw_status": 429,
            "payload": {},
        }
    )
    service = RequestFulfillmentService(
        repository=repository,  # type: ignore[arg-type]
        fitbit_client=fitbit_client,  # type: ignore[arg-type]
    )

    stats = service.process_pending_requests()

    assert stats.fulfilled == 1
    assert fitbit_client.fetch_user_data_for_date_calls[0]["source_timezone"] == "America/New_York"
    assert repository.saved_payload is not None
    assert "timezone_from_fitbit_unavailable" in repository.saved_payload["notes"]
    assert "timezone_fallback_to_client" in repository.saved_payload["notes"]


def test_request_fulfillment_falls_back_to_utc_when_fitbit_invalid_and_client_missing() -> None:
    request = _Request(
        id="req-fitbit-timezone-3",
        user_id="00000000-0000-0000-0000-00000000ab05",
        created_at=1772721000,
        status="pending",
    )
    repository = _InMemoryRepository(request)
    fitbit_client = _TimezoneAwareFitbitClient(
        timezone_blob={
            "__missing": True,
            "reason": "timezone_invalid",
            "raw_status": 200,
            "payload": {},
        }
    )
    service = RequestFulfillmentService(
        repository=repository,  # type: ignore[arg-type]
        fitbit_client=fitbit_client,  # type: ignore[arg-type]
    )

    stats = service.process_pending_requests()

    assert stats.fulfilled == 1
    assert fitbit_client.fetch_user_data_for_date_calls[0]["source_timezone"] == "UTC"
    assert repository.saved_payload is not None
    assert "timezone_from_fitbit_invalid" in repository.saved_payload["notes"]
    assert "timezone_fallback_to_utc" in repository.saved_payload["notes"]


def test_request_fulfillment_does_not_mix_day_boundaries_across_timezones() -> None:
    user_id = "00000000-0000-0000-0000-00000000ab06"
    created_at = 1772681400  # 2026-03-05 03:30:00 UTC
    requests = [
        _Request(
            id="req-timezone-west",
            user_id=user_id,
            created_at=created_at,
            status="pending",
            client_features_json=json.dumps({"timezone": "America/Los_Angeles"}),
        ),
        _Request(
            id="req-timezone-east",
            user_id=user_id,
            created_at=created_at,
            status="pending",
            client_features_json=json.dumps({"timezone": "Asia/Tokyo"}),
        ),
    ]
    repository = _MultiRequestInMemoryRepository(requests)
    fitbit_client = _TimezoneAwareFitbitClient(
        timezone_blob={
            "__missing": True,
            "reason": "timezone_unavailable",
            "raw_status": 429,
            "payload": {},
        }
    )
    service = RequestFulfillmentService(
        repository=repository,  # type: ignore[arg-type]
        fitbit_client=fitbit_client,  # type: ignore[arg-type]
    )

    stats = service.process_pending_requests()

    assert stats.fulfilled == 2
    assert len(fitbit_client.fetch_user_data_for_date_calls) == 2
    west_call = next(
        call
        for call in fitbit_client.fetch_user_data_for_date_calls
        if call["source_timezone"] == "America/Los_Angeles"
    )
    east_call = next(
        call
        for call in fitbit_client.fetch_user_data_for_date_calls
        if call["source_timezone"] == "Asia/Tokyo"
    )
    assert (
        west_call["date_iso"] != east_call["date_iso"]
        or west_call["night_date_iso"] != east_call["night_date_iso"]
    )
