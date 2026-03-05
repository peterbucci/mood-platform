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
CURRENT_USER_ID = "00000000-0000-0000-0000-00000000ef01"
OTHER_USER_ID = "00000000-0000-0000-0000-00000000ef02"


def test_post_labels_creates_label_for_owned_feature(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        feature_id = "11111111-1111-1111-1111-111111111111"
        request_id = "req-label-1"
        _insert_feature(
            database_url=database_url,
            feature_id=feature_id,
            user_id=CURRENT_USER_ID,
            created_at=1700000000,
            source="fitbit-pipeline",
            data={"steps": {"count": 1000}},
        )
        _insert_request(
            database_url=database_url,
            request_id=request_id,
            user_id=CURRENT_USER_ID,
            created_at=1700000001,
            status="fulfilled",
            source="phone",
            feature_id=feature_id,
        )

        with TestClient(app) as client:
            response = client.post(
                "/labels",
                json={
                    "featureId": feature_id,
                    "label": "Felt productive",
                    "emotionWord": "happy",
                    "category": "energized",
                },
            )

        assert response.status_code == 201
        payload = response.json()
        assert payload["userId"] == CURRENT_USER_ID
        assert payload["featureId"] == feature_id
        assert payload["requestId"] == request_id
        assert payload["label"] == "Felt productive"
        assert payload["emotionWord"] == "happy"
        assert payload["category"] == "energized"
        uuid.UUID(payload["id"])
        assert isinstance(payload["createdAt"], str)

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT "userId", "featureId", "requestId", label, "emotionWord", category
                    FROM labels
                    WHERE id = %s
                    """,
                    (payload["id"],),
                )
                row = cursor.fetchone()

        assert row == (
            CURRENT_USER_ID,
            feature_id,
            request_id,
            "Felt productive",
            "happy",
            "energized",
        )

        db_session._session_factory.cache_clear()


def test_post_labels_rejects_feature_not_owned_by_current_user(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        feature_id = "22222222-2222-2222-2222-222222222222"
        _insert_feature(
            database_url=database_url,
            feature_id=feature_id,
            user_id=OTHER_USER_ID,
            created_at=1700000100,
            source="fitbit-pipeline",
            data={"steps": {"count": 500}},
        )
        _insert_request(
            database_url=database_url,
            request_id="req-label-2",
            user_id=OTHER_USER_ID,
            created_at=1700000101,
            status="fulfilled",
            source="phone",
            feature_id=feature_id,
        )

        with TestClient(app) as client:
            response = client.post(
                "/labels",
                json={
                    "featureId": feature_id,
                    "label": "Not mine",
                    "emotionWord": "anxious",
                    "category": "stressed",
                },
            )

        assert response.status_code == 404
        assert response.json() == {
            "detail": f"Feature {feature_id} was not found for current user."
        }

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM labels")
                count = cursor.fetchone()[0]
        assert count == 0

        db_session._session_factory.cache_clear()


def test_post_labels_validates_category_taxonomy(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.post(
                "/labels",
                json={
                    "featureId": "33333333-3333-3333-3333-333333333333",
                    "label": "Invalid category payload",
                    "emotionWord": "okay",
                    "category": "neutral",
                },
            )

        assert response.status_code == 422
        db_session._session_factory.cache_clear()


def test_labels_cascade_when_feature_deleted(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        feature_id = "44444444-4444-4444-4444-444444444444"
        request_id = "req-label-4"
        _insert_feature(
            database_url=database_url,
            feature_id=feature_id,
            user_id=CURRENT_USER_ID,
            created_at=1700000200,
            source="fitbit-pipeline",
            data={"steps": {"count": 100}},
        )
        _insert_request(
            database_url=database_url,
            request_id=request_id,
            user_id=CURRENT_USER_ID,
            created_at=1700000201,
            status="fulfilled",
            source="phone",
            feature_id=feature_id,
        )
        _create_label_via_api(feature_id=feature_id)

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM features WHERE id = %s", (feature_id,))
            connection.commit()

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM labels WHERE "requestId" = %s', (request_id,))
                count = cursor.fetchone()[0]
        assert count == 0

        db_session._session_factory.cache_clear()


def test_labels_cascade_when_request_deleted(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        feature_id = "55555555-5555-5555-5555-555555555555"
        request_id = "req-label-5"
        _insert_feature(
            database_url=database_url,
            feature_id=feature_id,
            user_id=CURRENT_USER_ID,
            created_at=1700000300,
            source="fitbit-pipeline",
            data={"steps": {"count": 450}},
        )
        _insert_request(
            database_url=database_url,
            request_id=request_id,
            user_id=CURRENT_USER_ID,
            created_at=1700000301,
            status="fulfilled",
            source="phone",
            feature_id=feature_id,
        )
        _create_label_via_api(feature_id=feature_id)

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM requests WHERE id = %s", (request_id,))
            connection.commit()

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM labels WHERE "featureId" = %s', (feature_id,))
                count = cursor.fetchone()[0]
        assert count == 0

        db_session._session_factory.cache_clear()


def _create_label_via_api(*, feature_id: str) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/labels",
            json={
                "featureId": feature_id,
                "label": "Linked label",
                "emotionWord": "calm",
                "category": "calm",
            },
        )
    assert response.status_code == 201


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for labels endpoint tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_labels_{uuid.uuid4().hex[:8]}"
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


def _insert_feature(
    *,
    database_url: str,
    feature_id: str,
    user_id: str,
    created_at: int,
    source: str,
    data: dict[str, object],
) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO features (id, "userId", "createdAt", source, data)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (feature_id, user_id, created_at, source, json.dumps(data)),
            )
        connection.commit()
