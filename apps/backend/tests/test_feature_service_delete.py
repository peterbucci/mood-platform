from __future__ import annotations

import uuid

import pytest
from app.repositories.request_feature_delete_repository import RequestFeatureDeleteWriteError
from app.services.feature_service import FeatureDeleteError, FeatureNotFoundError, FeatureService


class _FakeFeatureRepository:
    def get_latest_feature(self, *, user_id: str):  # pragma: no cover - not used in these tests
        raise AssertionError("not used")

    def get_feature_by_id(self, *, user_id: str, feature_id: str):  # pragma: no cover - not used
        raise AssertionError("not used")

    def list_features(
        self, *, user_id: str, limit: int, offset: int
    ):  # pragma: no cover - not used
        raise AssertionError("not used")

    def get_latest_label_for_feature(
        self, *, user_id: str, feature_id: str
    ):  # pragma: no cover - not used
        raise AssertionError("not used")


class _FakeDeleteRepository:
    def __init__(self, *, deleted_feature_exists: bool = True) -> None:
        self.deleted_feature_exists = deleted_feature_exists
        self.deleted_feature_id: str | None = None
        self.committed = False
        self.rolled_back = False
        self.raise_on_delete = False

    def delete_unit_by_feature_id(
        self,
        *,
        user_id: str,
        feature_id: str,
        commit: bool = True,
    ):
        if self.raise_on_delete:
            raise RequestFeatureDeleteWriteError("cleanup failed")
        if not self.deleted_feature_exists:
            return None
        self.deleted_feature_id = feature_id
        return {"id": feature_id}

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_delete_feature_service_deletes_linked_unit() -> None:
    owner = uuid.UUID("00000000-0000-0000-0000-00000000be01")
    delete_repository = _FakeDeleteRepository()
    service = FeatureService(
        repository=_FakeFeatureRepository(),  # type: ignore[arg-type]
        delete_repository=delete_repository,  # type: ignore[arg-type]
        owner_user_id=owner,
    )

    result = service.delete_feature(feature_id="feat-service-delete-1")

    assert result == {"id": "feat-service-delete-1"}
    assert delete_repository.deleted_feature_id == "feat-service-delete-1"
    assert delete_repository.committed is True
    assert delete_repository.rolled_back is False


def test_delete_feature_service_raises_not_found_for_missing_feature() -> None:
    owner = uuid.UUID("00000000-0000-0000-0000-00000000be02")
    delete_repository = _FakeDeleteRepository(deleted_feature_exists=False)
    service = FeatureService(
        repository=_FakeFeatureRepository(),  # type: ignore[arg-type]
        delete_repository=delete_repository,  # type: ignore[arg-type]
        owner_user_id=owner,
    )

    with pytest.raises(FeatureNotFoundError):
        service.delete_feature(feature_id="missing-feature")

    assert delete_repository.committed is False
    assert delete_repository.rolled_back is True


def test_delete_feature_service_rolls_back_on_cleanup_failure() -> None:
    owner = uuid.UUID("00000000-0000-0000-0000-00000000be03")
    delete_repository = _FakeDeleteRepository()
    delete_repository.raise_on_delete = True
    service = FeatureService(
        repository=_FakeFeatureRepository(),  # type: ignore[arg-type]
        delete_repository=delete_repository,  # type: ignore[arg-type]
        owner_user_id=owner,
    )

    with pytest.raises(FeatureDeleteError):
        service.delete_feature(feature_id="feat-service-delete-3")

    assert delete_repository.committed is False
    assert delete_repository.rolled_back is True
