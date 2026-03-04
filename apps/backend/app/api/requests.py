from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_feature_request_service
from app.schemas.request_status import RequestListResponse
from app.schemas.responses import RequestResponse
from app.services.feature_request_service import FeatureRequestService

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=RequestListResponse)
def list_requests(
    feature_request_service: Annotated[FeatureRequestService, Depends(get_feature_request_service)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> RequestListResponse:
    items = feature_request_service.list_requests(limit=limit, offset=offset)
    return RequestListResponse(
        items=[RequestResponse(**item) for item in items],
        limit=limit,
        offset=offset,
    )
