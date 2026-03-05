from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from app.services.fitbit_token_service import (
    FitbitTokenNotConnectedError,
    FitbitTokenService,
)
from app.settings import Settings


@dataclass
class _FakeTokenRow:
    user_id: uuid.UUID
    fitbit_user_id: str | None
    access_token: str
    refresh_token: str
    expires_at: datetime
    scope: str


class _FakeTokenRepository:
    def __init__(self) -> None:
        self._rows: dict[uuid.UUID, _FakeTokenRow] = {}

    def upsert_token(
        self,
        *,
        user_id: uuid.UUID,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
        scope: str,
        fitbit_user_id: str | None = None,
    ) -> None:
        self._rows[user_id] = _FakeTokenRow(
            user_id=user_id,
            fitbit_user_id=fitbit_user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scope=scope,
        )

    def get_token(self, *, user_id: uuid.UUID) -> _FakeTokenRow | None:
        return self._rows.get(user_id)

    def delete_token(self, *, user_id: uuid.UUID) -> bool:
        return self._rows.pop(user_id, None) is not None


def test_get_access_token_returns_existing_token_when_not_expired() -> None:
    user_id = uuid.UUID("00000000-0000-0000-0000-00000000ba01")
    repository = _FakeTokenRepository()
    repository.upsert_token(
        user_id=user_id,
        fitbit_user_id="fitbit-user-a",
        access_token="access-valid",
        refresh_token="refresh-valid",
        expires_at=datetime.now(tz=UTC) + timedelta(minutes=20),
        scope="sleep heartrate activity profile",
    )
    service = FitbitTokenService(repository=repository, settings=_settings())

    assert service.get_access_token(user_id=user_id) == "access-valid"


def test_get_access_token_refreshes_when_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid.UUID("00000000-0000-0000-0000-00000000ba02")
    repository = _FakeTokenRepository()
    repository.upsert_token(
        user_id=user_id,
        fitbit_user_id="fitbit-user-b",
        access_token="access-old",
        refresh_token="refresh-old",
        expires_at=datetime.now(tz=UTC) - timedelta(minutes=1),
        scope="sleep heartrate activity profile",
    )
    service = FitbitTokenService(repository=repository, settings=_settings())

    def _mock_refresh_request(*, refresh_token: str) -> dict[str, object]:
        assert refresh_token == "refresh-old"
        return {
            "access_token": "access-new",
            "refresh_token": "refresh-new",
            "expires_in": 3600,
            "scope": "sleep heartrate activity profile",
            "user_id": "fitbit-user-b",
        }

    monkeypatch.setattr(service, "_request_refresh_token", _mock_refresh_request)

    access_token = service.get_access_token(user_id=user_id)
    stored_token = repository.get_token(user_id=user_id)

    assert access_token == "access-new"
    assert stored_token is not None
    assert stored_token.access_token == "access-new"
    assert stored_token.refresh_token == "refresh-new"
    assert stored_token.expires_at > datetime.now(tz=UTC)


def test_get_access_token_raises_when_not_connected() -> None:
    service = FitbitTokenService(repository=_FakeTokenRepository(), settings=_settings())

    with pytest.raises(FitbitTokenNotConnectedError):
        service.get_access_token(user_id=uuid.UUID("00000000-0000-0000-0000-00000000ba03"))


def _settings() -> Settings:
    return Settings(
        FITBIT_CLIENT_ID="test-fitbit-client-id",
        FITBIT_CLIENT_SECRET="test-fitbit-client-secret",
        FITBIT_REDIRECT_URI="http://localhost:8000/fitbit/oauth/callback",
    )
