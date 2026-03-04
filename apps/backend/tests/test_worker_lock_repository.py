from __future__ import annotations

import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import psycopg
from app.db.session import to_sqlalchemy_database_url
from app.repositories.worker_lock_repository import WorkerLockRepository
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_CONFIG = ROOT_DIR / "apps" / "backend" / "alembic.ini"


def test_lock_can_be_acquired_and_released() -> None:
    with _temporary_migrated_database() as database_url:
        session_factory = _session_factory(database_url)
        with session_factory() as session:
            repository = WorkerLockRepository(session=session)
            assert repository.try_acquire(
                lock_key="fulfillment_lock:user-1",
                owner_id="worker-a",
                ttl_seconds=10,
            )
            assert repository.release(
                lock_key="fulfillment_lock:user-1",
                owner_id="worker-a",
            )


def test_second_worker_cannot_acquire_before_ttl_expires() -> None:
    with _temporary_migrated_database() as database_url:
        session_factory = _session_factory(database_url)
        with session_factory() as session_a:
            repo_a = WorkerLockRepository(session=session_a)
            assert repo_a.try_acquire(
                lock_key="fulfillment_lock:user-2",
                owner_id="worker-a",
                ttl_seconds=1.0,
            )

        with session_factory() as session_b:
            repo_b = WorkerLockRepository(session=session_b)
            assert not repo_b.try_acquire(
                lock_key="fulfillment_lock:user-2",
                owner_id="worker-b",
                ttl_seconds=1.0,
            )


def test_lock_can_be_reacquired_after_ttl_expiry() -> None:
    with _temporary_migrated_database() as database_url:
        session_factory = _session_factory(database_url)
        with session_factory() as session_a:
            repo_a = WorkerLockRepository(session=session_a)
            assert repo_a.try_acquire(
                lock_key="fulfillment_lock:user-3",
                owner_id="worker-a",
                ttl_seconds=0.1,
            )

        time.sleep(0.2)

        with session_factory() as session_b:
            repo_b = WorkerLockRepository(session=session_b)
            assert repo_b.try_acquire(
                lock_key="fulfillment_lock:user-3",
                owner_id="worker-b",
                ttl_seconds=1.0,
            )


def test_lock_renewal_extends_lock_for_same_owner() -> None:
    with _temporary_migrated_database() as database_url:
        session_factory = _session_factory(database_url)
        with session_factory() as session_a:
            repo_a = WorkerLockRepository(session=session_a)
            assert repo_a.try_acquire(
                lock_key="fulfillment_lock:user-4",
                owner_id="worker-a",
                ttl_seconds=0.1,
            )
            assert repo_a.renew(
                lock_key="fulfillment_lock:user-4",
                owner_id="worker-a",
                ttl_seconds=1.0,
            )

        time.sleep(0.2)

        with session_factory() as session_b:
            repo_b = WorkerLockRepository(session=session_b)
            assert not repo_b.try_acquire(
                lock_key="fulfillment_lock:user-4",
                owner_id="worker-b",
                ttl_seconds=1.0,
            )


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for worker lock repository tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_worker_lock_{uuid.uuid4().hex[:8]}"
        self._admin_url = parsed_url.set(database="postgres").render_as_string(hide_password=False)
        self._temp_url = parsed_url.set(database=self._temp_database).render_as_string(
            hide_password=False
        )

        with psycopg.connect(self._admin_url, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(self._temp_database)
                )
            )
            connection.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self._temp_database))
            )

        return self._temp_url

    def __exit__(self, exc_type, exc, tb) -> None:
        with psycopg.connect(self._admin_url, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(self._temp_database)
                )
            )


class _temporary_migrated_database:
    def __enter__(self) -> str:
        self._database_ctx = _temporary_database()
        database_url = self._database_ctx.__enter__()
        _run_alembic_upgrade(database_url=database_url)
        return database_url

    def __exit__(self, exc_type, exc, tb) -> None:
        self._database_ctx.__exit__(exc_type, exc, tb)


def _run_alembic_upgrade(*, database_url: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ALEMBIC_CONFIG),
            "upgrade",
            "head",
        ],
        check=True,
        cwd=ROOT_DIR,
        env=env,
    )


def _session_factory(database_url: str) -> sessionmaker:
    return sessionmaker(bind=create_engine(to_sqlalchemy_database_url(database_url)))
