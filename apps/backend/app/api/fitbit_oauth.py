from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app.dependencies import get_fitbit_oauth_service
from app.schemas.fitbit_oauth import FitbitOAuthCallbackResponse
from app.services.fitbit_oauth_service import (
    FitbitOAuthConfigurationError,
    FitbitOAuthExchangeError,
    FitbitOAuthService,
    FitbitOAuthStateError,
)
from app.services.mood_entry_service import get_owner_user_id

router = APIRouter(prefix="/fitbit/oauth", tags=["fitbit-oauth"])


@router.get("/start")
def start_fitbit_oauth(
    fitbit_oauth_service: Annotated[FitbitOAuthService, Depends(get_fitbit_oauth_service)],
) -> RedirectResponse:
    try:
        authorization_url = fitbit_oauth_service.start_authorization(user_id=get_owner_user_id())
    except FitbitOAuthConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return RedirectResponse(url=authorization_url)


@router.get("/callback", response_model=FitbitOAuthCallbackResponse)
def fitbit_oauth_callback(
    code: str,
    state: str,
    fitbit_oauth_service: Annotated[FitbitOAuthService, Depends(get_fitbit_oauth_service)],
) -> FitbitOAuthCallbackResponse:
    try:
        expires_at = fitbit_oauth_service.handle_callback(
            user_id=get_owner_user_id(),
            code=code,
            state=state,
        )
    except FitbitOAuthStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FitbitOAuthExchangeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except FitbitOAuthConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    return FitbitOAuthCallbackResponse(
        connected=True,
        expiresAt=expires_at,
    )
