import logging

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/fitbit", tags=["fitbit-webhook"])
logger = logging.getLogger(__name__)


@router.get("/webhook", response_class=PlainTextResponse)
def verify_fitbit_webhook_challenge(
    verify: str | None = Query(default=None),
) -> PlainTextResponse:
    if verify is None or not verify.strip():
        logger.warning("Fitbit webhook verification request missing challenge.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing verification challenge",
        )

    logger.info("Fitbit webhook verification challenge accepted.")
    return PlainTextResponse(content=verify, media_type="text/plain")
