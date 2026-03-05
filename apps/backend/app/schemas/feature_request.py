from typing import Any

from pydantic import BaseModel


class FeatureRequestResponse(BaseModel):
    requestId: str
    status: str


class FeatureRequestCreatePayload(BaseModel):
    clientFeatures: dict[str, Any] | None = None
