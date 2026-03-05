from __future__ import annotations

import httpx
from app.dependencies import get_fitbit_token_service
from app.main import app
from app.services.fitbit_api_client import FitbitApiClient
from fastapi.testclient import TestClient


class _DummyTokenService:
    def get_access_token(self, *, user_id):  # noqa: ANN001, ARG002
        return "token"

    def refresh_token(self, *, user_id):  # noqa: ANN001, ARG002
        return None


def test_fitbit_proxy_allows_supported_path_and_forwards_response(monkeypatch) -> None:
    def _mock_fitbit_fetch(
        self,  # noqa: ARG001
        *,
        user_id,  # noqa: ANN001, ARG002
        url: str,
        method: str = "GET",
        headers=None,  # noqa: ANN001, ARG002
        params=None,  # noqa: ANN001, ARG002
        json_payload=None,  # noqa: ANN001, ARG002
        data=None,  # noqa: ANN001, ARG002
        timeout: float = 10.0,  # noqa: ARG002
    ) -> httpx.Response:
        assert method == "GET"
        assert "/1/user/-/activities/date/2026-03-05.json" in url
        return httpx.Response(status_code=200, json={"ok": True})

    monkeypatch.setattr(FitbitApiClient, "fitbit_fetch", _mock_fitbit_fetch)
    app.dependency_overrides[get_fitbit_token_service] = lambda: _DummyTokenService()
    try:
        with TestClient(app) as client:
            response = client.get(
                "/fitbit/proxy",
                params={"path": "/1/user/-/activities/date/2026-03-05.json"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_fitbit_proxy_rejects_disallowed_paths() -> None:
    app.dependency_overrides[get_fitbit_token_service] = lambda: _DummyTokenService()
    try:
        with TestClient(app) as client:
            blocked_response = client.get("/fitbit/proxy", params={"path": "/oauth2/token"})
            invalid_prefix_response = client.get("/fitbit/proxy", params={"path": "/2/user/-/foo"})
    finally:
        app.dependency_overrides.clear()

    assert blocked_response.status_code == 400
    assert invalid_prefix_response.status_code == 400
