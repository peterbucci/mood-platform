from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.repositories.mood_entry_repository import MissingFeatureSetError
from app.services.mood_entry_service import (
    MoodEntryFeatureReferenceError,
    MoodEntryService,
    MoodEntryValidationError,
)


class MockMoodEntryRepository:
    def __init__(self, mood_entry_id: uuid.UUID | None = None) -> None:
        self.mood_entry_id = mood_entry_id or uuid.uuid4()
        self.calls: list[dict[str, object]] = []
        self.raise_missing_feature = False

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
        if self.raise_missing_feature:
            raise MissingFeatureSetError("sleep_features_id", uuid.uuid4())

        self.calls.append(
            {
                "user_id": user_id,
                "entry_at": entry_at,
                "label_category_key": label_category_key,
                "label_emotion": label_emotion,
                "note": note,
                "feature_set_ids": feature_set_ids,
            }
        )
        return self.mood_entry_id


def test_create_normalizes_entry_at_to_utc() -> None:
    mock_repository = MockMoodEntryRepository()
    owner_user_id = uuid.UUID("00000000-0000-0000-0000-000000000009")
    service = MoodEntryService(repository=mock_repository, owner_user_id=owner_user_id)
    entry_at = datetime.fromisoformat("2026-03-04T08:30:00+02:00")

    created_id = service.create(
        entry_at=entry_at,
        label_category_key="calm",
        label_emotion=" Relaxed ",
        note="steady morning",
        feature_set_ids={},
    )

    assert created_id == mock_repository.mood_entry_id
    assert len(mock_repository.calls) == 1
    assert mock_repository.calls[0]["user_id"] == owner_user_id
    assert mock_repository.calls[0]["entry_at"] == datetime(2026, 3, 4, 6, 30, tzinfo=UTC)
    assert mock_repository.calls[0]["label_emotion"] == "Relaxed"


def test_create_rejects_naive_timestamp() -> None:
    mock_repository = MockMoodEntryRepository()
    service = MoodEntryService(repository=mock_repository, owner_user_id=uuid.uuid4())

    try:
        service.create(
            entry_at=datetime(2026, 3, 4, 8, 30),
            label_category_key="calm",
            label_emotion="Relaxed",
            note=None,
            feature_set_ids={},
        )
    except MoodEntryValidationError as exc:
        assert "timezone" in str(exc)
    else:
        raise AssertionError("Expected MoodEntryValidationError for naive timestamps.")


def test_create_surfaces_missing_feature_error() -> None:
    mock_repository = MockMoodEntryRepository()
    mock_repository.raise_missing_feature = True
    service = MoodEntryService(repository=mock_repository, owner_user_id=uuid.uuid4())

    try:
        service.create(
            entry_at=datetime(2026, 3, 4, 8, 30, tzinfo=UTC),
            label_category_key="tired",
            label_emotion="Drained",
            note=None,
            feature_set_ids={},
        )
    except MoodEntryFeatureReferenceError:
        pass
    else:
        raise AssertionError("Expected MoodEntryFeatureReferenceError for invalid feature ids.")
