from __future__ import annotations

import hashlib
import hmac
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

OWNER_USER_ID = "00000000-0000-0000-0000-00000000bb01"
FITBIT_USER_ID = "fitbit-user-1"
WEBHOOK_SECRET = "test-fitbit-webhook-secret"
WEBHOOK_URL = "/fitbit/webhook"


def test_webhook_valid_signature_returns_204_and_enqueues_job(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_token(
            database_url=database_url,
            user_id=OWNER_USER_ID,
            fitbit_user_id=FITBIT_USER_ID,
        )
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        raw_body = b'[{"collectionType":"sleep","date":"2026-03-05","ownerId":"fitbit-user-1"}]'
        signature = _build_signature(secret=WEBHOOK_SECRET, raw_body=raw_body)

        with TestClient(app) as client:
            response = client.post(
                WEBHOOK_URL,
                content=raw_body,
                headers={
                    "Content-Type": "application/json",
                    "X-Fitbit-Signature": signature,
                },
            )

        assert response.status_code == 204
        assert _count_webhook_jobs(database_url=database_url) == 1
        db_session._session_factory.cache_clear()


def test_webhook_invalid_signature_returns_403_and_does_not_enqueue(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_token(
            database_url=database_url,
            user_id=OWNER_USER_ID,
            fitbit_user_id=FITBIT_USER_ID,
        )
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        raw_body = b'[{"collectionType":"sleep","date":"2026-03-05","ownerId":"fitbit-user-1"}]'
        invalid_signature = "deadbeef"

        with TestClient(app) as client:
            response = client.post(
                WEBHOOK_URL,
                content=raw_body,
                headers={
                    "Content-Type": "application/json",
                    "X-Fitbit-Signature": invalid_signature,
                },
            )

        assert response.status_code == 403
        assert response.json() == {"detail": "Invalid webhook signature"}
        assert _count_webhook_jobs(database_url=database_url) == 0
        db_session._session_factory.cache_clear()


def test_webhook_missing_signature_returns_401_and_does_not_enqueue(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_token(
            database_url=database_url,
            user_id=OWNER_USER_ID,
            fitbit_user_id=FITBIT_USER_ID,
        )
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        raw_body = b'[{"collectionType":"sleep","date":"2026-03-05","ownerId":"fitbit-user-1"}]'

        with TestClient(app) as client:
            response = client.post(
                WEBHOOK_URL,
                content=raw_body,
                headers={"Content-Type": "application/json"},
            )

        assert response.status_code == 401
        assert response.json() == {"detail": "Missing webhook signature"}
        assert _count_webhook_jobs(database_url=database_url) == 0
        db_session._session_factory.cache_clear()


def test_webhook_signature_uses_raw_body_bytes(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_token(
            database_url=database_url,
            user_id=OWNER_USER_ID,
            fitbit_user_id=FITBIT_USER_ID,
        )
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        raw_body = (
            b'[\n  {"ownerId":"fitbit-user-1","date":"2026-03-05","collectionType":"sleep"}\n]'
        )
        reserialized_body = (
            b'[{"collectionType":"sleep","date":"2026-03-05","ownerId":"fitbit-user-1"}]'
        )
        wrong_signature = _build_signature(secret=WEBHOOK_SECRET, raw_body=reserialized_body)

        with TestClient(app) as client:
            response = client.post(
                WEBHOOK_URL,
                content=raw_body,
                headers={
                    "Content-Type": "application/json",
                    "X-Fitbit-Signature": wrong_signature,
                },
            )

        assert response.status_code == 403
        assert _count_webhook_jobs(database_url=database_url) == 0
        db_session._session_factory.cache_clear()


def test_webhook_coalesces_duplicate_jobs_for_same_user(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_token(
            database_url=database_url,
            user_id=OWNER_USER_ID,
            fitbit_user_id=FITBIT_USER_ID,
        )
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        raw_body = b'[{"collectionType":"sleep","date":"2026-03-05","ownerId":"fitbit-user-1"}]'
        signature = _build_signature(secret=WEBHOOK_SECRET, raw_body=raw_body)

        with TestClient(app) as client:
            first_response = client.post(
                WEBHOOK_URL,
                content=raw_body,
                headers={
                    "Content-Type": "application/json",
                    "X-Fitbit-Signature": signature,
                },
            )
            second_response = client.post(
                WEBHOOK_URL,
                content=raw_body,
                headers={
                    "Content-Type": "application/json",
                    "X-Fitbit-Signature": signature,
                },
            )

        assert first_response.status_code == 204
        assert second_response.status_code == 204
        assert _count_webhook_jobs(database_url=database_url) == 1
        db_session._session_factory.cache_clear()


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for Fitbit webhook ingestion tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_fitbit_webhook_{uuid.uuid4().hex[:8]}"
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
    monkeypatch.setenv("FITBIT_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setenv("FITBIT_WEBHOOK_COALESCE_SECONDS", "30")
    db_session._session_factory.cache_clear()


def _seed_fitbit_token(*, database_url: str, user_id: str, fitbit_user_id: str) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO users (id) VALUES (%s)", (user_id,))
            cursor.execute(
                """
                INSERT INTO fitbit_tokens (
                    user_id, fitbit_user_id, access_token, refresh_token, expires_at, scope
                )
                VALUES (%s, %s, %s, %s, now() + interval '1 day', %s)
                """,
                (
                    user_id,
                    fitbit_user_id,
                    "access-token",
                    "refresh-token",
                    "sleep heartrate activity profile",
                ),
            )
        connection.commit()


def _count_webhook_jobs(*, database_url: str) -> int:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM webhook_jobs")
            return int(cursor.fetchone()[0])


def _build_signature(*, secret: str, raw_body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
