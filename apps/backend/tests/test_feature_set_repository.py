from __future__ import annotations

import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import pytest
from app.db.models import SleepFeatures
from app.db.session import to_sqlalchemy_database_url
from app.repositories.feature_set_repository import FeatureSetRepository
from app.settings import Settings
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[3]
ALEMBIC_CONFIG = ROOT_DIR / "apps" / "backend" / "alembic.ini"
BASE_REVISION = "20260304_000001"


def test_feature_set_stores_extractor_metadata() -> None:
    with _temporary_migrated_database() as database_url:
        session_factory = sessionmaker(
            bind=create_engine(to_sqlalchemy_database_url(database_url)),
            expire_on_commit=False,
        )
        with session_factory() as session:
            repository = FeatureSetRepository(
                session=session,
                settings=Settings(FEATURE_EXTRACTOR_VERSION="v9.2.0"),
            )
            feature_id = repository.create_feature_set(
                table_name="sleep_features",
                user_id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
                captured_at=datetime(2026, 3, 4, 12, 0, tzinfo=UTC),
                window_start=datetime(2026, 3, 4, 8, 0, tzinfo=UTC),
                window_end=datetime(2026, 3, 4, 12, 0, tzinfo=UTC),
                source_timezone="America/New_York",
                feature_values={"total_sleep_minutes": 410},
            )

            stored_row = session.get(SleepFeatures, feature_id)
            assert stored_row is not None
            assert stored_row.extractor_version == "v9.2.0"
            assert stored_row.window_start == datetime(2026, 3, 4, 8, 0, tzinfo=UTC)
            assert stored_row.window_end == datetime(2026, 3, 4, 12, 0, tzinfo=UTC)
            assert stored_row.source_timezone == "America/New_York"


def test_feature_sets_can_filter_by_extractor_version() -> None:
    with _temporary_migrated_database() as database_url:
        session_factory = sessionmaker(
            bind=create_engine(to_sqlalchemy_database_url(database_url)),
            expire_on_commit=False,
        )
        with session_factory() as session:
            repository = FeatureSetRepository(
                session=session,
                settings=Settings(FEATURE_EXTRACTOR_VERSION="v1"),
            )
            user_id = uuid.UUID("00000000-0000-0000-0000-000000000011")
            captured_at = datetime(2026, 3, 5, 12, 0, tzinfo=UTC)

            repository.create_feature_set(
                table_name="sleep_features",
                user_id=user_id,
                captured_at=captured_at,
                window_start=datetime(2026, 3, 5, 8, 0, tzinfo=UTC),
                window_end=datetime(2026, 3, 5, 12, 0, tzinfo=UTC),
                source_timezone="UTC",
                feature_values={"total_sleep_minutes": 430},
            )
            second_id = repository.create_feature_set(
                table_name="sleep_features",
                user_id=user_id,
                captured_at=captured_at,
                window_start=datetime(2026, 3, 5, 10, 0, tzinfo=UTC),
                window_end=datetime(2026, 3, 5, 12, 0, tzinfo=UTC),
                source_timezone="UTC",
                extractor_version="v2",
                feature_values={"total_sleep_minutes": 450},
            )

            filtered_rows = repository.list_feature_sets_by_extractor_version(
                table_name="sleep_features",
                extractor_version="v2",
            )
            assert len(filtered_rows) == 1
            assert filtered_rows[0].id == second_id
            assert filtered_rows[0].extractor_version == "v2"


def test_migration_backfills_feature_metadata_for_existing_rows() -> None:
    with _temporary_database() as database_url:
        _run_alembic_upgrade(revision=BASE_REVISION, database_url=database_url)
        _insert_legacy_sleep_feature_row(database_url=database_url)
        _run_alembic_upgrade(revision="head", database_url=database_url)

        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT extractor_version, window_start, window_end, source_timezone, captured_at
                    FROM sleep_features
                    WHERE id = %s
                    """,
                    ("11111111-1111-1111-1111-111111111111",),
                )
                stored_row = cursor.fetchone()

        assert stored_row is not None
        assert stored_row[0] == "v1"
        assert stored_row[1] == stored_row[4]
        assert stored_row[2] == stored_row[4]
        assert stored_row[3] == "UTC"


class _temporary_database:
    def __enter__(self) -> str:
        base_database_url = os.getenv("DATABASE_URL", "").strip()
        if not base_database_url:
            pytest.skip("DATABASE_URL is required for PostgreSQL integration tests.")

        parsed_url = make_url(base_database_url)
        if not parsed_url.database:
            pytest.skip("DATABASE_URL must include a database name.")

        self._temp_database = f"mood_feature_meta_{uuid.uuid4().hex[:8]}"
        self._admin_url = parsed_url.set(database="postgres").render_as_string(hide_password=False)
        self._temp_url = parsed_url.set(database=self._temp_database).render_as_string(
            hide_password=False
        )

        try:
            with psycopg.connect(self._admin_url, autocommit=True) as connection:
                connection.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                        sql.Identifier(self._temp_database)
                    )
                )
                connection.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self._temp_database))
                )
        except psycopg.Error as exc:  # pragma: no cover - environment-dependent
            pytest.skip(f"Cannot provision temporary PostgreSQL database: {exc}")

        return self._temp_url

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            with psycopg.connect(self._admin_url, autocommit=True) as connection:
                connection.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                        sql.Identifier(self._temp_database)
                    )
                )
        except psycopg.Error:
            pass


class _temporary_migrated_database:
    def __enter__(self) -> str:
        self._database_ctx = _temporary_database()
        database_url = self._database_ctx.__enter__()
        _run_alembic_upgrade(revision="head", database_url=database_url)
        return database_url

    def __exit__(self, exc_type, exc, tb) -> None:
        self._database_ctx.__exit__(exc_type, exc, tb)


def _run_alembic_upgrade(*, revision: str, database_url: str) -> None:
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
            revision,
        ],
        check=True,
        cwd=ROOT_DIR,
        env=env,
    )


def _insert_legacy_sleep_feature_row(*, database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (id)
                VALUES ('00000000-0000-0000-0000-000000000001')
                """
            )
            cursor.execute(
                """
                INSERT INTO sleep_features (id, user_id, captured_at, total_sleep_minutes)
                VALUES ('11111111-1111-1111-1111-111111111111',
                        '00000000-0000-0000-0000-000000000001',
                        '2026-03-04T10:00:00Z',
                        420)
                """
            )
        connection.commit()
