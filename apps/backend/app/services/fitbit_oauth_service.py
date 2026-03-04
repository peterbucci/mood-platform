from __future__ import annotations

import base64
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

from app.repositories.fitbit_oauth_repository import (
    FitbitOAuthRepository,
    FitbitOAuthRepositoryError,
)
from app.settings import Settings

STATE_TTL_MINUTES = 10


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


class FitbitOAuthService:
    def __init__(
        self,
        *,
        repository: FitbitOAuthRepository,
        settings: Settings,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._http_client = http_client

    def start_authorization(self, *, user_id: uuid.UUID) -> str:
        self._assert_oauth_configured()
        state = secrets.token_urlsafe(32)
        self._repository.create_state(
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

        state_valid = self._repository.consume_state(state=state, user_id=user_id)
        if not state_valid:
            raise FitbitOAuthStateError("Invalid or expired OAuth state.")

        token_payload = self.exchange_authorization_code(code=code)
        expires_at = datetime.now(tz=UTC) + timedelta(seconds=token_payload.expires_in)
        self._repository.upsert_connection(
            user_id=user_id,
            fitbit_user_id=token_payload.user_id,
            access_token=token_payload.access_token,
            refresh_token=token_payload.refresh_token,
            scope=token_payload.scope,
            expires_at=expires_at,
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

    def get_status(self, *, user_id: uuid.UUID) -> tuple[bool, datetime | None]:
        try:
            connection = self._repository.get_connection(user_id=user_id)
        except FitbitOAuthRepositoryError as exc:
            raise FitbitOAuthExchangeError("Failed to load OAuth connection status.") from exc

        if connection is None:
            return False, None
        return True, connection.expires_at

    def unlink(self, *, user_id: uuid.UUID) -> bool:
        try:
            return self._repository.delete_connection(user_id=user_id)
        except FitbitOAuthRepositoryError as exc:
            raise FitbitOAuthExchangeError("Failed to unlink OAuth connection.") from exc
