from __future__ import annotations

import uuid

import httpx
import pytest
from app.services.fitbit_data_client import (
    FitbitAuthorizationError,
    FitbitSignalPullClient,
    StaticFitbitPayloadClient,
    _normalize_timezone_blob,
    build_fitbit_client,
)
from app.settings import Settings


class _UnusedSessionFactory:
    def __call__(self):
        raise RuntimeError("Session factory is not used in this unit test.")


class _StubTokenService:
    def __init__(self) -> None:
        self.mark_calls: list[tuple[uuid.UUID, bool]] = []

    def mark_needs_reauth(self, *, user_id: uuid.UUID, required: bool) -> None:
        self.mark_calls.append((user_id, required))


def test_fetch_signal_returns_missing_for_not_found_rate_limit_and_5xx() -> None:
    client = FitbitSignalPullClient(  # type: ignore[arg-type]
        session_factory=_UnusedSessionFactory(),
        settings=_test_settings(max_retries=0),
    )

    not_found = client._fetch_signal(  # noqa: SLF001
        signal_name="spo2",
        fetch_fn=lambda: httpx.Response(404, json={"errors": []}),
    )
    assert not_found["__missing"] is True
    assert not_found["reason"] == "not_found"
    assert not_found["raw_status"] == 404
    assert isinstance(not_found["payload"], dict)

    rate_limited = client._fetch_signal(  # noqa: SLF001
        signal_name="spo2",
        fetch_fn=lambda: httpx.Response(429, json={"errors": []}),
    )
    assert rate_limited["__missing"] is True
    assert rate_limited["reason"] == "rate_limited"
    assert rate_limited["raw_status"] == 429

    upstream_error = client._fetch_signal(  # noqa: SLF001
        signal_name="spo2",
        fetch_fn=lambda: httpx.Response(503, json={"errors": []}),
    )
    assert upstream_error["__missing"] is True
    assert upstream_error["reason"] == "upstream_error"
    assert upstream_error["raw_status"] == 503
    assert isinstance(upstream_error["payload"], dict)


def test_fetch_signal_raises_on_auth_errors() -> None:
    client = FitbitSignalPullClient(  # type: ignore[arg-type]
        session_factory=_UnusedSessionFactory(),
        settings=_test_settings(max_retries=0),
    )
    with pytest.raises(FitbitAuthorizationError):
        client._fetch_signal(  # noqa: SLF001
            signal_name="sleep",
            fetch_fn=lambda: httpx.Response(401, json={"errors": []}),
        )


def test_fetch_signal_marks_reauth_on_scope_forbidden() -> None:
    client = FitbitSignalPullClient(  # type: ignore[arg-type]
        session_factory=_UnusedSessionFactory(),
        settings=_test_settings(max_retries=0, forbidden_cache_seconds=1),
    )
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
    client = FitbitSignalPullClient(  # type: ignore[arg-type]
        session_factory=_UnusedSessionFactory(),
        settings=_test_settings(max_retries=0),
    )
    wrapped = client._fetch_signal(  # noqa: SLF001
        signal_name="hrv",
        fetch_fn=lambda: httpx.Response(200, json={"hrv": [{"value": {"dailyRmssd": 31.2}}]}),
    )
    assert wrapped["__missing"] is False
    assert wrapped["reason"] is None
    assert wrapped["raw_status"] == 200
    assert wrapped["payload"]["hrv"][0]["value"]["dailyRmssd"] == 31.2


def test_fetch_signal_retries_after_read_timeout_and_succeeds(monkeypatch) -> None:
    monkeypatch.setattr("app.services.fitbit_data_client.time.sleep", lambda _: None)
    client = FitbitSignalPullClient(  # type: ignore[arg-type]
        session_factory=_UnusedSessionFactory(),
        settings=_test_settings(max_retries=1, backoff_base_seconds=0.01),
    )
    attempts = 0

    def _fetch_fn() -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadTimeout(
                "read timed out",
                request=httpx.Request(
                    "GET", "https://api.fitbit.com/1/user/-/hrv/date/2026-03-05/all.json"
                ),
            )
        return httpx.Response(200, json={"hrv": [{"value": {"dailyRmssd": 28.1}}]})

    wrapped = client._fetch_signal(  # noqa: SLF001
        signal_name="hrv_all",
        fetch_fn=_fetch_fn,
    )

    assert attempts == 2
    assert wrapped["__missing"] is False
    assert wrapped["raw_status"] == 200


