from __future__ import annotations

import statistics
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

MISSING_SIGNAL_MARKER = "__missing"


def build_feature_payload(
    *,
    raw_fitbit_data: dict[str, Any],
    anchor_datetime: datetime | None = None,
    client_features: dict[str, Any] | None = None,
    weather_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    notes: list[str] = []
    anchor = anchor_datetime or datetime.now(tz=UTC)
    passthrough_client_features = _filtered_client_features(client_features)

    activity_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("activity_summary", "activity"),
        missing_reason="missing_activity",
    )
    sleep_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("sleep",),
        missing_reason="missing_sleep",
    )
    heart_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("heart", "heart_rate"),
        missing_reason="missing_heart_rate",
    )
    hrv_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("hrv",),
        missing_reason="missing_hrv",
    )
    breathing_rate_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("breathing_rate",),
        missing_reason="missing_breathing_rate",
    )
    spo2_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("spo2",),
        missing_reason="missing_spo2",
    )
    temp_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("temp",),
        missing_reason="missing_temp",
    )
    nutrition_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("nutrition",),
        missing_reason="missing_nutrition",
    )
    water_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("water",),
        missing_reason="missing_water",
    )
    steps_intraday_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("steps_intraday",),
        missing_reason="missing_intraday_steps",
    )
    calories_intraday_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("calories_intraday",),
        missing_reason="missing_intraday_calories",
    )
    azm_intraday_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("azm_intraday",),
        missing_reason="missing_intraday_azm",
    )
    heart_intraday_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("heart_intraday",),
        missing_reason="missing_intraday_heart",
    )
    latest_exercise_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("latest_exercise",),
        missing_reason="missing_latest_exercise",
    )
    steps_7d_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("steps_7d",),
        missing_reason="missing_steps_7d",
    )
    heart_7d_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("heart_7d",),
        missing_reason="missing_heart_7d",
    )
    hrv_range_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("hrv_range",),
        missing_reason="missing_hrv_range",
    )
    hrv_all_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("hrv_all",),
        missing_reason="missing_hrv_all",
    )
    sleep_range_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("sleep_range",),
        missing_reason="missing_sleep_range",
    )
    breathing_rate_all_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("breathing_rate_all",),
        missing_reason="missing_breathing_rate_all",
    )
    breathing_rate_range_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("breathing_rate_range",),
        missing_reason="missing_breathing_rate_range",
    )
    spo2_range_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("spo2_range",),
        missing_reason="missing_spo2_range",
    )
    temp_range_blob = _signal_blob(
        raw_fitbit_data=raw_fitbit_data,
        signal_keys=("temp_range",),
        missing_reason="missing_temp_range",
    )
    weather_blob = _signal_blob(
        raw_fitbit_data=weather_context or {},
        signal_keys=("weather",),
        missing_reason="missing_weather",
    )
    air_quality_blob = _signal_blob(
        raw_fitbit_data=weather_context or {},
        signal_keys=("air_quality",),
        missing_reason="missing_air_quality",
    )

    activity_features = features_from_activity(blob=activity_blob)
    nutrition_features = features_from_nutrition(blob=nutrition_blob, notes=notes)
    water_features = features_from_water(blob=water_blob, notes=notes)

    payload = {
        # Keep existing top-level keys stable for API clients.
        "sleep": _legacy_or_derived_sleep_section(
            raw_fitbit_data=raw_fitbit_data,
            sleep_blob=sleep_blob,
        ),
        "steps": _legacy_or_derived_steps_section(
            raw_fitbit_data=raw_fitbit_data, activity_features=activity_features
        ),
        "exercise": _legacy_or_derived_exercise_section(
            raw_fitbit_data=raw_fitbit_data,
            activity_blob=activity_blob,
            activity_features=activity_features,
        ),
        "heart_rate": _legacy_or_derived_heart_rate_section(
            raw_fitbit_data=raw_fitbit_data,
            heart_blob=heart_blob,
        ),
        "resting_heart_rate": _legacy_or_derived_resting_heart_rate_section(
            raw_fitbit_data=raw_fitbit_data,
            heart_blob=heart_blob,
            activity_blob=activity_blob,
        ),
        "calories": _legacy_or_derived_calories_section(
            raw_fitbit_data=raw_fitbit_data,
            activity_features=activity_features,
            nutrition_features=nutrition_features,
        ),
        # New parity sections.
        "activity": activity_features,
        "hrv": features_from_hrv(blob=hrv_blob, notes=notes),
        "breathing_rate": features_from_breathing_rate(blob=breathing_rate_blob, notes=notes),
        "spo2": features_from_spo2(blob=spo2_blob, notes=notes),
        "temp": features_from_temp(blob=temp_blob, notes=notes),
        "nutrition": nutrition_features,
        "water": water_features,
        "derived": build_derived_features(
            anchor_datetime=anchor,
            activity_blob=activity_blob,
            heart_blob=heart_blob,
            sleep_blob=sleep_blob,
            hrv_blob=hrv_blob,
            breathing_rate_blob=breathing_rate_blob,
            spo2_blob=spo2_blob,
            temp_blob=temp_blob,
            nutrition_blob=nutrition_blob,
            water_blob=water_blob,
            steps_intraday_blob=steps_intraday_blob,
            calories_intraday_blob=calories_intraday_blob,
            azm_intraday_blob=azm_intraday_blob,
            heart_intraday_blob=heart_intraday_blob,
            latest_exercise_blob=latest_exercise_blob,
            steps_7d_blob=steps_7d_blob,
            heart_7d_blob=heart_7d_blob,
            hrv_range_blob=hrv_range_blob,
            hrv_all_blob=hrv_all_blob,
            sleep_range_blob=sleep_range_blob,
            breathing_rate_all_blob=breathing_rate_all_blob,
            breathing_rate_range_blob=breathing_rate_range_blob,
            spo2_range_blob=spo2_range_blob,
            temp_range_blob=temp_range_blob,
            weather_blob=weather_blob,
            air_quality_blob=air_quality_blob,
            client_features=passthrough_client_features,
            notes=notes,
        ),
        "clientFeatures": passthrough_client_features,
        "notes": notes,
    }
    return payload


def features_from_activity(*, blob: dict[str, Any] | None) -> dict[str, int | float | None]:
    output = {
        "steps_count": None,
        "calories_out_kcal": None,
        "active_zone_minutes": None,
    }
    payload = _blob_payload(blob)
    summary = payload.get("summary") if isinstance(payload.get("summary"), Mapping) else {}
    output["steps_count"] = _to_int(summary.get("steps"))
    output["calories_out_kcal"] = _to_int(summary.get("caloriesOut"))

    zone_minutes = _to_int(summary.get("activeZoneMinutes"))
    if zone_minutes is not None:
        output["active_zone_minutes"] = zone_minutes
        return output

    very = _to_int(summary.get("veryActiveMinutes"))
    fairly = _to_int(summary.get("fairlyActiveMinutes"))
    lightly = _to_int(summary.get("lightlyActiveMinutes"))
    if any(value is not None for value in (very, fairly, lightly)):
        output["active_zone_minutes"] = (very or 0) + (fairly or 0) + (lightly or 0)
    return output


