from typing import Literal

from pydantic import BaseModel

from app.schemas.responses import RequestResponse


class RequestListResponse(BaseModel):
    items: list[RequestResponse]
    limit: int
    offset: int


class RequestStatusResponse(BaseModel):
    id: str
    status: Literal["pending", "fulfilled", "canceled"]
    featureId: str | None
    createdAt: int


class RequestDeleteResponse(BaseModel):
    id: str


class PendingRequestCountResponse(BaseModel):
    pendingCount: int
