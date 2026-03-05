from __future__ import annotations

import uuid
from typing import Any

from app.repositories.feature_request_repository import (
    FeatureRequestRepository,
    FeatureRequestWriteError,
)


class FeatureRequestPersistenceError(Exception):
    pass


class FeatureRequestService:
    def __init__(self, repository: FeatureRequestRepository, owner_user_id: uuid.UUID) -> None:
        self._repository = repository
        self._owner_user_id = owner_user_id

    def create_request(self, *, client_features: dict[str, Any] | None = None) -> tuple[str, str]:
        try:
            return self._repository.create_request_with_client_features(
                user_id=str(self._owner_user_id),
                client_features=client_features,
            )
        except FeatureRequestWriteError as exc:
            raise FeatureRequestPersistenceError(str(exc)) from exc

    def list_requests(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        request_rows = self._repository.list_requests(
            user_id=str(self._owner_user_id),
            limit=limit,
            offset=offset,
        )
        items: list[dict[str, Any]] = []
        for request, feature in request_rows:
            payload: dict[str, Any] = {
                "id": request.id,
                "userId": request.user_id,
                "createdAt": request.created_at,
                "status": request.status,
                "source": request.source,
                "featureId": request.feature_id,
            }
            if feature is not None:
                payload["feature"] = {
                    "id": feature.id,
                    "createdAt": feature.created_at,
                    "source": feature.source,
                }
            items.append(payload)
        return items
