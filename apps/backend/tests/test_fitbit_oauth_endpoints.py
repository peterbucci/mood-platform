from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import psycopg
from app.db import session as db_session
from app.main import app
from app.services.fitbit_oauth_service import FitbitOAuthService
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy.engine import make_url

ROOT_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_CONFIG = ROOT_DIR / "apps" / "backend" / "alembic.ini"
OWNER_USER_ID = "00000000-0000-0000-0000-00000000fa01"


def test_fitbit_oauth_start_redirects_to_fitbit(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.get("/fitbit/oauth/start", follow_redirects=False)

        assert response.status_code == 307
        assert "location" in response.headers

        parsed_location = urlparse(response.headers["location"])
        assert parsed_location.scheme == "https"
        assert parsed_location.netloc == "www.fitbit.com"
        assert parsed_location.path == "/oauth2/authorize"

        query = parse_qs(parsed_location.query)
        assert query["client_id"] == ["test-fitbit-client-id"]
        assert query["redirect_uri"] == ["http://localhost:8000/fitbit/oauth/callback"]
        assert query["response_type"] == ["code"]
        assert query["scope"] == ["sleep heartrate activity profile"]

        state = query["state"][0]
        assert state

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT state
                    FROM fitbit_oauth_states
                    WHERE state = %s
                    """,
                    (state,),
                )
                state_row = cursor.fetchone()

        assert state_row is not None
        db_session._session_factory.cache_clear()


def test_fitbit_oauth_callback_exchanges_code_and_persists_tokens(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        def _mock_request_tokens(self, *, code: str) -> dict[str, object]:
            assert code == "oauth-code-1"
            return {
                "access_token": "access-token-1",
                "refresh_token": "refresh-token-1",
                "expires_in": 3600,
                "scope": "sleep heartrate activity profile",
                "user_id": "fitbit-user-1",
            }

        monkeypatch.setattr(FitbitOAuthService, "_request_tokens", _mock_request_tokens)

        with TestClient(app) as client:
            start_response = client.get("/fitbit/oauth/start", follow_redirects=False)
            state = parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]
            callback_response = client.get(
                "/fitbit/oauth/callback",
                params={"code": "oauth-code-1", "state": state},
            )

        assert callback_response.status_code == 200
        callback_payload = callback_response.json()
        assert callback_payload["connected"] is True
        assert callback_payload["expiresAt"] is not None

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT fitbit_user_id, access_token, refresh_token, scope
                    FROM fitbit_tokens
                    WHERE user_id = %s
                    """,
                    (OWNER_USER_ID,),
                )
                token_row = cursor.fetchone()

        assert token_row is not None
        assert token_row[0] == "fitbit-user-1"
        assert token_row[1] == "access-token-1"
        assert token_row[2] == "refresh-token-1"
        assert token_row[3] == "sleep heartrate activity profile"
        db_session._session_factory.cache_clear()


def test_fitbit_oauth_status_reports_connection_state(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        def _mock_request_tokens(self, *, code: str) -> dict[str, object]:
            assert code == "oauth-code-2"
            return {
                "access_token": "access-token-2",
                "refresh_token": "refresh-token-2",
                "expires_in": 1800,
                "scope": "sleep heartrate activity profile",
                "user_id": "fitbit-user-2",
            }

        monkeypatch.setattr(FitbitOAuthService, "_request_tokens", _mock_request_tokens)

        with TestClient(app) as client:
            initial_status = client.get("/fitbit/oauth/status")
            assert initial_status.status_code == 200
            assert initial_status.json() == {"connected": False, "expiresAt": None}

            start_response = client.get("/fitbit/oauth/start", follow_redirects=False)
            state = parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]
            callback_response = client.get(
                "/fitbit/oauth/callback",
                params={"code": "oauth-code-2", "state": state},
            )
            assert callback_response.status_code == 200

            connected_status = client.get("/fitbit/oauth/status")

        assert connected_status.status_code == 200
        connected_payload = connected_status.json()
        assert connected_payload["connected"] is True
        assert connected_payload["expiresAt"] is not None
        db_session._session_factory.cache_clear()


def test_fitbit_oauth_unlink_clears_connection(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        def _mock_request_tokens(self, *, code: str) -> dict[str, object]:
            assert code == "oauth-code-3"
            return {
                "access_token": "access-token-3",
                "refresh_token": "refresh-token-3",
                "expires_in": 3600,
                "scope": "sleep heartrate activity profile",
                "user_id": "fitbit-user-3",
            }

        monkeypatch.setattr(FitbitOAuthService, "_request_tokens", _mock_request_tokens)

        with TestClient(app) as client:
            start_response = client.get("/fitbit/oauth/start", follow_redirects=False)
            state = parse_qs(urlparse(start_response.headers["location"]).query)["state"][0]
            callback_response = client.get(
                "/fitbit/oauth/callback",
                params={"code": "oauth-code-3", "state": state},
            )
            assert callback_response.status_code == 200

            unlink_response = client.post("/fitbit/oauth/unlink")
            status_response = client.get("/fitbit/oauth/status")

        assert unlink_response.status_code == 200
        assert unlink_response.json() == {"success": True}
        assert status_response.status_code == 200
        assert status_response.json() == {"connected": False, "expiresAt": None}

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_id
                    FROM fitbit_tokens
                    WHERE user_id = %s
                    """,
                    (OWNER_USER_ID,),
                )
                token_row = cursor.fetchone()

        assert token_row is None
        db_session._session_factory.cache_clear()


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for Fitbit OAuth endpoint tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_fitbit_oauth_{uuid.uuid4().hex[:8]}"
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
    monkeypatch.setenv("OWNER_USER_ID", OWNER_USER_ID)
    monkeypatch.setenv("FITBIT_CLIENT_ID", "test-fitbit-client-id")
    monkeypatch.setenv("FITBIT_CLIENT_SECRET", "test-fitbit-client-secret")
    monkeypatch.setenv("FITBIT_REDIRECT_URI", "http://localhost:8000/fitbit/oauth/callback")
    db_session._session_factory.cache_clear()
