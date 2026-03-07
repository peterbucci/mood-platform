from __future__ import annotations

# ruff: noqa: E402
import argparse
import json
import os
import random
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import sqlalchemy as sa

# Allow running as a script from repo root:
# python apps/backend/scripts/seed_recent_requests_features_labels.py
BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.models import Feature, FeatureRequest, Label, User
from app.db.session import _session_factory
from app.services.mood_entry_service import get_owner_user_id

FULFILLED_STATUS = "fulfilled"
CANCELED_STATUS = "canceled"

DEFAULT_SOURCE = "seed-script"

MOOD_EMOTIONS: dict[str, list[str]] = {
    "energized": ["Happy", "Excited", "Motivated", "Cheerful"],
    "calm": ["Calm", "Relaxed", "Content", "Peaceful"],
    "stressed": ["Stressed", "Anxious", "Overwhelmed", "Nervous"],
    "tired": ["Tired", "Sad", "Low", "Drained"],
}


@dataclass(frozen=True)
class SeedConfig:
    count: int
    days: int
    user_id: str
    source: str
    append: bool
    seed: int
    fulfilled_ratio: float


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Populate requests/features/labels with realistic synthetic data over the last N days."
        )
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Total requests to create (default: 100).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Time window in days (default: 30).",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="User UUID string. Defaults to OWNER_USER_ID or fallback owner UUID.",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=DEFAULT_SOURCE,
        help=f"Source value for generated rows (default: {DEFAULT_SOURCE!r}).",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append new data without deleting previously seeded rows for this user/source.",
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed (default: 7).")
    parser.add_argument(
        "--fulfilled-ratio",
        type=float,
        default=0.75,
        help="Fraction of requests that are fulfilled (default: 0.75). Remainder is canceled.",
    )
    return parser


def _extract_database_url_from_env_file(env_path: Path) -> str | None:
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != "DATABASE_URL":
            continue
        cleaned = value.strip().strip('"').strip("'")
        if cleaned:
            return cleaned
    return None


def _ensure_database_url_available() -> None:
    if os.getenv("DATABASE_URL", "").strip():
        return

    candidate_paths = [REPO_ROOT / ".env", BACKEND_ROOT / ".env"]
    for env_path in candidate_paths:
        extracted = _extract_database_url_from_env_file(env_path)
        if extracted:
            os.environ["DATABASE_URL"] = extracted
            print(f"Loaded DATABASE_URL from {env_path}.")
            return


def _validate_config(args: argparse.Namespace) -> SeedConfig:
    owner_user_id = (
        args.user_id.strip() if isinstance(args.user_id, str) else str(get_owner_user_id())
    )
    try:
        uuid.UUID(owner_user_id)
    except ValueError as exc:
        raise ValueError("--user-id must be a valid UUID.") from exc

    if args.count <= 0:
        raise ValueError("--count must be greater than 0.")
    if args.days <= 0:
        raise ValueError("--days must be greater than 0.")
    if not (0.0 <= args.fulfilled_ratio <= 1.0):
        raise ValueError("--fulfilled-ratio must be between 0 and 1.")

    source = args.source.strip()
    if not source:
        raise ValueError("--source must not be blank.")

    return SeedConfig(
        count=args.count,
        days=args.days,
        user_id=owner_user_id,
        source=source,
        append=args.append,
        seed=args.seed,
        fulfilled_ratio=args.fulfilled_ratio,
    )


def _random_timestamp_within_days(*, now_utc: datetime, days: int, rng: random.Random) -> datetime:
    lookback_seconds = days * 24 * 60 * 60
    offset_seconds = rng.uniform(0, lookback_seconds)
    return now_utc - timedelta(seconds=offset_seconds)


def _pick_mood(rng: random.Random) -> tuple[str, str]:
    category = rng.choice(list(MOOD_EMOTIONS.keys()))
    emotion = rng.choice(MOOD_EMOTIONS[category])
    return category, emotion


def _build_feature_payload(
    *,
    captured_at: datetime,
    category: str,
    emotion: str,
    rng: random.Random,
) -> dict[str, object]:
    steps_count = rng.randint(1200, 14000)
    active_minutes = rng.randint(15, 120)
    avg_bpm = rng.randint(62, 96)
    sleep_minutes = rng.randint(300, 510)
    sleep_efficiency = rng.randint(78, 96)
    hrv_rmssd = round(rng.uniform(18.0, 48.0), 2)

    return {
        "sleep": {
            "total_sleep_minutes": sleep_minutes,
            "sleep_efficiency_pct": sleep_efficiency,
        },
        "activity": {
            "steps_count": steps_count,
            "active_zone_minutes": active_minutes,
        },
        "heart_rate": {
            "avg_bpm": avg_bpm,
        },
        "hrv": {
            "daily_rmssd": hrv_rmssd,
        },
        "derived": {
            "dayOfWeek": captured_at.astimezone(UTC).isoweekday(),
            "hourOfDay": captured_at.hour,
            "isWeekend": captured_at.weekday() >= 5,
        },
        "meta": {
            "source_timezone": "America/New_York",
            "window_start": (captured_at - timedelta(hours=18)).isoformat(),
            "window_end": captured_at.isoformat(),
        },
        "notes": [],
        "seed": {
            "category": category,
            "emotion": emotion,
        },
    }