def features_from_hrv(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, float | None]:
    output = {
        "daily_rmssd": None,
        "deep_rmssd": None,
        "coverage": None,
    }
    if _is_missing_blob(blob):
        _add_note(notes, "missing_hrv")
        return output

    payload = _blob_payload(blob)
    value = _extract_first_nested_dict(payload=payload, list_key="hrv", value_key="value")
    if not value:
        value = payload.get("value") if isinstance(payload.get("value"), Mapping) else {}

    output["daily_rmssd"] = _to_float(value.get("dailyRmssd") or value.get("rmssd"))
    output["deep_rmssd"] = _to_float(value.get("deepRmssd") or value.get("deepSleepRmssd"))
    output["coverage"] = _to_float(value.get("coverage"))

    if all(v is None for v in output.values()):
        _add_note(notes, "partial_hrv")
    elif any(v is None for v in output.values()):
        _add_note(notes, "partial_hrv")
    return output


def features_from_breathing_rate(
    *, blob: dict[str, Any] | None, notes: list[str]
) -> dict[str, float | None]:
    output = {"sleeping_br": None}
    if _is_missing_blob(blob):
        if _blob_reason(blob) in {"forbidden", "forbidden_scope", "needs_reauth"}:
            _add_note(notes, "missing_breathing_rate_forbidden")
        else:
            _add_note(notes, "missing_breathing_rate")
        return output

    payload = _blob_payload(blob)
    value = _extract_first_nested_dict(payload=payload, list_key="br", value_key="value")
    if not value:
        value = payload
    output["sleeping_br"] = _to_float(
        value.get("breathingRate")
        or value.get("sleepingBreathingRate")
        or _get_nested(value, "deepSleepSummary", "breathingRate")
    )
    if output["sleeping_br"] is None:
        _add_note(notes, "partial_breathing_rate")
    return output


def features_from_spo2(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, float | None]:
    output = {
        "avg_spo2": None,
        "min_spo2": None,
        "max_spo2": None,
    }
    if _is_missing_blob(blob):
        _add_note(notes, "missing_spo2")
        return output

    payload = _blob_payload(blob)
    value = _extract_first_nested_dict(payload=payload, list_key="spo2", value_key="value")
    if not value:
        value = payload.get("value") if isinstance(payload.get("value"), Mapping) else payload

    output["avg_spo2"] = _to_float(value.get("avg") or value.get("average"))
    output["min_spo2"] = _to_float(value.get("min"))
    output["max_spo2"] = _to_float(value.get("max"))

    if all(v is None for v in output.values()):
        _add_note(notes, "partial_spo2")
    elif any(v is None for v in output.values()):
        _add_note(notes, "partial_spo2")
    return output


def features_from_temp(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, float | None]:
    output = {"skin_temp_deviation_c": None}
    if _is_missing_blob(blob):
        _add_note(notes, "missing_temp")
        return output

    payload = _blob_payload(blob)
    value = _extract_first_nested_dict(payload=payload, list_key="tempSkin", value_key="value")
    if not value:
        value = payload.get("value") if isinstance(payload.get("value"), Mapping) else payload

    output["skin_temp_deviation_c"] = _to_float(
        value.get("nightlyRelative")
        or value.get("temperatureVariation")
        or value.get("skinTempDeviation")
    )
    if output["skin_temp_deviation_c"] is None:
        _add_note(notes, "partial_temp")
    return output


def features_from_nutrition(
    *, blob: dict[str, Any] | None, notes: list[str]
) -> dict[str, int | float | None]:
    output = {
        "calories_in_kcal": None,
        "carbs_g": None,
        "fat_g": None,
        "protein_g": None,
    }
    if _is_missing_blob(blob):
        _add_note(notes, "missing_nutrition")
        return output

    payload = _blob_payload(blob)
    summary = payload.get("summary") if isinstance(payload.get("summary"), Mapping) else {}
    output["calories_in_kcal"] = _to_int(summary.get("calories"))
    output["carbs_g"] = _to_float(summary.get("carbs"))
    output["fat_g"] = _to_float(summary.get("fat"))
    output["protein_g"] = _to_float(summary.get("protein"))

    if all(v is None for v in output.values()):
        _add_note(notes, "partial_nutrition")
    elif any(v is None for v in output.values()):
        _add_note(notes, "partial_nutrition")
    return output


def features_from_water(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, int | None]:
    output = {"water_ml": None}
    if _is_missing_blob(blob):
        _add_note(notes, "missing_water")
        return output

    payload = _blob_payload(blob)
    summary = payload.get("summary") if isinstance(payload.get("summary"), Mapping) else {}
    output["water_ml"] = _to_int(summary.get("water"))
    if output["water_ml"] is None:
        water_entries = payload.get("water")
        if isinstance(water_entries, list) and water_entries:
            for entry in water_entries:
                if isinstance(entry, Mapping):
                    amount = _to_float(entry.get("amount"))
                    if amount is not None:
                        output["water_ml"] = int(amount)
                        break

    if output["water_ml"] is None:
        _add_note(notes, "partial_water")
    return output


