from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    CalorieFeatures,
    DailyFeatures,
    ExerciseFeatures,
    HrFeatures,
    PersonalFeatures,
    RestingHrFeatures,
    SleepFeatures,
    StepsFeatures,
    User,
)
from app.settings import Settings, get_settings

FEATURE_MODELS = {
    "personal_features": PersonalFeatures,
    "daily_features": DailyFeatures,
    "sleep_features": SleepFeatures,
    "steps_features": StepsFeatures,
    "exercise_features": ExerciseFeatures,
    "hr_features": HrFeatures,
    "resting_hr_features": RestingHrFeatures,
    "calorie_features": CalorieFeatures,
}


class FeatureSetRepositoryError(Exception):
    pass


class UnknownFeatureTableError(FeatureSetRepositoryError):
    pass


class FeatureSetWriteError(FeatureSetRepositoryError):
    pass


class FeatureSetRepository:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()

    def create_feature_set(
        self,
        *,
        table_name: str,
        user_id: uuid.UUID,
        captured_at: datetime,
        window_start: datetime,
        window_end: datetime,
        source_timezone: str,
        feature_values: dict[str, Any] | None = None,
        extractor_version: str | None = None,
    ) -> uuid.UUID:
        model = FEATURE_MODELS.get(table_name)
        if model is None:
            raise UnknownFeatureTableError(f"Unknown feature table: {table_name}")

        metadata_source_timezone = source_timezone.strip()
        if not metadata_source_timezone:
            raise FeatureSetRepositoryError("source_timezone must not be blank.")

        metadata_extractor_version = extractor_version or self._settings.FEATURE_EXTRACTOR_VERSION
        payload = {
            "user_id": user_id,
            "captured_at": captured_at,
            "extractor_version": metadata_extractor_version,
            "window_start": window_start,
            "window_end": window_end,
            "source_timezone": metadata_source_timezone,
            **(feature_values or {}),
        }

        try:
            self._ensure_user_exists(user_id=user_id)
            feature_row = model(**payload)
            self._session.add(feature_row)
            self._session.commit()
            return feature_row.id
        except IntegrityError as exc:
            self._session.rollback()
            raise FeatureSetWriteError(f"Failed to insert {table_name}.") from exc

    def list_feature_sets_by_extractor_version(
        self,
        *,
        table_name: str,
        extractor_version: str,
    ) -> list[Any]:
        model = FEATURE_MODELS.get(table_name)
        if model is None:
            raise UnknownFeatureTableError(f"Unknown feature table: {table_name}")

        result = self._session.execute(
            sa.select(model).where(model.extractor_version == extractor_version)
        )
        return result.scalars().all()

    def _ensure_user_exists(self, *, user_id: uuid.UUID) -> None:
        existing_user_id = self._session.execute(
            sa.select(User.id).where(User.id == user_id)
        ).scalar_one_or_none()
        if existing_user_id is None:
            self._session.add(User(id=user_id))
            self._session.flush()
