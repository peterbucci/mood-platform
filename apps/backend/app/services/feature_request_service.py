from __future__ import annotations

import uuid

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

    def create_request(self) -> tuple[str, str]:
        try:
            return self._repository.create_request(user_id=str(self._owner_user_id))
        except FeatureRequestWriteError as exc:
            raise FeatureRequestPersistenceError(str(exc)) from exc
