from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any

import httpx
from redis import Redis

from app.settings import get_settings

logger = logging.getLogger(__name__)

DEFAULT_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
DEFAULT_WEATHER_CACHE_TTL_SECONDS = 900


class WeatherContextClient:
    def __init__(
        self,
        *,
        redis_url: str | None = None,
        ttl_seconds: int | None = None,
        weather_url: str = DEFAULT_WEATHER_URL,
        air_quality_url: str = DEFAULT_AIR_QUALITY_URL,
    ) -> None:
        configured_redis_url = (redis_url or os.getenv("REDIS_URL", "")).strip()
        self._redis: Redis | None = None
        if configured_redis_url:
            try:
                self._redis = Redis.from_url(
                    configured_redis_url,
                    decode_responses=True,
                    socket_connect_timeout=1,
                    socket_timeout=1,
                )
            except Exception:
                logger.exception("Failed to initialize Redis cache client for weather context.")
                self._redis = None

        configured_ttl_seconds = (
            ttl_seconds if ttl_seconds is not None else get_settings().WEATHER_CACHE_TTL_SECONDS
        )
        self._ttl_seconds = max(30, configured_ttl_seconds)
        self._weather_url = weather_url
        self._air_quality_url = air_quality_url
        self._memory_lock = threading.RLock()
        self._memory_cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def fetch_context(
        self,
        *,
        lat: float | None,
        lon: float | None,
        date_iso: str,
    ) -> dict[str, Any]:
        if lat is None or lon is None:
            missing = _missing("missing_location")
            return {
                "weather": missing,
                "air_quality": missing,
            }

        cache_key = self._cache_key(lat=lat, lon=lon, date_iso=date_iso)
        cached = self._read_cache(cache_key=cache_key)
        if cached is not None:
            return cached

        with httpx.Client(timeout=10) as client:
            weather = self._fetch(
                client=client,
                url=self._weather_url,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,apparent_temperature,precipitation",
                    "timezone": "auto",
                },
            )
            air_quality = self._fetch(
                client=client,
                url=self._air_quality_url,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "us_aqi",
                    "timezone": "auto",
                },
            )

        payload = {
            "weather": weather,
            "air_quality": air_quality,
        }
        self._write_cache(cache_key=cache_key, payload=payload)
        return payload

    def _fetch(self, *, client: httpx.Client, url: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = client.get(url, params=params)
        except httpx.RequestError:
            logger.exception("Weather/AQ request failed: %s", url)
            return _missing("request_error")

        if response.status_code == 404:
            return _missing("not_found", response.status_code)
        if response.status_code == 429:
            return _missing("rate_limited", response.status_code)
        if 500 <= response.status_code < 600:
            return _missing("upstream_error", response.status_code)
        if not 200 <= response.status_code < 300:
            return _missing("unexpected_status", response.status_code)

        try:
            payload = response.json()
        except ValueError:
            return _missing("malformed_json", response.status_code)

        if isinstance(payload, dict):
            normalized_payload = payload
        elif isinstance(payload, list):
            normalized_payload = {"items": payload}
        else:
            normalized_payload = {"value": payload}

        return _present(normalized_payload, response.status_code)

    def _cache_key(self, *, lat: float, lon: float, date_iso: str) -> str:
        rounded_lat = round(lat, 3)
        rounded_lon = round(lon, 3)
        return f"weather_context:{date_iso}:{rounded_lat}:{rounded_lon}"

    def _read_cache(self, *, cache_key: str) -> dict[str, Any] | None:
        now = time.time()
        with self._memory_lock:
            cached_value = self._memory_cache.get(cache_key)
            if cached_value is not None:
                expires_at, payload = cached_value
                if expires_at > now:
                    return payload
                self._memory_cache.pop(cache_key, None)

        if self._redis is None:
            return None

        try:
            raw_value = self._redis.get(cache_key)
        except Exception:
            logger.exception("Redis cache read failed for weather context.")
            return None
        if not raw_value:
            return None
        try:
            parsed_value = json.loads(raw_value)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed_value, dict):
            return None
        return parsed_value

    def _write_cache(self, *, cache_key: str, payload: dict[str, Any]) -> None:
        expires_at = time.time() + self._ttl_seconds
        with self._memory_lock:
            self._memory_cache[cache_key] = (expires_at, payload)

        if self._redis is None:
            return

        try:
            self._redis.setex(cache_key, self._ttl_seconds, json.dumps(payload))
        except Exception:
            logger.exception("Redis cache write failed for weather context.")


def _present(payload: dict[str, Any], raw_status: int) -> dict[str, Any]:
    return {
        "__missing": False,
        "reason": None,
        "raw_status": raw_status,
        "payload": payload,
    }


def _missing(reason: str, raw_status: int | None = None) -> dict[str, Any]:
    return {
        "__missing": True,
        "reason": reason,
        "raw_status": raw_status,
        "payload": {},
    }
