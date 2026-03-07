from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
from app.db import session as db_session
from app.main import app
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy.engine import make_url

ROOT_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_CONFIG = ROOT_DIR / "apps" / "backend" / "alembic.ini"
CURRENT_USER_ID = "00000000-0000-0000-0000-00000000bc01"
OTHER_USER_ID = "00000000-0000-0000-0000-00000000bc02"


def test_delete_feature_success(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        _insert_feature(
            database_url=database_url,
            feature_id="feat_delete_1",
            user_id=CURRENT_USER_ID,
            created_at=1700001000,
        )

        with TestClient(app) as client:
            response = client.delete("/features/feat_delete_1")

        assert response.status_code == 200
        assert response.json() == {"id": "feat_delete_1"}

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM features WHERE id = %s", ("feat_delete_1",))
                count = cursor.fetchone()[0]
        assert count == 0

        db_session._session_factory.cache_clear()


def test_delete_feature_returns_404_when_missing(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.delete("/features/does-not-exist")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Feature does-not-exist was not found for current user."
        }

        db_session._session_factory.cache_clear()


def test_delete_feature_returns_404_for_other_user(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        _insert_feature(
            database_url=database_url,
            feature_id="feat_delete_other_user",
            user_id=OTHER_USER_ID,
            created_at=1700001001,
        )

        with TestClient(app) as client:
            response = client.delete("/features/feat_delete_other_user")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Feature feat_delete_other_user was not found for current user."
        }

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM features WHERE id = %s",
                    ("feat_delete_other_user",),
                )
                count = cursor.fetchone()[0]
        assert count == 1

        db_session._session_factory.cache_clear()


def test_delete_feature_deletes_linked_request_and_label(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        feature_id = "feat_delete_with_refs"
        request_id = "req_delete_with_refs"
        _insert_feature(
            database_url=database_url,
            feature_id=feature_id,
            user_id=CURRENT_USER_ID,
            created_at=1700001002,
        )
        _insert_request(
            database_url=database_url,
            request_id=request_id,
            user_id=CURRENT_USER_ID,
            created_at=1700001003,
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

        with TestClient(app) as client:
            response = client.delete(f"/features/{feature_id}")

        assert response.status_code == 200
        assert response.json() == {"id": feature_id}

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM features WHERE id = %s", (feature_id,))
                feature_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM labels WHERE "featureId" = %s', (feature_id,))
                label_count = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM requests
                    WHERE id = %s
                    """,
                    (request_id,),
                )
                request_count = cursor.fetchone()[0]

        assert feature_count == 0
        assert label_count == 0
        assert request_count == 0

        db_session._session_factory.cache_clear()


def test_delete_feature_deletes_all_requests_linked_to_snapshot(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        feature_id = "feat_delete_multi_refs"
        _insert_feature(
            database_url=database_url,
            feature_id=feature_id,
            user_id=CURRENT_USER_ID,
            created_at=1700001004,
        )
        _insert_request(
            database_url=database_url,
            request_id="req_multi_1",
            user_id=CURRENT_USER_ID,
            created_at=1700001005,
            status="fulfilled",
            source="phone",
            feature_id=feature_id,
        )
        _insert_request(
            database_url=database_url,
            request_id="req_multi_2",
            user_id=CURRENT_USER_ID,
            created_at=1700001006,
            status="fulfilled",
            source="phone",
            feature_id=feature_id,
        )

        with TestClient(app) as client:
            response = client.delete(f"/features/{feature_id}")

        assert response.status_code == 200
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM requests
                    WHERE id IN ('req_multi_1', 'req_multi_2')
                    ORDER BY id ASC
                    """
                )
                rows = cursor.fetchall()
        assert rows == []

        db_session._session_factory.cache_clear()


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for feature delete endpoint tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_feature_delete_{uuid.uuid4().hex[:8]}"
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
                    "post-run label",
                    "calm",
                    "calm",
                ),
            )
        connection.commit()
