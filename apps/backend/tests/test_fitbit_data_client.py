from __future__ import annotations

import uuid

import httpx
import pytest
from app.services.fitbit_data_client import (
    FitbitAuthorizationError,
    FitbitRateLimitError,
    FitbitSignalPullClient,
    StaticFitbitPayloadClient,
    build_fitbit_client,
)


class _UnusedSessionFactory:
    def __call__(self):
        raise RuntimeError("Session factory is not used in this unit test.")


class _StubTokenService:
    def __init__(self) -> None:
        self.mark_calls: list[tuple[uuid.UUID, bool]] = []

    def mark_needs_reauth(self, *, user_id: uuid.UUID, required: bool) -> None:
        self.mark_calls.append((user_id, required))


def test_fetch_signal_returns_missing_for_not_found_rate_limit_and_5xx() -> None:
    client = FitbitSignalPullClient(session_factory=_UnusedSessionFactory())  # type: ignore[arg-type]

    not_found = client._fetch_signal(  # noqa: SLF001
        signal_name="spo2",
        fetch_fn=lambda: httpx.Response(404, json={"errors": []}),
    )
    assert not_found["__missing"] is True
    assert not_found["reason"] == "not_found"
    assert not_found["raw_status"] == 404
    assert isinstance(not_found["payload"], dict)

    with pytest.raises(FitbitRateLimitError):
        client._fetch_signal(  # noqa: SLF001
            signal_name="spo2",
            fetch_fn=lambda: httpx.Response(429, json={"errors": []}),
        )

    upstream_error = client._fetch_signal(  # noqa: SLF001
        signal_name="spo2",
        fetch_fn=lambda: httpx.Response(503, json={"errors": []}),
    )
    assert upstream_error["__missing"] is True
    assert upstream_error["reason"] == "upstream_error"
    assert upstream_error["raw_status"] == 503
    assert isinstance(upstream_error["payload"], dict)


def test_fetch_signal_raises_on_auth_errors() -> None:
    client = FitbitSignalPullClient(session_factory=_UnusedSessionFactory())  # type: ignore[arg-type]
    with pytest.raises(FitbitAuthorizationError):
        client._fetch_signal(  # noqa: SLF001
            signal_name="sleep",
            fetch_fn=lambda: httpx.Response(401, json={"errors": []}),
        )


def test_fetch_signal_marks_reauth_on_scope_forbidden() -> None:
    client = FitbitSignalPullClient(session_factory=_UnusedSessionFactory())  # type: ignore[arg-type]
    token_service = _StubTokenService()
    user_id = uuid.UUID("00000000-0000-0000-0000-00000000cd01")

    missing = client._fetch_signal(  # noqa: SLF001
        signal_name="breathing_rate",
        fetch_fn=lambda: httpx.Response(
            403,
            json={"errors": [{"errorType": "insufficient_scope"}]},
        ),
        token_service=token_service,  # type: ignore[arg-type]
        user_id=user_id,
    )

    assert missing["__missing"] is True
    assert missing["reason"] == "forbidden_scope"
    assert token_service.mark_calls == [(user_id, True)]


def test_fetch_signal_returns_present_wrapper_for_valid_json() -> None:
    client = FitbitSignalPullClient(session_factory=_UnusedSessionFactory())  # type: ignore[arg-type]
    wrapped = client._fetch_signal(  # noqa: SLF001
        signal_name="hrv",
        fetch_fn=lambda: httpx.Response(200, json={"hrv": [{"value": {"dailyRmssd": 31.2}}]}),
    )
    assert wrapped["__missing"] is False
    assert wrapped["reason"] is None
    assert wrapped["raw_status"] == 200
    assert wrapped["payload"]["hrv"][0]["value"]["dailyRmssd"] == 31.2


def test_build_fitbit_client_prefers_static_payload_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("FITBIT_STATIC_PAYLOAD", '{"steps":{"count":1234}}')
    client = build_fitbit_client(session_factory=_UnusedSessionFactory())  # type: ignore[arg-type]
    assert isinstance(client, StaticFitbitPayloadClient)
    assert client.fetch_user_data(user_id="user-1") == {"steps": {"count": 1234}}