def build_derived_features(
    *,
    anchor_datetime: datetime,
    activity_blob: dict[str, Any] | None,
    heart_blob: dict[str, Any] | None,
    sleep_blob: dict[str, Any] | None,
    hrv_blob: dict[str, Any] | None,
    breathing_rate_blob: dict[str, Any] | None,
    spo2_blob: dict[str, Any] | None,
    temp_blob: dict[str, Any] | None,
    nutrition_blob: dict[str, Any] | None,
    water_blob: dict[str, Any] | None,
    steps_intraday_blob: dict[str, Any] | None,
    calories_intraday_blob: dict[str, Any] | None,
    azm_intraday_blob: dict[str, Any] | None,
    heart_intraday_blob: dict[str, Any] | None,
    latest_exercise_blob: dict[str, Any] | None,
    steps_7d_blob: dict[str, Any] | None,
    heart_7d_blob: dict[str, Any] | None,
    hrv_range_blob: dict[str, Any] | None,
    hrv_all_blob: dict[str, Any] | None,
    sleep_range_blob: dict[str, Any] | None,
    breathing_rate_all_blob: dict[str, Any] | None,
    breathing_rate_range_blob: dict[str, Any] | None,
    spo2_range_blob: dict[str, Any] | None,
    temp_range_blob: dict[str, Any] | None,
    weather_blob: dict[str, Any] | None,
    air_quality_blob: dict[str, Any] | None,
    client_features: dict[str, Any],
    notes: list[str],
) -> dict[str, Any]:
    derived = _default_derived_features()
    derived["hourOfDay"] = anchor_datetime.hour
    derived["dayOfWeek"] = anchor_datetime.weekday()
    derived["isWeekend"] = anchor_datetime.weekday() >= 5

    steps_series = _extract_intraday_series(
        blob=steps_intraday_blob,
        dataset_key="activities-steps-intraday",
        value_key="value",
    )
    if not steps_series:
        _add_note(notes, "missing_intraday_steps")
    else:
        derived["stepsLast5m"] = _window_sum(steps_series, 5)
        derived["stepsLast15m"] = _window_sum(steps_series, 15)
        derived["stepsLast30m"] = _window_sum(steps_series, 30)
        derived["stepsLast60m"] = _window_sum(steps_series, 60)
        derived["stepsLast3h"] = _window_sum(steps_series, 180)
        derived["stepBurst5m"] = _rolling_max_sum(steps_series, 5)
        derived["zeroStreakMax60m"] = _zero_streak_max(steps_series, 60)
        derived["stepsSlopeLast60m"] = _slope(steps_series[-60:])
        recent_5 = _window_sum(steps_series, 5)
        previous_10 = _window_sum(steps_series[-15:-5], 10)
        if recent_5 is not None and previous_10 is not None:
            derived["stepsAccel5to15m"] = recent_5 - (previous_10 / 2.0)
        derived["sedentaryMinsLast3h"] = _zero_count(steps_series, 180)

    calories_series = _extract_intraday_series(
        blob=calories_intraday_blob,
        dataset_key="activities-calories-intraday",
        value_key="value",
    )
    if not calories_series:
        _add_note(notes, "missing_intraday_calories")
    else:
        derived["caloriesOutLast3h"] = _window_sum(calories_series, 180)

    activity_payload = _blob_payload(activity_blob)
    activity_summary = (
        activity_payload.get("summary")
        if isinstance(activity_payload.get("summary"), Mapping)
        else {}
    )
    derived["azmToday"] = _to_int(activity_summary.get("activeZoneMinutes"))
    if derived["azmToday"] is None:
        derived["azmToday"] = _sum_non_null(
            [
                _to_int(activity_summary.get("veryActiveMinutes")),
                _to_int(activity_summary.get("fairlyActiveMinutes")),
                _to_int(activity_summary.get("lightlyActiveMinutes")),
            ]
        )
    derived["caloriesOutToday"] = _to_int(activity_summary.get("caloriesOut"))
    derived["restingHR"] = _extract_resting_heart_rate(
        activity_blob=activity_blob,
        heart_blob=heart_blob,
    )

    azm_total_series, azm_fat_series, azm_cardio_series, azm_peak_series = _extract_azm_series(
        blob=azm_intraday_blob
    )
    if not azm_total_series:
        _add_note(notes, "missing_intraday_azm")
    else:
        derived["azmLast30m"] = _window_sum(azm_total_series, 30)
        derived["azmLast60m"] = _window_sum(azm_total_series, 60)
        derived["azmFatBurnLast30m"] = _window_sum(azm_fat_series, 30)
        derived["azmCardioLast30m"] = _window_sum(azm_cardio_series, 30)
        derived["azmPeakLast30m"] = _window_sum(azm_peak_series, 30)
        derived["azmIntensityMinutes30m"] = _sum_non_null(
            [derived["azmCardioLast30m"], derived["azmPeakLast30m"]]
        )
        derived["azmIntensityMinutes60m"] = _sum_non_null(
            [_window_sum(azm_cardio_series, 60), _window_sum(azm_peak_series, 60)]
        )
        derived["azmZeroStreakMax60m"] = _zero_streak_max(azm_total_series, 60)
        derived["azmSlopeLast60m"] = _slope(azm_total_series[-60:])
        derived["azmSpike30m"] = _rolling_max_sum(azm_total_series, 30)
        derived["azmFatBurnMinutes"] = _sum_non_null(azm_fat_series)
        derived["azmCardioMinutes"] = _sum_non_null(azm_cardio_series)
        derived["azmPeakMinutes"] = _sum_non_null(azm_peak_series)

    heart_series = _extract_intraday_series(
        blob=heart_intraday_blob,
        dataset_key="activities-heart-intraday",
        value_key="value",
    )
    if not heart_series:
        _add_note(notes, "missing_intraday_heart")
    else:
        derived["hrNow"] = _last_value(heart_series)
        derived["hrAvgLast5m"] = _window_avg(heart_series, 5)
        derived["hrAvgLast15m"] = _window_avg(heart_series, 15)
        derived["hrAvgLast60m"] = _window_avg(heart_series, 60)
        derived["hrMinLast15m"] = _window_min(heart_series, 15)
        derived["hrMaxLast15m"] = _window_max(heart_series, 15)
        now_value = _last_value(heart_series)
        if now_value is not None:
            if len(heart_series) >= 6:
                derived["hrDelta5m"] = now_value - heart_series[-6]
            if len(heart_series) >= 16:
                derived["hrDelta15m"] = now_value - heart_series[-16]
        derived["hrSlopeLast30m"] = _slope(heart_series[-30:])
        derived["hrStdLast30m"] = _stddev(heart_series[-30:])
        derived["hrStdLast60m"] = _stddev(heart_series[-60:])
        derived["hrSlopeLast60m"] = _slope(heart_series[-60:])

    rhr_series = _extract_resting_heart_rate_series(heart_7d_blob=heart_7d_blob)
    if rhr_series:
        derived["rhrMean7d"] = _window_avg(rhr_series, len(rhr_series))
        derived["rhrStd7d"] = _stddev(rhr_series)
        derived["restingHR7dTrend"] = _slope(rhr_series)
    else:
        _add_note(notes, "missing_heart_7d")

    if (
        derived["hrNow"] is not None
        and derived["rhrMean7d"] is not None
        and derived["rhrStd7d"] not in (None, 0)
    ):
        derived["hrZNow"] = (derived["hrNow"] - derived["rhrMean7d"]) / derived["rhrStd7d"]
    if (
        derived["hrAvgLast15m"] is not None
        and derived["rhrMean7d"] is not None
        and derived["rhrStd7d"] not in (None, 0)
    ):
        derived["hrZLast15m"] = (derived["hrAvgLast15m"] - derived["rhrMean7d"]) / derived[
            "rhrStd7d"
        ]

    sleep_payload = _blob_payload(sleep_blob)
    primary_sleep = _primary_sleep_entry(sleep_payload)
    if primary_sleep is None:
        _add_note(notes, "missing_sleep")
    else:
        minutes_asleep = _to_float(primary_sleep.get("minutesAsleep"))
        if minutes_asleep is not None:
            derived["sleepDurationLastNightHrs"] = round(minutes_asleep / 60.0, 3)
        derived["sleepEfficiency"] = _to_float(primary_sleep.get("efficiency"))
        derived["wasoMinutes"] = _to_float(primary_sleep.get("minutesAwake"))
        levels_summary = _get_nested(primary_sleep, "levels", "summary")
        deep_minutes = _to_float(_get_nested(levels_summary, "deep", "minutes"))
        rem_minutes = _to_float(_get_nested(levels_summary, "rem", "minutes"))
        total_minutes = _to_float(primary_sleep.get("minutesAsleep"))
        if total_minutes and total_minutes > 0:
            if rem_minutes is not None:
                derived["remRatio"] = rem_minutes / total_minutes
            if deep_minutes is not None:
                derived["deepRatio"] = deep_minutes / total_minutes
        start_time = _parse_datetime(primary_sleep.get("startTime"))
        end_time = _parse_datetime(primary_sleep.get("endTime"))
        if start_time is not None:
            derived["sleepOnsetLocalHour"] = start_time.hour
        if end_time is not None:
            derived["wakeTimeLocalHour"] = end_time.hour
        awakenings = _to_float(primary_sleep.get("awakeningsCount"))
        if awakenings is not None and total_minutes and total_minutes > 0:
            derived["sleepFragmentationScore"] = awakenings / total_minutes

    sleep_entries = _extract_sleep_entries(blob=sleep_range_blob)
    if sleep_entries:
        bed_hours = [
            _parse_datetime(entry.get("startTime")).hour
            for entry in sleep_entries
            if _parse_datetime(entry.get("startTime")) is not None
        ]
        durations_hours = [
            (_to_float(entry.get("minutesAsleep")) or 0) / 60.0
            for entry in sleep_entries
            if _to_float(entry.get("minutesAsleep")) is not None
        ]
        if len(bed_hours) >= 2:
            derived["bedtimeStdDev7d"] = _stddev([float(hour) for hour in bed_hours])
        if durations_hours:
            avg_sleep = statistics.mean(durations_hours)
            derived["sleepDebtHrs"] = max(0.0, 8.0 - avg_sleep)
    else:
        _add_note(notes, "missing_sleep_range")

    hrv_value = features_from_hrv(blob=hrv_blob, notes=notes)
    if hrv_value["daily_rmssd"] is not None:
        derived["hrvRmssdDaily"] = hrv_value["daily_rmssd"]
    if hrv_value["deep_rmssd"] is not None:
        derived["hrvDeepRmssdDaily"] = hrv_value["deep_rmssd"]

    hrv_range_values = _extract_hrv_daily_values(blob=hrv_range_blob)
    if hrv_range_values:
        derived["hrvRmssd7dAvg"] = statistics.mean(hrv_range_values)
        if derived["hrvRmssdDaily"] is not None:
            derived["hrvRmssdDeviationFrom7d"] = derived["hrvRmssdDaily"] - derived["hrvRmssd7dAvg"]
    else:
        _add_note(notes, "missing_hrv_range")

    hrv_intraday = _extract_hrv_intraday_values(blob=hrv_all_blob)
    if hrv_intraday["rmssd"]:
        derived["hrvIntradayRmssdMean"] = statistics.mean(hrv_intraday["rmssd"])
        derived["hrvIntradayRmssdStdDev"] = _stddev(hrv_intraday["rmssd"])
    if hrv_intraday["lf"]:
        derived["hrvIntradayLfMean"] = statistics.mean(hrv_intraday["lf"])
    if hrv_intraday["hf"]:
        derived["hrvIntradayHfMean"] = statistics.mean(hrv_intraday["hf"])
    if hrv_intraday["lf_hf_ratio"]:
        derived["hrvIntradayLfHfRatioMean"] = statistics.mean(hrv_intraday["lf_hf_ratio"])
    if hrv_intraday["coverage"]:
        derived["hrvIntradayCoverageMean"] = statistics.mean(hrv_intraday["coverage"])
    if not any(hrv_intraday.values()):
        _add_note(notes, "missing_hrv_all")

    br_value = _extract_breathing_metrics(
        blob=breathing_rate_blob,
        all_blob=breathing_rate_all_blob,
    )
    if br_value["brFullNight"] is not None:
        derived["brFullNight"] = br_value["brFullNight"]
    derived["brDeepSleep"] = br_value["brDeepSleep"]
    derived["brRemSleep"] = br_value["brRemSleep"]
    derived["brLightSleep"] = br_value["brLightSleep"]
    br_range_values = _extract_breathing_range_values(blob=breathing_rate_range_blob)
    if br_range_values:
        derived["brFullNight7dAvg"] = statistics.mean(br_range_values)
        if derived["brFullNight"] is not None:
            derived["brFullNightDeviationFrom7d"] = (
                derived["brFullNight"] - derived["brFullNight7dAvg"]
            )
    else:
        _add_note(notes, "missing_breathing_rate_range")

    spo2_metrics = features_from_spo2(blob=spo2_blob, notes=notes)
    derived["spo2Avg"] = spo2_metrics["avg_spo2"]
    derived["spo2Min"] = spo2_metrics["min_spo2"]
    derived["spo2Max"] = spo2_metrics["max_spo2"]
    if spo2_metrics["min_spo2"] is not None and spo2_metrics["max_spo2"] is not None:
        derived["spo2Range"] = spo2_metrics["max_spo2"] - spo2_metrics["min_spo2"]
    spo2_range_values = _extract_spo2_range_values(blob=spo2_range_blob)
    if spo2_range_values:
        derived["spo2Avg7dAvg"] = statistics.mean(spo2_range_values)
        if derived["spo2Avg"] is not None:
            derived["spo2AvgDeviationFrom7d"] = derived["spo2Avg"] - derived["spo2Avg7dAvg"]
    else:
        _add_note(notes, "missing_spo2_range")

    temp_metrics = features_from_temp(blob=temp_blob, notes=notes)
    derived["tempSkinNightlyRelative"] = temp_metrics["skin_temp_deviation_c"]
    temp_range_values = _extract_temp_range_values(blob=temp_range_blob)
    if temp_range_values:
        derived["tempSkinNightlyRelative7dAvg"] = statistics.mean(temp_range_values)
        if derived["tempSkinNightlyRelative"] is not None:
            derived["tempSkinNightlyRelativeDeviationFrom7d"] = (
                derived["tempSkinNightlyRelative"] - derived["tempSkinNightlyRelative7dAvg"]
            )
    else:
        _add_note(notes, "missing_temp_range")

    exercise = _extract_latest_exercise_metrics(
        blob=latest_exercise_blob,
        anchor_datetime=anchor_datetime,
    )
    derived.update(exercise)
    if all(
        exercise.get(key) is None
        for key in (
            "timeSinceLastExerciseMin",
            "lastExerciseType",
            "lastExerciseDurationMinutes",
        )
    ):
        _add_note(notes, "missing_latest_exercise")

    nutrition = _extract_nutrition_metrics(nutrition_blob=nutrition_blob, water_blob=water_blob)
    derived.update(nutrition)

    derived["acuteArousalIndex"] = _acute_arousal_index(
        hr_z_now=_to_float(derived.get("hrZNow")),
        sleep_debt_hours=_to_float(derived.get("sleepDebtHrs")),
    )
    if _to_float(derived.get("stepsLast60m")) is not None:
        derived["recentActivityXTimeOfDay"] = _to_float(derived.get("stepsLast60m")) * (
            anchor_datetime.hour / 24.0
        )
    if (
        _to_float(derived.get("sleepDurationLastNightHrs")) is not None
        and _to_float(derived.get("stepsLast3h")) is not None
    ):
        derived["lowSleepHighActivityFlag"] = (
            _to_float(derived.get("sleepDurationLastNightHrs")) < 6.0
            and _to_float(derived.get("stepsLast3h")) > 500
        )
    if _to_float(derived.get("azmToday")) is not None:
        derived["overexertionFlag"] = _to_float(derived.get("azmToday")) > 120
    if _to_float(derived.get("hrZNow")) is not None:
        derived["stressSpikeFlag"] = _to_float(derived.get("hrZNow")) > 1.5
    if _to_float(derived.get("stepsLast60m")) is not None:
        if anchor_datetime.hour >= 20:
            derived["eveningRestlessnessScore"] = _to_float(derived.get("stepsLast60m")) / 200.0
        if anchor_datetime.hour <= 11 and _to_float(derived.get("stepsLast60m")) is not None:
            derived["morningLethargyScore"] = max(
                0.0, 1.0 - (_to_float(derived.get("stepsLast60m")) / 200.0)
            )
    derived["doomscrollingScore"] = _to_float(client_features.get("doomscrollingScore"))
    derived["daylightNowFlag"] = _to_bool(client_features.get("daylightNowFlag"))
    derived["daylightMinsRemaining"] = _to_float(client_features.get("daylightMinsRemaining"))

    location_cluster = client_features.get("locationClusterKey")
    if isinstance(location_cluster, str) and location_cluster.strip():
        normalized_cluster = location_cluster.strip()
        derived["locationClusterKey"] = normalized_cluster
        derived[f"locationClusterOneHot_{normalized_cluster}"] = 1
    derived["commuteFlag"] = _to_bool(client_features.get("commuteFlag"))

    weather_payload = _blob_payload(weather_blob)
    if _is_missing_blob(weather_blob):
        _add_note(notes, "missing_weather")
    else:
        current_weather = (
            weather_payload.get("current")
            if isinstance(weather_payload.get("current"), Mapping)
            else {}
        )
        derived["weatherTempF"] = _c_to_f(_to_float(current_weather.get("temperature_2m")))
        derived["weatherFeelsLikeF"] = _c_to_f(
            _to_float(current_weather.get("apparent_temperature"))
        )
        derived["weatherPrecipMm"] = _to_float(current_weather.get("precipitation"))
        if (
            derived["weatherTempF"] is None
            and derived["weatherFeelsLikeF"] is None
            and derived["weatherPrecipMm"] is None
        ):
            _add_note(notes, "partial_weather")

    air_quality_payload = _blob_payload(air_quality_blob)
    if _is_missing_blob(air_quality_blob):
        _add_note(notes, "missing_air_quality")
    else:
        current_aq = (
            air_quality_payload.get("current")
            if isinstance(air_quality_payload.get("current"), Mapping)
            else {}
        )
        derived["outdoorAQI"] = _to_float(current_aq.get("us_aqi"))
        if derived["outdoorAQI"] is None:
            _add_note(notes, "partial_air_quality")

    steps_7d_values = _extract_steps_7d_values(blob=steps_7d_blob)
    if steps_7d_values and _to_float(derived.get("stepsLast3h")) is not None:
        steps_today = _to_float(activity_summary.get("steps"))
        if steps_today is None:
            steps_today = _to_float(derived.get("stepsLast3h"))
        mean_7d = statistics.mean(steps_7d_values)
        std_7d = _stddev(steps_7d_values)
        if steps_today is not None and std_7d not in (None, 0):
            derived["stepsZToday"] = (steps_today - mean_7d) / std_7d
    else:
        _add_note(notes, "missing_steps_7d")

    derived["activityInertia"] = _to_float(derived.get("stepsSlopeLast60m"))

    if (
        _to_float(derived.get("sleepEfficiency")) is not None
        and _to_float(derived.get("hrvRmssdDeviationFrom7d")) is not None
    ):
        derived["recoveryIndex"] = (_to_float(derived.get("sleepEfficiency")) / 100.0) + (
            _to_float(derived.get("hrvRmssdDeviationFrom7d")) / 10.0
        )

    return derived


