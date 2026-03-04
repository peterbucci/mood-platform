from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


class FeatureSetMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    captured_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


class PersonalFeatures(FeatureSetMixin, Base):
    __tablename__ = "personal_features"
    __table_args__ = (
        sa.Index(
            "ix_personal_features_user_captured_at_desc",
            "user_id",
            sa.text("captured_at DESC"),
        ),
    )

    age_years: Mapped[int | None] = mapped_column(sa.Integer)
    sex: Mapped[str | None] = mapped_column(sa.Text)
    height_cm: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2))
    weight_kg: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2))
    smoker: Mapped[bool | None] = mapped_column(sa.Boolean)


class DailyFeatures(FeatureSetMixin, Base):
    __tablename__ = "daily_features"
    __table_args__ = (
        sa.Index("ix_daily_features_user_captured_at_desc", "user_id", sa.text("captured_at DESC")),
    )

    water_ml: Mapped[int | None] = mapped_column(sa.Integer)
    mindfulness_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    screen_time_minutes: Mapped[int | None] = mapped_column(sa.Integer)


class SleepFeatures(FeatureSetMixin, Base):
    __tablename__ = "sleep_features"
    __table_args__ = (
        sa.Index("ix_sleep_features_user_captured_at_desc", "user_id", sa.text("captured_at DESC")),
    )

    total_sleep_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    deep_sleep_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    sleep_efficiency_pct: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2))


class StepsFeatures(FeatureSetMixin, Base):
    __tablename__ = "steps_features"
    __table_args__ = (
        sa.Index("ix_steps_features_user_captured_at_desc", "user_id", sa.text("captured_at DESC")),
    )

    steps_count: Mapped[int | None] = mapped_column(sa.Integer)
    distance_km: Mapped[Decimal | None] = mapped_column(sa.Numeric(6, 2))
    floors_climbed: Mapped[int | None] = mapped_column(sa.Integer)


class ExerciseFeatures(FeatureSetMixin, Base):
    __tablename__ = "exercise_features"
    __table_args__ = (
        sa.Index(
            "ix_exercise_features_user_captured_at_desc",
            "user_id",
            sa.text("captured_at DESC"),
        ),
    )

    active_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    workout_count: Mapped[int | None] = mapped_column(sa.Integer)
    vigorous_minutes: Mapped[int | None] = mapped_column(sa.Integer)


class HrFeatures(FeatureSetMixin, Base):
    __tablename__ = "hr_features"
    __table_args__ = (
        sa.Index("ix_hr_features_user_captured_at_desc", "user_id", sa.text("captured_at DESC")),
    )

    avg_bpm: Mapped[int | None] = mapped_column(sa.Integer)
    min_bpm: Mapped[int | None] = mapped_column(sa.Integer)
    max_bpm: Mapped[int | None] = mapped_column(sa.Integer)


class RestingHrFeatures(FeatureSetMixin, Base):
    __tablename__ = "resting_hr_features"
    __table_args__ = (
        sa.Index(
            "ix_resting_hr_features_user_captured_at_desc",
            "user_id",
            sa.text("captured_at DESC"),
        ),
    )

    resting_bpm: Mapped[int | None] = mapped_column(sa.Integer)
    baseline_shift_bpm: Mapped[int | None] = mapped_column(sa.Integer)


class CalorieFeatures(FeatureSetMixin, Base):
    __tablename__ = "calorie_features"
    __table_args__ = (
        sa.Index(
            "ix_calorie_features_user_captured_at_desc",
            "user_id",
            sa.text("captured_at DESC"),
        ),
    )

    calories_consumed_kcal: Mapped[int | None] = mapped_column(sa.Integer)
    calories_burned_kcal: Mapped[int | None] = mapped_column(sa.Integer)
    net_calories_kcal: Mapped[int | None] = mapped_column(sa.Integer)


class MoodEntry(Base):
    __tablename__ = "mood_entries"
    __table_args__ = (
        sa.CheckConstraint(
            "label_category_key IN ('energized','calm','stressed','tired')",
            name="ck_mood_entries_label_category_key",
        ),
        sa.Index("ix_mood_entries_user_entry_at_desc", "user_id", sa.text("entry_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    entry_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    label_category_key: Mapped[str] = mapped_column(sa.Text, nullable=False)
    label_emotion: Mapped[str] = mapped_column(sa.Text, nullable=False)
    note: Mapped[str | None] = mapped_column(sa.Text)

    personal_features_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("personal_features.id", ondelete="RESTRICT"),
    )
    daily_features_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("daily_features.id", ondelete="RESTRICT"),
    )
    sleep_features_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("sleep_features.id", ondelete="RESTRICT"),
    )
    steps_features_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("steps_features.id", ondelete="RESTRICT"),
    )
    exercise_features_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("exercise_features.id", ondelete="RESTRICT"),
    )
    hr_features_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("hr_features.id", ondelete="RESTRICT"),
    )
    resting_hr_features_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("resting_hr_features.id", ondelete="RESTRICT"),
    )
    calorie_features_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("calorie_features.id", ondelete="RESTRICT"),
    )
