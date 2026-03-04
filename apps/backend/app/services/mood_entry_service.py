from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

from app.repositories.mood_entry_repository import (
    MissingFeatureSetError,
    MoodEntryRepository,
    MoodEntryWriteError,
)

DEFAULT_OWNER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class MoodEntryValidationError(Exception):
    pass


class MoodEntryFeatureReferenceError(Exception):
    pass


class MoodEntryPersistenceError(Exception):
    pass


def get_owner_user_id() -> uuid.UUID:
    configured_user_id = os.getenv("OWNER_USER_ID", "").strip()
    if not configured_user_id:
        return DEFAULT_OWNER_USER_ID
    try:
        return uuid.UUID(configured_user_id)
    except ValueError as exc:
        raise RuntimeError("OWNER_USER_ID must be a valid UUID.") from exc


class MoodEntryService:
    def __init__(self, repository: MoodEntryRepository, owner_user_id: uuid.UUID) -> None:
        self._repository = repository
        self._owner_user_id = owner_user_id

    def create(
        self,
        *,
        entry_at: datetime,
        label_category_key: str,
        label_emotion: str,
        note: str | None,
        feature_set_ids: dict[str, uuid.UUID | None],
    ) -> uuid.UUID:
        if entry_at.tzinfo is None or entry_at.utcoffset() is None:
            raise MoodEntryValidationError("entry_at must include timezone information.")

        cleaned_emotion = label_emotion.strip()
        if not cleaned_emotion:
            raise MoodEntryValidationError("label_emotion must not be blank.")

        entry_at_utc = entry_at.astimezone(UTC)

        try:
            return self._repository.create(
                user_id=self._owner_user_id,
                entry_at=entry_at_utc,
                label_category_key=label_category_key,
                label_emotion=cleaned_emotion,
                note=note,
                feature_set_ids=feature_set_ids,
            )
        except MissingFeatureSetError as exc:
            raise MoodEntryFeatureReferenceError(str(exc)) from exc
        except MoodEntryWriteError as exc:
            raise MoodEntryPersistenceError(str(exc)) from exc