def _legacy_or_derived_sleep_section(
    *, raw_fitbit_data: dict[str, Any], sleep_blob: dict[str, Any] | None
) -> dict[str, Any]:
    legacy = _legacy_section(raw_fitbit_data=raw_fitbit_data, key="sleep")
    if legacy is not None:
        return legacy

    payload = _blob_payload(sleep_blob)
    entries = payload.get("sleep")
    if not isinstance(entries, list) or not entries:
        return {}

    primary = None
    for entry in entries:
        if isinstance(entry, Mapping) and bool(entry.get("isMainSleep")):
            primary = entry
            break
    if primary is None and isinstance(entries[0], Mapping):
        primary = entries[0]
    if not isinstance(primary, Mapping):
        return {}

    levels_summary = _get_nested(primary, "levels", "summary")
    return {
        "total_sleep_minutes": _to_int(primary.get("minutesAsleep")),
        "deep_sleep_minutes": _to_int(_get_nested(levels_summary, "deep", "minutes")),
        "sleep_efficiency_pct": _to_float(primary.get("efficiency")),
    }


def _legacy_or_derived_steps_section(
    *, raw_fitbit_data: dict[str, Any], activity_features: dict[str, int | float | None]
) -> dict[str, Any]:
    legacy = _legacy_section(raw_fitbit_data=raw_fitbit_data, key="steps")
    if legacy is not None:
        return legacy
    return {"count": _to_int(activity_features.get("steps_count"))}


