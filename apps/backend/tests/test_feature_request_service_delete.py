from __future__ import annotations

import uuid

import pytest
from app.repositories.request_feature_delete_repository import RequestFeatureDeleteWriteError
from app.services.feature_request_service import (
    FeatureRequestDeleteError,
    FeatureRequestNotFoundError,
    FeatureRequestService,
)


class _FakeRequestRepository:
    def create_request_with_client_features(
        self, *, user_id: str, client_features
    ):  # pragma: no cover
        raise AssertionError("not used")

    def list_requests(self, *, user_id: str, limit: int, offset: int):  # pragma: no cover
        raise AssertionError("not used")

    def get_request_by_id_for_user(self, *, user_id: str, request_id: str):  # pragma: no cover
        raise AssertionError("not used")

    def count_pending_requests(self, *, user_id: str | None = None):  # pragma: no cover
        raise AssertionError("not used")


class _FakeDeleteRepository:
    def __init__(self, *, request_exists: bool = True) -> None:
        self.request_exists = request_exists
        self.deleted_request_id: str | None = None
        self.committed = False
        self.rolled_back = False
        self.raise_on_delete = False

    def delete_unit_by_request_id(
        self,
        *,
        user_id: str,
        request_id: str,
        commit: bool = True,
    ):
        if self.raise_on_delete:
            raise RequestFeatureDeleteWriteError("cleanup failed")
        if not self.request_exists:
            return None
        self.deleted_request_id = request_id
        return {"id": request_id}

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_delete_request_service_deletes_linked_unit() -> None:
    owner = uuid.UUID("00000000-0000-0000-0000-00000000bf01")
    delete_repository = _FakeDeleteRepository()
    service = FeatureRequestService(
        repository=_FakeRequestRepository(),  # type: ignore[arg-type]
        delete_repository=delete_repository,  # type: ignore[arg-type]
        owner_user_id=owner,
    )

    result = service.delete_request(request_id="req-service-delete-1")

    assert result == {"id": "req-service-delete-1"}
    assert delete_repository.deleted_request_id == "req-service-delete-1"
    assert delete_repository.committed is True
    assert delete_repository.rolled_back is False


def test_delete_request_service_raises_not_found_for_missing_request() -> None:
    owner = uuid.UUID("00000000-0000-0000-0000-00000000bf02")
    delete_repository = _FakeDeleteRepository(request_exists=False)
    service = FeatureRequestService(
        repository=_FakeRequestRepository(),  # type: ignore[arg-type]
        delete_repository=delete_repository,  # type: ignore[arg-type]
        owner_user_id=owner,
    )

    with pytest.raises(FeatureRequestNotFoundError):
        service.delete_request(request_id="missing-request")

    assert delete_repository.committed is False
    assert delete_repository.rolled_back is True


def test_delete_request_service_rolls_back_on_cleanup_failure() -> None:
    owner = uuid.UUID("00000000-0000-0000-0000-00000000bf03")
    delete_repository = _FakeDeleteRepository()
    delete_repository.raise_on_delete = True
    service = FeatureRequestService(
        repository=_FakeRequestRepository(),  # type: ignore[arg-type]
        delete_repository=delete_repository,  # type: ignore[arg-type]
        owner_user_id=owner,
    )

    with pytest.raises(FeatureRequestDeleteError):
        service.delete_request(request_id="req-service-delete-3")

    assert delete_repository.committed is False
    assert delete_repository.rolled_back is True
