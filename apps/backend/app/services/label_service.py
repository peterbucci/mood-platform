from __future__ import annotations

import uuid
from typing import Any

from app.repositories.label_repository import (
    LabelFeatureNotFoundError,
    LabelRepository,
    LabelRequestNotFoundError,
    LabelWriteError,
)


class LabelValidationError(Exception):
    pass


class LabelFeatureReferenceError(Exception):
    pass


class LabelTraceabilityError(Exception):
    pass


class LabelPersistenceError(Exception):
    pass


class LabelService:
    def __init__(self, repository: LabelRepository, owner_user_id: uuid.UUID) -> None:
        self._repository = repository
        self._owner_user_id = owner_user_id

    def create(
        self,
        *,
        feature_id: str,
        label: str | None,
        emotion_word: str,
        category: str,
    ) -> dict[str, Any]:
        normalized_feature_id = feature_id.strip()
        if not normalized_feature_id:
            raise LabelValidationError("featureId must not be blank.")

        normalized_emotion_word = emotion_word.strip()
        if not normalized_emotion_word:
            raise LabelValidationError("emotionWord must not be blank.")

        normalized_label: str | None = None
        if isinstance(label, str):
            stripped_label = label.strip()
            if stripped_label:
                normalized_label = stripped_label

        try:
            created = self._repository.create_label(
                user_id=str(self._owner_user_id),
                feature_id=normalized_feature_id,
                label=normalized_label,
                emotion_word=normalized_emotion_word,
                category=category,
            )
        except LabelFeatureNotFoundError as exc:
            raise LabelFeatureReferenceError(str(exc)) from exc
        except LabelRequestNotFoundError as exc:
            raise LabelTraceabilityError(str(exc)) from exc
        except LabelWriteError as exc:
            raise LabelPersistenceError(str(exc)) from exc

        return {
            "id": created.id,
            "userId": created.user_id,
            "featureId": created.feature_id,
            "requestId": created.request_id,
            "label": created.label,
            "emotionWord": created.emotion_word,
            "category": created.category,
            "createdAt": created.created_at,
        }
