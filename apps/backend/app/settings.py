from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlencode

DEFAULT_FEATURE_EXTRACTOR_VERSION = "v1"
DEFAULT_FITBIT_AUTH_BASE_URL = "https://www.fitbit.com/oauth2/authorize"
DEFAULT_FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
DEFAULT_FITBIT_OAUTH_SCOPE = "sleep heartrate activity profile"


@dataclass(frozen=True)
class Settings:
    FEATURE_EXTRACTOR_VERSION: str = DEFAULT_FEATURE_EXTRACTOR_VERSION
    FITBIT_CLIENT_ID: str = ""
    FITBIT_CLIENT_SECRET: str = ""
    FITBIT_REDIRECT_URI: str = ""
    FITBIT_AUTH_BASE_URL: str = DEFAULT_FITBIT_AUTH_BASE_URL
    FITBIT_TOKEN_URL: str = DEFAULT_FITBIT_TOKEN_URL
    FITBIT_OAUTH_SCOPE: str = DEFAULT_FITBIT_OAUTH_SCOPE
    FITBIT_WEBHOOK_SECRET: str = ""

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
        FITBIT_WEBHOOK_SECRET=os.getenv("FITBIT_WEBHOOK_SECRET", "").strip(),
    )
