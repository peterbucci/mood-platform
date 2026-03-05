from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CreateLabelRequest(BaseModel):
    featureId: str = Field(min_length=1)
    label: str | None = None
    emotionWord: str = Field(min_length=1)
    category: Literal["energized", "calm", "stressed", "tired"]


class LabelResponse(BaseModel):
    id: uuid.UUID
    userId: str
    featureId: str
    requestId: str
    label: str | None
    emotionWord: str
    category: Literal["energized", "calm", "stressed", "tired"]
    createdAt: datetime
