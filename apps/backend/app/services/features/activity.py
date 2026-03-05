from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.features.shared import blob_payload, to_int


def features_from_activity(*, blob: dict[str, Any] | None) -> dict[str, int | float | None]:
    output = {
        "steps_count": None,
        "calories_out_kcal": None,
        "active_zone_minutes": None,
    }
    payload = blob_payload(blob)
    summary = payload.get("summary") if isinstance(payload.get("summary"), Mapping) else {}
    output["steps_count"] = to_int(summary.get("steps"))
    output["calories_out_kcal"] = to_int(summary.get("caloriesOut"))

    zone_minutes = to_int(summary.get("activeZoneMinutes"))
    if zone_minutes is not None:
        output["active_zone_minutes"] = zone_minutes
        return output

    very = to_int(summary.get("veryActiveMinutes"))
    fairly = to_int(summary.get("fairlyActiveMinutes"))
    lightly = to_int(summary.get("lightlyActiveMinutes"))
    if any(value is not None for value in (very, fairly, lightly)):
        output["active_zone_minutes"] = (very or 0) + (fairly or 0) + (lightly or 0)
    return output


def extract_resting_heart_rate(
    *,
    activity_blob: dict[str, Any] | None,
    heart_blob: dict[str, Any] | None,
) -> int | None:
    heart_payload = blob_payload(heart_blob)
    activities_heart = heart_payload.get("activities-heart")
    if isinstance(activities_heart, list):
        for entry in activities_heart:
            if not isinstance(entry, Mapping):
                continue
            value = entry.get("value")
            if not isinstance(value, Mapping):
                continue
            resting = to_int(value.get("restingHeartRate"))
            if resting is not None:
                return resting

    activity_payload = blob_payload(activity_blob)
    summary = activity_payload.get("summary")
    if isinstance(summary, Mapping):
        return to_int(summary.get("restingHeartRate"))
    return None


def extract_resting_heart_rate_series(*, heart_7d_blob: dict[str, Any] | None) -> list[float]:
    heart_payload = blob_payload(heart_7d_blob)
    entries = heart_payload.get("activities-heart")
    if not isinstance(entries, list):
        return []
    values: list[float] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        value = entry.get("value")
        if not isinstance(value, Mapping):
            continue
        resting = to_int(value.get("restingHeartRate"))
        if resting is not None:
            values.append(float(resting))
    return values
