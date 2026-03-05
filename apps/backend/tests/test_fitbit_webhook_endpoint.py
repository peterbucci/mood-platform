from __future__ import annotations

from app.main import app
from fastapi.testclient import TestClient


def test_fitbit_webhook_returns_verification_challenge_as_plain_text() -> None:
    with TestClient(app) as client:
        response = client.get("/fitbit/webhook", params={"verify": "abc123"})

    assert response.status_code == 200
    assert response.text == "abc123"
    assert response.headers["content-type"].startswith("text/plain")


def test_fitbit_webhook_returns_400_when_verification_challenge_missing() -> None:
    with TestClient(app) as client:
        response = client.get("/fitbit/webhook")

    assert response.status_code == 400
    assert response.json() == {"detail": "Missing verification challenge"}


def test_fitbit_webhook_endpoint_is_visible_in_openapi() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()
    assert "/fitbit/webhook" in openapi_spec["paths"]
    assert "get" in openapi_spec["paths"]["/fitbit/webhook"]
