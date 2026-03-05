from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_label_service
from app.schemas.label import CreateLabelRequest, LabelResponse
from app.services.label_service import (
    LabelFeatureReferenceError,
    LabelPersistenceError,
    LabelService,
    LabelTraceabilityError,
    LabelValidationError,
)

router = APIRouter(prefix="/labels", tags=["labels"])


@router.post("", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
def create_label(
    payload: CreateLabelRequest,
    label_service: Annotated[LabelService, Depends(get_label_service)],
) -> LabelResponse:
    try:
        created = label_service.create(
            feature_id=payload.featureId,
            label=payload.label,
            emotion_word=payload.emotionWord,
            category=payload.category,
        )
    except LabelValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LabelFeatureReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LabelTraceabilityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LabelPersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return LabelResponse(**created)
