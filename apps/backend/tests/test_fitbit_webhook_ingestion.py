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
from app.services.encryption_service import build_encryption_service
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy.engine import make_url

ROOT_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_CONFIG = ROOT_DIR / "apps" / "backend" / "alembic.ini"

OWNER_USER_ID = "00000000-0000-0000-0000-00000000bb01"
FITBIT_USER_ID = "fitbit-user-1"
WEBHOOK_SECRET = "test-fitbit-webhook-secret"
WEBHOOK_URL = "/fitbit/webhook"
TEST_ENCRYPTION_KEY = "Qv2K-KSS7eDYAf9H2JWzImrxNr7AWyP3w7k3TKTKuig="


def test_webhook_valid_signature_returns_204(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_integration_settings(database_url=database_url, webhook_secret=WEBHOOK_SECRET)
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
        db_session._session_factory.cache_clear()


def test_webhook_returns_500_when_secret_not_configured(monkeypatch) -> None:
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
                headers={
                    "Content-Type": "application/json",
                    "X-Fitbit-Signature": "deadbeef",
                },
            )

        assert response.status_code == 500
        assert response.json() == {"detail": "Fitbit integration not configured."}
        db_session._session_factory.cache_clear()


def test_webhook_invalid_signature_returns_403(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_integration_settings(database_url=database_url, webhook_secret=WEBHOOK_SECRET)
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
        db_session._session_factory.cache_clear()


def test_webhook_missing_signature_returns_401(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_integration_settings(database_url=database_url, webhook_secret=WEBHOOK_SECRET)
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
        db_session._session_factory.cache_clear()


def test_webhook_signature_uses_raw_body_bytes(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_integration_settings(database_url=database_url, webhook_secret=WEBHOOK_SECRET)
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
        db_session._session_factory.cache_clear()


def test_webhook_duplicate_events_for_same_user_return_204(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_integration_settings(database_url=database_url, webhook_secret=WEBHOOK_SECRET)
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
    env["APP_SECRET_ENCRYPTION_KEY"] = TEST_ENCRYPTION_KEY
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
    monkeypatch.setenv("APP_SECRET_ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)
    monkeypatch.setenv("FITBIT_WEBHOOK_COALESCE_SECONDS", "10")
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


def _build_signature(*, secret: str, raw_body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()


def _seed_fitbit_integration_settings(*, database_url: str, webhook_secret: str) -> None:
    encryption_service = build_encryption_service(TEST_ENCRYPTION_KEY)
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO integration_settings (id, fitbit_webhook_secret_encrypted)
                VALUES (1, %s)
                ON CONFLICT (id) DO UPDATE
                SET fitbit_webhook_secret_encrypted = EXCLUDED.fitbit_webhook_secret_encrypted,
                    updated_at = now()
                """,
                (encryption_service.encrypt_value(webhook_secret),),
            )
        connection.commit()
