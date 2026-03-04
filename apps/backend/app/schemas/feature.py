from typing import Any

from pydantic import BaseModel


class FeatureResponse(BaseModel):
    id: str
    userId: str
    createdAt: int
    source: str
    data: dict[str, Any]
