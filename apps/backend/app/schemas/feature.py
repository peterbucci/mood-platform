from pydantic import BaseModel

from app.schemas.responses import FeatureResponse


class FeatureListResponse(BaseModel):
    items: list[FeatureResponse]
    limit: int
    offset: int
