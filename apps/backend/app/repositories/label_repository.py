from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Feature, FeatureRequest, Label


class LabelFeatureNotFoundError(Exception):
    pass


class LabelRequestNotFoundError(Exception):
    pass


class LabelWriteError(Exception):
    pass


class LabelRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_label(
        self,
        *,
        user_id: str,
        feature_id: str,
        label: str | None,
        emotion_word: str,
        category: str,
    ) -> Label:
        feature_owner = self._session.execute(
            sa.select(Feature.user_id).where(
                Feature.id == feature_id,
                Feature.user_id == user_id,
            )
        ).scalar_one_or_none()
        if feature_owner is None:
            raise LabelFeatureNotFoundError(f"Feature {feature_id} was not found for current user.")

        request_id = self._session.execute(
            sa.select(FeatureRequest.id)
            .where(
                FeatureRequest.feature_id == feature_id,
                FeatureRequest.user_id == user_id,
            )
            .order_by(FeatureRequest.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if request_id is None:
            raise LabelRequestNotFoundError(
                f"Feature {feature_id} is not linked to a fulfilled request."
            )

        try:
            row = Label(
                user_id=user_id,
                feature_id=feature_id,
                request_id=request_id,
                label=label,
                emotion_word=emotion_word,
                category=category,
            )
            self._session.add(row)
            self._session.commit()
            self._session.refresh(row)
            return row
        except IntegrityError as exc:
            self._session.rollback()
            raise LabelWriteError("Failed to create label.") from exc
