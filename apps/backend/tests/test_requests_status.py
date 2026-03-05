from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
import pytest
from app.db import session as db_session
from app.main import app
from fastapi.testclient import TestClient
from psycopg import sql
from sqlalchemy.engine import make_url

ROOT_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_CONFIG = ROOT_DIR / "apps" / "backend" / "alembic.ini"
CURRENT_USER_ID = "00000000-0000-0000-0000-00000000dd01"
OTHER_USER_ID = "00000000-0000-0000-0000-00000000dd02"


def test_get_requests_returns_empty_list_when_no_requests(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.get("/requests")

        assert response.status_code == 200
        assert response.json() == {"items": [], "limit": 20, "offset": 0}

        db_session._session_factory.cache_clear()


def test_get_requests_includes_pending_request(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        _insert_request(
            database_url=database_url,
            request_id="req_pending_1",
            user_id=CURRENT_USER_ID,
            created_at=1700000000,
            status="pending",
            source="phone",
            feature_id=None,
        )

        with TestClient(app) as client:
            response = client.get("/requests")

        assert response.status_code == 200
        assert response.json() == {
            "items": [
                {
                    "id": "req_pending_1",
                    "userId": CURRENT_USER_ID,
                    "createdAt": 1700000000,
                    "status": "pending",
                    "source": "phone",
                    "featureId": None,
                }
            ],
            "limit": 20,
            "offset": 0,
        }

        db_session._session_factory.cache_clear()


def test_get_requests_includes_feature_id_for_fulfilled_request(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        _insert_feature(
            database_url=database_url,
            feature_id="feat_1",
            user_id=CURRENT_USER_ID,
            created_at=1700000200,
            source="phone-request",
            data={"steps": 1200},
        )
        _insert_request(
            database_url=database_url,
            request_id="req_fulfilled_1",
            user_id=CURRENT_USER_ID,
            created_at=1700000100,
            status="fulfilled",
            source="phone",
            feature_id="feat_1",
        )

        with TestClient(app) as client:
            response = client.get("/requests")

        assert response.status_code == 200
        assert response.json() == {
            "items": [
                {
                    "id": "req_fulfilled_1",
                    "userId": CURRENT_USER_ID,
                    "createdAt": 1700000100,
                    "status": "fulfilled",
                    "source": "phone",
                    "featureId": "feat_1",
                }
            ],
            "limit": 20,
            "offset": 0,
        }

        db_session._session_factory.cache_clear()


def test_get_requests_applies_pagination_and_ordering(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        _insert_request(
            database_url=database_url,
            request_id="req_1",
            user_id=CURRENT_USER_ID,
            created_at=1700000000,
            status="pending",
            source="phone",
            feature_id=None,
        )
        _insert_request(
            database_url=database_url,
            request_id="req_2",
            user_id=CURRENT_USER_ID,
            created_at=1700000100,
            status="pending",
            source="phone",
            feature_id=None,
        )
        _insert_request(
            database_url=database_url,
            request_id="req_3",
            user_id=CURRENT_USER_ID,
            created_at=1700000200,
            status="pending",
            source="phone",
            feature_id=None,
        )
        _insert_request(
            database_url=database_url,
            request_id="req_other_user",
            user_id=OTHER_USER_ID,
            created_at=1700000300,
            status="pending",
            source="phone",
            feature_id=None,
        )

        with TestClient(app) as client:
            first_page = client.get("/requests?limit=1&offset=0")
            second_page = client.get("/requests?limit=1&offset=1")

        assert first_page.status_code == 200
        assert first_page.json() == {
            "items": [
                {
                    "id": "req_3",
                    "userId": CURRENT_USER_ID,
                    "createdAt": 1700000200,
                    "status": "pending",
                    "source": "phone",
                    "featureId": None,
                }
            ],
            "limit": 1,
            "offset": 0,
        }

        assert second_page.status_code == 200
        assert second_page.json() == {
            "items": [
                {
                    "id": "req_2",
                    "userId": CURRENT_USER_ID,
                    "createdAt": 1700000100,
                    "status": "pending",
                    "source": "phone",
                    "featureId": None,
                }
            ],
            "limit": 1,
            "offset": 1,
        }

        db_session._session_factory.cache_clear()


def test_get_request_by_id_returns_status_and_feature_id(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)
        _insert_feature(
            database_url=database_url,
            feature_id="feat_status_1",
            user_id=CURRENT_USER_ID,
            created_at=1700000400,
            source="phone-request",
            data={"steps": 900},
        )
        _insert_request(
            database_url=database_url,
            request_id="req_status_1",
            user_id=CURRENT_USER_ID,
            created_at=1700000300,
            status="fulfilled",
            source="phone",
            feature_id="feat_status_1",
        )

        with TestClient(app) as client:
            response = client.get("/requests/req_status_1")

        assert response.status_code == 200
        assert response.json() == {
            "id": "req_status_1",
            "status": "fulfilled",
            "featureId": "feat_status_1",
            "createdAt": 1700000300,
        }

        db_session._session_factory.cache_clear()


def test_get_request_by_id_returns_404_when_missing(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with TestClient(app) as client:
            response = client.get("/requests/does-not-exist")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Request does-not-exist was not found for current user."
        }

        db_session._session_factory.cache_clear()


def test_pending_count_reflects_pending_requests_and_decreases_when_fulfilled(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        _insert_request(
            database_url=database_url,
            request_id="req_pending_a",
            user_id=CURRENT_USER_ID,
            created_at=1700000500,
            status="pending",
            source="phone",
            feature_id=None,
        )
        _insert_request(
            database_url=database_url,
            request_id="req_pending_b",
            user_id=CURRENT_USER_ID,
            created_at=1700000501,
            status="pending",
            source="phone",
            feature_id=None,
        )
        _insert_feature(
            database_url=database_url,
            feature_id="feat_other",
            user_id=CURRENT_USER_ID,
            created_at=1700000502,
            source="phone-request",
            data={"steps": 2100},
        )
        _insert_request(
            database_url=database_url,
            request_id="req_fulfilled_a",
            user_id=CURRENT_USER_ID,
            created_at=1700000503,
            status="fulfilled",
            source="phone",
            feature_id="feat_other",
        )
        _insert_request(
            database_url=database_url,
            request_id="req_pending_other_user",
            user_id=OTHER_USER_ID,
            created_at=1700000504,
            status="pending",
            source="phone",
            feature_id=None,
        )

        with TestClient(app) as client:
            initial_response = client.get("/requests/pending/count")
            other_user_response = client.get(f"/requests/pending/count?userId={OTHER_USER_ID}")

        assert initial_response.status_code == 200
        assert initial_response.json() == {"pendingCount": 2}
        assert other_user_response.status_code == 200
        assert other_user_response.json() == {"pendingCount": 1}

        _insert_feature(
            database_url=database_url,
            feature_id="feat_newly_fulfilled",
            user_id=CURRENT_USER_ID,
            created_at=1700000505,
            source="phone-request",
            data={"steps": 2200},
        )
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE requests
                    SET status = 'fulfilled', "featureId" = %s
                    WHERE id = %s
                    """,
                    ("feat_newly_fulfilled", "req_pending_a"),
                )
            connection.commit()

        with TestClient(app) as client:
            after_fulfillment_response = client.get("/requests/pending/count")

        assert after_fulfillment_response.status_code == 200
        assert after_fulfillment_response.json() == {"pendingCount": 1}

        db_session._session_factory.cache_clear()


def test_request_status_constraints_enforced_in_database(monkeypatch) -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _configure_runtime_env(monkeypatch=monkeypatch, database_url=database_url)

        with pytest.raises(psycopg.errors.CheckViolation):
            _insert_request(
                database_url=database_url,
                request_id="req_bad_status",
                user_id=CURRENT_USER_ID,
                created_at=1700000600,
                status="processing",
                source="phone",
                feature_id=None,
            )

        with pytest.raises(psycopg.errors.CheckViolation):
            _insert_request(
                database_url=database_url,
                request_id="req_pending_with_feature",
                user_id=CURRENT_USER_ID,
                created_at=1700000601,
                status="pending",
                source="phone",
                feature_id="some_feature",
            )

        with pytest.raises(psycopg.errors.CheckViolation):
            _insert_request(
                database_url=database_url,
                request_id="req_fulfilled_without_feature",
                user_id=CURRENT_USER_ID,
                created_at=1700000602,
                status="fulfilled",
                source="phone",
                feature_id=None,
            )

        db_session._session_factory.cache_clear()


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for request status integration tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_request_status_{uuid.uuid4().hex[:8]}"
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
