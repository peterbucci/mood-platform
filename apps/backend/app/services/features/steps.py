from __future__ import annotations

import statistics
from collections.abc import Mapping
from typing import Any

from app.services.features.shared import (
    add_note,
    blob_payload,
    extract_intraday_series,
    rolling_max_sum,
    slope,
    stddev,
    to_float,
    window_sum,
    zero_count,
    zero_streak_max,
)


def derive_steps_intraday_metrics(
    *,
    steps_intraday_blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, float | int | None]:
    derived: dict[str, float | int | None] = {}
    steps_series = extract_intraday_series(
        blob=steps_intraday_blob,
        dataset_key="activities-steps-intraday",
        value_key="value",
    )
    if not steps_series:
        add_note(notes, "missing_intraday_steps")
        return derived

    derived["stepsLast5m"] = window_sum(steps_series, 5)
    derived["stepsLast15m"] = window_sum(steps_series, 15)
    derived["stepsLast30m"] = window_sum(steps_series, 30)
    derived["stepsLast60m"] = window_sum(steps_series, 60)
    derived["stepsLast3h"] = window_sum(steps_series, 180)
    derived["stepBurst5m"] = rolling_max_sum(steps_series, 5)
    derived["zeroStreakMax60m"] = zero_streak_max(steps_series, 60)
    derived["stepsSlopeLast60m"] = slope(steps_series[-60:])
    recent_5 = window_sum(steps_series, 5)
    previous_10 = window_sum(steps_series[-15:-5], 10)
    if recent_5 is not None and previous_10 is not None:
        derived["stepsAccel5to15m"] = recent_5 - (previous_10 / 2.0)
    derived["sedentaryMinsLast3h"] = zero_count(steps_series, 180)
    return derived


def derive_calories_intraday_metrics(
    *,
    calories_intraday_blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, float | None]:
    derived: dict[str, float | None] = {}
    calories_series = extract_intraday_series(
        blob=calories_intraday_blob,
        dataset_key="activities-calories-intraday",
        value_key="value",
    )
    if not calories_series:
        add_note(notes, "missing_intraday_calories")
        return derived
    derived["caloriesOutLast3h"] = window_sum(calories_series, 180)
    return derived


def extract_steps_7d_values(*, blob: dict[str, Any] | None) -> list[float]:
    payload = blob_payload(blob)
    entries = payload.get("activities-steps")
    if not isinstance(entries, list):
        return []
    values: list[float] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        value = to_float(entry.get("value"))
        if value is not None:
            values.append(value)
    return values


def derive_steps_z_today(
    *,
    steps_7d_blob: dict[str, Any] | None,
    steps_today: float | None,
    notes: list[str],
) -> dict[str, float | None]:
    derived: dict[str, float | None] = {}
    steps_7d_values = extract_steps_7d_values(blob=steps_7d_blob)
    if steps_7d_values and steps_today is not None:
        mean_7d = statistics.mean(steps_7d_values)
        std_7d = stddev(steps_7d_values)
        if std_7d not in (None, 0):
            derived["stepsZToday"] = (steps_today - mean_7d) / std_7d
    else:
        add_note(notes, "missing_steps_7d")
    return derived