def test_fetch_signal_retries_429_with_retry_after(monkeypatch) -> None:
    slept_for: list[float] = []
    monkeypatch.setattr("app.services.fitbit_data_client.time.sleep", slept_for.append)
    client = FitbitSignalPullClient(  # type: ignore[arg-type]
        session_factory=_UnusedSessionFactory(),
        settings=_test_settings(max_retries=1, backoff_base_seconds=0.01),
    )
    attempts = 0

    def _fetch_fn() -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, json={"ok": True})

    wrapped = client._fetch_signal(  # noqa: SLF001
        signal_name="steps_intraday",
        fetch_fn=_fetch_fn,
    )

    assert attempts == 2
    assert wrapped["__missing"] is False
    assert slept_for == [2.0]


def test_fetch_signal_uses_forbidden_capability_cache() -> None:
    client = FitbitSignalPullClient(  # type: ignore[arg-type]
        session_factory=_UnusedSessionFactory(),
        settings=_test_settings(max_retries=0, forbidden_cache_seconds=3600),
    )
    user_id = uuid.UUID("00000000-0000-0000-0000-00000000cd02")
    first = client._fetch_signal(  # noqa: SLF001
        signal_name="spo2",
        fetch_fn=lambda: httpx.Response(403, json={"errors": []}),
        user_id=user_id,
    )
    second = client._fetch_signal(  # noqa: SLF001
        signal_name="spo2",
        fetch_fn=lambda: pytest.fail("fetch_fn should not be called due to forbidden cache"),
        user_id=user_id,
    )

    assert first["reason"] == "forbidden"
    assert second["reason"] == "forbidden_cached"


def test_build_fitbit_client_prefers_static_payload_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("FITBIT_STATIC_PAYLOAD", '{"steps":{"count":1234}}')
    client = build_fitbit_client(session_factory=_UnusedSessionFactory())  # type: ignore[arg-type]
    assert isinstance(client, StaticFitbitPayloadClient)
    assert client.fetch_user_data(user_id="user-1") == {"steps": {"count": 1234}}


def test_fetch_user_timezone_uses_cached_fitbit_timezone(monkeypatch) -> None:
    client = FitbitSignalPullClient(  # type: ignore[arg-type]
        session_factory=_UnusedSessionFactory(),
        settings=_test_settings(max_retries=0, timezone_cache_ttl_seconds=3600),
    )
    calls = 0

    def _fake_fetch_timezone_signal(*, user_id: str) -> dict[str, object]:
        nonlocal calls
        calls += 1
        assert user_id == "00000000-0000-0000-0000-00000000cd03"
        return {
            "__missing": False,
            "reason": None,
            "raw_status": 200,
            "payload": {"user": {"timezone": "America/New_York"}},
        }

    monkeypatch.setattr(client, "_fetch_fitbit_timezone_signal", _fake_fetch_timezone_signal)

    first = client.fetch_user_timezone(user_id="00000000-0000-0000-0000-00000000cd03")
    second = client.fetch_user_timezone(user_id="00000000-0000-0000-0000-00000000cd03")

    assert calls == 1
    assert first["__missing"] is False
    assert first["payload"]["timezone"] == "America/New_York"
    assert second["__missing"] is False
    assert second["payload"]["timezone"] == "America/New_York"


def test_fetch_user_timezone_marks_invalid_fitbit_timezone() -> None:
    timezone_blob = _normalize_timezone_blob(
        {
            "__missing": False,
            "reason": None,
            "raw_status": 200,
            "payload": {"user": {"timezone": "Mars/OlympusMons"}},
        }
    )
    assert timezone_blob["__missing"] is True
    assert timezone_blob["reason"] == "timezone_invalid"


def test_fetch_user_timezone_maps_missing_signal_to_unavailable() -> None:
    timezone_blob = _normalize_timezone_blob(
        {
            "__missing": True,
            "reason": "rate_limited",
            "raw_status": 429,
            "payload": {},
        }
    )
    assert timezone_blob["__missing"] is True
    assert timezone_blob["reason"] == "timezone_unavailable"
    assert timezone_blob["raw_status"] == 429


def _test_settings(
    *,
    max_retries: int,
    backoff_base_seconds: float = 0.1,
    forbidden_cache_seconds: int = 3600,
    timezone_cache_ttl_seconds: int = 604800,
) -> Settings:
    return Settings(
        FITBIT_MAX_RETRIES=max_retries,
        FITBIT_BACKOFF_BASE_SECONDS=backoff_base_seconds,
        FITBIT_FORBIDDEN_CACHE_SECONDS=forbidden_cache_seconds,
        FITBIT_TIMEZONE_CACHE_TTL_SECONDS=timezone_cache_ttl_seconds,
        FITBIT_MIN_FETCH_INTERVAL_SECONDS=0.0,
        FITBIT_MAX_CONCURRENT_FETCHES=2,
    )
