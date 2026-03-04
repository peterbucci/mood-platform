from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import psycopg
from app.db.session import to_sqlalchemy_database_url
from app.repositories.feature_request_repository import FeatureRequestRepository
from app.services.request_fulfillment_service import RequestFulfillmentService
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_CONFIG = ROOT_DIR / "apps" / "backend" / "alembic.ini"


class FakeFitbitServerError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


class FakeFitbitClient:
    def __init__(self, scripted_responses: dict[str, list[Any]]) -> None:
        self._scripted_responses = {
            user_id: list(items) for user_id, items in scripted_responses.items()
        }
        self.calls_by_user: dict[str, int] = {}

    def fetch_user_data(self, *, user_id: str) -> dict[str, Any]:
        self.calls_by_user[user_id] = self.calls_by_user.get(user_id, 0) + 1
        queue = self._scripted_responses.get(user_id, [])
        if not queue:
            return {}

        next_item = queue.pop(0)
        if isinstance(next_item, Exception):
            raise next_item
        if callable(next_item):
            return next_item()
        return next_item


def test_fulfillment_retries_transient_errors_and_handles_partial_payload(caplog) -> None:
    user_id = "00000000-0000-0000-0000-00000000ee01"
    request_id = "req_retry_partial"

    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _insert_request(
            database_url=database_url,
            request_id=request_id,
            user_id=user_id,
            created_at=1700000000,
            status="pending",
            source="phone",
            feature_id=None,
        )

        fitbit_client = FakeFitbitClient(
            {
                user_id: [
                    ConnectionError("temporary network issue"),
                    FakeFitbitServerError(status_code=503),
                    {"steps": {"count": 4321}},
                ]
            }
        )

        with _sqlalchemy_session(database_url) as session:
            service = RequestFulfillmentService(
                repository=FeatureRequestRepository(session=session),
                fitbit_client=fitbit_client,
                backoff_seconds=(0.001, 0.001, 0.001),
                sleep_func=lambda _: None,
            )
            caplog.set_level(logging.WARNING)
            stats = service.process_pending_requests()

        assert stats.processed == 1
        assert stats.fulfilled == 1
        assert stats.failed == 0
        assert fitbit_client.calls_by_user[user_id] == 3
        assert "Retrying Fitbit fetch" in caplog.text
        assert "missing Fitbit section 'sleep'" in caplog.text

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

                cursor.execute(
                    """
                    SELECT data
                    FROM features
                    WHERE "userId" = %s
                    """,
                    (user_id,),
                )
                feature_rows = cursor.fetchall()

        assert request_row is not None
        assert request_row[0] == "fulfilled"
        assert request_row[1] is not None
        assert len(feature_rows) == 1
        assert json.loads(feature_rows[0][0]) == {"steps": {"count": 4321}}


def test_worker_continues_after_single_request_failure(caplog) -> None:
    failing_user_id = "00000000-0000-0000-0000-00000000ee02"
    success_user_id = "00000000-0000-0000-0000-00000000ee03"
    failing_request_id = "req_fail"
    success_request_id = "req_success"

    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _insert_request(
            database_url=database_url,
            request_id=failing_request_id,
            user_id=failing_user_id,
            created_at=1700000000,
            status="pending",
            source="phone",
            feature_id=None,
        )
        _insert_request(
            database_url=database_url,
            request_id=success_request_id,
            user_id=success_user_id,
            created_at=1700000001,
            status="pending",
            source="phone",
            feature_id=None,
        )

        fitbit_client = FakeFitbitClient(
            {
                failing_user_id: [
                    ConnectionError("network"),
                    ConnectionError("network"),
                    ConnectionError("network"),
                    ConnectionError("network"),
                ],
                success_user_id: [{"steps": {"count": 999}}],
            }
        )

        with _sqlalchemy_session(database_url) as session:
            service = RequestFulfillmentService(
                repository=FeatureRequestRepository(session=session),
                fitbit_client=fitbit_client,
                backoff_seconds=(0.001, 0.001, 0.001),
                sleep_func=lambda _: None,
            )
            caplog.set_level(logging.INFO)
            stats = service.process_pending_requests()

        assert stats.processed == 2
        assert stats.fulfilled == 1
        assert stats.failed == 1
        assert "Failed to fulfill request req_fail." in caplog.text

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT status, "featureId"
                    FROM requests
                    WHERE id = %s
                    """,
                    (failing_request_id,),
                )
                failing_row = cursor.fetchone()
                cursor.execute(
                    """
                    SELECT status, "featureId"
                    FROM requests
                    WHERE id = %s
                    """,
                    (success_request_id,),
                )
                success_row = cursor.fetchone()
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM features
                    WHERE "userId" = %s
                    """,
                    (success_user_id,),
                )
                success_feature_count = cursor.fetchone()[0]

        assert failing_row == ("pending", None)
        assert success_row is not None
        assert success_row[0] == "fulfilled"
        assert success_row[1] is not None
        assert success_feature_count == 1


