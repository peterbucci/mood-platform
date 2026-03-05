from __future__ import annotations

import uuid

import httpx
import pytest
from app.services.fitbit_api_client import FitbitApiClient
from app.services.fitbit_oauth_service import FitbitOAuthExchangeError, FitbitOAuthService
from app.settings import Settings


def test_register_webhook_subscription_treats_409_as_success(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def _mock_register(
        self,  # noqa: ARG001
        *,
        user_id: uuid.UUID,  # noqa: ARG001
        subscription_id: str,
        subscriber_id: str,
    ) -> httpx.Response:
        captured["subscription_id"] = subscription_id
        captured["subscriber_id"] = subscriber_id
        return httpx.Response(status_code=409, json={"errors": []})

    monkeypatch.setattr(FitbitApiClient, "register_activity_subscription", _mock_register)

    service = FitbitOAuthService(
        state_repository=object(),  # type: ignore[arg-type]
        token_service=object(),  # type: ignore[arg-type]
        settings=Settings(FITBIT_SUBSCRIBER_ID="subscriber-1"),
    )
    service._register_webhook_subscription(user_id=uuid.uuid4())  # noqa: SLF001

    assert captured["subscription_id"] == "1"
    assert captured["subscriber_id"] == "subscriber-1"


def test_register_webhook_subscription_raises_for_non_success(monkeypatch) -> None:
    def _mock_register(
        self,  # noqa: ARG001
        *,
        user_id: uuid.UUID,  # noqa: ARG001
        subscription_id: str,  # noqa: ARG001
        subscriber_id: str,  # noqa: ARG001
    ) -> httpx.Response:
        return httpx.Response(status_code=500, json={"errors": []})

    monkeypatch.setattr(FitbitApiClient, "register_activity_subscription", _mock_register)

    service = FitbitOAuthService(
        state_repository=object(),  # type: ignore[arg-type]
        token_service=object(),  # type: ignore[arg-type]
        settings=Settings(FITBIT_SUBSCRIBER_ID="subscriber-1"),
    )

    with pytest.raises(FitbitOAuthExchangeError):
        service._register_webhook_subscription(user_id=uuid.uuid4())  # noqa: SLF001
