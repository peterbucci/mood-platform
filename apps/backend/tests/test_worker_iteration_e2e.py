from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import psycopg
from app.db.session import to_sqlalchemy_database_url
from app.services.request_fulfillment_service import FitbitClientProtocol
from app.worker import process_pending_once
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker


def _find_backend_root() -> Path:
    file_path = Path(__file__).resolve()
    for parent in file_path.parents:
        if (parent / "alembic.ini").exists() and (parent / "app").is_dir():
            return parent
        nested_backend = parent / "apps" / "backend"
        if (nested_backend / "alembic.ini").exists() and (nested_backend / "app").is_dir():
            return nested_backend
    raise RuntimeError("Could not locate backend root containing alembic.ini and app/.")


ROOT_DIR = _find_backend_root()
ALEMBIC_CONFIG = ROOT_DIR / "alembic.ini"


class StubFitbitClient(FitbitClientProtocol):
    def fetch_user_data(self, *, user_id: str) -> dict[str, Any]:
        del user_id
        return {"steps": {"count": 3210}}


def test_worker_single_iteration_fulfills_pending_request() -> None:
    user_id = "00000000-0000-0000-0000-00000000ff01"
    request_id = "req_worker_e2e_1"

    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _insert_pending_request(
            database_url=database_url,
            request_id=request_id,
            user_id=user_id,
        )

        session_factory = _session_factory(database_url)
        processed_count = process_pending_once(
            session_factory=session_factory,
            fitbit_client=StubFitbitClient(),
            user_batch_size=100,
            request_batch_size=100,
            lock_owner_id="worker-e2e",
            lock_ttl_seconds=30.0,
            lock_prefix="fulfillment_lock",
        )

        assert processed_count == 1

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
                request_row = cursor.fetchone()
                assert request_row is not None
                assert request_row[0] == "fulfilled"
                assert request_row[1] is not None

                cursor.execute(
                    """
                    SELECT source, data
                    FROM features
                    WHERE id = %s
                    """,
                    (request_row[1],),
                )
                feature_row = cursor.fetchone()

        assert feature_row is not None
        assert feature_row[0] == "fitbit-pipeline"
        parsed_payload = json.loads(feature_row[1])
        assert parsed_payload["steps"] == {"count": 3210}
        assert "notes" in parsed_payload
        assert "missing_hrv" in parsed_payload["notes"]


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for worker iteration tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_worker_iteration_{uuid.uuid4().hex[:8]}"
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


def _insert_pending_request(
    *,
    database_url: str,
    request_id: str,
    user_id: str,
) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO requests (id, "userId", "createdAt", status, "featureId", source)
                VALUES (%s, %s, %s, 'pending', NULL, 'phone')
                """,
                (request_id, user_id, 1700000000),
            )
        connection.commit()


def _session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(
        bind=create_engine(to_sqlalchemy_database_url(database_url)),
        expire_on_commit=False,
    )
