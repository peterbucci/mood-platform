from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FeatureSetIds(BaseModel):
    personal_features_id: uuid.UUID | None = None
    daily_features_id: uuid.UUID | None = None
    sleep_features_id: uuid.UUID | None = None
    steps_features_id: uuid.UUID | None = None
    exercise_features_id: uuid.UUID | None = None
    hr_features_id: uuid.UUID | None = None
    resting_hr_features_id: uuid.UUID | None = None
    calorie_features_id: uuid.UUID | None = None


class CreateMoodEntryRequest(BaseModel):
    entry_at: datetime
    label_category_key: Literal["energized", "calm", "stressed", "tired"]
    label_emotion: str = Field(min_length=1)
    note: str | None = None
    feature_set_ids: FeatureSetIds = Field(default_factory=FeatureSetIds)


class CreateMoodEntryResponse(BaseModel):
    id: uuid.UUID
