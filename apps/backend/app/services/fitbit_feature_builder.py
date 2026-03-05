from __future__ import annotations

import statistics
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from app.services.features import (
    FEATURE_REGISTRY,
    compute_acute_arousal_index,
    compute_doomscrolling_score,
    compute_evening_restlessness_score,
    compute_low_sleep_high_activity_flag,
    compute_morning_lethargy_score,
    compute_overexertion_flag,
    compute_recent_activity_x_time_of_day,
    compute_stress_spike_flag,
    derive_azm_intraday_metrics,
    derive_breathing_metrics,
    derive_calories_intraday_metrics,
    derive_hrv_metrics,
    derive_sleep_metrics,
    derive_spo2_metrics,
    derive_steps_intraday_metrics,
    derive_steps_z_today,
    derive_temp_metrics,
    enrich_context_features,
)
from app.services.features import (
    canonical_hrv_coverage as canonical_hrv_coverage_feature,
)
from app.services.features import (
    compute_day_hr_stats as compute_day_hr_stats_feature,
)
from app.services.features import (
    extract_nutrition_metrics as extract_nutrition_metrics_feature,
)
from app.services.features import (
    extract_resting_heart_rate as extract_resting_heart_rate_feature,
)
from app.services.features import (
    extract_resting_heart_rate_series as extract_resting_heart_rate_series_feature,
)
from app.services.features import (
    features_from_activity as features_from_activity_feature,
)
from app.services.features import (
    features_from_breathing_rate as features_from_breathing_rate_feature,
)
from app.services.features import (
    features_from_hrv as features_from_hrv_feature,
)
from app.services.features import (
    features_from_nutrition as features_from_nutrition_feature,
)
from app.services.features import (
    features_from_spo2 as features_from_spo2_feature,
)
from app.services.features import (
    features_from_temp as features_from_temp_feature,
)
from app.services.features import (
    features_from_water as features_from_water_feature,
)

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
    raw_client_features = dict(client_features or {}) if isinstance(client_features, dict) else {}
    source_timezone = _extract_source_timezone(
        client_features=raw_client_features,
        anchor_datetime=anchor,
    )
    enriched_context_features, context_notes = enrich_context_features(
        client_features=raw_client_features,
        anchor_datetime=anchor,
        source_timezone=source_timezone,
    )
    for context_note in context_notes:
        _add_note(notes, context_note)
    passthrough_client_features = _filtered_client_features(enriched_context_features)

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
    hrv_features = features_from_hrv(blob=hrv_blob, notes=notes)
    derived_features = build_derived_features(
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
    )
    hrv_features["coverage"] = _canonical_hrv_coverage(
        hrv_features=hrv_features,
        derived_features=derived_features,
    )

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
            heart_intraday_blob=heart_intraday_blob,
            notes=notes,
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
        "hrv": hrv_features,
        "breathing_rate": features_from_breathing_rate(blob=breathing_rate_blob, notes=notes),
        "spo2": features_from_spo2(blob=spo2_blob, notes=notes),
        "temp": features_from_temp(blob=temp_blob, notes=notes),
        "nutrition": nutrition_features,
        "water": water_features,
        "derived": derived_features,
        "clientFeatures": passthrough_client_features,
        "notes": notes,
    }
    FEATURE_REGISTRY.append_missing_notes(payload=payload, notes=notes)
    return payload


def features_from_activity(*, blob: dict[str, Any] | None) -> dict[str, int | float | None]:
    return features_from_activity_feature(blob=blob)


def features_from_hrv(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, float | None]:
    return features_from_hrv_feature(blob=blob, notes=notes)


def features_from_breathing_rate(
    *, blob: dict[str, Any] | None, notes: list[str]
) -> dict[str, float | None]:
    return features_from_breathing_rate_feature(blob=blob, notes=notes)


def features_from_spo2(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, float | None]:
    return features_from_spo2_feature(blob=blob, notes=notes)


def features_from_temp(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, float | None]:
    return features_from_temp_feature(blob=blob, notes=notes)


