from pydantic import BaseModel

from app.schemas.responses import RequestResponse


class RequestListResponse(BaseModel):
    items: list[RequestResponse]
    limit: int
    offset: int
