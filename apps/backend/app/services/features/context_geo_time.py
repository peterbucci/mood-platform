from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def enrich_context_features(
    *,
    client_features: dict[str, Any] | None,
    anchor_datetime: datetime,
    source_timezone: str,
) -> tuple[dict[str, Any], list[str]]:
    """Enrich client context with backend-computed geo/time fields.

    Returns `(enriched_features, notes_to_append)`.
    """
    features: dict[str, Any] = dict(client_features or {})
    notes: list[str] = []

    local_anchor = _to_local(anchor_datetime=anchor_datetime, source_timezone=source_timezone)
    hour = local_anchor.hour
    weekday = local_anchor.weekday()  # Monday=0
    day_of_week = (weekday + 1) % 7  # align with JS 0=Sunday
    is_weekend = day_of_week in {0, 6}

    features.setdefault("hourOfDay", hour)
    features.setdefault("dayOfWeek", day_of_week)
    features.setdefault("isWeekend", is_weekend)

    lat = _to_float(features.get("lat"))
    lon = _to_float(features.get("lon"))
    if lat is None or lon is None:
        notes.append("missing_location_context")
        return features, notes

    cluster_key = _grid_cluster_key(lat=lat, lon=lon)
    features.setdefault("locationClusterKey", cluster_key)
    features.setdefault(f"locationClusterOneHot_{cluster_key}", 1)

    commute_flag = _commute_flag(hour_of_day=hour, day_of_week=day_of_week, cluster_key=cluster_key)
    features.setdefault("commuteFlag", commute_flag)

    daylight_flag, daylight_minutes_remaining = _daylight_estimate(
        lat=lat,
        local_anchor=local_anchor,
    )
    features.setdefault("daylightNowFlag", daylight_flag)
    features.setdefault("daylightMinsRemaining", daylight_minutes_remaining)
    return features, notes


def _to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_local(*, anchor_datetime: datetime, source_timezone: str) -> datetime:
    if anchor_datetime.tzinfo is None:
        anchor_datetime = anchor_datetime.replace(tzinfo=UTC)
    try:
        tzinfo = ZoneInfo(source_timezone)
    except ZoneInfoNotFoundError:
        tzinfo = UTC
    return anchor_datetime.astimezone(tzinfo)


def _grid_cluster_key(*, lat: float, lon: float) -> str:
    # ~10-11km bins at equator; coarse enough for privacy and stable clusters.
    lat_bucket = int(math.floor((lat + 90.0) * 10))
    lon_bucket = int(math.floor((lon + 180.0) * 10))
    return f"grid_{lat_bucket}_{lon_bucket}"


def _commute_flag(*, hour_of_day: int, day_of_week: int, cluster_key: str | None) -> bool:
    if day_of_week in {0, 6}:
        return False
    if cluster_key and cluster_key.startswith("grid_"):
        # If we can assign a stable cluster, assume non-commute unless explicit client signal.
        return False
    return (7 <= hour_of_day <= 9) or (16 <= hour_of_day <= 19)


def _daylight_estimate(*, lat: float, local_anchor: datetime) -> tuple[bool, int]:
    """Approximate daylight from latitude and day-of-year.

    This avoids extra provider calls while providing deterministic server-side context.
    """
    doy = local_anchor.timetuple().tm_yday
    declination = math.radians(23.44) * math.sin(math.radians((360.0 / 365.0) * (doy - 81)))
    lat_rad = math.radians(max(-89.0, min(89.0, lat)))
    cos_hour_angle = -math.tan(lat_rad) * math.tan(declination)

    if cos_hour_angle <= -1:
        sunrise_hour = 0.0
        sunset_hour = 24.0
    elif cos_hour_angle >= 1:
        sunrise_hour = 12.0
        sunset_hour = 12.0
    else:
        daylight_hours = (2.0 / 15.0) * math.degrees(math.acos(cos_hour_angle))
        sunrise_hour = 12.0 - (daylight_hours / 2.0)
        sunset_hour = 12.0 + (daylight_hours / 2.0)

    local_hour_float = (
        local_anchor.hour + (local_anchor.minute / 60.0) + (local_anchor.second / 3600.0)
    )
    is_daylight = sunrise_hour <= local_hour_float <= sunset_hour
    minutes_remaining = int(max(0.0, (sunset_hour - local_hour_float) * 60.0)) if is_daylight else 0
    return is_daylight, minutes_remaining