def test_request_processing_is_idempotent() -> None:
    user_id = "00000000-0000-0000-0000-00000000ee04"
    request_id = "req_idempotent"

    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _insert_request(
            database_url=database_url,
            request_id=request_id,
            user_id=user_id,
            created_at=1700000000,
            status="pending",
            source="phone",
            feature_id=None,
        )

        fitbit_client = FakeFitbitClient({user_id: [{"steps": {"count": 123}}]})

        with _sqlalchemy_session(database_url) as session:
            service = RequestFulfillmentService(
                repository=FeatureRequestRepository(session=session),
                fitbit_client=fitbit_client,
                backoff_seconds=(0.001, 0.001, 0.001),
                sleep_func=lambda _: None,
            )
            first_outcome = service.process_request(request_id)
            second_outcome = service.process_request(request_id)

        assert first_outcome == "fulfilled"
        assert second_outcome == "skipped"
        assert fitbit_client.calls_by_user[user_id] == 1

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM features
                    WHERE "userId" = %s
                    """,
                    (user_id,),
                )
                feature_count = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT status, "featureId"
                    FROM requests
                    WHERE id = %s
                    """,
                    (request_id,),
                )
                request_row = cursor.fetchone()

        assert feature_count == 1
        assert request_row is not None
        assert request_row[0] == "fulfilled"
        assert request_row[1] is not None


def test_timeout_is_treated_as_retryable_failure() -> None:
    user_id = "00000000-0000-0000-0000-00000000ee05"
    request_id = "req_timeout"

    def slow_payload() -> dict[str, Any]:
        time.sleep(0.05)
        return {"steps": {"count": 10}}

    with _temporary_database() as database_url:
        _run_alembic_upgrade(database_url=database_url)
        _insert_request(
            database_url=database_url,
            request_id=request_id,
            user_id=user_id,
            created_at=1700000000,
            status="pending",
            source="phone",
            feature_id=None,
        )

        fitbit_client = FakeFitbitClient(
            {
                user_id: [
                    slow_payload,
                    {"steps": {"count": 10}},
                ]
            }
        )

        with _sqlalchemy_session(database_url) as session:
            service = RequestFulfillmentService(
                repository=FeatureRequestRepository(session=session),
                fitbit_client=fitbit_client,
                timeout_seconds=0.01,
                backoff_seconds=(0.001, 0.001, 0.001),
                sleep_func=lambda _: None,
            )
            stats = service.process_pending_requests()

        assert stats.fulfilled == 1
        assert fitbit_client.calls_by_user[user_id] == 2


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            raise RuntimeError("DATABASE_URL is required for request fulfillment tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            raise RuntimeError("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_fulfillment_{uuid.uuid4().hex[:8]}"
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


class _sqlalchemy_session:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._session: Session | None = None
        self._engine = None

    def __enter__(self) -> Session:
        sqlalchemy_url = to_sqlalchemy_database_url(self._database_url)
        self._engine = create_engine(sqlalchemy_url, pool_pre_ping=True)
        session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        self._session = session_factory()
        return self._session

    def __exit__(self, exc_type, exc, tb) -> None:
        assert self._session is not None
        self._session.close()
        assert self._engine is not None
        self._engine.dispose()


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
