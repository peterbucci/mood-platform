from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_feature_request_service, get_feature_service
from app.schemas.feature import FeatureResponse
from app.schemas.feature_request import FeatureRequestResponse
from app.services.feature_request_service import (
    FeatureRequestPersistenceError,
    FeatureRequestService,
)
from app.services.feature_service import FeatureDataParseError, FeatureNotFoundError, FeatureService

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


@router.get("/{feature_id}", response_model=FeatureResponse)
def get_feature_by_id(
    feature_id: str,
    feature_service: Annotated[FeatureService, Depends(get_feature_service)],
) -> FeatureResponse:
    try:
        feature = feature_service.get_feature_by_id(feature_id=feature_id)
    except FeatureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FeatureDataParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return FeatureResponse(**feature)
