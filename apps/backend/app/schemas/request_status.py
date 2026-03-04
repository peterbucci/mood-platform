from pydantic import BaseModel


class RequestFeatureMetadata(BaseModel):
    id: str
    createdAt: int
    source: str


class RequestStatus(BaseModel):
    id: str
    createdAt: int
    status: str
    source: str
    featureId: str | None
    feature: RequestFeatureMetadata | None = None


class RequestListResponse(BaseModel):
    items: list[RequestStatus]
    limit: int
    offset: int
