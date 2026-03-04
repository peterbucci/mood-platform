from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_feature_request_service
from app.schemas.feature_request import FeatureRequestResponse
from app.services.feature_request_service import (
    FeatureRequestPersistenceError,
    FeatureRequestService,
)

router = APIRouter(prefix="/features", tags=["features"])


@router.post("/request", response_model=FeatureRequestResponse)
def request_features(
    feature_request_service: Annotated[FeatureRequestService, Depends(get_feature_request_service)],
) -> FeatureRequestResponse:
    try:
        request_id, request_status = feature_request_service.create_request()
    except FeatureRequestPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return FeatureRequestResponse(requestId=request_id, status=request_status)
