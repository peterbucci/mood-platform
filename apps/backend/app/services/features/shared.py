from __future__ import annotations

import statistics
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

MISSING_SIGNAL_MARKER = "__missing"


def add_note(notes: list[str], note: str) -> None:
    if note not in notes:
        notes.append(note)


def is_missing_blob(blob: dict[str, Any] | None) -> bool:
    if not isinstance(blob, Mapping):
        return True
    return bool(blob.get(MISSING_SIGNAL_MARKER, False))


def blob_payload(blob: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(blob, Mapping):
        return {}
    payload = blob.get("payload")
    if isinstance(payload, Mapping):
        return dict(payload)
    return {}


def blob_reason(blob: dict[str, Any] | None) -> str | None:
    if not isinstance(blob, Mapping):
        return None
    reason = blob.get("reason")
    if isinstance(reason, str):
        normalized = reason.strip()
        return normalized or None
    return None


def extract_first_nested_dict(
    *,
    payload: dict[str, Any],
    list_key: str,
    value_key: str,
) -> dict[str, Any]:
    entries = payload.get(list_key)
    if not isinstance(entries, list):
        return {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        value = entry.get(value_key)
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def get_nested(source: Any, *keys: str) -> Any:
    current = source
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    parsed = to_float(value)
    if parsed is None:
        return None
    return int(parsed)


def to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized_value = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized_value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def sum_non_null(values: list[float | int | None]) -> float | int | None:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    if all(isinstance(value, int) for value in numeric_values):
        return int(sum(numeric_values))
    return float(sum(float(value) for value in numeric_values))


def extract_intraday_series(
    *,
    blob: dict[str, Any] | None,
    dataset_key: str,
    value_key: str,
) -> list[float]:
    payload = blob_payload(blob)
    dataset_parent = payload.get(dataset_key)
    if not isinstance(dataset_parent, Mapping):
        return []
    dataset = dataset_parent.get("dataset")
    if not isinstance(dataset, list):
        return []
    series: list[float] = []
    for point in dataset:
        if not isinstance(point, Mapping):
            continue
        numeric_value = to_float(point.get(value_key))
        if numeric_value is not None:
            series.append(numeric_value)
    return series


def window_sum(values: list[float], window: int) -> float | None:
    if not values:
        return None
    start_index = max(0, len(values) - max(1, window))
    return float(sum(values[start_index:]))


def window_avg(values: list[float], window: int) -> float | None:
    if not values:
        return None
    slice_values = values[max(0, len(values) - max(1, window)) :]
    if not slice_values:
        return None
    return float(sum(slice_values) / len(slice_values))


def window_min(values: list[float], window: int) -> float | None:
    if not values:
        return None
    slice_values = values[max(0, len(values) - max(1, window)) :]
    if not slice_values:
        return None
    return float(min(slice_values))


def window_max(values: list[float], window: int) -> float | None:
    if not values:
        return None
    slice_values = values[max(0, len(values) - max(1, window)) :]
    if not slice_values:
        return None
    return float(max(slice_values))


def rolling_max_sum(values: list[float], window: int) -> float | None:
    if not values:
        return None
    actual_window = max(1, window)
    if len(values) <= actual_window:
        return float(sum(values))
    return float(
        max(
            sum(values[index : index + actual_window])
            for index in range(len(values) - actual_window + 1)
        )
    )


def zero_streak_max(values: list[float], window: int) -> int | None:
    if not values:
        return None
    slice_values = values[max(0, len(values) - max(1, window)) :]
    current = 0
    max_streak = 0
    for value in slice_values:
        if value == 0:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return max_streak


def zero_count(values: list[float], window: int) -> int | None:
    if not values:
        return None
    slice_values = values[max(0, len(values) - max(1, window)) :]
    return sum(1 for value in slice_values if value == 0)


def slope(values: list[float]) -> float | None:
    if not values or len(values) < 2:
        return None
    n = len(values)
    x_values = list(range(n))
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values, strict=False))
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    if denominator == 0:
        return None
    return float(numerator / denominator)


def stddev(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    try:
        return float(statistics.pstdev(values))
    except statistics.StatisticsError:
        return None


def last_value(values: list[float]) -> float | None:
    if not values:
        return None
    return float(values[-1])
