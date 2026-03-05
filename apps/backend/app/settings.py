from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlencode

DEFAULT_FEATURE_EXTRACTOR_VERSION = "v1"
DEFAULT_FITBIT_AUTH_BASE_URL = "https://www.fitbit.com/oauth2/authorize"
DEFAULT_FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
DEFAULT_FITBIT_OAUTH_SCOPE = "sleep heartrate activity profile"
DEFAULT_FITBIT_WEBHOOK_COALESCE_SECONDS = 10
DEFAULT_WEATHER_CACHE_TTL_SECONDS = 900
DEFAULT_NIGHT_ANCHOR_START_HOUR = 18
DEFAULT_NIGHT_ANCHOR_END_HOUR = 12
DEFAULT_FITBIT_MIN_FETCH_INTERVAL_SECONDS = 0.2
DEFAULT_FITBIT_MAX_RETRIES = 3
DEFAULT_FITBIT_BACKOFF_BASE_SECONDS = 1.0
DEFAULT_FITBIT_DEFAULT_TIMEZONE = "UTC"


@dataclass(frozen=True)
class Settings:
    FEATURE_EXTRACTOR_VERSION: str = DEFAULT_FEATURE_EXTRACTOR_VERSION
    FITBIT_CLIENT_ID: str = ""
    FITBIT_CLIENT_SECRET: str = ""
    FITBIT_REDIRECT_URI: str = ""
    FITBIT_AUTH_BASE_URL: str = DEFAULT_FITBIT_AUTH_BASE_URL
    FITBIT_TOKEN_URL: str = DEFAULT_FITBIT_TOKEN_URL
    FITBIT_OAUTH_SCOPE: str = DEFAULT_FITBIT_OAUTH_SCOPE
    FITBIT_SUBSCRIBER_ID: str = ""
    FITBIT_WEBHOOK_SECRET: str = ""
    FITBIT_WEBHOOK_COALESCE_SECONDS: int = DEFAULT_FITBIT_WEBHOOK_COALESCE_SECONDS
    WEATHER_CACHE_TTL_SECONDS: int = DEFAULT_WEATHER_CACHE_TTL_SECONDS
    NIGHT_ANCHOR_START_HOUR: int = DEFAULT_NIGHT_ANCHOR_START_HOUR
    NIGHT_ANCHOR_END_HOUR: int = DEFAULT_NIGHT_ANCHOR_END_HOUR
    FITBIT_MIN_FETCH_INTERVAL_SECONDS: float = DEFAULT_FITBIT_MIN_FETCH_INTERVAL_SECONDS
    FITBIT_MAX_RETRIES: int = DEFAULT_FITBIT_MAX_RETRIES
    FITBIT_BACKOFF_BASE_SECONDS: float = DEFAULT_FITBIT_BACKOFF_BASE_SECONDS
    FITBIT_DEFAULT_TIMEZONE: str = DEFAULT_FITBIT_DEFAULT_TIMEZONE

    def fitbit_scope_query_value(self) -> str:
        return " ".join(self.FITBIT_OAUTH_SCOPE.split())

    def fitbit_authorization_query(self, *, state: str) -> str:
        return urlencode(
            {
                "client_id": self.FITBIT_CLIENT_ID,
                "redirect_uri": self.FITBIT_REDIRECT_URI,
                "response_type": "code",
                "scope": self.fitbit_scope_query_value(),
                "state": state,
            }
        )


