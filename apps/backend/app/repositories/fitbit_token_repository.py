from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import FitbitToken


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
        raise NotImplementedError

    def get_token(self, *, user_id: uuid.UUID) -> FitbitToken | None:
        raise NotImplementedError

    def delete_token(self, *, user_id: uuid.UUID) -> bool:
        raise NotImplementedError
