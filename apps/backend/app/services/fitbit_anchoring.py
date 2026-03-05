from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class FitbitAnchorContext:
    source_timezone: str
    anchor_utc: datetime
    anchor_local: datetime
    local_date_iso: str
    night_anchor_date_iso: str
    night_window_start_utc: datetime
    night_window_end_utc: datetime


def resolve_source_timezone(
    *,
    client_features: dict[str, Any] | None,
    fallback_timezone: str,
) -> str:
    if isinstance(client_features, dict):
        for key in ("source_timezone", "timezone", "tz", "timeZone"):
            value = client_features.get(key)
            if not isinstance(value, str):
                continue
            normalized = value.strip()
            if not normalized:
                continue
            if _is_valid_timezone(normalized):
                return normalized
    if _is_valid_timezone(fallback_timezone):
        return fallback_timezone
    return "UTC"


def build_anchor_context(
    *,
    created_at: int | None,
    client_features: dict[str, Any] | None,
    fallback_timezone: str,
    night_anchor_start_hour: int,
    night_anchor_end_hour: int,
) -> FitbitAnchorContext:
    anchor_utc = _request_anchor_utc(created_at)
    source_timezone = resolve_source_timezone(
        client_features=client_features,
        fallback_timezone=fallback_timezone,
    )
    tzinfo = ZoneInfo(source_timezone)
    anchor_local = anchor_utc.astimezone(tzinfo)
    local_date = anchor_local.date()

    # Node parity: if request is before "night end", use previous night anchor date.
    if anchor_local.hour < night_anchor_end_hour:
        night_anchor_date = local_date - timedelta(days=1)
    else:
        night_anchor_date = local_date

    night_window_start_local = datetime.combine(
        night_anchor_date,
        time(hour=night_anchor_start_hour),
        tzinfo=tzinfo,
    )
    night_window_end_local = datetime.combine(
        night_anchor_date + timedelta(days=1),
        time(hour=night_anchor_end_hour),
        tzinfo=tzinfo,
    )

    return FitbitAnchorContext(
        source_timezone=source_timezone,
        anchor_utc=anchor_utc,
        anchor_local=anchor_local,
        local_date_iso=local_date.isoformat(),
        night_anchor_date_iso=night_anchor_date.isoformat(),
        night_window_start_utc=night_window_start_local.astimezone(UTC),
        night_window_end_utc=night_window_end_local.astimezone(UTC),
    )


def _request_anchor_utc(created_at: int | None) -> datetime:
    if isinstance(created_at, int):
        return datetime.fromtimestamp(created_at, tz=UTC)
    return datetime.now(tz=UTC)


def _is_valid_timezone(timezone_name: str) -> bool:
    try:
        ZoneInfo(timezone_name)
        return True
    except ZoneInfoNotFoundError:
        return False
