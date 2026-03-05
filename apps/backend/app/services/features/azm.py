from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.features.shared import (
    add_note,
    blob_payload,
    rolling_max_sum,
    slope,
    sum_non_null,
    to_float,
    window_sum,
    zero_streak_max,
)


def derive_azm_intraday_metrics(
    *,
    azm_intraday_blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, float | int | None]:
    derived: dict[str, float | int | None] = {}
    azm_total_series, azm_fat_series, azm_cardio_series, azm_peak_series = extract_azm_series(
        blob=azm_intraday_blob
    )
    if not azm_total_series:
        add_note(notes, "missing_intraday_azm")
        return derived

    derived["azmLast30m"] = window_sum(azm_total_series, 30)
    derived["azmLast60m"] = window_sum(azm_total_series, 60)
    derived["azmFatBurnLast30m"] = window_sum(azm_fat_series, 30)
    derived["azmCardioLast30m"] = window_sum(azm_cardio_series, 30)
    derived["azmPeakLast30m"] = window_sum(azm_peak_series, 30)
    derived["azmIntensityMinutes30m"] = sum_non_null(
        [derived["azmCardioLast30m"], derived["azmPeakLast30m"]]
    )
    derived["azmIntensityMinutes60m"] = sum_non_null(
        [window_sum(azm_cardio_series, 60), window_sum(azm_peak_series, 60)]
    )
    derived["azmZeroStreakMax60m"] = zero_streak_max(azm_total_series, 60)
    derived["azmSlopeLast60m"] = slope(azm_total_series[-60:])
    derived["azmSpike30m"] = rolling_max_sum(azm_total_series, 30)
    derived["azmFatBurnMinutes"] = sum_non_null(azm_fat_series)
    derived["azmCardioMinutes"] = sum_non_null(azm_cardio_series)
    derived["azmPeakMinutes"] = sum_non_null(azm_peak_series)
    return derived


def extract_azm_series(
    *,
    blob: dict[str, Any] | None,
) -> tuple[list[float], list[float], list[float], list[float]]:
    payload = blob_payload(blob)
    dataset = extract_azm_dataset(payload=payload)
    if not dataset:
        return [], [], [], []

    total: list[float] = []
    fat: list[float] = []
    cardio: list[float] = []
    peak: list[float] = []
    for point in dataset:
        if not isinstance(point, Mapping):
            continue
        value = point.get("value")
        normalized_value = value if isinstance(value, Mapping) else point
        total_value = to_float(
            normalized_value.get("activeZoneMinutes")
            or normalized_value.get("value")
            or normalized_value.get("minutes")
        )
        fat_value = to_float(
            normalized_value.get("fatBurnActiveZoneMinutes") or normalized_value.get("fatBurn")
        )
        cardio_value = to_float(
            normalized_value.get("cardioActiveZoneMinutes") or normalized_value.get("cardio")
        )
        peak_value = to_float(
            normalized_value.get("peakActiveZoneMinutes") or normalized_value.get("peak")
        )

        total.append(total_value or 0.0)
        fat.append(fat_value or 0.0)
        cardio.append(cardio_value or 0.0)
        peak.append(peak_value or 0.0)
    return total, fat, cardio, peak


def extract_azm_dataset(*, payload: dict[str, Any]) -> list[Any]:
    candidate_keys = (
        "activities-active-zone-minutes-intraday",
        "activities-active-zone-minutes",
        "activities-azm-intraday",
    )
    for key in candidate_keys:
        parent = payload.get(key)
        if isinstance(parent, Mapping):
            dataset = parent.get("dataset")
            if isinstance(dataset, list):
                return dataset
        if isinstance(parent, list):
            for entry in parent:
                if not isinstance(entry, Mapping):
                    continue
                minutes = entry.get("minutes")
                if isinstance(minutes, list):
                    return minutes
    return []
