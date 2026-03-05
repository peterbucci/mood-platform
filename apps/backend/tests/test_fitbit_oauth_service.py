from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx
import pytest
from app.services.fitbit_api_client import FitbitApiClient
from app.services.fitbit_oauth_service import (
    FitbitOAuthExchangeError,
    FitbitOAuthService,
    FitbitTokenPayload,
)
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


def test_handle_callback_does_not_fail_when_subscription_registration_fails(monkeypatch) -> None:
    user_id = uuid.uuid4()
    expected_expiry = datetime(2026, 3, 5, 12, 0, tzinfo=UTC)

    class _StateRepo:
        def consume_state(self, *, state: str, user_id: uuid.UUID) -> bool:  # noqa: ARG002
            return True

    class _TokenService:
        def store_token(self, **kwargs):  # noqa: ANN003, ANN201
            _ = kwargs
            return expected_expiry

    service = FitbitOAuthService(
        state_repository=_StateRepo(),  # type: ignore[arg-type]
        token_service=_TokenService(),  # type: ignore[arg-type]
        settings=Settings(
            FITBIT_CLIENT_ID="client",
            FITBIT_CLIENT_SECRET="secret",
            FITBIT_REDIRECT_URI="https://example.test/callback",
        ),
    )

    monkeypatch.setattr(
        service,
        "exchange_authorization_code",
        lambda code: FitbitTokenPayload(  # noqa: ARG005
            access_token="access",
            refresh_token="refresh",
            expires_in=3600,
            scope="activity",
            user_id="fitbit-user",
        ),
    )

    def _raise_subscription_error(*, user_id: uuid.UUID) -> None:  # noqa: ARG001
        raise FitbitOAuthExchangeError("Failed to register Fitbit webhook subscription.")

    monkeypatch.setattr(service, "_register_webhook_subscription", _raise_subscription_error)

    expires_at = service.handle_callback(
        user_id=user_id,
        code="auth-code",
        state="state",
    )

    assert expires_at == expected_expiry
