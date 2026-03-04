from __future__ import annotations

import json
import uuid
from typing import Any

from app.db.models import Feature
from app.repositories.feature_repository import FeatureRepository


class FeatureNotFoundError(Exception):
    pass


class FeatureDataParseError(Exception):
    pass


class FeatureService:
    def __init__(self, repository: FeatureRepository, owner_user_id: uuid.UUID) -> None:
        self._repository = repository
        self._owner_user_id = owner_user_id

    def get_latest_feature(self) -> dict[str, Any]:
        feature = self._repository.get_latest_feature(user_id=str(self._owner_user_id))
        if feature is None:
            raise FeatureNotFoundError("No features found for current user.")
        return self._serialize_feature(feature)

    def get_feature_by_id(self, *, feature_id: str) -> dict[str, Any]:
        feature = self._repository.get_feature_by_id(
            user_id=str(self._owner_user_id),
            feature_id=feature_id,
        )
        if feature is None:
            raise FeatureNotFoundError(f"Feature {feature_id} was not found for current user.")
        return self._serialize_feature(feature)

    def list_features(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        features = self._repository.list_features(
            user_id=str(self._owner_user_id),
            limit=limit,
            offset=offset,
        )
        return [self._serialize_feature(feature) for feature in features]

    def _serialize_feature(self, feature: Feature) -> dict[str, Any]:
        try:
            parsed_data = json.loads(feature.data)
        except json.JSONDecodeError as exc:
            raise FeatureDataParseError(
                f"Feature {feature.id} contains invalid JSON data."
            ) from exc

        if not isinstance(parsed_data, dict):
            raise FeatureDataParseError(f"Feature {feature.id} data must deserialize to an object.")

        return {
            "id": feature.id,
            "userId": feature.user_id,
            "createdAt": feature.created_at,
            "source": feature.source,
            "data": parsed_data,
        }
