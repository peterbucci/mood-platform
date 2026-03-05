from __future__ import annotations

import statistics
from collections.abc import Mapping
from typing import Any

from app.services.features.shared import (
    add_note,
    blob_payload,
    extract_first_nested_dict,
    is_missing_blob,
    stddev,
    to_float,
)


def features_from_hrv(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, float | None]:
    output = {
        "daily_rmssd": None,
        "deep_rmssd": None,
        "coverage": None,
    }
    if is_missing_blob(blob):
        add_note(notes, "missing_hrv")
        return output

    payload = blob_payload(blob)
    value = extract_first_nested_dict(payload=payload, list_key="hrv", value_key="value")
    if not value:
        value = payload.get("value") if isinstance(payload.get("value"), Mapping) else {}

    output["daily_rmssd"] = to_float(value.get("dailyRmssd") or value.get("rmssd"))
    output["deep_rmssd"] = to_float(value.get("deepRmssd") or value.get("deepSleepRmssd"))
    output["coverage"] = to_float(value.get("coverage"))

    core_values = [output["daily_rmssd"], output["deep_rmssd"]]
    if all(v is None for v in core_values):
        add_note(notes, "partial_hrv")
    elif any(v is None for v in core_values):
        add_note(notes, "partial_hrv")
    return output


def canonical_hrv_coverage(
    *,
    hrv_features: dict[str, float | None],
    derived_features: dict[str, Any],
) -> float | None:
    intraday_coverage_mean = to_float(derived_features.get("hrvIntradayCoverageMean"))
    if intraday_coverage_mean is not None:
        return intraday_coverage_mean
    if to_float(hrv_features.get("daily_rmssd")) is not None:
        return 0.5
    return to_float(hrv_features.get("coverage"))


def extract_hrv_daily_values(*, blob: dict[str, Any] | None) -> list[float]:
    payload = blob_payload(blob)
    entries = payload.get("hrv")
    if not isinstance(entries, list):
        return []
    values: list[float] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        value = entry.get("value")
        if not isinstance(value, Mapping):
            continue
        rmssd = to_float(value.get("dailyRmssd") or value.get("rmssd"))
        if rmssd is not None:
            values.append(rmssd)
    return values


def extract_hrv_intraday_values(*, blob: dict[str, Any] | None) -> dict[str, list[float]]:
    payload = blob_payload(blob)
    entries = payload.get("hrv")
    rmssd_values: list[float] = []
    lf_values: list[float] = []
    hf_values: list[float] = []
    lf_hf_ratio_values: list[float] = []
    coverage_values: list[float] = []
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            minutes = entry.get("minutes")
            if not isinstance(minutes, list):
                continue
            for minute in minutes:
                if not isinstance(minute, Mapping):
                    continue
                minute_value = minute.get("value")
                if not isinstance(minute_value, Mapping):
                    continue
                rmssd = to_float(minute_value.get("rmssd"))
                if rmssd is not None:
                    rmssd_values.append(rmssd)
                lf = to_float(minute_value.get("lf"))
                if lf is not None:
                    lf_values.append(lf)
                hf = to_float(minute_value.get("hf"))
                if hf is not None:
                    hf_values.append(hf)
                if lf is not None and hf not in (None, 0):
                    lf_hf_ratio_values.append(lf / hf)
                coverage = to_float(minute_value.get("coverage"))
                if coverage is not None:
                    coverage_values.append(coverage)
    return {
        "rmssd": rmssd_values,
        "lf": lf_values,
        "hf": hf_values,
        "lf_hf_ratio": lf_hf_ratio_values,
        "coverage": coverage_values,
    }


def derive_hrv_metrics(
    *,
    hrv_blob: dict[str, Any] | None,
    hrv_range_blob: dict[str, Any] | None,
    hrv_all_blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, float | None]:
    derived: dict[str, float | None] = {}

    hrv_value = features_from_hrv(blob=hrv_blob, notes=notes)
    if hrv_value["daily_rmssd"] is not None:
        derived["hrvRmssdDaily"] = hrv_value["daily_rmssd"]
    if hrv_value["deep_rmssd"] is not None:
        derived["hrvDeepRmssdDaily"] = hrv_value["deep_rmssd"]

    hrv_range_values = extract_hrv_daily_values(blob=hrv_range_blob)
    if hrv_range_values:
        derived["hrvRmssd7dAvg"] = statistics.mean(hrv_range_values)
        if derived.get("hrvRmssdDaily") is not None:
            derived["hrvRmssdDeviationFrom7d"] = derived["hrvRmssdDaily"] - derived["hrvRmssd7dAvg"]
    else:
        add_note(notes, "missing_hrv_range")

    hrv_intraday = extract_hrv_intraday_values(blob=hrv_all_blob)
    if hrv_intraday["rmssd"]:
        derived["hrvIntradayRmssdMean"] = statistics.mean(hrv_intraday["rmssd"])
        derived["hrvIntradayRmssdStdDev"] = stddev(hrv_intraday["rmssd"])
    if hrv_intraday["lf"]:
        derived["hrvIntradayLfMean"] = statistics.mean(hrv_intraday["lf"])
    if hrv_intraday["hf"]:
        derived["hrvIntradayHfMean"] = statistics.mean(hrv_intraday["hf"])
    if hrv_intraday["lf_hf_ratio"]:
        derived["hrvIntradayLfHfRatioMean"] = statistics.mean(hrv_intraday["lf_hf_ratio"])
    if hrv_intraday["coverage"]:
        derived["hrvIntradayCoverageMean"] = statistics.mean(hrv_intraday["coverage"])
    if not any(hrv_intraday.values()):
        add_note(notes, "missing_hrv_all")

    return derived
