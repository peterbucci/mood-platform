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
                )
                .on_conflict_do_update(
                    index_elements=[FitbitToken.user_id],
                    set_={
                        "fitbit_user_id": fitbit_user_id,
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_at": expires_at,
                        "scope": scope,
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

    def _ensure_user_exists(self, *, user_id: uuid.UUID) -> None:
        existing_user_id = self._session.execute(
            sa.select(User.id).where(User.id == user_id)
        ).scalar_one_or_none()
        if existing_user_id is None:
            self._session.add(User(id=user_id))
            self._session.flush()
