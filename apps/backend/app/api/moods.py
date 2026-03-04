from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_mood_entry_service
from app.schemas.mood_entry import CreateMoodEntryRequest, CreateMoodEntryResponse
from app.services.mood_entry_service import (
    MoodEntryFeatureReferenceError,
    MoodEntryPersistenceError,
    MoodEntryService,
    MoodEntryValidationError,
)

router = APIRouter(prefix="/moods", tags=["moods"])


@router.post("", response_model=CreateMoodEntryResponse, status_code=status.HTTP_201_CREATED)
def create_mood_entry(
    payload: CreateMoodEntryRequest,
    mood_entry_service: Annotated[MoodEntryService, Depends(get_mood_entry_service)],
) -> CreateMoodEntryResponse:
    try:
        mood_entry_id = mood_entry_service.create(
            entry_at=payload.entry_at,
            label_category_key=payload.label_category_key,
            label_emotion=payload.label_emotion,
            note=payload.note,
            feature_set_ids=payload.feature_set_ids.model_dump(),
        )
    except MoodEntryValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except MoodEntryFeatureReferenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except MoodEntryPersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return CreateMoodEntryResponse(id=mood_entry_id)
