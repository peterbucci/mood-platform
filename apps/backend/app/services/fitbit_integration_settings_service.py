from __future__ import annotations

from dataclasses import dataclass, replace

from app.db.models import IntegrationSettings
from app.repositories.integration_settings_repository import (
    IntegrationSettingsRepository,
    IntegrationSettingsRepositoryError,
)
from app.services.encryption_service import (
    EncryptionServiceConfigurationError,
    EncryptionServiceDecryptError,
    build_encryption_service,
    mask_secret,
)
from app.settings import DEFAULT_FITBIT_OAUTH_SCOPE, Settings


class FitbitIntegrationSettingsValidationError(Exception):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Invalid Fitbit integration settings.")
        self.errors = errors


class FitbitIntegrationSettingsServiceError(Exception):
    pass


@dataclass(frozen=True)
class FitbitIntegrationSettingsView:
    client_id: str
    client_secret_masked: str | None
    redirect_uri: str
    scope: str
    subscriber_id: str
    webhook_secret_masked: str | None
    has_client_secret: bool
    has_webhook_secret: bool


def _normalize_text(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


class FitbitIntegrationSettingsService:
    def __init__(
        self,
        repository: IntegrationSettingsRepository,
        *,
        encryption_key: str,
    ) -> None:
        self._repository = repository
        self._encryption_key = encryption_key

    def _get_encryption_service(self):
        try:
            return build_encryption_service(self._encryption_key)
        except EncryptionServiceConfigurationError as exc:
            raise FitbitIntegrationSettingsServiceError(str(exc)) from exc

    def _decrypt_secret(self, encrypted_value: str | None) -> str:
        normalized_value = _normalize_text(encrypted_value)
        if not normalized_value:
            return ""

        try:
            return self._get_encryption_service().decrypt_value(normalized_value)
        except EncryptionServiceDecryptError as exc:
            raise FitbitIntegrationSettingsServiceError(
                "Failed to decrypt Fitbit integration settings."
            ) from exc

    def get_settings_view(self) -> FitbitIntegrationSettingsView:
        try:
            stored_settings = self._repository.get_settings()
        except IntegrationSettingsRepositoryError as exc:
            raise FitbitIntegrationSettingsServiceError(
                "Failed to load Fitbit integration settings."
            ) from exc
        return self._to_view(stored_settings)

    def get_runtime_settings(self, *, base_settings: Settings) -> Settings:
        try:
            stored_settings = self._repository.get_settings()
        except IntegrationSettingsRepositoryError as exc:
            raise FitbitIntegrationSettingsServiceError(
                "Failed to load Fitbit integration settings."
            ) from exc
        if stored_settings is None:
            return replace(
                base_settings,
                FITBIT_CLIENT_ID="",
                FITBIT_CLIENT_SECRET="",
                FITBIT_REDIRECT_URI="",
                FITBIT_OAUTH_SCOPE=DEFAULT_FITBIT_OAUTH_SCOPE,
                FITBIT_SUBSCRIBER_ID="",
                FITBIT_WEBHOOK_SECRET="",
            )

        normalized_scope = _normalize_text(stored_settings.fitbit_oauth_scope)
        return replace(
            base_settings,
            FITBIT_CLIENT_ID=_normalize_text(stored_settings.fitbit_client_id),
            FITBIT_CLIENT_SECRET=self._decrypt_secret(
                stored_settings.fitbit_client_secret_encrypted
            ),
            FITBIT_REDIRECT_URI=_normalize_text(stored_settings.fitbit_redirect_uri),
            FITBIT_OAUTH_SCOPE=normalized_scope or DEFAULT_FITBIT_OAUTH_SCOPE,
            FITBIT_SUBSCRIBER_ID=_normalize_text(stored_settings.fitbit_subscriber_id),
            FITBIT_WEBHOOK_SECRET=self._decrypt_secret(
                stored_settings.fitbit_webhook_secret_encrypted
            ),
        )

    def upsert_settings(
        self,
        *,
        client_id: str,
        client_secret: str | None,
        redirect_uri: str,
        scope: str | None,
        subscriber_id: str | None,
        webhook_secret: str | None,
    ) -> FitbitIntegrationSettingsView:
        try:
            stored_settings = self._repository.get_settings()
        except IntegrationSettingsRepositoryError as exc:
            raise FitbitIntegrationSettingsServiceError(
                "Failed to load Fitbit integration settings."
            ) from exc

        normalized_client_id = _normalize_text(client_id)
        normalized_redirect_uri = _normalize_text(redirect_uri)
        normalized_client_secret = None if client_secret is None else _normalize_text(client_secret)
        normalized_scope = None if scope is None else _normalize_text(scope)
        normalized_subscriber_id = None if subscriber_id is None else _normalize_text(subscriber_id)
        normalized_webhook_secret = (
            None if webhook_secret is None else _normalize_text(webhook_secret)
        )
        current_client_secret_encrypted = (
            _normalize_text(stored_settings.fitbit_client_secret_encrypted)
            if stored_settings is not None
            else ""
        )
        current_webhook_secret_encrypted = (
            _normalize_text(stored_settings.fitbit_webhook_secret_encrypted)
            if stored_settings is not None
            else ""
        )

        errors: dict[str, str] = {}
        if not normalized_client_id:
            errors["clientId"] = "Client ID is required."
        if not normalized_redirect_uri:
            errors["redirectUri"] = "Redirect URI is required."

        if normalized_client_secret:
            client_secret_encrypted = self._get_encryption_service().encrypt_value(
                normalized_client_secret
            )
        else:
            client_secret_encrypted = current_client_secret_encrypted

        if not client_secret_encrypted:
            errors["clientSecret"] = "Client Secret is required."

        if errors:
            raise FitbitIntegrationSettingsValidationError(errors)

        if normalized_webhook_secret:
            webhook_secret_encrypted = self._get_encryption_service().encrypt_value(
                normalized_webhook_secret
            )
        else:
            webhook_secret_encrypted = current_webhook_secret_encrypted or None

        try:
            updated_settings = self._repository.upsert_fitbit_settings(
                client_id=normalized_client_id,
                client_secret_encrypted=client_secret_encrypted,
                redirect_uri=normalized_redirect_uri,
                scope=normalized_scope or None,
                subscriber_id=normalized_subscriber_id or None,
                webhook_secret_encrypted=webhook_secret_encrypted,
            )
        except IntegrationSettingsRepositoryError as exc:
            raise FitbitIntegrationSettingsServiceError(
                "Failed to store Fitbit integration settings."
            ) from exc

        return self._to_view(updated_settings)

    def _to_view(
        self, stored_settings: IntegrationSettings | None
    ) -> FitbitIntegrationSettingsView:
        if stored_settings is None:
            return FitbitIntegrationSettingsView(
                client_id="",
                client_secret_masked=None,
                redirect_uri="",
                scope=DEFAULT_FITBIT_OAUTH_SCOPE,
                subscriber_id="",
                webhook_secret_masked=None,
                has_client_secret=False,
                has_webhook_secret=False,
            )

        normalized_client_secret = self._decrypt_secret(
            stored_settings.fitbit_client_secret_encrypted
        )
        normalized_webhook_secret = self._decrypt_secret(
            stored_settings.fitbit_webhook_secret_encrypted
        )
        normalized_scope = _normalize_text(stored_settings.fitbit_oauth_scope)

        return FitbitIntegrationSettingsView(
            client_id=_normalize_text(stored_settings.fitbit_client_id),
            client_secret_masked=mask_secret(normalized_client_secret),
            redirect_uri=_normalize_text(stored_settings.fitbit_redirect_uri),
            scope=normalized_scope or DEFAULT_FITBIT_OAUTH_SCOPE,
            subscriber_id=_normalize_text(stored_settings.fitbit_subscriber_id),
            webhook_secret_masked=mask_secret(normalized_webhook_secret),
            has_client_secret=bool(normalized_client_secret),
            has_webhook_secret=bool(normalized_webhook_secret),
        )
