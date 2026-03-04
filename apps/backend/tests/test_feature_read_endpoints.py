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
CURRENT_USER_ID = "00000000-0000-0000-0000-00000000bb01"
OTHER_USER_ID = "00000000-0000-0000-0000-00000000bb02"


def test_get_features_latest_returns_404_when_empty(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.get("/features/latest")

        assert response.status_code == 404
        assert response.json() == {"detail": "No features found for current user."}

        db_session._session_factory.cache_clear()


def test_get_feature_by_id_returns_404_when_not_found(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.get("/features/missing-feature-id")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Feature missing-feature-id was not found for current user."
        }

        db_session._session_factory.cache_clear()


def test_feature_read_endpoints_return_expected_payload_and_pagination(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_features(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            latest_response = client.get("/features/latest")
            by_id_response = client.get("/features/22222222-2222-2222-2222-222222222222")
            list_page_1 = client.get("/features?limit=1&offset=0")
            list_page_2 = client.get("/features?limit=1&offset=1")

        assert latest_response.status_code == 200
        assert latest_response.json() == {
            "id": "22222222-2222-2222-2222-222222222222",
            "userId": CURRENT_USER_ID,
            "createdAt": 1700000100,
            "source": "phone-request",
            "data": {"steps": 2000, "mood": "calm"},
        }

        assert by_id_response.status_code == 200
        assert by_id_response.json() == latest_response.json()

        assert list_page_1.status_code == 200
        assert list_page_1.json() == {
            "items": [latest_response.json()],
            "limit": 1,
            "offset": 0,
        }

        assert list_page_2.status_code == 200
        assert list_page_2.json() == {
            "items": [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "userId": CURRENT_USER_ID,
                    "createdAt": 1700000000,
                    "source": "phone-request",
                    "data": {"steps": 1000, "mood": "energized"},
                }
            ],
            "limit": 1,
            "offset": 1,
        }

        db_session._session_factory.cache_clear()


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for feature read endpoint tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_feature_read_{uuid.uuid4().hex[:8]}"
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


def _seed_features(*, database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO features (id, "userId", "createdAt", source, data)
                VALUES (%s, %s, %s, %s, %s),
                       (%s, %s, %s, %s, %s),
                       (%s, %s, %s, %s, %s)
                """,
                (
                    "11111111-1111-1111-1111-111111111111",
                    CURRENT_USER_ID,
                    1700000000,
                    "phone-request",
                    json.dumps({"steps": 1000, "mood": "energized"}),
                    "22222222-2222-2222-2222-222222222222",
                    CURRENT_USER_ID,
                    1700000100,
                    "phone-request",
                    json.dumps({"steps": 2000, "mood": "calm"}),
                    "33333333-3333-3333-3333-333333333333",
                    OTHER_USER_ID,
                    1700000200,
                    "phone-request",
                    json.dumps({"steps": 3000, "mood": "stressed"}),
                ),
            )
        connection.commit()
