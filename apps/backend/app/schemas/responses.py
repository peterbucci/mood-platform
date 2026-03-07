from typing import Any, Literal

from pydantic import BaseModel


class FeatureLabelResponse(BaseModel):
    category: Literal["energized", "calm", "stressed", "tired"]
    emotionWord: str


class FeatureResponse(BaseModel):
    id: str
    userId: str
    createdAt: int
    source: str
    data: dict[str, Any]
    label: FeatureLabelResponse | None = None


class RequestResponse(BaseModel):
    id: str
    userId: str
    createdAt: int
    status: Literal["pending", "fulfilled", "canceled"]
    featureId: str | None
    source: str
