from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import IntegrationSettings

SINGLETON_SETTINGS_ID = 1


class IntegrationSettingsRepositoryError(Exception):
    pass


class IntegrationSettingsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_settings(self) -> IntegrationSettings | None:
        try:
            return self._session.execute(
                sa.select(IntegrationSettings).where(
                    IntegrationSettings.id == SINGLETON_SETTINGS_ID
                )
            ).scalar_one_or_none()
        except SQLAlchemyError as exc:
            raise IntegrationSettingsRepositoryError(
                "Failed to load integration settings."
            ) from exc

    def upsert_fitbit_settings(
        self,
        *,
        client_id: str,
        client_secret_encrypted: str,
        redirect_uri: str,
        scope: str | None,
        subscriber_id: str | None,
        webhook_secret_encrypted: str | None,
    ) -> IntegrationSettings:
        try:
            self._session.execute(
                insert(IntegrationSettings)
                .values(
                    id=SINGLETON_SETTINGS_ID,
                    fitbit_client_id=client_id,
                    fitbit_client_secret_encrypted=client_secret_encrypted,
                    fitbit_redirect_uri=redirect_uri,
                    fitbit_oauth_scope=scope,
                    fitbit_subscriber_id=subscriber_id,
                    fitbit_webhook_secret_encrypted=webhook_secret_encrypted,
                )
                .on_conflict_do_update(
                    index_elements=[IntegrationSettings.id],
                    set_={
                        "fitbit_client_id": client_id,
                        "fitbit_client_secret_encrypted": client_secret_encrypted,
                        "fitbit_redirect_uri": redirect_uri,
                        "fitbit_oauth_scope": scope,
                        "fitbit_subscriber_id": subscriber_id,
                        "fitbit_webhook_secret_encrypted": webhook_secret_encrypted,
                        "updated_at": sa.func.now(),
                    },
                )
            )
            self._session.commit()
            self._session.expire_all()
            stored_settings = self.get_settings()
            if stored_settings is None:
                raise IntegrationSettingsRepositoryError("Fitbit settings were not persisted.")
            return stored_settings
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise IntegrationSettingsRepositoryError(
                "Failed to store integration settings."
            ) from exc
