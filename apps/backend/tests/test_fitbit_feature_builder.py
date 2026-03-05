from __future__ import annotations

from datetime import UTC, datetime

from app.services.fitbit_feature_builder import (
    build_feature_payload,
    features_from_breathing_rate,
    features_from_hrv,
    features_from_nutrition,
    features_from_spo2,
    features_from_temp,
    features_from_water,
)


def test_features_from_hrv_missing_adds_missing_note() -> None:
    notes: list[str] = []
    features = features_from_hrv(blob=_missing_blob("not_found"), notes=notes)

    assert features == {"daily_rmssd": None, "deep_rmssd": None, "coverage": None}
    assert notes == ["missing_hrv"]


def test_features_from_hrv_partial_adds_partial_note() -> None:
    notes: list[str] = []
    features = features_from_hrv(
        blob=_present_blob({"hrv": [{"value": {"dailyRmssd": 32.4}}]}),
        notes=notes,
    )

    assert features["daily_rmssd"] == 32.4
    assert features["deep_rmssd"] is None
    assert features["coverage"] is None
    assert notes == ["partial_hrv"]


def test_features_from_breathing_rate_missing_or_partial_add_notes() -> None:
    missing_notes: list[str] = []
    missing_features = features_from_breathing_rate(
        blob=_missing_blob("not_found"),
        notes=missing_notes,
    )
    assert missing_features == {"sleeping_br": None}
    assert missing_notes == ["missing_breathing_rate"]

    partial_notes: list[str] = []
    partial_features = features_from_breathing_rate(
        blob=_present_blob({"br": [{"value": {}}]}),
        notes=partial_notes,
    )
    assert partial_features == {"sleeping_br": None}
    assert partial_notes == ["partial_breathing_rate"]


def test_features_from_breathing_rate_forbidden_adds_forbidden_note() -> None:
    notes: list[str] = []
    features = features_from_breathing_rate(
        blob=_missing_blob("forbidden_scope"),
        notes=notes,
    )

    assert features == {"sleeping_br": None}
    assert notes == ["missing_breathing_rate_forbidden"]


def test_features_from_spo2_missing_or_partial_add_notes() -> None:
    missing_notes: list[str] = []
    missing_features = features_from_spo2(blob=_missing_blob("not_found"), notes=missing_notes)
    assert missing_features == {"avg_spo2": None, "min_spo2": None, "max_spo2": None}
    assert missing_notes == ["missing_spo2"]

    partial_notes: list[str] = []
    partial_features = features_from_spo2(
        blob=_present_blob({"spo2": [{"value": {"avg": 97.3}}]}),
        notes=partial_notes,
    )
    assert partial_features["avg_spo2"] == 97.3
    assert partial_features["min_spo2"] is None
    assert partial_features["max_spo2"] is None
    assert partial_notes == ["partial_spo2"]


def test_features_from_temp_missing_or_partial_add_notes() -> None:
    missing_notes: list[str] = []
    missing_features = features_from_temp(blob=_missing_blob("not_found"), notes=missing_notes)
    assert missing_features == {"skin_temp_deviation_c": None}
    assert missing_notes == ["missing_temp"]

    partial_notes: list[str] = []
    partial_features = features_from_temp(
        blob=_present_blob({"tempSkin": [{"value": {}}]}),
        notes=partial_notes,
    )
    assert partial_features == {"skin_temp_deviation_c": None}
    assert partial_notes == ["partial_temp"]


def test_features_from_nutrition_missing_or_partial_add_notes() -> None:
    missing_notes: list[str] = []
    missing_features = features_from_nutrition(blob=_missing_blob("not_found"), notes=missing_notes)
    assert missing_features == {
        "calories_in_kcal": None,
        "carbs_g": None,
        "fat_g": None,
        "protein_g": None,
    }
    assert missing_notes == ["missing_nutrition"]

    partial_notes: list[str] = []
    partial_features = features_from_nutrition(
        blob=_present_blob({"summary": {"calories": 2200}}),
        notes=partial_notes,
    )
    assert partial_features["calories_in_kcal"] == 2200
    assert partial_features["carbs_g"] is None
    assert partial_features["fat_g"] is None
    assert partial_features["protein_g"] is None
    assert partial_notes == ["partial_nutrition"]


def test_features_from_water_missing_or_partial_add_notes() -> None:
    missing_notes: list[str] = []
    missing_features = features_from_water(blob=_missing_blob("not_found"), notes=missing_notes)
    assert missing_features == {"water_ml": None}
    assert missing_notes == ["missing_water"]

    partial_notes: list[str] = []
    partial_features = features_from_water(
        blob=_present_blob({"summary": {}}),
        notes=partial_notes,
    )
    assert partial_features == {"water_ml": None}
    assert partial_notes == ["partial_water"]


