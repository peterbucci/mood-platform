from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Feature, FeatureRequest, Label


class FeatureDeleteWriteError(Exception):
    pass


class FeatureRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

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

    def get_feature_by_id_for_update(self, *, user_id: str, feature_id: str) -> Feature | None:
        result = self._session.execute(
            sa.select(Feature)
            .where(
                Feature.user_id == user_id,
                Feature.id == feature_id,
            )
            .with_for_update()
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

    def delete_feature_labels(
        self,
        *,
        user_id: str,
        feature_id: str,
        commit: bool = True,
    ) -> int:
        try:
            result = self._session.execute(
                sa.delete(Label).where(
                    Label.user_id == user_id,
                    Label.feature_id == feature_id,
                )
            )
            if commit:
                self._session.commit()
            return int(result.rowcount or 0)
        except IntegrityError as exc:
            self._session.rollback()
            raise FeatureDeleteWriteError("Failed to delete labels for feature.") from exc

    def null_requests_feature_reference(
        self,
        *,
        user_id: str,
        feature_id: str,
        commit: bool = True,
    ) -> int:
        # Keep the original request status unchanged while unlinking deleted features.
        try:
            result = self._session.execute(
                sa.update(FeatureRequest)
                .where(
                    FeatureRequest.user_id == user_id,
                    FeatureRequest.feature_id == feature_id,
                )
                .values(feature_id=None)
            )
            if commit:
                self._session.commit()
            return int(result.rowcount or 0)
        except IntegrityError as exc:
            self._session.rollback()
            raise FeatureDeleteWriteError("Failed to null request feature references.") from exc

    def delete_feature(
        self,
        *,
        user_id: str,
        feature_id: str,
        commit: bool = True,
    ) -> bool:
        try:
            result = self._session.execute(
                sa.delete(Feature).where(
                    Feature.user_id == user_id,
                    Feature.id == feature_id,
                )
            )
            if commit:
                self._session.commit()
            return int(result.rowcount or 0) == 1
        except IntegrityError as exc:
            self._session.rollback()
            raise FeatureDeleteWriteError("Failed to delete feature.") from exc
