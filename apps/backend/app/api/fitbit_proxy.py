from __future__ import annotations

import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.dependencies import get_fitbit_token_service
from app.services.fitbit_api_client import FitbitApiClient
from app.services.fitbit_token_service import FitbitTokenNotConnectedError, FitbitTokenService
from app.services.mood_entry_service import get_owner_user_id

router = APIRouter(prefix="/fitbit", tags=["fitbit-proxy"])
logger = logging.getLogger(__name__)

ALLOWED_PROXY_PREFIXES = ("/1/", "/1.2/")
BLOCKED_PROXY_PREFIXES = ("/oauth2/",)


@router.get("/proxy")
def proxy_fitbit_get(
    fitbit_token_service: Annotated[FitbitTokenService, Depends(get_fitbit_token_service)],
    path: str = Query(..., min_length=3),
) -> Response:
    normalized_path = path.strip()
    if not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"

    if normalized_path.startswith(BLOCKED_PROXY_PREFIXES) or "/oauth2/" in normalized_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proxy path is blocked.",
        )
    if not normalized_path.startswith(ALLOWED_PROXY_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proxy path must start with /1/ or /1.2/.",
        )

    owner_user_id = get_owner_user_id()
    api_client = FitbitApiClient(token_service=fitbit_token_service)
    try:
        upstream_response = api_client.fitbit_fetch(
            user_id=owner_user_id,
            url=api_client._fitbit_url(normalized_path),  # noqa: SLF001
            method="GET",
        )
    except FitbitTokenNotConnectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fitbit account is not connected.",
        ) from exc
    except httpx.HTTPError as exc:
        logger.exception("Fitbit proxy request failed for path %s.", normalized_path)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to call Fitbit proxy upstream.",
        ) from exc

    content_type = upstream_response.headers.get("content-type", "application/json")
    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        media_type=content_type.split(";")[0],
    )
