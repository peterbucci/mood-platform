from __future__ import annotations

import statistics
from collections.abc import Mapping
from typing import Any

from app.services.features.shared import (
    add_note,
    blob_payload,
    extract_first_nested_dict,
    get_nested,
    is_missing_blob,
    to_float,
)


def features_from_breathing_rate(
    *,
    blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, float | None]:
    output = {"sleeping_br": None}
    if is_missing_blob(blob):
        reason = (blob or {}).get("reason")
        if reason in {"forbidden", "forbidden_scope", "needs_reauth"}:
            add_note(notes, "missing_breathing_rate_forbidden")
        else:
            add_note(notes, "missing_breathing_rate")
        return output

    payload = blob_payload(blob)
    value = extract_first_nested_dict(payload=payload, list_key="br", value_key="value")
    if not value:
        value = payload
    output["sleeping_br"] = to_float(
        value.get("breathingRate")
        or value.get("sleepingBreathingRate")
        or get_nested(value, "deepSleepSummary", "breathingRate")
    )
    if output["sleeping_br"] is None:
        add_note(notes, "partial_breathing_rate")
    return output


def extract_breathing_metrics(
    *,
    blob: dict[str, Any] | None,
    all_blob: dict[str, Any] | None,
) -> dict[str, float | None]:
    output = {
        "brFullNight": None,
        "brDeepSleep": None,
        "brRemSleep": None,
        "brLightSleep": None,
    }
    payload = blob_payload(blob)
    value = extract_first_nested_dict(payload=payload, list_key="br", value_key="value")
    if not value:
        value = payload
    output["brFullNight"] = to_float(
        value.get("breathingRate")
        or value.get("sleepingBreathingRate")
        or get_nested(value, "fullSleepSummary", "breathingRate")
    )
    output["brDeepSleep"] = to_float(get_nested(value, "deepSleepSummary", "breathingRate"))
    output["brRemSleep"] = to_float(get_nested(value, "remSleepSummary", "breathingRate"))
    output["brLightSleep"] = to_float(get_nested(value, "lightSleepSummary", "breathingRate"))

    if (
        output["brFullNight"] is None
        or output["brDeepSleep"] is None
        or output["brRemSleep"] is None
        or output["brLightSleep"] is None
    ):
        all_payload = blob_payload(all_blob)
        all_value = extract_first_nested_dict(payload=all_payload, list_key="br", value_key="value")
        if all_value:
            if output["brFullNight"] is None:
                output["brFullNight"] = to_float(
                    all_value.get("breathingRate") or all_value.get("sleepingBreathingRate")
                )
            if output["brDeepSleep"] is None:
                output["brDeepSleep"] = to_float(
                    get_nested(all_value, "deepSleepSummary", "breathingRate")
                )
            if output["brRemSleep"] is None:
                output["brRemSleep"] = to_float(
                    get_nested(all_value, "remSleepSummary", "breathingRate")
                )
            if output["brLightSleep"] is None:
                output["brLightSleep"] = to_float(
                    get_nested(all_value, "lightSleepSummary", "breathingRate")
                )
    return output


def extract_breathing_range_values(*, blob: dict[str, Any] | None) -> list[float]:
    payload = blob_payload(blob)
    entries = payload.get("br")
    if not isinstance(entries, list):
        return []
    values: list[float] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        value = entry.get("value")
        if not isinstance(value, Mapping):
            continue
        br = to_float(value.get("breathingRate") or value.get("sleepingBreathingRate"))
        if br is not None:
            values.append(br)
    return values


def derive_breathing_metrics(
    *,
    breathing_rate_blob: dict[str, Any] | None,
    breathing_rate_all_blob: dict[str, Any] | None,
    breathing_rate_range_blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, float | None]:
    derived: dict[str, float | None] = {}
    br_value = extract_breathing_metrics(
        blob=breathing_rate_blob,
        all_blob=breathing_rate_all_blob,
    )
    if br_value["brFullNight"] is not None:
        derived["brFullNight"] = br_value["brFullNight"]
    derived["brDeepSleep"] = br_value["brDeepSleep"]
    derived["brRemSleep"] = br_value["brRemSleep"]
    derived["brLightSleep"] = br_value["brLightSleep"]

    br_range_values = extract_breathing_range_values(blob=breathing_rate_range_blob)
    if br_range_values:
        derived["brFullNight7dAvg"] = statistics.mean(br_range_values)
        if derived.get("brFullNight") is not None:
            derived["brFullNightDeviationFrom7d"] = (
                derived["brFullNight"] - derived["brFullNight7dAvg"]
            )
    else:
        add_note(notes, "missing_breathing_rate_range")
    return derived
