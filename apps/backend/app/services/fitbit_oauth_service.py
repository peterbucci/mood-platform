from __future__ import annotations

import base64
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

from app.repositories.fitbit_oauth_repository import (
    FitbitOAuthRepository,
)
from app.services.fitbit_api_client import FitbitApiClient
from app.services.fitbit_token_service import FitbitTokenRefreshError, FitbitTokenService
from app.settings import Settings

STATE_TTL_MINUTES = 10
logger = logging.getLogger(__name__)


class FitbitOAuthConfigurationError(Exception):
    pass


class FitbitOAuthExchangeError(Exception):
    pass


class FitbitOAuthStateError(Exception):
    pass


@dataclass(frozen=True)
class FitbitTokenPayload:
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str
    user_id: str


@dataclass(frozen=True)
class FitbitOAuthStatus:
    connected: bool
    expires_at: datetime | None
    fitbit_user_id: str | None = None
    scopes: list[str] | None = None
    last_sync_at: datetime | None = None
    message: str | None = None


class FitbitOAuthService:
    def __init__(
        self,
        *,
        state_repository: FitbitOAuthRepository,
        token_service: FitbitTokenService,
        settings: Settings,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._state_repository = state_repository
        self._token_service = token_service
        self._settings = settings
        self._http_client = http_client

    def start_authorization(self, *, user_id: uuid.UUID) -> str:
        self._assert_oauth_configured()
        state = secrets.token_urlsafe(32)
        self._state_repository.create_state(
            state=state,
            user_id=user_id,
            expires_at=datetime.now(tz=UTC) + timedelta(minutes=STATE_TTL_MINUTES),
        )
        query = self._settings.fitbit_authorization_query(state=state)
        return f"{self._settings.FITBIT_AUTH_BASE_URL}?{query}"

    def handle_callback(
        self,
        *,
        user_id: uuid.UUID,
        code: str,
        state: str,
    ) -> datetime:
        self._assert_oauth_configured()

        state_valid = self._state_repository.consume_state(state=state, user_id=user_id)
        if not state_valid:
            raise FitbitOAuthStateError("Invalid or expired OAuth state.")

        token_payload = self.exchange_authorization_code(code=code)
        expires_at = self._token_service.store_token(
            user_id=user_id,
            fitbit_user_id=token_payload.user_id,
            access_token=token_payload.access_token,
            refresh_token=token_payload.refresh_token,
            scope=token_payload.scope,
            expires_in=token_payload.expires_in,
        )
        try:
            self._register_webhook_subscription(user_id=user_id)
        except FitbitOAuthExchangeError:
            # Keep OAuth callback non-blocking for token persistence; the worker/webhook
            # path can still function and subscription issues can be repaired separately.
            logger.warning(
                (
                    "OAuth token stored but Fitbit webhook subscription registration "
                    "failed for user %s."
                ),
                user_id,
                exc_info=True,
            )
        return expires_at

    def exchange_authorization_code(self, *, code: str) -> FitbitTokenPayload:
        self._assert_oauth_configured()
        if not code.strip():
            raise FitbitOAuthExchangeError("Authorization code is required.")

        token_response_payload = self._request_tokens(code=code)
        return self.parse_token_payload(token_response_payload)

    @staticmethod
    def parse_token_payload(payload: dict[str, object]) -> FitbitTokenPayload:
        try:
            access_token = str(payload["access_token"])
            refresh_token = str(payload["refresh_token"])
            expires_in = int(payload["expires_in"])
            scope = str(payload["scope"])
            user_id = str(payload["user_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise FitbitOAuthExchangeError("Invalid token payload returned by Fitbit.") from exc

        if not access_token or not refresh_token or not user_id:
            raise FitbitOAuthExchangeError("Token payload is missing required token values.")

        return FitbitTokenPayload(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            scope=scope,
            user_id=user_id,
        )

    def _request_tokens(self, *, code: str) -> dict[str, object]:
        encoded_credentials = base64.b64encode(
            f"{self._settings.FITBIT_CLIENT_ID}:{self._settings.FITBIT_CLIENT_SECRET}".encode()
        ).decode("utf-8")
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._settings.FITBIT_REDIRECT_URI,
        }

        try:
            if self._http_client is not None:
                response = self._http_client.post(
                    self._settings.FITBIT_TOKEN_URL,
                    headers=headers,
                    data=body,
                )
            else:
                with httpx.Client(timeout=10) as client:
                    response = client.post(
                        self._settings.FITBIT_TOKEN_URL,
                        headers=headers,
                        data=body,
                    )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise FitbitOAuthExchangeError("Failed to exchange OAuth code for tokens.") from exc

        if not isinstance(payload, dict):
            raise FitbitOAuthExchangeError("Token exchange response was not a JSON object.")
        return payload

    def _assert_oauth_configured(self) -> None:
        if (
            not self._settings.FITBIT_CLIENT_ID
            or not self._settings.FITBIT_CLIENT_SECRET
            or not self._settings.FITBIT_REDIRECT_URI
        ):
            raise FitbitOAuthConfigurationError(
                "Fitbit OAuth is not configured. Set FITBIT_CLIENT_ID, "
                "FITBIT_CLIENT_SECRET, and FITBIT_REDIRECT_URI."
            )

    def _register_webhook_subscription(self, *, user_id: uuid.UUID) -> None:
        subscriber_id = self._settings.FITBIT_SUBSCRIBER_ID.strip()
        if not subscriber_id:
            logger.warning(
                "Skipping Fitbit webhook subscription registration: no subscriber id set."
            )
            return

        api_client = FitbitApiClient(
            token_service=self._token_service,
            http_client=self._http_client,
        )
        try:
            response = api_client.register_activity_subscription(
                user_id=user_id,
                subscription_id="1",
                subscriber_id=subscriber_id,
            )
        except httpx.HTTPError as exc:
            raise FitbitOAuthExchangeError(
                "Failed to register Fitbit webhook subscription."
            ) from exc

        if response.status_code == 409:
            logger.info("Fitbit webhook subscription already exists; treating as success.")
            return
        if 200 <= response.status_code < 300:
            logger.info("Fitbit webhook subscription registered.")
            return
        logger.warning(
            "Fitbit webhook subscription registration failed with status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise FitbitOAuthExchangeError("Failed to register Fitbit webhook subscription.")

    def get_status(self, *, user_id: uuid.UUID) -> FitbitOAuthStatus:
        try:
            stored_token = self._token_service.get_stored_token(user_id=user_id)
        except FitbitTokenRefreshError as exc:
            raise FitbitOAuthExchangeError("Failed to load OAuth connection status.") from exc

        if stored_token is None:
            return FitbitOAuthStatus(
                connected=False,
                expires_at=None,
                fitbit_user_id=None,
                scopes=None,
                last_sync_at=None,
                message="Fitbit account is not connected.",
            )
        scope_values = _split_scope_values(stored_token.scope)
        return FitbitOAuthStatus(
            connected=True,
            expires_at=stored_token.expires_at,
            fitbit_user_id=stored_token.fitbit_user_id,
            scopes=scope_values if scope_values else None,
            last_sync_at=stored_token.updated_at,
            message="Fitbit account is connected.",
        )

    def unlink(self, *, user_id: uuid.UUID) -> bool:
        try:
            return self._token_service.delete_stored_token(user_id=user_id)
        except FitbitTokenRefreshError as exc:
            raise FitbitOAuthExchangeError("Failed to unlink OAuth connection.") from exc


def _split_scope_values(raw_scope: str | None) -> list[str]:
    if not isinstance(raw_scope, str):
        return []
    return [scope for scope in raw_scope.split() if scope]