def test_build_feature_payload_contains_new_sections_and_notes() -> None:
    payload = build_feature_payload(
        raw_fitbit_data={
            "activity_summary": _present_blob(
                {
                    "summary": {
                        "steps": 5432,
                        "caloriesOut": 1900,
                        "lightlyActiveMinutes": 50,
                        "fairlyActiveMinutes": 20,
                        "veryActiveMinutes": 10,
                    },
                    "activities": [{"name": "walk"}],
                }
            ),
            "sleep": _present_blob({"sleep": [{"minutesAsleep": 420, "efficiency": 92}]}),
            "heart": _present_blob(
                {
                    "activities-heart": [{"value": {"restingHeartRate": 58}}],
                    "activities-heart-intraday": {"dataset": [{"value": 55}, {"value": 85}]},
                }
            ),
            "hrv": _missing_blob("not_found"),
            "breathing_rate": _present_blob({"br": [{"value": {"breathingRate": 13.8}}]}),
            "spo2": _present_blob({"spo2": [{"value": {"avg": 97.6, "min": 95, "max": 99}}]}),
            "temp": _present_blob({"tempSkin": [{"value": {"nightlyRelative": -0.3}}]}),
            "nutrition": _present_blob({"summary": {"calories": 2100, "carbs": 240}}),
            "water": _present_blob({"summary": {"water": 1800}}),
        }
    )

    assert payload["steps"]["count"] == 5432
    assert payload["activity"]["active_zone_minutes"] == 80
    assert payload["hrv"] == {"daily_rmssd": None, "deep_rmssd": None, "coverage": None}
    assert payload["breathing_rate"]["sleeping_br"] == 13.8
    assert payload["spo2"]["avg_spo2"] == 97.6
    assert payload["temp"]["skin_temp_deviation_c"] == -0.3
    assert payload["nutrition"]["calories_in_kcal"] == 2100
    assert payload["water"]["water_ml"] == 1800
    assert "missing_hrv" in payload["notes"]
    assert "partial_nutrition" in payload["notes"]


def test_build_feature_payload_derives_intraday_metrics_when_available() -> None:
    payload = build_feature_payload(
        raw_fitbit_data={
            "steps_intraday": _present_blob(
                {
                    "activities-steps-intraday": {
                        "dataset": [
                            {"time": "12:00:00", "value": 0},
                            {"time": "12:01:00", "value": 5},
                            {"time": "12:02:00", "value": 7},
                            {"time": "12:03:00", "value": 9},
                            {"time": "12:04:00", "value": 11},
                        ]
                    }
                }
            ),
            "calories_intraday": _present_blob(
                {
                    "activities-calories-intraday": {
                        "dataset": [
                            {"time": "12:00:00", "value": 1.0},
                            {"time": "12:01:00", "value": 1.1},
                            {"time": "12:02:00", "value": 1.2},
                            {"time": "12:03:00", "value": 1.3},
                            {"time": "12:04:00", "value": 1.4},
                        ]
                    }
                }
            ),
            "azm_intraday": _present_blob(
                {
                    "activities-active-zone-minutes-intraday": {
                        "dataset": [
                            {
                                "time": "12:00:00",
                                "value": {
                                    "activeZoneMinutes": 0,
                                    "fatBurnActiveZoneMinutes": 0,
                                    "cardioActiveZoneMinutes": 0,
                                    "peakActiveZoneMinutes": 0,
                                },
                            },
                            {
                                "time": "12:01:00",
                                "value": {
                                    "activeZoneMinutes": 1,
                                    "fatBurnActiveZoneMinutes": 1,
                                    "cardioActiveZoneMinutes": 0,
                                    "peakActiveZoneMinutes": 0,
                                },
                            },
                        ]
                    }
                }
            ),
            "heart_intraday": _present_blob(
                {
                    "activities-heart-intraday": {
                        "dataset": [
                            {"time": "12:00:00", "value": 64},
                            {"time": "12:01:00", "value": 70},
                        ]
                    }
                }
            ),
        },
        anchor_datetime=datetime(2026, 3, 5, 12, 5, tzinfo=UTC),
    )

    derived = payload["derived"]
    assert derived["stepsLast5m"] == 32.0
    assert derived["caloriesOutLast3h"] == 6.0
    assert derived["azmLast30m"] == 1.0
    assert derived["hrNow"] == 70.0
    assert "missing_intraday_steps" not in payload["notes"]
    assert "missing_intraday_calories" not in payload["notes"]
    assert "missing_intraday_azm" not in payload["notes"]
    assert "missing_intraday_heart" not in payload["notes"]


