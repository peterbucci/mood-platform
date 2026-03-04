from __future__ import annotations

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


def test_post_features_request_persists_pending_request(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)

        monkeypatch.setenv("DATABASE_URL", database_url)
        monkeypatch.setenv("OWNER_USER_ID", "00000000-0000-0000-0000-00000000aa01")
        db_session._session_factory.cache_clear()

        with TestClient(app) as client:
            response = client.post("/features/request")

        assert response.status_code == 200
        payload = response.json()
        assert set(payload.keys()) == {"requestId", "status"}
        assert payload["status"] == "pending"

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT "userId", status, source, "featureId"
                    FROM requests
                    WHERE id = %s
                    """,
                    (payload["requestId"],),
                )
                stored_request = cursor.fetchone()

        assert stored_request is not None
        assert stored_request[0] == "00000000-0000-0000-0000-00000000aa01"
        assert stored_request[1] == "pending"
        assert stored_request[2] == "phone"
        assert stored_request[3] is None

        db_session._session_factory.cache_clear()


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for request endpoint integration tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_feature_request_{uuid.uuid4().hex[:8]}"
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
