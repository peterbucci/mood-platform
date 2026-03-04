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


class FeatureRequest(Base):
    __tablename__ = "requests"

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    user_id: Mapped[str] = mapped_column("userId", sa.Text, nullable=False)
    created_at: Mapped[int] = mapped_column("createdAt", sa.Integer, nullable=False)
    status: Mapped[str] = mapped_column(sa.Text, nullable=False)
    feature_id: Mapped[str | None] = mapped_column("featureId", sa.Text)
    source: Mapped[str] = mapped_column(sa.Text, nullable=False)


class Feature(Base):
    __tablename__ = "features"
    __table_args__ = (sa.Index("ix_features_user_created_at_desc", "userId", "createdAt"),)

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    user_id: Mapped[str] = mapped_column("userId", sa.Text, nullable=False)
    created_at: Mapped[int] = mapped_column("createdAt", sa.Integer, nullable=False)
    source: Mapped[str] = mapped_column(sa.Text, nullable=False)
    data: Mapped[str] = mapped_column(sa.Text, nullable=False)


class WorkerLock(Base):
    __tablename__ = "worker_locks"
    __table_args__ = (sa.Index("ix_worker_locks_expires_at", "expires_at"),)

    lock_key: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    owner_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
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


class FitbitOAuthState(Base):
    __tablename__ = "fitbit_oauth_states"
    __table_args__ = (sa.Index("ix_fitbit_oauth_states_expires_at", "expires_at"),)

    state: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


class FitbitOAuthConnection(Base):
    __tablename__ = "fitbit_oauth_connections"
    __table_args__ = (sa.Index("ix_fitbit_oauth_connections_expires_at", "expires_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    fitbit_user_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    access_token: Mapped[str] = mapped_column(sa.Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(sa.Text, nullable=False)
    scope: Mapped[str] = mapped_column(sa.Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
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
    extractor_version: Mapped[str] = mapped_column(sa.Text, nullable=False)
    window_start: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    source_timezone: Mapped[str] = mapped_column(sa.Text, nullable=False)


class PersonalFeatures(FeatureSetMixin, Base):
    __tablename__ = "personal_features"
    __table_args__ = (
        sa.Index(
            "ix_personal_features_user_captured_at_desc",
            "user_id",
            sa.text("captured_at DESC"),
        ),
        sa.Index("ix_personal_features_extractor_version", "extractor_version"),
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
        sa.Index("ix_daily_features_extractor_version", "extractor_version"),
    )

    water_ml: Mapped[int | None] = mapped_column(sa.Integer)
    mindfulness_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    screen_time_minutes: Mapped[int | None] = mapped_column(sa.Integer)


class SleepFeatures(FeatureSetMixin, Base):
    __tablename__ = "sleep_features"
    __table_args__ = (
        sa.Index("ix_sleep_features_user_captured_at_desc", "user_id", sa.text("captured_at DESC")),
        sa.Index("ix_sleep_features_extractor_version", "extractor_version"),
    )

    total_sleep_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    deep_sleep_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    sleep_efficiency_pct: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2))


class StepsFeatures(FeatureSetMixin, Base):
    __tablename__ = "steps_features"
    __table_args__ = (
        sa.Index("ix_steps_features_user_captured_at_desc", "user_id", sa.text("captured_at DESC")),
        sa.Index("ix_steps_features_extractor_version", "extractor_version"),
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
        sa.Index("ix_exercise_features_extractor_version", "extractor_version"),
    )

    active_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    workout_count: Mapped[int | None] = mapped_column(sa.Integer)
    vigorous_minutes: Mapped[int | None] = mapped_column(sa.Integer)


class HrFeatures(FeatureSetMixin, Base):
    __tablename__ = "hr_features"
    __table_args__ = (
        sa.Index("ix_hr_features_user_captured_at_desc", "user_id", sa.text("captured_at DESC")),
        sa.Index("ix_hr_features_extractor_version", "extractor_version"),
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
        sa.Index("ix_resting_hr_features_extractor_version", "extractor_version"),
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
        sa.Index("ix_calorie_features_extractor_version", "extractor_version"),
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
