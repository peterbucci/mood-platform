from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_feature_service
from app.schemas.feature import FeatureDeleteResponse, FeatureListResponse
from app.schemas.responses import FeatureResponse
from app.services.feature_service import (
    FeatureDataParseError,
    FeatureDeleteError,
    FeatureNotFoundError,
    FeatureService,
)

router = APIRouter(prefix="/features", tags=["features"])


@router.get("/latest", response_model=FeatureResponse)
def get_latest_feature(
    feature_service: Annotated[FeatureService, Depends(get_feature_service)],
) -> FeatureResponse:
    try:
        feature = feature_service.get_latest_feature()
    except FeatureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FeatureDataParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return FeatureResponse(**feature)


@router.get("", response_model=FeatureListResponse)
def list_features(
    feature_service: Annotated[FeatureService, Depends(get_feature_service)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> FeatureListResponse:
    try:
        items = feature_service.list_features(limit=limit, offset=offset)
    except FeatureDataParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return FeatureListResponse(
        items=[FeatureResponse(**item) for item in items],
        limit=limit,
        offset=offset,
    )


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


@router.delete(
    "/{feature_id}",
    response_model=FeatureDeleteResponse,
    summary="Delete a feature and clean up dependent objects.",
)
def delete_feature_by_id(
    feature_id: str,
    feature_service: Annotated[FeatureService, Depends(get_feature_service)],
) -> FeatureDeleteResponse:
    try:
        deleted = feature_service.delete_feature(feature_id=feature_id)
    except FeatureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FeatureDeleteError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return FeatureDeleteResponse(**deleted)
