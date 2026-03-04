from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from app.db import session as db_session
from app.main import app
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy.engine import make_url

ROOT_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_CONFIG = ROOT_DIR / "apps" / "backend" / "alembic.ini"
CURRENT_USER_ID = "00000000-0000-0000-0000-00000000cc01"


def test_feature_request_pipeline_e2e(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)

        monkeypatch.setenv("DATABASE_URL", database_url)
        monkeypatch.setenv("OWNER_USER_ID", CURRENT_USER_ID)
        db_session._session_factory.cache_clear()

        with TestClient(app) as client:
            create_response = client.post("/features/request")

            assert create_response.status_code == 200
            create_payload = create_response.json()
            request_id = create_payload["requestId"]
            assert create_payload["status"] == "pending"

            with psycopg.connect(database_url) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT status, "featureId"
                        FROM requests
                        WHERE id = %s
                        """,
                        (request_id,),
                    )
                    pending_row = cursor.fetchone()

                    assert pending_row is not None
                    assert pending_row[0] == "pending"
                    assert pending_row[1] is None

                    feature_id = str(uuid.uuid4())
                    created_at = int(datetime.now(tz=UTC).timestamp())
                    feature_payload = {"steps": 1234, "sleepHours": 7.2}

                    cursor.execute(
                        """
                        INSERT INTO features (id, "userId", "createdAt", source, data)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            feature_id,
                            CURRENT_USER_ID,
                            created_at,
                            "phone-request",
                            json.dumps(feature_payload),
                        ),
                    )
                    cursor.execute(
                        """
                        UPDATE requests
                        SET status = 'fulfilled', "featureId" = %s
                        WHERE id = %s
                        """,
                        (feature_id, request_id),
                    )
                connection.commit()

            with psycopg.connect(database_url) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT status, "featureId"
                        FROM requests
                        WHERE id = %s
                        """,
                        (request_id,),
                    )
                    fulfilled_row = cursor.fetchone()

            assert fulfilled_row is not None
            assert fulfilled_row[0] == "fulfilled"
            assert fulfilled_row[1] == feature_id

            feature_response = client.get(f"/features/{feature_id}")

        assert feature_response.status_code == 200
        assert feature_response.json() == {
            "id": feature_id,
            "userId": CURRENT_USER_ID,
            "createdAt": created_at,
            "source": "phone-request",
            "data": {"steps": 1234, "sleepHours": 7.2},
        }

        db_session._session_factory.cache_clear()


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for pipeline e2e tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_pipeline_e2e_{uuid.uuid4().hex[:8]}"
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
