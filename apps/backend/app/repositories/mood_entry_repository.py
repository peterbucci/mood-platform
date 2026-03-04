from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    CalorieFeatures,
    DailyFeatures,
    ExerciseFeatures,
    HrFeatures,
    MoodEntry,
    PersonalFeatures,
    RestingHrFeatures,
    SleepFeatures,
    StepsFeatures,
    User,
)

FEATURE_TABLES = {
    "personal_features_id": PersonalFeatures,
    "daily_features_id": DailyFeatures,
    "sleep_features_id": SleepFeatures,
    "steps_features_id": StepsFeatures,
    "exercise_features_id": ExerciseFeatures,
    "hr_features_id": HrFeatures,
    "resting_hr_features_id": RestingHrFeatures,
    "calorie_features_id": CalorieFeatures,
}


class MissingFeatureSetError(Exception):
    def __init__(self, field_name: str, feature_id: uuid.UUID) -> None:
        self.field_name = field_name
        self.feature_id = feature_id
        super().__init__(f"{field_name}={feature_id} does not exist for this user.")


class MoodEntryWriteError(Exception):
    pass


class MoodEntryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        user_id: uuid.UUID,
        entry_at: datetime,
        label_category_key: str,
        label_emotion: str,
        note: str | None,
        feature_set_ids: dict[str, uuid.UUID | None],
    ) -> uuid.UUID:
        try:
            self._ensure_user_exists(user_id=user_id)
            self._validate_feature_sets(user_id=user_id, feature_set_ids=feature_set_ids)
            mood_entry = MoodEntry(
                user_id=user_id,
                entry_at=entry_at,
                label_category_key=label_category_key,
                label_emotion=label_emotion,
                note=note,
                **feature_set_ids,
            )
            self._session.add(mood_entry)
            self._session.commit()
            return mood_entry.id
        except MissingFeatureSetError:
            self._session.rollback()
            raise
        except IntegrityError as exc:
            self._session.rollback()
            raise MoodEntryWriteError(
                "Failed to create mood entry due to DB integrity constraints."
            ) from exc

    def _ensure_user_exists(self, *, user_id: uuid.UUID) -> None:
        existing_user_id = self._session.execute(
            sa.select(User.id).where(User.id == user_id)
        ).scalar_one_or_none()
        if existing_user_id is None:
            self._session.add(User(id=user_id))
            self._session.flush()

    def _validate_feature_sets(
        self,
        *,
        user_id: uuid.UUID,
        feature_set_ids: dict[str, uuid.UUID | None],
    ) -> None:
        for field_name, model in FEATURE_TABLES.items():
            feature_id = feature_set_ids.get(field_name)
            if feature_id is None:
                continue

            existing_feature_id = self._session.execute(
                sa.select(model.id).where(
                    model.id == feature_id,
                    model.user_id == user_id,
                )
            ).scalar_one_or_none()
            if existing_feature_id is None:
                raise MissingFeatureSetError(field_name=field_name, feature_id=feature_id)