def _legacy_or_derived_exercise_section(
    *,
    raw_fitbit_data: dict[str, Any],
    activity_blob: dict[str, Any] | None,
    activity_features: dict[str, int | float | None],
) -> dict[str, Any]:
    legacy = _legacy_section(raw_fitbit_data=raw_fitbit_data, key="exercise")
    if legacy is not None:
        return legacy

    payload = _blob_payload(activity_blob)
    summary = payload.get("summary") if isinstance(payload.get("summary"), Mapping) else {}
    activities = payload.get("activities")
    workout_count = len(activities) if isinstance(activities, list) else None
    vigorous = _to_int(summary.get("veryActiveMinutes"))
    active_zone_minutes = _to_int(activity_features.get("active_zone_minutes"))
    return {
        "active_minutes": active_zone_minutes,
        "workout_count": workout_count,
        "vigorous_minutes": vigorous,
    }


def _legacy_or_derived_heart_rate_section(
    *, raw_fitbit_data: dict[str, Any], heart_blob: dict[str, Any] | None
) -> dict[str, Any]:
    legacy = _legacy_section(raw_fitbit_data=raw_fitbit_data, key="heart_rate")
    if legacy is not None:
        return legacy

    payload = _blob_payload(heart_blob)
    dataset = _get_nested(payload, "activities-heart-intraday", "dataset")
    values: list[int] = []
    if isinstance(dataset, list):
        for point in dataset:
            if isinstance(point, Mapping):
                bpm = _to_int(point.get("value"))
                if bpm is not None:
                    values.append(bpm)
    if not values:
        return {"avg_bpm": None, "min_bpm": None, "max_bpm": None}
    return {
        "avg_bpm": int(sum(values) / len(values)),
        "min_bpm": min(values),
        "max_bpm": max(values),
    }


def _legacy_or_derived_resting_heart_rate_section(
    *,
    raw_fitbit_data: dict[str, Any],
    heart_blob: dict[str, Any] | None,
    activity_blob: dict[str, Any] | None,
) -> dict[str, Any]:
    legacy = _legacy_section(raw_fitbit_data=raw_fitbit_data, key="resting_heart_rate")
    if legacy is not None:
        return legacy

    heart_payload = _blob_payload(heart_blob)
    heart_entries = heart_payload.get("activities-heart")
    if isinstance(heart_entries, list):
        for entry in heart_entries:
            if not isinstance(entry, Mapping):
                continue
            value = entry.get("value")
            if isinstance(value, Mapping):
                resting = _to_int(value.get("restingHeartRate"))
                if resting is not None:
                    return {"bpm": resting}

    activity_payload = _blob_payload(activity_blob)
    summary = activity_payload.get("summary")
    if isinstance(summary, Mapping):
        resting = _to_int(summary.get("restingHeartRate"))
        if resting is not None:
            return {"bpm": resting}
    return {"bpm": None}


