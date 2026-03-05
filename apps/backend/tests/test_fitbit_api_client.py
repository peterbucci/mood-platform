from __future__ import annotations

import uuid
from dataclasses import dataclass

import httpx
from app.services.fitbit_api_client import FitbitApiClient


@dataclass
class _FakeToken:
    access_token: str


class _FakeTokenService:
    def __init__(self) -> None:
        self._token = _FakeToken(access_token="access-old")
        self.refresh_calls = 0
        self.get_access_token_calls = 0

    def get_access_token(self, *, user_id: uuid.UUID) -> str:
        _ = user_id
        self.get_access_token_calls += 1
        return self._token.access_token

    def refresh_token(self, *, user_id: uuid.UUID) -> _FakeToken:
        _ = user_id
        self.refresh_calls += 1
        self._token = _FakeToken(access_token="access-new")
        return self._token


def test_fitbit_fetch_refreshes_once_and_retries_on_401() -> None:
    user_id = uuid.UUID("00000000-0000-0000-0000-00000000ca01")
    token_service = _FakeTokenService()
    auth_headers: list[str] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        auth_headers.append(request.headers["Authorization"])
        if len(auth_headers) == 1:
            return httpx.Response(401, json={"errors": ["unauthorized"]})
        return httpx.Response(200, json={"ok": True})

    with httpx.Client(transport=httpx.MockTransport(_handler)) as http_client:
        client = FitbitApiClient(token_service=token_service, http_client=http_client)
        response = client.fitbit_fetch(
            user_id=user_id, url="https://api.fitbit.com/1/user/-/profile"
        )

    assert response.status_code == 200
    assert token_service.refresh_calls == 1
    assert auth_headers == ["Bearer access-old", "Bearer access-new"]


def test_fitbit_fetch_does_not_retry_more_than_once() -> None:
    user_id = uuid.UUID("00000000-0000-0000-0000-00000000ca02")
    token_service = _FakeTokenService()
    auth_headers: list[str] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        auth_headers.append(request.headers["Authorization"])
        return httpx.Response(401, json={"errors": ["unauthorized"]})

    with httpx.Client(transport=httpx.MockTransport(_handler)) as http_client:
        client = FitbitApiClient(token_service=token_service, http_client=http_client)
        response = client.fitbit_fetch(user_id=user_id, url="https://api.fitbit.com/1/user/-/sleep")

    assert response.status_code == 401
    assert token_service.refresh_calls == 1
    assert len(auth_headers) == 2


def test_fitbit_fetch_is_fail_fast_on_429() -> None:
    user_id = uuid.UUID("00000000-0000-0000-0000-00000000ca03")
    token_service = _FakeTokenService()
    request_count = 0

    def _handler(_request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(429, headers={"Retry-After": "2"})

    with httpx.Client(transport=httpx.MockTransport(_handler)) as http_client:
        client = FitbitApiClient(
            token_service=token_service,
            http_client=http_client,
        )
        response = client.fitbit_fetch(
            user_id=user_id,
            url="https://api.fitbit.com/1/user/-/activities/date/2026-03-05.json",
        )

    assert response.status_code == 429
    assert request_count == 1


def test_fitbit_endpoint_helpers_include_breathing_all_and_spo2_range_paths() -> None:
    user_id = uuid.UUID("00000000-0000-0000-0000-00000000ca04")
    token_service = _FakeTokenService()
    seen_paths: list[str] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(str(request.url.path))
        return httpx.Response(200, json={"ok": True})

    with httpx.Client(transport=httpx.MockTransport(_handler)) as http_client:
        client = FitbitApiClient(token_service=token_service, http_client=http_client)
        client.fetch_breathing_rate_all(user_id=user_id, date_iso="2026-03-05")
        client.fetch_spo2_range(
            user_id=user_id,
            start_date_iso="2026-02-27",
            end_date_iso="2026-03-05",
        )

    assert seen_paths == [
        "/1/user/-/br/date/2026-03-05/all.json",
        "/1/user/-/spo2/date/2026-02-27/2026-03-05.json",
    ]


def test_fetch_user_profile_uses_profile_endpoint() -> None:
    user_id = uuid.UUID("00000000-0000-0000-0000-00000000ca05")
    token_service = _FakeTokenService()
    seen_paths: list[str] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(str(request.url.path))
        return httpx.Response(200, json={"user": {"timezone": "America/New_York"}})

    with httpx.Client(transport=httpx.MockTransport(_handler)) as http_client:
        client = FitbitApiClient(token_service=token_service, http_client=http_client)
        response = client.fetch_user_profile(user_id=user_id)

    assert response.status_code == 200
    assert seen_paths == ["/1/user/-/profile.json"]
