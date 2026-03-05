from __future__ import annotations

from app.services.weather_context_client import WeatherContextClient


def test_weather_context_returns_missing_when_location_not_provided() -> None:
    client = WeatherContextClient(redis_url="", ttl_seconds=60)
    payload = client.fetch_context(lat=None, lon=None, date_iso="2026-03-05")

    assert payload["weather"]["__missing"] is True
    assert payload["weather"]["reason"] == "missing_location"
    assert payload["air_quality"]["__missing"] is True
    assert payload["air_quality"]["reason"] == "missing_location"