def _legacy_or_derived_calories_section(
    *,
    raw_fitbit_data: dict[str, Any],
    activity_features: dict[str, int | float | None],
    nutrition_features: dict[str, int | float | None],
) -> dict[str, Any]:
    legacy = _legacy_section(raw_fitbit_data=raw_fitbit_data, key="calories")
    if legacy is not None:
        return legacy

    calories_in = _to_int(nutrition_features.get("calories_in_kcal"))
    calories_out = _to_int(activity_features.get("calories_out_kcal"))
    net = None
    if calories_in is not None and calories_out is not None:
        net = calories_in - calories_out

    return {
        "consumed_kcal": calories_in,
        "burned_kcal": calories_out,
        "net_kcal": net,
    }


def _legacy_section(*, raw_fitbit_data: dict[str, Any], key: str) -> dict[str, Any] | None:
    value = raw_fitbit_data.get(key)
    if not isinstance(value, Mapping):
        return None
    if MISSING_SIGNAL_MARKER in value or "payload" in value:
        return None
    return dict(value)


def _signal_blob(
    *,
    raw_fitbit_data: dict[str, Any],
    signal_keys: tuple[str, ...],
    missing_reason: str,
) -> dict[str, Any]:
    for key in signal_keys:
        candidate = raw_fitbit_data.get(key)
        if isinstance(candidate, Mapping):
            if MISSING_SIGNAL_MARKER in candidate or "payload" in candidate:
                return dict(candidate)
            return _present_blob(dict(candidate))
    return _missing_blob(reason=missing_reason)


def _present_blob(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        MISSING_SIGNAL_MARKER: False,
        "reason": None,
        "raw_status": 200,
        "payload": payload,
    }


def _missing_blob(*, reason: str, raw_status: int | None = None) -> dict[str, Any]:
    return {
        MISSING_SIGNAL_MARKER: True,
        "reason": reason,
        "raw_status": raw_status,
        "payload": {},
    }


def _is_missing_blob(blob: dict[str, Any] | None) -> bool:
    if not isinstance(blob, Mapping):
        return True
    return bool(blob.get(MISSING_SIGNAL_MARKER, False))