def get_settings() -> Settings:
    configured_version = os.getenv(
        "FEATURE_EXTRACTOR_VERSION",
        DEFAULT_FEATURE_EXTRACTOR_VERSION,
    ).strip()
    if not configured_version:
        configured_version = DEFAULT_FEATURE_EXTRACTOR_VERSION

    configured_fitbit_webhook_coalesce_seconds = os.getenv(
        "FITBIT_WEBHOOK_COALESCE_SECONDS",
        str(DEFAULT_FITBIT_WEBHOOK_COALESCE_SECONDS),
    ).strip()
    try:
        fitbit_webhook_coalesce_seconds = int(configured_fitbit_webhook_coalesce_seconds)
    except ValueError:
        fitbit_webhook_coalesce_seconds = DEFAULT_FITBIT_WEBHOOK_COALESCE_SECONDS

    configured_weather_cache_ttl_seconds = os.getenv(
        "WEATHER_CACHE_TTL_SECONDS",
        str(DEFAULT_WEATHER_CACHE_TTL_SECONDS),
    ).strip()
    try:
        weather_cache_ttl_seconds = int(configured_weather_cache_ttl_seconds)
    except ValueError:
        weather_cache_ttl_seconds = DEFAULT_WEATHER_CACHE_TTL_SECONDS

    configured_night_anchor_start_hour = os.getenv(
        "NIGHT_ANCHOR_START_HOUR",
        str(DEFAULT_NIGHT_ANCHOR_START_HOUR),
    ).strip()
    try:
        night_anchor_start_hour = int(configured_night_anchor_start_hour)
    except ValueError:
        night_anchor_start_hour = DEFAULT_NIGHT_ANCHOR_START_HOUR

    configured_night_anchor_end_hour = os.getenv(
        "NIGHT_ANCHOR_END_HOUR",
        str(DEFAULT_NIGHT_ANCHOR_END_HOUR),
    ).strip()
    try:
        night_anchor_end_hour = int(configured_night_anchor_end_hour)
    except ValueError:
        night_anchor_end_hour = DEFAULT_NIGHT_ANCHOR_END_HOUR

    configured_fitbit_min_fetch_interval_seconds = os.getenv(
        "FITBIT_MIN_FETCH_INTERVAL_SECONDS",
        str(DEFAULT_FITBIT_MIN_FETCH_INTERVAL_SECONDS),
    ).strip()
    try:
        fitbit_min_fetch_interval_seconds = float(configured_fitbit_min_fetch_interval_seconds)
    except ValueError:
        fitbit_min_fetch_interval_seconds = DEFAULT_FITBIT_MIN_FETCH_INTERVAL_SECONDS

    configured_fitbit_max_retries = os.getenv(
        "FITBIT_MAX_RETRIES",
        str(DEFAULT_FITBIT_MAX_RETRIES),
    ).strip()
    try:
        fitbit_max_retries = int(configured_fitbit_max_retries)
    except ValueError:
        fitbit_max_retries = DEFAULT_FITBIT_MAX_RETRIES

    configured_fitbit_backoff_base_seconds = os.getenv(
        "FITBIT_BACKOFF_BASE_SECONDS",
        str(DEFAULT_FITBIT_BACKOFF_BASE_SECONDS),
    ).strip()
    try:
        fitbit_backoff_base_seconds = float(configured_fitbit_backoff_base_seconds)
    except ValueError:
        fitbit_backoff_base_seconds = DEFAULT_FITBIT_BACKOFF_BASE_SECONDS

    return Settings(
        FEATURE_EXTRACTOR_VERSION=configured_version,
        FITBIT_CLIENT_ID=os.getenv("FITBIT_CLIENT_ID", "").strip(),
        FITBIT_CLIENT_SECRET=os.getenv("FITBIT_CLIENT_SECRET", "").strip(),
        FITBIT_REDIRECT_URI=os.getenv("FITBIT_REDIRECT_URI", "").strip(),
        FITBIT_AUTH_BASE_URL=os.getenv(
            "FITBIT_AUTH_BASE_URL",
            DEFAULT_FITBIT_AUTH_BASE_URL,
        ).strip(),
        FITBIT_TOKEN_URL=os.getenv(
            "FITBIT_TOKEN_URL",
            DEFAULT_FITBIT_TOKEN_URL,
        ).strip(),
        FITBIT_OAUTH_SCOPE=os.getenv(
            "FITBIT_OAUTH_SCOPE",
            DEFAULT_FITBIT_OAUTH_SCOPE,
        ).strip(),
        FITBIT_SUBSCRIBER_ID=os.getenv("FITBIT_SUBSCRIBER_ID", "").strip(),
        FITBIT_WEBHOOK_SECRET=os.getenv("FITBIT_WEBHOOK_SECRET", "").strip(),
        FITBIT_WEBHOOK_COALESCE_SECONDS=max(1, fitbit_webhook_coalesce_seconds),
        WEATHER_CACHE_TTL_SECONDS=max(30, weather_cache_ttl_seconds),
        NIGHT_ANCHOR_START_HOUR=max(0, min(23, night_anchor_start_hour)),
        NIGHT_ANCHOR_END_HOUR=max(0, min(23, night_anchor_end_hour)),
        FITBIT_MIN_FETCH_INTERVAL_SECONDS=max(0.0, fitbit_min_fetch_interval_seconds),
        FITBIT_MAX_RETRIES=max(0, fitbit_max_retries),
        FITBIT_BACKOFF_BASE_SECONDS=max(0.1, fitbit_backoff_base_seconds),
        FITBIT_DEFAULT_TIMEZONE=os.getenv(
            "FITBIT_DEFAULT_TIMEZONE",
            DEFAULT_FITBIT_DEFAULT_TIMEZONE,
        ).strip()
        or DEFAULT_FITBIT_DEFAULT_TIMEZONE,
    )
