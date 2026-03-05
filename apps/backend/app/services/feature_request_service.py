from __future__ import annotations

import uuid
from typing import Any

from app.repositories.feature_request_repository import (
    FeatureRequestRepository,
    FeatureRequestWriteError,
)


class FeatureRequestPersistenceError(Exception):
    pass


class FeatureRequestNotFoundError(Exception):
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

    def get_request_by_id(self, *, request_id: str) -> dict[str, Any]:
        request = self._repository.get_request_by_id_for_user(
            user_id=str(self._owner_user_id),
            request_id=request_id,
        )
        if request is None:
            raise FeatureRequestNotFoundError(
                f"Request {request_id} was not found for current user."
            )
        return {
            "id": request.id,
            "status": request.status,
            "featureId": request.feature_id,
            "createdAt": request.created_at,
        }

    def get_pending_request_count(self, *, user_id: str | None = None) -> int:
        target_user_id = str(self._owner_user_id)
        if isinstance(user_id, str):
            stripped_user_id = user_id.strip()
            if stripped_user_id:
                target_user_id = stripped_user_id
        return self._repository.count_pending_requests(user_id=target_user_id)
