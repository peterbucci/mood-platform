from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import FitbitToken, User


class FitbitTokenRepositoryError(Exception):
    pass


class FitbitTokenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_token(
        self,
        *,
        user_id: uuid.UUID,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
        scope: str,
        fitbit_user_id: str | None = None,
    ) -> None:
        try:
            self._ensure_user_exists(user_id=user_id)
            self._session.execute(
                insert(FitbitToken)
                .values(
                    user_id=user_id,
                    fitbit_user_id=fitbit_user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                    scope=scope,
                    needs_reauth=False,
                )
                .on_conflict_do_update(
                    index_elements=[FitbitToken.user_id],
                    set_={
                        "fitbit_user_id": fitbit_user_id,
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_at": expires_at,
                        "scope": scope,
                        "needs_reauth": False,
                        "updated_at": sa.func.now(),
                    },
                )
            )
            self._session.commit()
            self._session.expire_all()
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise FitbitTokenRepositoryError("Failed to upsert Fitbit token.") from exc

    def get_token(self, *, user_id: uuid.UUID) -> FitbitToken | None:
        try:
            return self._session.execute(
                sa.select(FitbitToken).where(FitbitToken.user_id == user_id)
            ).scalar_one_or_none()
        except SQLAlchemyError as exc:
            raise FitbitTokenRepositoryError("Failed to load Fitbit token.") from exc

    def delete_token(self, *, user_id: uuid.UUID) -> bool:
        try:
            deleted_user_id = self._session.execute(
                sa.delete(FitbitToken)
                .where(FitbitToken.user_id == user_id)
                .returning(FitbitToken.user_id)
            ).scalar_one_or_none()
            self._session.commit()
            return deleted_user_id is not None
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise FitbitTokenRepositoryError("Failed to delete Fitbit token.") from exc

    def get_user_id_by_fitbit_user_id(self, *, fitbit_user_id: str) -> uuid.UUID | None:
        try:
            return self._session.execute(
                sa.select(FitbitToken.user_id).where(FitbitToken.fitbit_user_id == fitbit_user_id)
            ).scalar_one_or_none()
        except SQLAlchemyError as exc:
            raise FitbitTokenRepositoryError(
                "Failed to load internal user by Fitbit user id."
            ) from exc

    def set_needs_reauth(self, *, user_id: uuid.UUID, needs_reauth: bool) -> None:
        try:
            self._session.execute(
                sa.update(FitbitToken)
                .where(FitbitToken.user_id == user_id)
                .values(
                    needs_reauth=needs_reauth,
                    updated_at=sa.func.now(),
                )
            )
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise FitbitTokenRepositoryError("Failed to update Fitbit reauth flag.") from exc

    def is_reauth_required(self, *, user_id: uuid.UUID) -> bool:
        try:
            return bool(
                self._session.execute(
                    sa.select(FitbitToken.needs_reauth).where(FitbitToken.user_id == user_id)
                ).scalar_one_or_none()
            )
        except SQLAlchemyError as exc:
            raise FitbitTokenRepositoryError("Failed to load Fitbit reauth flag.") from exc

    def _ensure_user_exists(self, *, user_id: uuid.UUID) -> None:
        existing_user_id = self._session.execute(
            sa.select(User.id).where(User.id == user_id)
        ).scalar_one_or_none()
        if existing_user_id is None:
            self._session.add(User(id=user_id))
            self._session.flush()