def test_build_feature_payload_derives_intraday_azm_from_minutes_shape() -> None:
    payload = build_feature_payload(
        raw_fitbit_data={
            "azm_intraday": _present_blob(
                {
                    "activities-active-zone-minutes-intraday": [
                        {
                            "dateTime": "2026-03-05",
                            "minutes": [
                                {
                                    "minute": "2026-03-05T12:00:00",
                                    "value": {
                                        "activeZoneMinutes": 0,
                                        "fatBurnActiveZoneMinutes": 0,
                                        "cardioActiveZoneMinutes": 0,
                                        "peakActiveZoneMinutes": 0,
                                    },
                                },
                                {
                                    "minute": "2026-03-05T12:01:00",
                                    "value": {
                                        "activeZoneMinutes": 2,
                                        "fatBurnActiveZoneMinutes": 1,
                                        "cardioActiveZoneMinutes": 1,
                                        "peakActiveZoneMinutes": 0,
                                    },
                                },
                            ],
                        }
                    ]
                }
            )
        },
        anchor_datetime=datetime(2026, 3, 5, 12, 5, tzinfo=UTC),
    )

    derived = payload["derived"]
    assert derived["azmLast30m"] == 2.0
    assert derived["azmFatBurnMinutes"] == 1.0
    assert derived["azmCardioMinutes"] == 1.0
    assert "missing_intraday_azm" not in payload["notes"]


def test_build_feature_payload_uses_breathing_all_and_spo2_range() -> None:
    payload = build_feature_payload(
        raw_fitbit_data={
            "breathing_rate": _present_blob({"br": [{"value": {"breathingRate": 10.2}}]}),
            "breathing_rate_all": _present_blob(
                {
                    "br": [
                        {
                            "value": {
                                "deepSleepSummary": {"breathingRate": 10.9},
                                "remSleepSummary": {"breathingRate": 11.3},
                                "lightSleepSummary": {"breathingRate": 9.8},
                            }
                        }
                    ]
                }
            ),
            "breathing_rate_range": _present_blob(
                {
                    "br": [
                        {"value": {"breathingRate": 10.1}},
                        {"value": {"breathingRate": 10.4}},
                    ]
                }
            ),
            "spo2": _present_blob({"spo2": [{"value": {"avg": 96.7, "min": 93.5, "max": 99.8}}]}),
            "spo2_range": _present_blob(
                {
                    "spo2": [
                        {"value": {"avg": 96.0}},
                        {"value": {"avg": 97.0}},
                        {"value": {"avg": 98.0}},
                    ]
                }
            ),
        }
    )

    derived = payload["derived"]
    assert derived["brFullNight"] == 10.2
    assert derived["brDeepSleep"] == 10.9
    assert derived["brRemSleep"] == 11.3
    assert derived["brLightSleep"] == 9.8
    assert derived["spo2Avg"] == 96.7
    assert derived["spo2Avg7dAvg"] == 97.0
    assert round(derived["spo2AvgDeviationFrom7d"], 1) == -0.3


def test_build_feature_payload_extracts_latest_exercise_azm_from_zone_minutes() -> None:
    payload = build_feature_payload(
        raw_fitbit_data={
            "latest_exercise": _present_blob(
                {
                    "activities": [
                        {
                            "activityName": "Run",
                            "startTime": "2026-03-05T11:30:00-05:00",
                            "duration": 1800000,
                            "steps": 3500,
                            "calories": 320,
                            "averageHeartRate": 141,
                            "activeZoneMinutes": {
                                "totalMinutes": 14,
                                "minutesInHeartRateZones": [
                                    {"type": "FAT_BURN", "minutes": 8},
                                    {"type": "CARDIO", "minutes": 4},
                                    {"type": "PEAK", "minutes": 2},
                                ],
                            },
                        }
                    ]
                }
            )
        },
        anchor_datetime=datetime(2026, 3, 5, 12, 0, tzinfo=UTC),
    )

    derived = payload["derived"]
    assert derived["lastExerciseType"] == "Run"
    assert derived["lastExerciseDurationMinutes"] == 30.0
    assert derived["lastExerciseSteps"] == 3500.0
    assert derived["lastExerciseCalories"] == 320.0
    assert derived["lastExerciseAvgHr"] == 141.0
    assert derived["lastExerciseAzmTotal"] == 14.0
    assert derived["lastExerciseAzmFatBurn"] == 8.0
    assert derived["lastExerciseAzmCardio"] == 4.0
    assert derived["lastExerciseAzmPeak"] == 2.0


def _missing_blob(reason: str) -> dict[str, object]:
    return {
        "__missing": True,
        "reason": reason,
        "raw_status": 404,
        "payload": {},
    }


def _present_blob(payload: dict[str, object]) -> dict[str, object]:
    return {
        "__missing": False,
        "reason": None,
        "raw_status": 200,
        "payload": payload,
    }
