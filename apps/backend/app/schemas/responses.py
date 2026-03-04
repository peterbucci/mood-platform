from typing import Any, Literal

from pydantic import BaseModel


class FeatureResponse(BaseModel):
    id: str
    userId: str
    createdAt: int
    source: str
    data: dict[str, Any]


class RequestResponse(BaseModel):
    id: str
    userId: str
    createdAt: int
    status: Literal["pending", "fulfilled", "canceled"]
    featureId: str | None
    source: str
