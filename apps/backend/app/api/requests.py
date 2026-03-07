from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_feature_request_service
from app.schemas.request_status import (
    PendingRequestCountResponse,
    RequestDeleteResponse,
    RequestListResponse,
    RequestStatusResponse,
)
from app.schemas.responses import RequestResponse
from app.services.feature_request_service import (
    FeatureRequestDeleteError,
    FeatureRequestNotFoundError,
    FeatureRequestService,
)

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


@router.get("/pending/count", response_model=PendingRequestCountResponse)
def get_pending_request_count(
    feature_request_service: Annotated[FeatureRequestService, Depends(get_feature_request_service)],
    user_id: str | None = Query(default=None, alias="userId"),
) -> PendingRequestCountResponse:
    pending_count = feature_request_service.get_pending_request_count(user_id=user_id)
    return PendingRequestCountResponse(pendingCount=pending_count)


@router.get("/{request_id}", response_model=RequestStatusResponse)
def get_request_by_id(
    request_id: str,
    feature_request_service: Annotated[FeatureRequestService, Depends(get_feature_request_service)],
) -> RequestStatusResponse:
    try:
        item = feature_request_service.get_request_by_id(request_id=request_id)
    except FeatureRequestNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RequestStatusResponse(**item)


@router.delete(
    "/{request_id}",
    response_model=RequestDeleteResponse,
    summary="Delete a request and any linked snapshot/labels.",
    responses={
        404: {"description": "Request not found for current user."},
        500: {"description": "Linked delete failed and was rolled back."},
    },
)
def delete_request(
    request_id: str,
    feature_request_service: Annotated[FeatureRequestService, Depends(get_feature_request_service)],
) -> RequestDeleteResponse:
    """Delete the request delete-unit: request, linked snapshot, and linked labels."""
    try:
        item = feature_request_service.delete_request(request_id=request_id)
    except FeatureRequestNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FeatureRequestDeleteError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return RequestDeleteResponse(**item)
