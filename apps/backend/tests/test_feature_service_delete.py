from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest
from app.repositories.feature_repository import FeatureDeleteWriteError
from app.services.feature_service import FeatureDeleteError, FeatureNotFoundError, FeatureService


@dataclass
class _Feature:
    id: str
    user_id: str


class _FakeFeatureRepository:
    def __init__(self, feature: _Feature | None) -> None:
        self._feature = feature
        self.deleted_labels = False
        self.unlinked_requests = False
        self.deleted_feature = False
        self.committed = False
        self.rolled_back = False
        self.raise_on_cleanup = False

    def get_feature_by_id_for_update(self, *, user_id: str, feature_id: str) -> _Feature | None:
        if self._feature is None:
            return None
        if self._feature.user_id != user_id:
            return None
        if self._feature.id != feature_id:
            return None
        return self._feature

    def delete_feature_labels(self, *, user_id: str, feature_id: str, commit: bool = True) -> int:
        if self.raise_on_cleanup:
            raise FeatureDeleteWriteError("cleanup failed")
        assert user_id == self._feature.user_id
        assert feature_id == self._feature.id
        self.deleted_labels = True
        return 1

    def null_requests_feature_reference(
        self,
        *,
        user_id: str,
        feature_id: str,
        commit: bool = True,
    ) -> int:
        assert user_id == self._feature.user_id
        assert feature_id == self._feature.id
        self.unlinked_requests = True
        return 1

    def delete_feature(self, *, user_id: str, feature_id: str, commit: bool = True) -> bool:
        assert user_id == self._feature.user_id
        assert feature_id == self._feature.id
        self.deleted_feature = True
        self._feature = None
        return True

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_delete_feature_service_cleans_up_and_deletes() -> None:
    owner = uuid.UUID("00000000-0000-0000-0000-00000000be01")
    repository = _FakeFeatureRepository(
        feature=_Feature(
            id="feat-service-delete-1",
            user_id=str(owner),
        )
    )
    service = FeatureService(repository=repository, owner_user_id=owner)  # type: ignore[arg-type]

    result = service.delete_feature(feature_id="feat-service-delete-1")

    assert result == {"id": "feat-service-delete-1"}
    assert repository.deleted_labels is True
    assert repository.unlinked_requests is True
    assert repository.deleted_feature is True
    assert repository.committed is True
    assert repository.rolled_back is False


def test_delete_feature_service_raises_not_found_for_missing_feature() -> None:
    owner = uuid.UUID("00000000-0000-0000-0000-00000000be02")
    repository = _FakeFeatureRepository(feature=None)
    service = FeatureService(repository=repository, owner_user_id=owner)  # type: ignore[arg-type]

    with pytest.raises(FeatureNotFoundError):
        service.delete_feature(feature_id="missing-feature")

    assert repository.committed is False
    assert repository.rolled_back is True


def test_delete_feature_service_rolls_back_on_cleanup_failure() -> None:
    owner = uuid.UUID("00000000-0000-0000-0000-00000000be03")
    repository = _FakeFeatureRepository(
        feature=_Feature(
            id="feat-service-delete-3",
            user_id=str(owner),
        )
    )
    repository.raise_on_cleanup = True
    service = FeatureService(repository=repository, owner_user_id=owner)  # type: ignore[arg-type]

    with pytest.raises(FeatureDeleteError):
        service.delete_feature(feature_id="feat-service-delete-3")

    assert repository.committed is False
    assert repository.rolled_back is True
