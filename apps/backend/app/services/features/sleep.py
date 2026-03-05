from __future__ import annotations

import statistics
from collections.abc import Mapping
from typing import Any

from app.services.features.shared import (
    add_note,
    blob_payload,
    get_nested,
    parse_datetime,
    stddev,
    to_float,
)


def derive_sleep_metrics(
    *,
    sleep_blob: dict[str, Any] | None,
    sleep_range_blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, float | int | None]:
    derived: dict[str, float | int | None] = {}

    sleep_payload = blob_payload(sleep_blob)
    primary_sleep = primary_sleep_entry(sleep_payload)
    if primary_sleep is None:
        add_note(notes, "missing_sleep")
    else:
        minutes_asleep = to_float(primary_sleep.get("minutesAsleep"))
        if minutes_asleep is not None:
            derived["sleepDurationLastNightHrs"] = round(minutes_asleep / 60.0, 3)
        derived["sleepEfficiency"] = to_float(primary_sleep.get("efficiency"))
        levels_summary = get_nested(primary_sleep, "levels", "summary")
        awake_minutes = to_float(primary_sleep.get("minutesAwake"))
        if awake_minutes is None:
            awake_minutes = to_float(get_nested(levels_summary, "wake", "minutes"))
        if awake_minutes is not None and awake_minutes > 0:
            derived["wasoMinutes"] = awake_minutes
        deep_minutes = to_float(get_nested(levels_summary, "deep", "minutes"))
        rem_minutes = to_float(get_nested(levels_summary, "rem", "minutes"))
        total_minutes = to_float(primary_sleep.get("minutesAsleep"))
        if total_minutes and total_minutes > 0:
            if rem_minutes is not None:
                derived["remRatio"] = rem_minutes / total_minutes
            if deep_minutes is not None:
                derived["deepRatio"] = deep_minutes / total_minutes
        start_time = parse_datetime(primary_sleep.get("startTime"))
        end_time = parse_datetime(primary_sleep.get("endTime"))
        if start_time is not None:
            derived["sleepOnsetLocalHour"] = start_time.hour
        if end_time is not None:
            derived["wakeTimeLocalHour"] = end_time.hour

        total_window_minutes = (total_minutes or 0.0) + (awake_minutes or 0.0)
        if awake_minutes is not None and awake_minutes > 0 and total_window_minutes > 0:
            fragmentation_ratio = awake_minutes / total_window_minutes
            derived["sleepFragmentationScore"] = min(1.0, max(0.0, fragmentation_ratio))
        elif awake_minutes is None or total_window_minutes <= 0:
            add_note(notes, "missing_sleep_fragmentation_detail")

    sleep_entries = extract_sleep_entries(blob=sleep_range_blob)
    if sleep_entries:
        bed_hours = [
            parse_datetime(entry.get("startTime")).hour
            for entry in sleep_entries
            if parse_datetime(entry.get("startTime")) is not None
        ]
        durations_hours = [
            (to_float(entry.get("minutesAsleep")) or 0) / 60.0
            for entry in sleep_entries
            if to_float(entry.get("minutesAsleep")) is not None
        ]
        if len(bed_hours) >= 2:
            derived["bedtimeStdDev7d"] = stddev([float(hour) for hour in bed_hours])
        if durations_hours:
            avg_sleep = statistics.mean(durations_hours)
            derived["sleepDebtHrs"] = max(0.0, 8.0 - avg_sleep)
    else:
        add_note(notes, "missing_sleep_range")

    return derived


def primary_sleep_entry(payload: dict[str, Any]) -> Mapping[str, Any] | None:
    sleep_entries = payload.get("sleep")
    if not isinstance(sleep_entries, list) or not sleep_entries:
        return None
    for entry in sleep_entries:
        if isinstance(entry, Mapping) and bool(entry.get("isMainSleep")):
            return entry
    first = sleep_entries[0]
    if isinstance(first, Mapping):
        return first
    return None


def extract_sleep_entries(*, blob: dict[str, Any] | None) -> list[Mapping[str, Any]]:
    payload = blob_payload(blob)
    sleep_entries = payload.get("sleep")
    if not isinstance(sleep_entries, list):
        return []
    return [entry for entry in sleep_entries if isinstance(entry, Mapping)]
