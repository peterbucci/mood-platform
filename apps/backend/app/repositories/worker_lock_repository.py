from __future__ import annotations

from datetime import UTC, datetime, timedelta

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class WorkerLockRepositoryError(Exception):
    pass


class WorkerLockRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def try_acquire(self, *, lock_key: str, owner_id: str, ttl_seconds: float) -> bool:
        expires_at = datetime.now(tz=UTC) + timedelta(seconds=ttl_seconds)
        statement = sa.text(
            """
            INSERT INTO worker_locks (lock_key, owner_id, expires_at, created_at, updated_at)
            VALUES (:lock_key, :owner_id, :expires_at, now(), now())
            ON CONFLICT (lock_key) DO UPDATE
            SET owner_id = EXCLUDED.owner_id,
                expires_at = EXCLUDED.expires_at,
                updated_at = now()
            WHERE worker_locks.expires_at <= now()
               OR worker_locks.owner_id = EXCLUDED.owner_id
            RETURNING lock_key
            """
        )

        try:
            acquired_lock_key = self._session.execute(
                statement,
                {
                    "lock_key": lock_key,
                    "owner_id": owner_id,
                    "expires_at": expires_at,
                },
            ).scalar_one_or_none()
            self._session.commit()
            return acquired_lock_key is not None
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise WorkerLockRepositoryError("Failed to acquire worker lock.") from exc

    def renew(self, *, lock_key: str, owner_id: str, ttl_seconds: float) -> bool:
        expires_at = datetime.now(tz=UTC) + timedelta(seconds=ttl_seconds)
        statement = sa.text(
            """
            UPDATE worker_locks
            SET expires_at = :expires_at,
                updated_at = now()
            WHERE lock_key = :lock_key
              AND owner_id = :owner_id
            RETURNING lock_key
            """
        )

        try:
            renewed_lock_key = self._session.execute(
                statement,
                {
                    "lock_key": lock_key,
                    "owner_id": owner_id,
                    "expires_at": expires_at,
                },
            ).scalar_one_or_none()
            self._session.commit()
            return renewed_lock_key is not None
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise WorkerLockRepositoryError("Failed to renew worker lock.") from exc

    def release(self, *, lock_key: str, owner_id: str) -> bool:
        statement = sa.text(
            """
            DELETE FROM worker_locks
            WHERE lock_key = :lock_key
              AND owner_id = :owner_id
            RETURNING lock_key
            """
        )

        try:
            released_lock_key = self._session.execute(
                statement,
                {
                    "lock_key": lock_key,
                    "owner_id": owner_id,
                },
            ).scalar_one_or_none()
            self._session.commit()
            return released_lock_key is not None
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise WorkerLockRepositoryError("Failed to release worker lock.") from exc
