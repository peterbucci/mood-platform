from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_FEATURE_EXTRACTOR_VERSION = "v1"


@dataclass(frozen=True)
class Settings:
    FEATURE_EXTRACTOR_VERSION: str = DEFAULT_FEATURE_EXTRACTOR_VERSION


def get_settings() -> Settings:
    configured_version = os.getenv(
        "FEATURE_EXTRACTOR_VERSION",
        DEFAULT_FEATURE_EXTRACTOR_VERSION,
    ).strip()
    if not configured_version:
        configured_version = DEFAULT_FEATURE_EXTRACTOR_VERSION
    return Settings(FEATURE_EXTRACTOR_VERSION=configured_version)
