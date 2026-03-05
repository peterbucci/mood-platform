from __future__ import annotations

from app.services.fitbit_anchoring import build_anchor_context, resolve_source_timezone


def test_resolve_source_timezone_prefers_valid_client_timezone() -> None:
    timezone_name = resolve_source_timezone(
        client_features={"timezone": "America/New_York"},
        fallback_timezone="UTC",
    )
    assert timezone_name == "America/New_York"


def test_resolve_source_timezone_falls_back_when_invalid() -> None:
    timezone_name = resolve_source_timezone(
        client_features={"timezone": "Mars/OlympusMons"},
        fallback_timezone="UTC",
    )
    assert timezone_name == "UTC"


def test_build_anchor_context_uses_local_date_and_night_anchor() -> None:
    # 2026-03-05T14:30:00Z => 2026-03-05 08:30 local in America/Chicago.
    created_at = 1772721000
    context = build_anchor_context(
        created_at=created_at,
        client_features={"timezone": "America/Chicago"},
        fallback_timezone="UTC",
        night_anchor_start_hour=18,
        night_anchor_end_hour=12,
    )

    assert context.source_timezone == "America/Chicago"
    assert context.local_date_iso == "2026-03-05"
    assert context.night_anchor_date_iso == "2026-03-04"
    assert context.night_window_start_utc.isoformat() == "2026-03-05T00:00:00+00:00"
    assert context.night_window_end_utc.isoformat() == "2026-03-05T18:00:00+00:00"
