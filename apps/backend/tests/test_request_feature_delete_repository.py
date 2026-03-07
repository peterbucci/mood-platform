from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
import pytest
from app.db import session as db_session
from app.db.models import Feature
from app.repositories.request_feature_delete_repository import (
    RequestFeatureDeleteRepository,
    RequestFeatureDeleteWriteError,
)
from psycopg import sql
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

ROOT_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_CONFIG = ROOT_DIR / "apps" / "backend" / "alembic.ini"
CURRENT_USER_ID = "00000000-0000-0000-0000-00000000de01"


def test_delete_unit_by_request_id_rolls_back_when_feature_delete_fails(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        feature_id = "feat_repo_rollback"
        request_id = "req_repo_rollback"
        _insert_feature(
            database_url=database_url,
            feature_id=feature_id,
            user_id=CURRENT_USER_ID,
            created_at=1700002000,
        )
        _insert_request(
            database_url=database_url,
            request_id=request_id,
            user_id=CURRENT_USER_ID,
            created_at=1700002001,
            status="fulfilled",
            source="phone",
            feature_id=feature_id,
        )
        _insert_label(
            database_url=database_url,
            user_id=CURRENT_USER_ID,
            feature_id=feature_id,
            request_id=request_id,
        )

        session = db_session._session_factory()()
        repository = RequestFeatureDeleteRepository(session=session)
        original_execute = session.execute
        failure_injected = False

        def execute_with_failure(statement, *args, **kwargs):
            nonlocal failure_injected
            statement_table = getattr(statement, "table", None)
            if (
                not failure_injected
                and statement_table is not None
                and getattr(statement_table, "name", None) == Feature.__tablename__
            ):
                failure_injected = True
                raise IntegrityError(
                    "DELETE FROM features",
                    None,
                    Exception("forced feature delete failure"),
                )
            return original_execute(statement, *args, **kwargs)

        monkeypatch.setattr(session, "execute", execute_with_failure)

        try:
            with pytest.raises(RequestFeatureDeleteWriteError):
                repository.delete_unit_by_request_id(
                    user_id=CURRENT_USER_ID,
                    request_id=request_id,
                    commit=False,
                )
        finally:
            session.close()

        assert failure_injected is True

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM features WHERE id = %s", (feature_id,))
                feature_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM requests WHERE id = %s", (request_id,))
                request_count = cursor.fetchone()[0]
                cursor.execute(
                    'SELECT COUNT(*) FROM labels WHERE "requestId" = %s AND "featureId" = %s',
                    (request_id, feature_id),
                )
                label_count = cursor.fetchone()[0]

        assert feature_count == 1
        assert request_count == 1
        assert label_count == 1

        db_session._session_factory.cache_clear()


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for repository delete tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_delete_repo_{uuid.uuid4().hex[:8]}"
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


def _configure_runtime_env(*, monkeypatch, database_url: str) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("OWNER_USER_ID", CURRENT_USER_ID)
    db_session._session_factory.cache_clear()


def _insert_feature(*, database_url: str, feature_id: str, user_id: str, created_at: int) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO features (id, "userId", "createdAt", source, data)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (feature_id, user_id, created_at, "fitbit-pipeline", json.dumps({"steps": 1000})),
            )
        connection.commit()


def _insert_request(
    *,
    database_url: str,
    request_id: str,
    user_id: str,
    created_at: int,
    status: str,
    source: str,
    feature_id: str | None,
) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO requests (id, "userId", "createdAt", status, source, "featureId")
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (request_id, user_id, created_at, status, source, feature_id),
            )
        connection.commit()


def _insert_label(*, database_url: str, user_id: str, feature_id: str, request_id: str) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO labels (
                    id, "userId", "featureId", "requestId", label, "emotionWord", category
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    user_id,
                    feature_id,
                    request_id,
                    "snapshot mood",
                    "calm",
                    "calm",
                ),
            )
        connection.commit()
