from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return None


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _clamp01(value: float) -> float:
    return _clamp(value, 0.0, 1.0)


def compute_acute_arousal_index(
    *,
    hr_delta_5m: float | None,
    hr_slope_last_30m: float | None,
    hr_z_now: float | None,
    step_burst_5m: float | None,
    steps_last_15m: float | None,
    zero_streak_max_60m: float | None,
    azm_spike_30m: float | None,
    post_exercise_window_90m: bool | None,
    sleep_duration_last_night_hrs: float | None,
) -> float | None:
    """Compute immediate sympathetic activation score on a 0..10 scale.

    Inputs are minute-window heart/activity dynamics. Missing values are treated
    as zero-contribution unless all acute drivers are unavailable.
    """
    has_hr_signal = any(v is not None for v in (hr_delta_5m, hr_slope_last_30m, hr_z_now))
    has_movement_signal = any(v is not None for v in (step_burst_5m, steps_last_15m, azm_spike_30m))
    if not has_hr_signal and not has_movement_signal:
        return None

    hr_component = (
        1.2 * (hr_delta_5m or 0.0) + 30.0 * (hr_slope_last_30m or 0.0) + 1.0 * (hr_z_now or 0.0)
    )
    movement_component = (
        0.015 * (steps_last_15m or 0.0)
        + 0.5 * (step_burst_5m or 0.0)
        + 1.0 * (azm_spike_30m or 0.0)
    )

    sedentary_penalty = 0.0
    if zero_streak_max_60m is not None:
        if zero_streak_max_60m >= 45 and (step_burst_5m or 0.0) < 15 and (hr_delta_5m or 0.0) < 5:
            sedentary_penalty = -1.0
        elif zero_streak_max_60m >= 45 and (
            (step_burst_5m or 0.0) > 30 or (hr_delta_5m or 0.0) > 10
        ):
            sedentary_penalty = 1.0

    exercise_suppression = -1.5 if post_exercise_window_90m else 0.0
    sleep_suppression = (
        -0.5
        if (sleep_duration_last_night_hrs is not None and sleep_duration_last_night_hrs < 6)
        else 0.0
    )
    score = (
        hr_component
        + movement_component
        + sedentary_penalty
        + exercise_suppression
        + sleep_suppression
    )
    return _clamp(score, 0.0, 10.0)


def compute_recent_activity_x_time_of_day(
    *,
    hour_of_day: int | None,
    is_weekend: bool | None,
    steps_last_30m: float | None,
    steps_last_60m: float | None,
    azm_last_30m: float | None,
    azm_last_60m: float | None,
    zero_streak_max_60m: float | None,
    steps_z_today: float | None,
    post_exercise_window_90m: bool | None,
    hr_z_now: float | None,
    hr_z_last_15m: float | None,
) -> float | None:
    """Compute activity-context score in [-2,2] using local-time expectations."""
    if hour_of_day is None:
        return None

    steps_30 = steps_last_30m if steps_last_30m is not None else steps_last_60m
    azm_30 = azm_last_30m if azm_last_30m is not None else azm_last_60m
    hr_z = hr_z_last_15m if hr_z_last_15m is not None else hr_z_now
    if steps_30 is None or azm_30 is None or hr_z is None:
        return None

    expected_steps = 300.0
    expected_azm = 2.0
    if hour_of_day < 6:
        expected_steps = 60.0
        expected_azm = 0.2
    elif hour_of_day < 12:
        expected_steps = 400.0
        expected_azm = 3.0
    elif hour_of_day < 17:
        expected_steps = 550.0
        expected_azm = 4.0
    else:
        expected_steps = 350.0
        expected_azm = 2.5

    if is_weekend:
        expected_steps *= 1.25
        expected_azm *= 1.25

    step_dev = (steps_30 - expected_steps) / max(expected_steps, 1.0)
    azm_dev = (azm_30 - expected_azm) / (expected_azm + 0.01)
    hr_component = 0.3 if hr_z > 0.5 else (-0.2 if hr_z < -0.5 else 0.0)

    night_penalty = -1.0 if (hour_of_day < 6 and not post_exercise_window_90m) else 0.0
    sedentary_boost = (
        0.5 if ((zero_streak_max_60m or 0.0) >= 30 and (steps_30 > 400 or azm_30 > 4)) else 0.0
    )
    day_bias = (
        0.3
        if ((steps_z_today or 0.0) > 1.5)
        else (-0.2 if ((steps_z_today or 0.0) < -1.0) else 0.0)
    )
    score = 0.7 * (step_dev + azm_dev) + hr_component + sedentary_boost + day_bias + night_penalty
    return _clamp(score, -2.0, 2.0)


def compute_low_sleep_high_activity_flag(
    *,
    sleep_duration_last_night_hrs: float | None,
    sleep_debt_hrs: float | None,
    steps_z_today: float | None,
    azm_today: float | None,
    last_exercise_duration_minutes: float | None,
    hours_since_last_exercise: float | None,
    hr_z_now: float | None,
) -> bool:
    """Flag probable low-sleep/high-load condition."""
    short_sleep = sleep_duration_last_night_hrs is not None and sleep_duration_last_night_hrs < 6
    sleep_debt = sleep_debt_hrs is not None and sleep_debt_hrs >= 2.0
    high_activity = (azm_today is not None and azm_today >= 60) or (
        steps_z_today is not None and steps_z_today > 1.0
    )
    recent_heavy_exercise = (
        last_exercise_duration_minutes is not None
        and last_exercise_duration_minutes >= 40
        and hours_since_last_exercise is not None
        and hours_since_last_exercise <= 6
    )
    hr_confirm = hr_z_now is not None and hr_z_now > 0.5
    return bool(
        (short_sleep or sleep_debt) and (high_activity or recent_heavy_exercise or hr_confirm)
    )


