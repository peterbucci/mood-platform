from __future__ import annotations

import statistics
from collections.abc import Mapping
from typing import Any

from app.services.features.shared import (
    add_note,
    blob_payload,
    extract_first_nested_dict,
    is_missing_blob,
    to_float,
)


def features_from_temp(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, float | None]:
    output = {"skin_temp_deviation_c": None}
    if is_missing_blob(blob):
        add_note(notes, "missing_temp")
        return output

    payload = blob_payload(blob)
    value = extract_first_nested_dict(payload=payload, list_key="tempSkin", value_key="value")
    if not value:
        value = payload.get("value") if isinstance(payload.get("value"), Mapping) else payload

    output["skin_temp_deviation_c"] = to_float(
        value.get("nightlyRelative")
        or value.get("temperatureVariation")
        or value.get("skinTempDeviation")
    )
    if output["skin_temp_deviation_c"] is None:
        add_note(notes, "partial_temp")
    return output


def extract_temp_range_values(*, blob: dict[str, Any] | None) -> list[float]:
    payload = blob_payload(blob)
    entries = payload.get("tempSkin")
    if not isinstance(entries, list):
        return []
    values: list[float] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        value = entry.get("value")
        if not isinstance(value, Mapping):
            continue
        nightly = to_float(
            value.get("nightlyRelative")
            or value.get("temperatureVariation")
            or value.get("skinTempDeviation")
        )
        if nightly is not None:
            values.append(nightly)
    return values


def derive_temp_metrics(
    *,
    temp_blob: dict[str, Any] | None,
    temp_range_blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, float | None]:
    derived: dict[str, float | None] = {}
    temp_metrics = features_from_temp(blob=temp_blob, notes=notes)
    derived["tempSkinNightlyRelative"] = temp_metrics["skin_temp_deviation_c"]

    temp_range_values = extract_temp_range_values(blob=temp_range_blob)
    if temp_range_values:
        derived["tempSkinNightlyRelative7dAvg"] = statistics.mean(temp_range_values)
        if derived["tempSkinNightlyRelative"] is not None:
            derived["tempSkinNightlyRelativeDeviationFrom7d"] = (
                derived["tempSkinNightlyRelative"] - derived["tempSkinNightlyRelative7dAvg"]
            )
    else:
        add_note(notes, "missing_temp_range")
    return derived
