from __future__ import annotations

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
TEST_ENCRYPTION_KEY = "Qv2K-KSS7eDYAf9H2JWzImrxNr7AWyP3w7k3TKTKuig="


def test_get_fitbit_settings_returns_masked_values(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_integration_settings(
            database_url=database_url,
            client_id="fitbit-client-id",
            client_secret="fitbit-secret-1234",
            redirect_uri="http://localhost:8000/fitbit/oauth/callback",
            scope="activity sleep",
            subscriber_id="subscriber-1",
            webhook_secret="webhook-secret-9876",
        )
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.get("/settings/fitbit")

        assert response.status_code == 200
        assert response.json() == {
            "clientId": "fitbit-client-id",
            "clientSecretMasked": "********1234",
            "redirectUri": "http://localhost:8000/fitbit/oauth/callback",
            "scope": "activity sleep",
            "subscriberId": "subscriber-1",
            "webhookSecretMasked": "********9876",
            "hasClientSecret": True,
            "hasWebhookSecret": True,
        }
        db_session._session_factory.cache_clear()


def test_put_fitbit_settings_stores_and_masks_values(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.put(
                "/settings/fitbit",
                json={
                    "clientId": "new-fitbit-client",
                    "clientSecret": "new-fitbit-secret-2222",
                    "redirectUri": "http://localhost:8000/fitbit/oauth/callback",
                    "scope": "activity heartrate sleep",
                    "subscriberId": "subscriber-2",
                    "webhookSecret": "new-webhook-secret-3333",
                },
            )

        assert response.status_code == 200
        assert response.json() == {
            "clientId": "new-fitbit-client",
            "clientSecretMasked": "********2222",
            "redirectUri": "http://localhost:8000/fitbit/oauth/callback",
            "scope": "activity heartrate sleep",
            "subscriberId": "subscriber-2",
            "webhookSecretMasked": "********3333",
            "hasClientSecret": True,
            "hasWebhookSecret": True,
        }

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        fitbit_client_id,
                        fitbit_client_secret_encrypted,
                        fitbit_redirect_uri,
                        fitbit_oauth_scope,
                        fitbit_subscriber_id,
                        fitbit_webhook_secret_encrypted
                    FROM integration_settings
                    WHERE id = 1
                    """
                )
                row = cursor.fetchone()

        assert row is not None
        assert row[0] == "new-fitbit-client"
        assert row[1] != "new-fitbit-secret-2222"
        assert row[2] == "http://localhost:8000/fitbit/oauth/callback"
        assert row[3] == "activity heartrate sleep"
        assert row[4] == "subscriber-2"
        assert row[5] != "new-webhook-secret-3333"
        encryption_service = build_encryption_service(TEST_ENCRYPTION_KEY)
        assert encryption_service.decrypt_value(row[1]) == "new-fitbit-secret-2222"
        assert encryption_service.decrypt_value(row[5]) == "new-webhook-secret-3333"
        db_session._session_factory.cache_clear()


def test_put_fitbit_settings_preserves_existing_client_secret_when_omitted(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _seed_fitbit_integration_settings(
            database_url=database_url,
            client_id="fitbit-client-id",
            client_secret="fitbit-secret-1234",
            redirect_uri="http://localhost:8000/fitbit/oauth/callback",
            scope="activity sleep",
            subscriber_id="subscriber-1",
            webhook_secret="webhook-secret-9876",
        )
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.put(
                "/settings/fitbit",
                json={
                    "clientId": "fitbit-client-id",
                    "redirectUri": "http://localhost:8000/fitbit/oauth/callback",
                    "scope": "activity sleep",
                    "subscriberId": "subscriber-9",
                },
            )

        assert response.status_code == 200
        assert response.json()["clientSecretMasked"] == "********1234"

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT fitbit_client_secret_encrypted, fitbit_subscriber_id
                    FROM integration_settings
                    WHERE id = 1
                    """
                )
                row = cursor.fetchone()

        assert row is not None
        encryption_service = build_encryption_service(TEST_ENCRYPTION_KEY)
        assert encryption_service.decrypt_value(row[0]) == "fitbit-secret-1234"
        assert row[1] == "subscriber-9"
        db_session._session_factory.cache_clear()


def test_put_fitbit_settings_validates_required_fields(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.put(
                "/settings/fitbit",
                json={
                    "clientId": "",
                    "clientSecret": "",
                    "redirectUri": "",
                },
            )

        assert response.status_code == 422
        assert response.json() == {
            "detail": {
                "message": "Invalid Fitbit integration settings.",
                "errors": {
                    "clientId": "Client ID is required.",
                    "clientSecret": "Client Secret is required.",
                    "redirectUri": "Redirect URI is required.",
                },
            }
        }
        db_session._session_factory.cache_clear()


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for Fitbit settings endpoint tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_fitbit_settings_{uuid.uuid4().hex[:8]}"
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
    db_session._session_factory.cache_clear()


def _seed_fitbit_integration_settings(
    *,
    database_url: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    scope: str,
    subscriber_id: str,
    webhook_secret: str,
) -> None:
    encryption_service = build_encryption_service(TEST_ENCRYPTION_KEY)
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO integration_settings (
                    id,
                    fitbit_client_id,
                    fitbit_client_secret_encrypted,
                    fitbit_redirect_uri,
                    fitbit_oauth_scope,
                    fitbit_subscriber_id,
                    fitbit_webhook_secret_encrypted
                )
                VALUES (1, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET fitbit_client_id = EXCLUDED.fitbit_client_id,
                    fitbit_client_secret_encrypted = EXCLUDED.fitbit_client_secret_encrypted,
                    fitbit_redirect_uri = EXCLUDED.fitbit_redirect_uri,
                    fitbit_oauth_scope = EXCLUDED.fitbit_oauth_scope,
                    fitbit_subscriber_id = EXCLUDED.fitbit_subscriber_id,
                    fitbit_webhook_secret_encrypted = EXCLUDED.fitbit_webhook_secret_encrypted,
                    updated_at = now()
                """,
                (
                    client_id,
                    encryption_service.encrypt_value(client_secret),
                    redirect_uri,
                    scope,
                    subscriber_id,
                    encryption_service.encrypt_value(webhook_secret),
                ),
            )
        connection.commit()
