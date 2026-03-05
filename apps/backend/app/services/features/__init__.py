from app.services.features.activity import (
    extract_resting_heart_rate,
    extract_resting_heart_rate_series,
    features_from_activity,
)
from app.services.features.azm import derive_azm_intraday_metrics
from app.services.features.breathing import (
    derive_breathing_metrics,
    features_from_breathing_rate,
)
from app.services.features.composites import (
    compute_acute_arousal_index,
    compute_doomscrolling_score,
    compute_evening_restlessness_score,
    compute_low_sleep_high_activity_flag,
    compute_morning_lethargy_score,
    compute_overexertion_flag,
    compute_recent_activity_x_time_of_day,
    compute_stress_spike_flag,
)
from app.services.features.context_geo_time import enrich_context_features
from app.services.features.heart import compute_day_hr_stats
from app.services.features.hrv import (
    canonical_hrv_coverage,
    derive_hrv_metrics,
    features_from_hrv,
)
from app.services.features.nutrition import (
    extract_nutrition_metrics,
    features_from_nutrition,
    features_from_water,
)
from app.services.features.registry import FEATURE_REGISTRY
from app.services.features.sleep import derive_sleep_metrics
from app.services.features.spo2 import derive_spo2_metrics, features_from_spo2
from app.services.features.steps import (
    derive_calories_intraday_metrics,
    derive_steps_intraday_metrics,
    derive_steps_z_today,
)
from app.services.features.temp import derive_temp_metrics, features_from_temp

__all__ = [
    "FEATURE_REGISTRY",
    "canonical_hrv_coverage",
    "compute_acute_arousal_index",
    "compute_day_hr_stats",
    "compute_doomscrolling_score",
    "compute_evening_restlessness_score",
    "compute_low_sleep_high_activity_flag",
    "compute_morning_lethargy_score",
    "compute_overexertion_flag",
    "compute_recent_activity_x_time_of_day",
    "compute_stress_spike_flag",
    "derive_azm_intraday_metrics",
    "derive_breathing_metrics",
    "derive_calories_intraday_metrics",
    "derive_hrv_metrics",
    "derive_sleep_metrics",
    "derive_spo2_metrics",
    "derive_steps_intraday_metrics",
    "derive_steps_z_today",
    "derive_temp_metrics",
    "enrich_context_features",
    "extract_nutrition_metrics",
    "extract_resting_heart_rate",
    "extract_resting_heart_rate_series",
    "features_from_activity",
    "features_from_breathing_rate",
    "features_from_hrv",
    "features_from_nutrition",
    "features_from_spo2",
    "features_from_temp",
    "features_from_water",
]
