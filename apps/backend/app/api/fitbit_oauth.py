import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app.dependencies import get_fitbit_oauth_service
from app.services.fitbit_oauth_service import FitbitOAuthConfigurationError, FitbitOAuthService

router = APIRouter(prefix="/fitbit/oauth", tags=["fitbit-oauth"])


@router.get("/start")
def start_fitbit_oauth(
    fitbit_oauth_service: Annotated[FitbitOAuthService, Depends(get_fitbit_oauth_service)],
) -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    try:
        authorization_url = fitbit_oauth_service.build_authorization_url(state=state)
    except FitbitOAuthConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return RedirectResponse(url=authorization_url)
