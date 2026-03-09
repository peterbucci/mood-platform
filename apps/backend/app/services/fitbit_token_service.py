from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

from app.repositories.fitbit_token_repository import (
    FitbitTokenRepository,
    FitbitTokenRepositoryError,
)
from app.settings import Settings

DEFAULT_EXPIRY_SKEW_SECONDS = 60


class FitbitTokenNotConnectedError(Exception):
    pass


class FitbitTokenRefreshError(Exception):
    pass


class FitbitTokenConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class FitbitRefreshTokenPayload:
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str
    user_id: str | None


class FitbitTokenService:
    def __init__(
        self,
        *,
        repository: FitbitTokenRepository,
        settings: Settings,
        http_client: httpx.Client | None = None,
        default_expiry_skew_seconds: int = DEFAULT_EXPIRY_SKEW_SECONDS,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._http_client = http_client
        self._default_expiry_skew_seconds = default_expiry_skew_seconds

    @staticmethod
    def is_expired(
        expires_at: datetime,
        *,
        skew_seconds: int = DEFAULT_EXPIRY_SKEW_SECONDS,
    ) -> bool:
        return datetime.now(tz=UTC) + timedelta(seconds=skew_seconds) >= expires_at.astimezone(UTC)

    def get_access_token(self, *, user_id: uuid.UUID) -> str:
        token = self._get_required_token(user_id=user_id)
        if self.is_expired(token.expires_at, skew_seconds=self._default_expiry_skew_seconds):
            token = self.refresh_token(user_id=user_id)
        return token.access_token

    def store_token(
        self,
        *,
        user_id: uuid.UUID,
        fitbit_user_id: str | None,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        scope: str,
    ) -> datetime:
        expires_at = datetime.now(tz=UTC) + timedelta(seconds=expires_in)
        try:
            self._repository.upsert_token(
                user_id=user_id,
                fitbit_user_id=fitbit_user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                scope=scope,
                expires_at=expires_at,
            )
        except FitbitTokenRepositoryError as exc:
            raise FitbitTokenRefreshError("Failed to store Fitbit token.") from exc
        return expires_at

    def get_stored_token(self, *, user_id: uuid.UUID) -> object | None:
        try:
            return self._repository.get_token(user_id=user_id)
        except FitbitTokenRepositoryError as exc:
            raise FitbitTokenRefreshError("Failed to load Fitbit token.") from exc

    def delete_stored_token(self, *, user_id: uuid.UUID) -> bool:
        try:
            return self._repository.delete_token(user_id=user_id)
        except FitbitTokenRepositoryError as exc:
            raise FitbitTokenRefreshError("Failed to delete Fitbit token.") from exc

    def mark_needs_reauth(self, *, user_id: uuid.UUID, required: bool) -> None:
        try:
            self._repository.set_needs_reauth(user_id=user_id, needs_reauth=required)
        except FitbitTokenRepositoryError as exc:
            raise FitbitTokenRefreshError("Failed to update Fitbit reauth requirement.") from exc

    def is_reauth_required(self, *, user_id: uuid.UUID) -> bool:
        try:
            return self._repository.is_reauth_required(user_id=user_id)
        except FitbitTokenRepositoryError as exc:
            raise FitbitTokenRefreshError("Failed to check Fitbit reauth requirement.") from exc

    def refresh_token(self, *, user_id: uuid.UUID) -> object:
        self._assert_oauth_configured()

        current_token = self._get_required_token(user_id=user_id)
        refresh_payload = self._request_refresh_token(
            refresh_token=current_token.refresh_token,
        )
        parsed_payload = self.parse_refresh_payload(
            payload=refresh_payload,
            existing_scope=current_token.scope,
            existing_fitbit_user_id=current_token.fitbit_user_id,
            existing_refresh_token=current_token.refresh_token,
        )

        expires_at = datetime.now(tz=UTC) + timedelta(seconds=parsed_payload.expires_in)
        self._repository.upsert_token(
            user_id=user_id,
            fitbit_user_id=parsed_payload.user_id,
            access_token=parsed_payload.access_token,
            refresh_token=parsed_payload.refresh_token,
            scope=parsed_payload.scope,
            expires_at=expires_at,
        )
        refreshed_token = self._repository.get_token(user_id=user_id)
        if refreshed_token is None:
            raise FitbitTokenRefreshError("Token refresh succeeded but no token row was found.")
        return refreshed_token

    # Compatibility helper matching the story contract naming.
    def getAccessToken(self, user_id: uuid.UUID) -> str:  # noqa: N802
        return self.get_access_token(user_id=user_id)

    def _get_required_token(self, *, user_id: uuid.UUID) -> object:
        try:
            token = self._repository.get_token(user_id=user_id)
        except FitbitTokenRepositoryError as exc:
            raise FitbitTokenRefreshError("Failed to load Fitbit token.") from exc

        if token is None:
            raise FitbitTokenNotConnectedError("User does not have a connected Fitbit account.")
        return token

    @staticmethod
    def parse_refresh_payload(
        *,
        payload: dict[str, object],
        existing_scope: str,
        existing_fitbit_user_id: str | None,
        existing_refresh_token: str,
    ) -> FitbitRefreshTokenPayload:
        try:
            access_token = str(payload["access_token"])
            expires_in = int(payload["expires_in"])
        except (KeyError, TypeError, ValueError) as exc:
            raise FitbitTokenRefreshError(
                "Invalid token refresh payload returned by Fitbit."
            ) from exc

        if not access_token:
            raise FitbitTokenRefreshError("Token refresh payload is missing access token.")

        refresh_token = str(payload.get("refresh_token") or existing_refresh_token)
        if not refresh_token:
            raise FitbitTokenRefreshError("Token refresh payload is missing refresh token.")

        scope = str(payload.get("scope") or existing_scope)
        if not scope:
            raise FitbitTokenRefreshError("Token refresh payload is missing scope.")

        user_id = payload.get("user_id")
        if user_id is None:
            fitbit_user_id = existing_fitbit_user_id
        else:
            fitbit_user_id = str(user_id)

        return FitbitRefreshTokenPayload(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            scope=scope,
            user_id=fitbit_user_id,
        )

    def _request_refresh_token(self, *, refresh_token: str) -> dict[str, object]:
        if not refresh_token.strip():
            raise FitbitTokenRefreshError("Refresh token is required.")

        encoded_credentials = base64.b64encode(
            f"{self._settings.FITBIT_CLIENT_ID}:{self._settings.FITBIT_CLIENT_SECRET}".encode()
        ).decode("utf-8")
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
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
            raise FitbitTokenRefreshError("Failed to refresh Fitbit token.") from exc

        if not isinstance(payload, dict):
            raise FitbitTokenRefreshError("Token refresh response was not a JSON object.")
        return payload

    def _assert_oauth_configured(self) -> None:
        if not self._settings.FITBIT_CLIENT_ID or not self._settings.FITBIT_CLIENT_SECRET:
            raise FitbitTokenConfigurationError("Fitbit integration not configured.")
