from __future__ import annotations

from datetime import UTC, datetime

from app.services.features.context_geo_time import enrich_context_features


def test_enrich_context_features_adds_geo_time_fields_when_location_present() -> None:
    anchor = datetime(2026, 3, 5, 13, 30, tzinfo=UTC)
    enriched, notes = enrich_context_features(
        client_features={"lat": 42.3601, "lon": -71.0589},
        anchor_datetime=anchor,
        source_timezone="America/New_York",
    )

    assert notes == []
    assert enriched["hourOfDay"] == 8
    assert enriched["dayOfWeek"] == 4
    assert enriched["isWeekend"] is False
    assert isinstance(enriched["daylightNowFlag"], bool)
    assert isinstance(enriched["daylightMinsRemaining"], int)
    assert enriched["locationClusterKey"].startswith("grid_")
    assert isinstance(enriched["commuteFlag"], bool)


def test_enrich_context_features_without_location_sets_missing_note() -> None:
    anchor = datetime(2026, 3, 5, 13, 30, tzinfo=UTC)
    enriched, notes = enrich_context_features(
        client_features={},
        anchor_datetime=anchor,
        source_timezone="America/New_York",
    )

    assert notes == ["missing_location_context"]
    assert enriched["hourOfDay"] == 8
    assert enriched["dayOfWeek"] == 4
    assert enriched["isWeekend"] is False
    assert "locationClusterKey" not in enriched
    assert "daylightNowFlag" not in enriched


def test_enrich_context_features_handles_dst_transition_consistently() -> None:
    # 2026-03-08 07:30 UTC maps to 03:30 local in America/New_York after spring forward.
    anchor = datetime(2026, 3, 8, 7, 30, tzinfo=UTC)
    enriched, notes = enrich_context_features(
        client_features={"lat": 42.3601, "lon": -71.0589},
        anchor_datetime=anchor,
        source_timezone="America/New_York",
    )

    assert notes == []
    assert enriched["hourOfDay"] == 3
    assert enriched["dayOfWeek"] == 0
    assert enriched["isWeekend"] is True