def _blob_payload(blob: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(blob, Mapping):
        return {}
    payload = blob.get("payload")
    if isinstance(payload, Mapping):
        return dict(payload)
    return {}


def _blob_reason(blob: dict[str, Any] | None) -> str | None:
    if not isinstance(blob, Mapping):
        return None
    reason = blob.get("reason")
    if isinstance(reason, str):
        normalized = reason.strip()
        return normalized or None
    return None


def _extract_first_nested_dict(
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


def _get_nested(source: Any, *keys: str) -> Any:
    current = source
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    parsed = _to_float(value)
    if parsed is None:
        return None
    return int(parsed)


def _filtered_client_features(client_features: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(client_features, dict):
        return {}
    filtered: dict[str, Any] = {}
    for key, value in client_features.items():
        if key in {"lat", "lon", "anchorMs"}:
            continue
        filtered[key] = value
    return filtered


def _default_derived_features() -> dict[str, Any]:
    keys = [
        # Steps/activity
        "stepsLast5m",
        "stepsLast15m",
        "stepsLast30m",
        "stepsLast60m",
        "stepsLast3h",
        "stepBurst5m",
        "zeroStreakMax60m",
        "stepsSlopeLast60m",
        "stepsAccel5to15m",
        "sedentaryMinsLast3h",
        "azmToday",
        "caloriesOutToday",
        "restingHR",
        "hourOfDay",
        "dayOfWeek",
        "isWeekend",
        "caloriesOutLast3h",
        # AZM
        "azmLast30m",
        "azmLast60m",
        "azmFatBurnLast30m",
        "azmCardioLast30m",
        "azmPeakLast30m",
        "azmFatBurnMinutes",
        "azmCardioMinutes",
        "azmPeakMinutes",
        "azmIntensityMinutes30m",
        "azmIntensityMinutes60m",
        "azmZeroStreakMax60m",
        "azmSlopeLast60m",
        "azmSpike30m",
        # Heart
        "hrNow",
        "hrAvgLast5m",
        "hrAvgLast15m",
        "hrAvgLast60m",
        "hrMinLast15m",
        "hrMaxLast15m",
        "hrDelta5m",
        "hrDelta15m",
        "hrSlopeLast30m",
        "hrStdLast30m",
        "hrStdLast60m",
        "hrSlopeLast60m",
        "rhrMean7d",
        "rhrStd7d",
        "hrZNow",
        "hrZLast15m",
        "restingHR7dTrend",
        # Sleep/recovery
        "sleepDurationLastNightHrs",
        "sleepEfficiency",
        "wasoMinutes",
        "remRatio",
        "deepRatio",
        "bedtimeStdDev7d",
        "sleepOnsetLocalHour",
        "wakeTimeLocalHour",
        "sleepFragmentationScore",
        "sleepDebtHrs",
        "recoveryIndex",
        # HRV
        "hrvRmssdDaily",
        "hrvDeepRmssdDaily",
        "hrvRmssd7dAvg",
        "hrvRmssdDeviationFrom7d",
        "hrvIntradayRmssdMean",
        "hrvIntradayRmssdStdDev",
        "hrvIntradayLfMean",
        "hrvIntradayHfMean",
        "hrvIntradayLfHfRatioMean",
        "hrvIntradayCoverageMean",
        # Breathing
        "brFullNight",
        "brDeepSleep",
        "brRemSleep",
        "brLightSleep",
        "brFullNight7dAvg",
        "brFullNightDeviationFrom7d",
        # SpO2/temp
        "spo2Avg",
        "spo2Min",
        "spo2Max",
        "spo2Range",
        "spo2Avg7dAvg",
        "spo2AvgDeviationFrom7d",
        "tempSkinNightlyRelative",
        "tempSkinNightlyRelative7dAvg",
        "tempSkinNightlyRelativeDeviationFrom7d",
        # Exercise
        "timeSinceLastExerciseMin",
        "postExerciseWindow90m",
        "lastExerciseType",
        "lastExerciseStartTime",
        "lastExerciseDurationMinutes",
        "lastExerciseSteps",
        "lastExerciseCalories",
        "lastExerciseAvgHr",
        "lastExerciseAzmTotal",
        "lastExerciseAzmFatBurn",
        "lastExerciseAzmCardio",
        "lastExerciseAzmPeak",
        # Nutrition
        "totalCaloriesIntake",
        "snackCaloriesFraction",
        "caloriesFromMeals",
        "caloriesFromSnacks",
        "totalCarbsGrams",
        "totalFatGrams",
        "totalFiberGrams",
        "totalProteinGrams",
        "totalSodiumMg",
        "totalWaterMl",
        "mealsLoggedCount",
        "caloriesPerMealAvg",
        # Composite/context
        "acuteArousalIndex",
        "recentActivityXTimeOfDay",
        "lowSleepHighActivityFlag",
        "overexertionFlag",
        "stressSpikeFlag",
        "eveningRestlessnessScore",
        "morningLethargyScore",
        "doomscrollingScore",
        "daylightNowFlag",
        "daylightMinsRemaining",
        "locationClusterKey",
        "commuteFlag",
        "weatherTempF",
        "weatherFeelsLikeF",
        "weatherPrecipMm",
        "outdoorAQI",
        "stepsZToday",
        "activityInertia",
    ]
    return {key: None for key in keys}


def _extract_intraday_series(
    *,
    blob: dict[str, Any] | None,
    dataset_key: str,
    value_key: str,
) -> list[float]:
    payload = _blob_payload(blob)
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
        value = point.get(value_key)
        numeric_value = _to_float(value)
        if numeric_value is not None:
            series.append(numeric_value)
    return series


def _window_sum(values: list[float], window: int) -> float | None:
    if not values:
        return None
    start_index = max(0, len(values) - max(1, window))
    return float(sum(values[start_index:]))


def _window_avg(values: list[float], window: int) -> float | None:
    if not values:
        return None
    slice_values = values[max(0, len(values) - max(1, window)) :]
    if not slice_values:
        return None
    return float(sum(slice_values) / len(slice_values))


def _window_min(values: list[float], window: int) -> float | None:
    if not values:
        return None
    slice_values = values[max(0, len(values) - max(1, window)) :]
    if not slice_values:
        return None
    return float(min(slice_values))


def _window_max(values: list[float], window: int) -> float | None:
    if not values:
        return None
    slice_values = values[max(0, len(values) - max(1, window)) :]
    if not slice_values:
        return None
    return float(max(slice_values))


def _rolling_max_sum(values: list[float], window: int) -> float | None:
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


def _zero_streak_max(values: list[float], window: int) -> int | None:
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


def _zero_count(values: list[float], window: int) -> int | None:
    if not values:
        return None
    slice_values = values[max(0, len(values) - max(1, window)) :]
    return sum(1 for value in slice_values if value == 0)


def _slope(values: list[float]) -> float | None:
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


def _stddev(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    try:
        return float(statistics.pstdev(values))
    except statistics.StatisticsError:
        return None


def _last_value(values: list[float]) -> float | None:
    if not values:
        return None
    return float(values[-1])


def _sum_non_null(values: list[float | int | None]) -> float | int | None:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    if all(isinstance(value, int) for value in numeric_values):
        return int(sum(numeric_values))
    return float(sum(float(value) for value in numeric_values))


def _extract_resting_heart_rate(
    *,
    activity_blob: dict[str, Any] | None,
    heart_blob: dict[str, Any] | None,
) -> int | None:
    heart_payload = _blob_payload(heart_blob)
    activities_heart = heart_payload.get("activities-heart")
    if isinstance(activities_heart, list):
        for entry in activities_heart:
            if not isinstance(entry, Mapping):
                continue
            value = entry.get("value")
            if not isinstance(value, Mapping):
                continue
            resting = _to_int(value.get("restingHeartRate"))
            if resting is not None:
                return resting

    activity_payload = _blob_payload(activity_blob)
    summary = activity_payload.get("summary")
    if isinstance(summary, Mapping):
        return _to_int(summary.get("restingHeartRate"))
    return None


def _extract_azm_series(
    *,
    blob: dict[str, Any] | None,
) -> tuple[list[float], list[float], list[float], list[float]]:
    payload = _blob_payload(blob)
    candidate_keys = (
        "activities-active-zone-minutes-intraday",
        "activities-active-zone-minutes",
        "activities-azm-intraday",
    )
    dataset: list[Any] | None = None
    for key in candidate_keys:
        parent = payload.get(key)
        if isinstance(parent, Mapping) and isinstance(parent.get("dataset"), list):
            dataset = parent.get("dataset")
            break
    if dataset is None:
        return [], [], [], []

    total: list[float] = []
    fat: list[float] = []
    cardio: list[float] = []
    peak: list[float] = []
    for point in dataset:
        if not isinstance(point, Mapping):
            continue
        value = point.get("value")
        if isinstance(value, Mapping):
            total_value = _to_float(
                value.get("activeZoneMinutes") or value.get("value") or value.get("minutes")
            )
            fat_value = _to_float(value.get("fatBurnActiveZoneMinutes") or value.get("fatBurn"))
            cardio_value = _to_float(value.get("cardioActiveZoneMinutes") or value.get("cardio"))
            peak_value = _to_float(value.get("peakActiveZoneMinutes") or value.get("peak"))
        else:
            total_value = _to_float(value)
            fat_value = None
            cardio_value = None
            peak_value = None

        total.append(total_value or 0.0)
        fat.append(fat_value or 0.0)
        cardio.append(cardio_value or 0.0)
        peak.append(peak_value or 0.0)
    return total, fat, cardio, peak


def _extract_resting_heart_rate_series(*, heart_7d_blob: dict[str, Any] | None) -> list[float]:
    payload = _blob_payload(heart_7d_blob)
    entries = payload.get("activities-heart")
    if not isinstance(entries, list):
        return []
    values: list[float] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        value = entry.get("value")
        if not isinstance(value, Mapping):
            continue
        resting = _to_float(value.get("restingHeartRate"))
        if resting is not None:
            values.append(resting)
    return values


def _primary_sleep_entry(payload: dict[str, Any]) -> Mapping[str, Any] | None:
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


def _parse_datetime(value: Any) -> datetime | None:
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


def _extract_sleep_entries(*, blob: dict[str, Any] | None) -> list[Mapping[str, Any]]:
    payload = _blob_payload(blob)
    sleep_entries = payload.get("sleep")
    if not isinstance(sleep_entries, list):
        return []
    return [entry for entry in sleep_entries if isinstance(entry, Mapping)]


def _extract_hrv_daily_values(*, blob: dict[str, Any] | None) -> list[float]:
    payload = _blob_payload(blob)
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
        rmssd = _to_float(value.get("dailyRmssd") or value.get("rmssd"))
        if rmssd is not None:
            values.append(rmssd)
    return values


def _extract_hrv_intraday_values(*, blob: dict[str, Any] | None) -> dict[str, list[float]]:
    payload = _blob_payload(blob)
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
                rmssd = _to_float(minute_value.get("rmssd"))
                if rmssd is not None:
                    rmssd_values.append(rmssd)
                lf = _to_float(minute_value.get("lf"))
                if lf is not None:
                    lf_values.append(lf)
                hf = _to_float(minute_value.get("hf"))
                if hf is not None:
                    hf_values.append(hf)
                if lf is not None and hf not in (None, 0):
                    lf_hf_ratio_values.append(lf / hf)
                coverage = _to_float(minute_value.get("coverage"))
                if coverage is not None:
                    coverage_values.append(coverage)
    return {
        "rmssd": rmssd_values,
        "lf": lf_values,
        "hf": hf_values,
        "lf_hf_ratio": lf_hf_ratio_values,
        "coverage": coverage_values,
    }


def _extract_breathing_metrics(
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
    payload = _blob_payload(blob)
    value = _extract_first_nested_dict(payload=payload, list_key="br", value_key="value")
    if not value:
        value = payload
    output["brFullNight"] = _to_float(
        value.get("breathingRate")
        or value.get("sleepingBreathingRate")
        or _get_nested(value, "fullSleepSummary", "breathingRate")
    )
    output["brDeepSleep"] = _to_float(_get_nested(value, "deepSleepSummary", "breathingRate"))
    output["brRemSleep"] = _to_float(_get_nested(value, "remSleepSummary", "breathingRate"))
    output["brLightSleep"] = _to_float(_get_nested(value, "lightSleepSummary", "breathingRate"))

    if output["brFullNight"] is None:
        all_payload = _blob_payload(all_blob)
        all_value = _extract_first_nested_dict(
            payload=all_payload,
            list_key="br",
            value_key="value",
        )
        if all_value:
            output["brFullNight"] = _to_float(
                all_value.get("breathingRate") or all_value.get("sleepingBreathingRate")
            )
    return output


def _extract_breathing_range_values(*, blob: dict[str, Any] | None) -> list[float]:
    payload = _blob_payload(blob)
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
        br = _to_float(value.get("breathingRate") or value.get("sleepingBreathingRate"))
        if br is not None:
            values.append(br)
    return values


def _extract_spo2_range_values(*, blob: dict[str, Any] | None) -> list[float]:
    payload = _blob_payload(blob)
    entries = payload.get("spo2")
    if not isinstance(entries, list):
        return []
    values: list[float] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        value = entry.get("value")
        if not isinstance(value, Mapping):
            continue
        avg = _to_float(value.get("avg") or value.get("average"))
        if avg is not None:
            values.append(avg)
    return values


def _extract_temp_range_values(*, blob: dict[str, Any] | None) -> list[float]:
    payload = _blob_payload(blob)
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
        nightly = _to_float(
            value.get("nightlyRelative")
            or value.get("temperatureVariation")
            or value.get("skinTempDeviation")
        )
        if nightly is not None:
            values.append(nightly)
    return values


def _extract_latest_exercise_metrics(
    *,
    blob: dict[str, Any] | None,
    anchor_datetime: datetime,
) -> dict[str, Any]:
    output = {
        "timeSinceLastExerciseMin": None,
        "postExerciseWindow90m": None,
        "lastExerciseType": None,
        "lastExerciseStartTime": None,
        "lastExerciseDurationMinutes": None,
        "lastExerciseSteps": None,
        "lastExerciseCalories": None,
        "lastExerciseAvgHr": None,
        "lastExerciseAzmTotal": None,
        "lastExerciseAzmFatBurn": None,
        "lastExerciseAzmCardio": None,
        "lastExerciseAzmPeak": None,
    }
    payload = _blob_payload(blob)
    activities = payload.get("activities")
    if not isinstance(activities, list) or not activities:
        return output
    latest = next((entry for entry in activities if isinstance(entry, Mapping)), None)
    if latest is None:
        return output

    output["lastExerciseType"] = latest.get("activityName") or latest.get("name")
    output["lastExerciseStartTime"] = latest.get("startTime")

    duration_ms = _to_float(latest.get("duration"))
    if duration_ms is not None:
        output["lastExerciseDurationMinutes"] = duration_ms / 60000.0
    output["lastExerciseSteps"] = _to_float(latest.get("steps"))
    output["lastExerciseCalories"] = _to_float(latest.get("calories"))

    active_zone = latest.get("activeZoneMinutes")
    if isinstance(active_zone, Mapping):
        output["lastExerciseAzmTotal"] = _to_float(active_zone.get("total"))
        output["lastExerciseAzmFatBurn"] = _to_float(active_zone.get("fatBurn"))
        output["lastExerciseAzmCardio"] = _to_float(active_zone.get("cardio"))
        output["lastExerciseAzmPeak"] = _to_float(active_zone.get("peak"))

    heart_rate_zones = latest.get("heartRateZones")
    if isinstance(heart_rate_zones, list):
        weighted_sum = 0.0
        weighted_minutes = 0.0
        for zone in heart_rate_zones:
            if not isinstance(zone, Mapping):
                continue
            minutes = _to_float(zone.get("minutes"))
            max_hr = _to_float(zone.get("max"))
            min_hr = _to_float(zone.get("min"))
            if minutes is None or minutes <= 0:
                continue
            if max_hr is None or min_hr is None:
                continue
            avg_zone = (max_hr + min_hr) / 2.0
            weighted_sum += avg_zone * minutes
            weighted_minutes += minutes
        if weighted_minutes > 0:
            output["lastExerciseAvgHr"] = weighted_sum / weighted_minutes

    parsed_start = _parse_datetime(latest.get("startTime"))
    if parsed_start is not None:
        delta = anchor_datetime - parsed_start.astimezone(anchor_datetime.tzinfo or UTC)
        output["timeSinceLastExerciseMin"] = max(0.0, delta.total_seconds() / 60.0)
        output["postExerciseWindow90m"] = output["timeSinceLastExerciseMin"] <= 90.0
    return output


def _extract_nutrition_metrics(
    *,
    nutrition_blob: dict[str, Any] | None,
    water_blob: dict[str, Any] | None,
) -> dict[str, Any]:
    output = {
        "totalCaloriesIntake": None,
        "snackCaloriesFraction": None,
        "caloriesFromMeals": None,
        "caloriesFromSnacks": None,
        "totalCarbsGrams": None,
        "totalFatGrams": None,
        "totalFiberGrams": None,
        "totalProteinGrams": None,
        "totalSodiumMg": None,
        "totalWaterMl": None,
        "mealsLoggedCount": None,
        "caloriesPerMealAvg": None,
    }
    nutrition_payload = _blob_payload(nutrition_blob)
    summary = nutrition_payload.get("summary")
    if isinstance(summary, Mapping):
        output["totalCaloriesIntake"] = _to_float(summary.get("calories"))
        output["totalCarbsGrams"] = _to_float(summary.get("carbs"))
        output["totalFatGrams"] = _to_float(summary.get("fat"))
        output["totalFiberGrams"] = _to_float(summary.get("fiber"))
        output["totalProteinGrams"] = _to_float(summary.get("protein"))
        output["totalSodiumMg"] = _to_float(summary.get("sodium"))

    foods = nutrition_payload.get("foods")
    if isinstance(foods, list):
        meal_count = 0
        meal_calories = 0.0
        snack_calories = 0.0
        for food in foods:
            if not isinstance(food, Mapping):
                continue
            calories = _to_float(food.get("calories"))
            if calories is None:
                continue
            meal_type = food.get("mealTypeId")
            if meal_type in (4, "4"):
                snack_calories += calories
            else:
                meal_calories += calories
            meal_count += 1
        if meal_count > 0:
            output["mealsLoggedCount"] = meal_count
            output["caloriesPerMealAvg"] = (meal_calories + snack_calories) / meal_count
            output["caloriesFromMeals"] = meal_calories
            output["caloriesFromSnacks"] = snack_calories
            total = meal_calories + snack_calories
            if total > 0:
                output["snackCaloriesFraction"] = snack_calories / total

    water_payload = _blob_payload(water_blob)
    water_summary = water_payload.get("summary")
    if isinstance(water_summary, Mapping):
        output["totalWaterMl"] = _to_float(water_summary.get("water"))
    return output


def _acute_arousal_index(*, hr_z_now: float | None, sleep_debt_hours: float | None) -> float | None:
    if hr_z_now is None and sleep_debt_hours is None:
        return None
    return (hr_z_now or 0.0) + ((sleep_debt_hours or 0.0) / 2.0)


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _c_to_f(value_c: float | None) -> float | None:
    if value_c is None:
        return None
    return (value_c * 9.0 / 5.0) + 32.0


def _extract_steps_7d_values(*, blob: dict[str, Any] | None) -> list[float]:
    payload = _blob_payload(blob)
    entries = payload.get("activities-steps")
    if not isinstance(entries, list):
        return []
    values: list[float] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        value = _to_float(entry.get("value"))
        if value is not None:
            values.append(value)
    return values


def _add_note(notes: list[str], note: str) -> None:
    if note not in notes:
        notes.append(note)