def _cleanup_previous_seed_rows(
    *,
    session: sa.orm.Session,
    user_id: str,
    source: str,
) -> tuple[int, int, int]:
    request_ids = list(
        session.scalars(
            sa.select(FeatureRequest.id).where(
                FeatureRequest.user_id == user_id,
                FeatureRequest.source == source,
            )
        )
    )
    feature_ids = list(
        session.scalars(
            sa.select(Feature.id).where(
                Feature.user_id == user_id,
                Feature.source == source,
            )
        )
    )

    deleted_labels = 0
    if request_ids or feature_ids:
        where_clause = sa.and_(Label.user_id == user_id)
        if request_ids and feature_ids:
            where_clause = sa.and_(
                Label.user_id == user_id,
                sa.or_(Label.request_id.in_(request_ids), Label.feature_id.in_(feature_ids)),
            )
        elif request_ids:
            where_clause = sa.and_(Label.user_id == user_id, Label.request_id.in_(request_ids))
        else:
            where_clause = sa.and_(Label.user_id == user_id, Label.feature_id.in_(feature_ids))

        deleted_labels = int(session.execute(sa.delete(Label).where(where_clause)).rowcount or 0)

    deleted_requests = int(
        session.execute(
            sa.delete(FeatureRequest).where(
                FeatureRequest.user_id == user_id,
                FeatureRequest.source == source,
            )
        ).rowcount
        or 0
    )
    deleted_features = int(
        session.execute(
            sa.delete(Feature).where(
                Feature.user_id == user_id,
                Feature.source == source,
            )
        ).rowcount
        or 0
    )

    return deleted_requests, deleted_features, deleted_labels


def _ensure_user_row(*, session: sa.orm.Session, user_id: str, now_utc: datetime) -> None:
    user_uuid = uuid.UUID(user_id)
    existing_user = session.get(User, user_uuid)
    if existing_user is not None:
        return
    session.add(User(id=user_uuid, created_at=now_utc, updated_at=now_utc))


def seed_recent_requests_features_labels(config: SeedConfig) -> None:
    rng = random.Random(config.seed)
    now_utc = datetime.now(tz=UTC)

    fulfilled_count = int(round(config.count * config.fulfilled_ratio))
    if fulfilled_count > config.count:
        fulfilled_count = config.count
    canceled_count = max(0, config.count - fulfilled_count)

    statuses = [FULFILLED_STATUS] * fulfilled_count + [CANCELED_STATUS] * canceled_count
    rng.shuffle(statuses)

    session_factory = _session_factory()
    with session_factory() as session:
        if not config.append:
            deleted_requests, deleted_features, deleted_labels = _cleanup_previous_seed_rows(
                session=session,
                user_id=config.user_id,
                source=config.source,
            )
            print(
                "Deleted previous seeded rows: "
                f"requests={deleted_requests} features={deleted_features} labels={deleted_labels}"
            )

        _ensure_user_row(session=session, user_id=config.user_id, now_utc=now_utc)

        created_requests = 0
        created_features = 0
        created_labels = 0

        for status in statuses:
            request_dt = _random_timestamp_within_days(now_utc=now_utc, days=config.days, rng=rng)
            request_id = str(uuid.uuid4())
            category, emotion = _pick_mood(rng)

            feature_id: str | None = None
            if status == FULFILLED_STATUS:
                feature_id = str(uuid.uuid4())
                feature_dt = min(
                    now_utc,
                    request_dt + timedelta(minutes=rng.randint(5, 120)),
                )
                payload = _build_feature_payload(
                    captured_at=feature_dt,
                    category=category,
                    emotion=emotion,
                    rng=rng,
                )
                session.add(
                    Feature(
                        id=feature_id,
                        user_id=config.user_id,
                        created_at=int(feature_dt.timestamp()),
                        source=config.source,
                        data=json.dumps(payload),
                        source_timezone="America/New_York",
                        window_start=feature_dt - timedelta(hours=18),
                        window_end=feature_dt,
                    )
                )
                created_features += 1

            session.add(
                FeatureRequest(
                    id=request_id,
                    user_id=config.user_id,
                    created_at=int(request_dt.timestamp()),
                    status=status,
                    feature_id=feature_id,
                    source=config.source,
                    client_features_json=json.dumps(
                        {
                            "timezone": "America/New_York",
                            "moodCategory": category,
                            "moodEmotion": emotion,
                        }
                    ),
                    attempts=0,
                    next_attempt_at=None,
                    last_error_code=None,
                    last_error_signal=None,
                )
            )
            created_requests += 1

            if status == FULFILLED_STATUS and feature_id is not None:
                session.add(
                    Label(
                        user_id=config.user_id,
                        feature_id=feature_id,
                        request_id=request_id,
                        label=f"{category} - {emotion}",
                        emotion_word=emotion,
                        category=category,
                        created_at=(request_dt + timedelta(minutes=2)).astimezone(UTC),
                    )
                )
                created_labels += 1

        session.commit()

    print(
        "Seed complete: "
        f"requests={created_requests} features={created_features} labels={created_labels} "
        f"userId={config.user_id} days={config.days} source={config.source!r}"
    )


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    _ensure_database_url_available()

    try:
        config = _validate_config(args)
        seed_recent_requests_features_labels(config)
    except ValueError as exc:
        parser.error(str(exc))
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Seeding failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
