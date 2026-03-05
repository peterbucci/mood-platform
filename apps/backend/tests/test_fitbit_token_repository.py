from __future__ import annotations

import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from app.db.models import FitbitToken
from app.db.session import to_sqlalchemy_database_url
from app.repositories.fitbit_token_repository import FitbitTokenRepository
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_CONFIG = ROOT_DIR / "apps" / "backend" / "alembic.ini"


def test_fitbit_token_repository_upsert_get_delete() -> None:
    with _temporary_migrated_database() as database_url:
        session_factory = sessionmaker(
            bind=create_engine(to_sqlalchemy_database_url(database_url)),
            expire_on_commit=False,
        )
        user_id = uuid.UUID("00000000-0000-0000-0000-00000000aa11")

        with session_factory() as session:
            repository = FitbitTokenRepository(session=session)

            repository.upsert_token(
                user_id=user_id,
                fitbit_user_id="fitbit-user-1",
                access_token="access-1",
                refresh_token="refresh-1",
                expires_at=datetime(2026, 3, 5, 12, 0, tzinfo=UTC),
                scope="sleep heartrate activity profile",
            )

            stored_token = repository.get_token(user_id=user_id)
            assert stored_token is not None
            assert stored_token.user_id == user_id
            assert stored_token.fitbit_user_id == "fitbit-user-1"
            assert stored_token.access_token == "access-1"
            assert stored_token.refresh_token == "refresh-1"
            assert stored_token.scope == "sleep heartrate activity profile"

            repository.upsert_token(
                user_id=user_id,
                fitbit_user_id="fitbit-user-1",
                access_token="access-2",
                refresh_token="refresh-2",
                expires_at=datetime(2026, 3, 5, 13, 0, tzinfo=UTC),
                scope="sleep profile",
            )

            updated_token = repository.get_token(user_id=user_id)
            assert updated_token is not None
            assert updated_token.access_token == "access-2"
            assert updated_token.refresh_token == "refresh-2"
            assert updated_token.scope == "sleep profile"

            deleted = repository.delete_token(user_id=user_id)
            assert deleted is True
            assert repository.get_token(user_id=user_id) is None
            assert repository.delete_token(user_id=user_id) is False


def test_fitbit_token_repository_get_returns_none_when_missing() -> None:
    with _temporary_migrated_database() as database_url:
        session_factory = sessionmaker(
            bind=create_engine(to_sqlalchemy_database_url(database_url)),
            expire_on_commit=False,
        )

        with session_factory() as session:
            repository = FitbitTokenRepository(session=session)
            assert (
                repository.get_token(user_id=uuid.UUID("00000000-0000-0000-0000-00000000aa12"))
                is None
            )
            assert session.query(FitbitToken).count() == 0


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for Fitbit token repository tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_fitbit_token_repo_{uuid.uuid4().hex[:8]}"
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
