from __future__ import annotations

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import FitbitOAuthConnection, FitbitOAuthState, User


class FitbitOAuthRepositoryError(Exception):
    pass


class FitbitOAuthRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_state(self, *, state: str, user_id: uuid.UUID, expires_at: datetime) -> None:
        try:
            self._ensure_user_exists(user_id=user_id)
            state_row = FitbitOAuthState(
                state=state,
                user_id=user_id,
                expires_at=expires_at.astimezone(UTC),
            )
            self._session.add(state_row)
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise FitbitOAuthRepositoryError("Failed to create OAuth state.") from exc

    def consume_state(self, *, state: str, user_id: uuid.UUID) -> bool:
        try:
            deleted_state = self._session.execute(
                sa.delete(FitbitOAuthState)
                .where(
                    FitbitOAuthState.state == state,
                    FitbitOAuthState.user_id == user_id,
                    FitbitOAuthState.expires_at >= sa.func.now(),
                )
                .returning(FitbitOAuthState.state)
            ).scalar_one_or_none()
            self._session.commit()
            return deleted_state is not None
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise FitbitOAuthRepositoryError("Failed to consume OAuth state.") from exc

    def upsert_connection(
        self,
        *,
        user_id: uuid.UUID,
        fitbit_user_id: str,
        access_token: str,
        refresh_token: str,
        scope: str,
        expires_at: datetime,
    ) -> None:
        try:
            self._ensure_user_exists(user_id=user_id)
            self._session.execute(
                insert(FitbitOAuthConnection)
                .values(
                    user_id=user_id,
                    fitbit_user_id=fitbit_user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    scope=scope,
                    expires_at=expires_at.astimezone(UTC),
                )
                .on_conflict_do_update(
                    index_elements=[FitbitOAuthConnection.user_id],
                    set_={
                        "fitbit_user_id": fitbit_user_id,
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "scope": scope,
                        "expires_at": expires_at.astimezone(UTC),
                        "updated_at": sa.func.now(),
                    },
                )
            )
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise FitbitOAuthRepositoryError("Failed to store OAuth connection.") from exc

    def get_connection(self, *, user_id: uuid.UUID) -> FitbitOAuthConnection | None:
        result = self._session.execute(
            sa.select(FitbitOAuthConnection).where(FitbitOAuthConnection.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def delete_connection(self, *, user_id: uuid.UUID) -> bool:
        try:
            deleted_user = self._session.execute(
                sa.delete(FitbitOAuthConnection)
                .where(FitbitOAuthConnection.user_id == user_id)
                .returning(FitbitOAuthConnection.user_id)
            ).scalar_one_or_none()
            self._session.commit()
            return deleted_user is not None
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise FitbitOAuthRepositoryError("Failed to delete OAuth connection.") from exc

    def _ensure_user_exists(self, *, user_id: uuid.UUID) -> None:
        existing_user_id = self._session.execute(
            sa.select(User.id).where(User.id == user_id)
        ).scalar_one_or_none()
        if existing_user_id is None:
            self._session.add(User(id=user_id))
            self._session.flush()