def features_from_nutrition(
    *, blob: dict[str, Any] | None, notes: list[str]
) -> dict[str, int | float | None]:
    return features_from_nutrition_feature(blob=blob, notes=notes)


def features_from_water(*, blob: dict[str, Any] | None, notes: list[str]) -> dict[str, int | None]:
    return features_from_water_feature(blob=blob, notes=notes)


def _canonical_hrv_coverage(
    *,
    hrv_features: dict[str, float | None],
    derived_features: dict[str, Any],
) -> float | None:
    return canonical_hrv_coverage_feature(
        hrv_features=hrv_features,
        derived_features=derived_features,
    )


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
    derived["dayOfWeek"] = (anchor_datetime.weekday() + 1) % 7
    derived["isWeekend"] = derived["dayOfWeek"] in {0, 6}

    derived.update(
        derive_steps_intraday_metrics(
            steps_intraday_blob=steps_intraday_blob,
            notes=notes,
        )
    )
    derived.update(
        derive_calories_intraday_metrics(
            calories_intraday_blob=calories_intraday_blob,
            notes=notes,
        )
    )

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
    derived["restingHR"] = extract_resting_heart_rate_feature(
        activity_blob=activity_blob,
        heart_blob=heart_blob,
    )
    derived.update(
        derive_azm_intraday_metrics(
            azm_intraday_blob=azm_intraday_blob,
            notes=notes,
        )
    )

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

    rhr_series = extract_resting_heart_rate_series_feature(heart_7d_blob=heart_7d_blob)
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

    derived.update(
        derive_sleep_metrics(
            sleep_blob=sleep_blob,
            sleep_range_blob=sleep_range_blob,
            notes=notes,
        )
    )

    derived.update(
        derive_hrv_metrics(
            hrv_blob=hrv_blob,
            hrv_range_blob=hrv_range_blob,
            hrv_all_blob=hrv_all_blob,
            notes=notes,
        )
    )

    derived.update(
        derive_breathing_metrics(
            breathing_rate_blob=breathing_rate_blob,
            breathing_rate_all_blob=breathing_rate_all_blob,
            breathing_rate_range_blob=breathing_rate_range_blob,
            notes=notes,
        )
    )

    derived.update(
        derive_spo2_metrics(
            spo2_blob=spo2_blob,
            spo2_range_blob=spo2_range_blob,
            notes=notes,
        )
    )

    derived.update(
        derive_temp_metrics(
            temp_blob=temp_blob,
            temp_range_blob=temp_range_blob,
            notes=notes,
        )
    )

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

    nutrition = extract_nutrition_metrics_feature(
        nutrition_blob=nutrition_blob,
        water_blob=water_blob,
    )
    derived.update(nutrition)

    derived["acuteArousalIndex"] = compute_acute_arousal_index(
        hr_delta_5m=_to_float(derived.get("hrDelta5m")),
        hr_slope_last_30m=_to_float(derived.get("hrSlopeLast30m")),
        hr_z_now=_to_float(derived.get("hrZNow")),
        step_burst_5m=_to_float(derived.get("stepBurst5m")),
        steps_last_15m=_to_float(derived.get("stepsLast15m")),
        zero_streak_max_60m=_to_float(derived.get("zeroStreakMax60m")),
        azm_spike_30m=_to_float(derived.get("azmSpike30m")),
        post_exercise_window_90m=_to_bool(derived.get("postExerciseWindow90m")),
        sleep_duration_last_night_hrs=_to_float(derived.get("sleepDurationLastNightHrs")),
    )
    derived["recentActivityXTimeOfDay"] = compute_recent_activity_x_time_of_day(
        hour_of_day=_to_int(derived.get("hourOfDay")),
        is_weekend=_to_bool(derived.get("isWeekend")),
        steps_last_30m=_to_float(derived.get("stepsLast30m")),
        steps_last_60m=_to_float(derived.get("stepsLast60m")),
        azm_last_30m=_to_float(derived.get("azmLast30m")),
        azm_last_60m=_to_float(derived.get("azmLast60m")),
        zero_streak_max_60m=_to_float(derived.get("zeroStreakMax60m")),
        steps_z_today=_to_float(derived.get("stepsZToday")),
        post_exercise_window_90m=_to_bool(derived.get("postExerciseWindow90m")),
        hr_z_now=_to_float(derived.get("hrZNow")),
        hr_z_last_15m=_to_float(derived.get("hrZLast15m")),
    )
    hours_since_last_exercise = None
    if _to_float(derived.get("timeSinceLastExerciseMin")) is not None:
        hours_since_last_exercise = _to_float(derived.get("timeSinceLastExerciseMin")) / 60.0
    low_sleep_high_activity_flag = compute_low_sleep_high_activity_flag(
        sleep_duration_last_night_hrs=_to_float(derived.get("sleepDurationLastNightHrs")),
        sleep_debt_hrs=_to_float(derived.get("sleepDebtHrs")),
        steps_z_today=_to_float(derived.get("stepsZToday")),
        azm_today=_to_float(derived.get("azmToday")),
        last_exercise_duration_minutes=_to_float(derived.get("lastExerciseDurationMinutes")),
        hours_since_last_exercise=hours_since_last_exercise,
        hr_z_now=_to_float(derived.get("hrZNow")),
    )
    derived["lowSleepHighActivityFlag"] = low_sleep_high_activity_flag
    derived["overexertionFlag"] = compute_overexertion_flag(
        low_sleep_high_activity_flag=low_sleep_high_activity_flag,
        sleep_duration_last_night_hrs=_to_float(derived.get("sleepDurationLastNightHrs")),
        sleep_debt_hrs=_to_float(derived.get("sleepDebtHrs")),
        azm_today=_to_float(derived.get("azmToday")),
        hours_since_last_exercise=hours_since_last_exercise,
        last_exercise_duration_minutes=_to_float(derived.get("lastExerciseDurationMinutes")),
    )
    derived["stressSpikeFlag"] = compute_stress_spike_flag(
        hr_z_now=_to_float(derived.get("hrZNow")),
        hr_z_last_15m=_to_float(derived.get("hrZLast15m")),
        hr_delta_5m=_to_float(derived.get("hrDelta5m")),
        hr_delta_15m=_to_float(derived.get("hrDelta15m")),
        hr_slope_last_30m=_to_float(derived.get("hrSlopeLast30m")),
        post_exercise_window_90m=_to_bool(derived.get("postExerciseWindow90m")),
    )
    derived["eveningRestlessnessScore"] = compute_evening_restlessness_score(
        hour_of_day=_to_int(derived.get("hourOfDay")),
        steps_last_60m=_to_float(derived.get("stepsLast60m")),
        azm_last_60m=_to_float(derived.get("azmLast60m")),
        azm_last_30m=_to_float(derived.get("azmLast30m")),
        hr_z_now=_to_float(derived.get("hrZNow")),
        hr_z_last_15m=_to_float(derived.get("hrZLast15m")),
    )
    derived["morningLethargyScore"] = compute_morning_lethargy_score(
        hour_of_day=_to_int(derived.get("hourOfDay")),
        steps_last_60m=_to_float(derived.get("stepsLast60m")),
        sleep_debt_hrs=_to_float(derived.get("sleepDebtHrs")),
        hr_z_now=_to_float(derived.get("hrZNow")),
        hr_z_last_15m=_to_float(derived.get("hrZLast15m")),
    )
    derived["doomscrollingScore"] = compute_doomscrolling_score(
        hour_of_day=_to_int(derived.get("hourOfDay")),
        sedentary_mins_last_3h=_to_float(derived.get("sedentaryMinsLast3h")),
        steps_last_30m=_to_float(derived.get("stepsLast30m")),
        steps_last_60m=_to_float(derived.get("stepsLast60m")),
        snack_calories_fraction=_to_float(derived.get("snackCaloriesFraction")),
        client_doomscrolling_score=client_features.get("doomscrollingScore"),
    )
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

    steps_today = _to_float(activity_summary.get("steps"))
    if steps_today is None:
        steps_today = _to_float(derived.get("stepsLast3h"))
    derived.update(
        derive_steps_z_today(
            steps_7d_blob=steps_7d_blob,
            steps_today=steps_today,
            notes=notes,
        )
    )

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
    *,
    raw_fitbit_data: dict[str, Any],
    heart_blob: dict[str, Any] | None,
    heart_intraday_blob: dict[str, Any] | None,
    notes: list[str],
) -> dict[str, Any]:
    legacy = _legacy_section(raw_fitbit_data=raw_fitbit_data, key="heart_rate")
    if legacy is not None:
        return legacy

    # Day-level heart stats should come from the same intraday minute signal used for
    # derived heart features, so top-level and derived payloads stay consistent.
    intraday_values = _extract_intraday_series(
        blob=heart_intraday_blob,
        dataset_key="activities-heart-intraday",
        value_key="value",
    )
    if not intraday_values:
        intraday_values = _extract_intraday_series(
            blob=heart_blob,
            dataset_key="activities-heart-intraday",
            value_key="value",
        )
    if not intraday_values:
        _add_note(notes, "missing_intraday_hr_day_stats")
        return {"avg_bpm": None, "min_bpm": None, "max_bpm": None}
    avg_bpm, min_bpm, max_bpm = compute_day_hr_stats_feature(intraday_values)
    return {
        "avg_bpm": avg_bpm,
        "min_bpm": min_bpm,
        "max_bpm": max_bpm,
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


def _extract_source_timezone(*, client_features: dict[str, Any], anchor_datetime: datetime) -> str:
    for key in ("source_timezone", "timezone", "tz", "timeZone"):
        value = client_features.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    anchor_tz = getattr(anchor_datetime.tzinfo, "key", None)
    if isinstance(anchor_tz, str) and anchor_tz.strip():
        return anchor_tz.strip()
    return "UTC"


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
    output["lastExerciseAvgHr"] = _to_float(
        latest.get("averageHeartRate") or latest.get("averageHR")
    )

    active_zone = latest.get("activeZoneMinutes")
    if isinstance(active_zone, Mapping):
        output["lastExerciseAzmTotal"] = _to_float(
            active_zone.get("totalMinutes") or active_zone.get("total")
        )
        output["lastExerciseAzmFatBurn"] = _to_float(active_zone.get("fatBurn"))
        output["lastExerciseAzmCardio"] = _to_float(active_zone.get("cardio"))
        output["lastExerciseAzmPeak"] = _to_float(active_zone.get("peak"))

        zone_minutes = active_zone.get("minutesInHeartRateZones")
        if isinstance(zone_minutes, list):
            for zone in zone_minutes:
                if not isinstance(zone, Mapping):
                    continue
                zone_name = str(
                    zone.get("type") or zone.get("name") or zone.get("zone") or ""
                ).strip()
                minutes = _to_float(zone.get("minutes"))
                if minutes is None:
                    continue
                normalized_name = zone_name.lower().replace("_", " ").replace("-", " ")
                if "fat" in normalized_name and "burn" in normalized_name:
                    output["lastExerciseAzmFatBurn"] = minutes
                elif "cardio" in normalized_name:
                    output["lastExerciseAzmCardio"] = minutes
                elif "peak" in normalized_name:
                    output["lastExerciseAzmPeak"] = minutes

            if output["lastExerciseAzmTotal"] is None:
                output["lastExerciseAzmTotal"] = _sum_non_null(
                    [
                        output["lastExerciseAzmFatBurn"],
                        output["lastExerciseAzmCardio"],
                        output["lastExerciseAzmPeak"],
                    ]
                )

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
        if weighted_minutes > 0 and output["lastExerciseAvgHr"] is None:
            output["lastExerciseAvgHr"] = weighted_sum / weighted_minutes

    parsed_start = _parse_datetime(latest.get("startTime"))
    if parsed_start is not None:
        delta = anchor_datetime - parsed_start.astimezone(anchor_datetime.tzinfo or UTC)
        output["timeSinceLastExerciseMin"] = max(0.0, delta.total_seconds() / 60.0)
        output["postExerciseWindow90m"] = output["timeSinceLastExerciseMin"] <= 90.0
    return output


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


def _add_note(notes: list[str], note: str) -> None:
    if note not in notes:
        notes.append(note)
