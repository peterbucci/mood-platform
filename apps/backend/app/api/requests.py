from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_feature_request_service
from app.schemas.request_status import (
    PendingRequestCountResponse,
    RequestListResponse,
    RequestStatusResponse,
)
from app.schemas.responses import RequestResponse
from app.services.feature_request_service import (
    FeatureRequestConflictError,
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
    response_model=RequestResponse,
    summary="Cancel a pending request",
    responses={
        404: {"description": "Request not found for current user."},
        409: {"description": "Request cannot be canceled in current state."},
    },
)
def cancel_request(
    request_id: str,
    feature_request_service: Annotated[FeatureRequestService, Depends(get_feature_request_service)],
    delete_feature_too: bool = Query(default=False, alias="deleteFeatureToo"),
) -> RequestResponse:
    try:
        item = feature_request_service.cancel_request(
            request_id=request_id,
            delete_feature_too=delete_feature_too,
        )
    except FeatureRequestNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FeatureRequestConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return RequestResponse(**item)
