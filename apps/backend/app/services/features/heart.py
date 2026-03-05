from __future__ import annotations


def compute_day_hr_stats(
    intraday_hr_series: list[float],
) -> tuple[float | None, float | None, float | None]:
    if not intraday_hr_series:
        return (None, None, None)
    return (
        float(sum(intraday_hr_series) / len(intraday_hr_series)),
        float(min(intraday_hr_series)),
        float(max(intraday_hr_series)),
    )
