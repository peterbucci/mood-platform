"""add feature extractor metadata to all feature tables

Revision ID: 20260304_000002
Revises: 20260304_000001
Create Date: 2026-03-04 00:00:02.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260304_000002"
down_revision: str | None = "20260304_000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FEATURE_TABLES = (
    "personal_features",
    "daily_features",
    "sleep_features",
    "steps_features",
    "exercise_features",
    "hr_features",
    "resting_hr_features",
    "calorie_features",
)


def _add_metadata_columns(table_name: str) -> None:
    op.add_column(table_name, sa.Column("extractor_version", sa.Text(), nullable=True))
    op.add_column(table_name, sa.Column("window_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column(table_name, sa.Column("window_end", sa.DateTime(timezone=True), nullable=True))
    op.add_column(table_name, sa.Column("source_timezone", sa.Text(), nullable=True))


def _backfill_metadata_columns(table_name: str) -> None:
    op.execute(
        sa.text(
            f"""
            UPDATE {table_name}
            SET
              extractor_version = COALESCE(extractor_version, :extractor_version),
              window_start = COALESCE(window_start, captured_at),
              window_end = COALESCE(window_end, captured_at),
              source_timezone = COALESCE(source_timezone, :source_timezone)
            """
        ).bindparams(extractor_version="v1", source_timezone="UTC")
    )


def _enforce_constraints(table_name: str) -> None:
    op.alter_column(table_name, "extractor_version", existing_type=sa.Text(), nullable=False)
    op.alter_column(
        table_name,
        "window_start",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.alter_column(
        table_name,
        "window_end",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.alter_column(table_name, "source_timezone", existing_type=sa.Text(), nullable=False)


def _create_indexes(table_name: str) -> None:
    op.create_index(
        f"ix_{table_name}_extractor_version",
        table_name,
        ["extractor_version"],
        unique=False,
    )


def upgrade() -> None:
    for table_name in FEATURE_TABLES:
        _add_metadata_columns(table_name)
        _backfill_metadata_columns(table_name)
        _enforce_constraints(table_name)
        _create_indexes(table_name)


def downgrade() -> None:
    for table_name in FEATURE_TABLES:
        op.drop_index(f"ix_{table_name}_extractor_version", table_name=table_name)
        op.drop_column(table_name, "source_timezone")
        op.drop_column(table_name, "window_end")
        op.drop_column(table_name, "window_start")
        op.drop_column(table_name, "extractor_version")
