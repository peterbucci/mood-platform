from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.models import Feature


class FeatureRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_feature_by_id(self, *, user_id: str, feature_id: str) -> Feature | None:
        result = self._session.execute(
            sa.select(Feature).where(
                Feature.user_id == user_id,
                Feature.id == feature_id,
            )
        )
        return result.scalar_one_or_none()