def compute_overexertion_flag(
    *,
    low_sleep_high_activity_flag: bool | None,
    sleep_duration_last_night_hrs: float | None,
    sleep_debt_hrs: float | None,
    azm_today: float | None,
    hours_since_last_exercise: float | None,
    last_exercise_duration_minutes: float | None,
) -> bool | None:
    """Detect high-load/low-recovery mismatch."""
    if low_sleep_high_activity_flag:
        return True
    has_any_signal = any(
        v is not None
        for v in (
            sleep_duration_last_night_hrs,
            sleep_debt_hrs,
            azm_today,
            hours_since_last_exercise,
            last_exercise_duration_minutes,
        )
    )
    if not has_any_signal:
        return None
    short_sleep = sleep_duration_last_night_hrs is not None and sleep_duration_last_night_hrs < 6
    high_sleep_debt = sleep_debt_hrs is not None and sleep_debt_hrs >= 2
    high_azm = azm_today is not None and azm_today >= 60
    recent_long_exercise = (
        last_exercise_duration_minutes is not None
        and last_exercise_duration_minutes >= 45
        and hours_since_last_exercise is not None
        and hours_since_last_exercise <= 8
    )
    return bool(
        ((short_sleep or high_sleep_debt) and high_azm) or (high_azm and recent_long_exercise)
    )


def compute_stress_spike_flag(
    *,
    hr_z_now: float | None,
    hr_z_last_15m: float | None,
    hr_delta_5m: float | None,
    hr_delta_15m: float | None,
    hr_slope_last_30m: float | None,
    post_exercise_window_90m: bool | None,
) -> bool | None:
    """Detect acute stress-like spikes in HR that are not exercise-recovery effects."""
    z = hr_z_last_15m if hr_z_last_15m is not None else hr_z_now
    if z is None:
        return None
    if post_exercise_window_90m:
        return False
    high_hr = z >= 1.0
    sharp_jump = (
        (hr_delta_5m is not None and hr_delta_5m >= 10)
        or (hr_delta_15m is not None and hr_delta_15m >= 15)
        or (hr_slope_last_30m is not None and hr_slope_last_30m >= 0.3)
    )
    return bool(high_hr and sharp_jump)


def compute_evening_restlessness_score(
    *,
    hour_of_day: int | None,
    steps_last_60m: float | None,
    azm_last_60m: float | None,
    azm_last_30m: float | None,
    hr_z_now: float | None,
    hr_z_last_15m: float | None,
) -> float | None:
    """Compute evening restlessness score on 0..1; returns None outside evening window."""
    if hour_of_day is None or hour_of_day < 20:
        return None
    if hour_of_day > 23:
        return None

    movement = _clamp01((steps_last_60m or 0.0) / 1000.0)
    azm_value = azm_last_60m if azm_last_60m is not None else azm_last_30m
    azm_score = _clamp01((azm_value or 0.0) / 20.0)
    hr_value = hr_z_now if hr_z_now is not None else hr_z_last_15m
    hr_score = _clamp01(((hr_value or 0.0) + 1.0) / 3.0)
    return _clamp01(0.4 * movement + 0.3 * azm_score + 0.3 * hr_score)


def compute_morning_lethargy_score(
    *,
    hour_of_day: int | None,
    steps_last_60m: float | None,
    sleep_debt_hrs: float | None,
    hr_z_now: float | None,
    hr_z_last_15m: float | None,
) -> float | None:
    """Compute morning lethargy score on 0..1; returns None outside morning window."""
    if hour_of_day is None:
        return None
    if hour_of_day < 6 or hour_of_day > 11:
        return None

    sleep_debt_score = _clamp01((sleep_debt_hrs or 0.0) / 3.0)
    inactivity_score = _clamp01((200.0 - (steps_last_60m or 0.0)) / 200.0)
    hr_value = hr_z_now if hr_z_now is not None else hr_z_last_15m
    low_hr_score = (
        _clamp01(-(hr_value or 0.0) / 2.0) if (hr_value is not None and hr_value < 0) else 0.0
    )
    return _clamp01(0.5 * sleep_debt_score + 0.3 * inactivity_score + 0.2 * low_hr_score)


def compute_doomscrolling_score(
    *,
    hour_of_day: int | None,
    sedentary_mins_last_3h: float | None,
    steps_last_30m: float | None,
    steps_last_60m: float | None,
    snack_calories_fraction: float | None,
    client_doomscrolling_score: Any,
) -> float | None:
    """Estimate late-night sedentary phone-use proxy score on 0..1.

    If the client provides a direct score we trust it; otherwise we derive a
    backend score in the late-night window (22:00-02:59 local).
    """
    explicit_client_score = _to_float(client_doomscrolling_score)
    if explicit_client_score is not None:
        return _clamp01(explicit_client_score)

    if hour_of_day is None:
        return None
    is_late_night = hour_of_day >= 22 or hour_of_day <= 2
    if not is_late_night:
        return None

    sed_score = _clamp01((sedentary_mins_last_3h or 0.0) / 180.0)
    steps_value = steps_last_30m if steps_last_30m is not None else steps_last_60m
    low_steps_score = _clamp01((100.0 - (steps_value or 0.0)) / 100.0)
    snack_score = _clamp01(snack_calories_fraction or 0.0)
    return _clamp01(0.5 * sed_score + 0.3 * low_steps_score + 0.2 * snack_score)
