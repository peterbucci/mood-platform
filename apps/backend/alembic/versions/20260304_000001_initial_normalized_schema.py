"""create normalized schema for users, feature sets, and mood entries

Revision ID: 20260304_000001
Revises:
Create Date: 2026-03-04 00:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260304_000001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_feature_table(
    table_name: str,
    *feature_columns: sa.Column,
) -> None:
    op.create_table(
        table_name,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        *feature_columns,
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        f"ix_{table_name}_user_captured_at_desc",
        table_name,
        ["user_id", sa.text("captured_at DESC")],
        unique=False,
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_feature_table(
        "personal_features",
        sa.Column("age_years", sa.Integer(), nullable=True),
        sa.Column("sex", sa.Text(), nullable=True),
        sa.Column("height_cm", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("smoker", sa.Boolean(), nullable=True),
    )
    _create_feature_table(
        "daily_features",
        sa.Column("water_ml", sa.Integer(), nullable=True),
        sa.Column("mindfulness_minutes", sa.Integer(), nullable=True),
        sa.Column("screen_time_minutes", sa.Integer(), nullable=True),
    )
    _create_feature_table(
        "sleep_features",
        sa.Column("total_sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("deep_sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("sleep_efficiency_pct", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    _create_feature_table(
        "steps_features",
        sa.Column("steps_count", sa.Integer(), nullable=True),
        sa.Column("distance_km", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("floors_climbed", sa.Integer(), nullable=True),
    )
    _create_feature_table(
        "exercise_features",
        sa.Column("active_minutes", sa.Integer(), nullable=True),
        sa.Column("workout_count", sa.Integer(), nullable=True),
        sa.Column("vigorous_minutes", sa.Integer(), nullable=True),
    )
    _create_feature_table(
        "hr_features",
        sa.Column("avg_bpm", sa.Integer(), nullable=True),
        sa.Column("min_bpm", sa.Integer(), nullable=True),
        sa.Column("max_bpm", sa.Integer(), nullable=True),
    )
    _create_feature_table(
        "resting_hr_features",
        sa.Column("resting_bpm", sa.Integer(), nullable=True),
        sa.Column("baseline_shift_bpm", sa.Integer(), nullable=True),
    )
    _create_feature_table(
        "calorie_features",
        sa.Column("calories_consumed_kcal", sa.Integer(), nullable=True),
        sa.Column("calories_burned_kcal", sa.Integer(), nullable=True),
        sa.Column("net_calories_kcal", sa.Integer(), nullable=True),
    )

    # RESTRICT keeps feature rows from being deleted if a mood entry references them.
    op.create_table(
        "mood_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("entry_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("label_category_key", sa.Text(), nullable=False),
        sa.Column("label_emotion", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("personal_features_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("daily_features_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sleep_features_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("steps_features_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exercise_features_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("hr_features_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resting_hr_features_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("calorie_features_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "label_category_key IN ('energized','calm','stressed','tired')",
            name="ck_mood_entries_label_category_key",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["personal_features_id"],
            ["personal_features.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["daily_features_id"],
            ["daily_features.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["sleep_features_id"],
            ["sleep_features.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["steps_features_id"],
            ["steps_features.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["exercise_features_id"],
            ["exercise_features.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["hr_features_id"],
            ["hr_features.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["resting_hr_features_id"],
            ["resting_hr_features.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["calorie_features_id"],
            ["calorie_features.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mood_entries_user_entry_at_desc",
        "mood_entries",
        ["user_id", sa.text("entry_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_mood_entries_user_entry_at_desc", table_name="mood_entries")
    op.drop_table("mood_entries")

    op.drop_index("ix_calorie_features_user_captured_at_desc", table_name="calorie_features")
    op.drop_table("calorie_features")

    op.drop_index("ix_resting_hr_features_user_captured_at_desc", table_name="resting_hr_features")
    op.drop_table("resting_hr_features")

    op.drop_index("ix_hr_features_user_captured_at_desc", table_name="hr_features")
    op.drop_table("hr_features")

    op.drop_index("ix_exercise_features_user_captured_at_desc", table_name="exercise_features")
    op.drop_table("exercise_features")

    op.drop_index("ix_steps_features_user_captured_at_desc", table_name="steps_features")
    op.drop_table("steps_features")

    op.drop_index("ix_sleep_features_user_captured_at_desc", table_name="sleep_features")
    op.drop_table("sleep_features")

    op.drop_index("ix_daily_features_user_captured_at_desc", table_name="daily_features")
    op.drop_table("daily_features")

    op.drop_index("ix_personal_features_user_captured_at_desc", table_name="personal_features")
    op.drop_table("personal_features")

    op.drop_table("users")
