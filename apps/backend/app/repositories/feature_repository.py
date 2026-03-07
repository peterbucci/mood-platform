from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.models import Feature, Label


class FeatureRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_latest_feature(self, *, user_id: str) -> Feature | None:
        result = self._session.execute(
            sa.select(Feature)
            .where(Feature.user_id == user_id)
            .order_by(Feature.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    def get_feature_by_id(self, *, user_id: str, feature_id: str) -> Feature | None:
        result = self._session.execute(
            sa.select(Feature).where(
                Feature.user_id == user_id,
                Feature.id == feature_id,
            )
        )
        return result.scalar_one_or_none()

    def list_features(self, *, user_id: str, limit: int, offset: int) -> list[Feature]:
        result = self._session.execute(
            sa.select(Feature)
            .where(Feature.user_id == user_id)
            .order_by(Feature.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    def get_latest_label_for_feature(self, *, user_id: str, feature_id: str) -> Label | None:
        result = self._session.execute(
            sa.select(Label)
            .where(
                Label.user_id == user_id,
                Label.feature_id == feature_id,
            )
            .order_by(Label.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
