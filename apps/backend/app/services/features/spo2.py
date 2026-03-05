from __future__ import annotations

import statistics
from collections.abc import Mapping
from typing import Any

from app.services.features.shared import (
    add_note,
    blob_payload,
    blob_reason,
    extract_first_nested_dict,
    is_missing_blob,
    to_float,
)


def features_from_spo2(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, float | None]:
    output = {
        "avg_spo2": None,
        "min_spo2": None,
        "max_spo2": None,
    }
    if is_missing_blob(blob):
        add_note(notes, "missing_spo2")
        return output

    payload = blob_payload(blob)
    value = extract_first_nested_dict(payload=payload, list_key="spo2", value_key="value")
    if not value:
        value = payload.get("value") if isinstance(payload.get("value"), Mapping) else payload

    output["avg_spo2"] = to_float(value.get("avg") or value.get("average"))
    output["min_spo2"] = to_float(value.get("min"))
    output["max_spo2"] = to_float(value.get("max"))

    if all(v is None for v in output.values()):
        add_note(notes, "partial_spo2")
    elif any(v is None for v in output.values()):
        add_note(notes, "partial_spo2")
    return output


def extract_spo2_range_values(*, blob: dict[str, Any] | None) -> list[float]:
    payload = blob_payload(blob)
    entries = payload.get("spo2")
    if not isinstance(entries, list):
        fallback_entries = payload.get("items")
        if isinstance(fallback_entries, list):
            entries = fallback_entries
        else:
            return []
    values: list[float] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        value = entry.get("value")
        if not isinstance(value, Mapping):
            continue
        avg = to_float(value.get("avg") or value.get("average"))
        if avg is not None:
            values.append(avg)
    return values


def derive_spo2_metrics(
    *,
    spo2_blob: dict[str, Any] | None,
    spo2_range_blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, float | None]:
    derived: dict[str, float | None] = {}
    spo2_metrics = features_from_spo2(blob=spo2_blob, notes=notes)
    derived["spo2Avg"] = spo2_metrics["avg_spo2"]
    derived["spo2Min"] = spo2_metrics["min_spo2"]
    derived["spo2Max"] = spo2_metrics["max_spo2"]
    if spo2_metrics["min_spo2"] is not None and spo2_metrics["max_spo2"] is not None:
        derived["spo2Range"] = spo2_metrics["max_spo2"] - spo2_metrics["min_spo2"]

    spo2_range_values = extract_spo2_range_values(blob=spo2_range_blob)
    if spo2_range_values:
        derived["spo2Avg7dAvg"] = statistics.mean(spo2_range_values)
        if derived["spo2Avg"] is not None:
            derived["spo2AvgDeviationFrom7d"] = derived["spo2Avg"] - derived["spo2Avg7dAvg"]
    elif blob_reason(spo2_range_blob) != "disabled_intraday":
        add_note(notes, "missing_spo2_range")
    return derived
