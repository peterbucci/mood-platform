import logging
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import PlainTextResponse

from app.dependencies import get_fitbit_webhook_ingestion_service
from app.services.fitbit_webhook_ingestion_service import FitbitWebhookIngestionService
from app.services.fitbit_webhook_signature import FitbitWebhookSignatureVerifier
from app.settings import get_settings

router = APIRouter(prefix="/fitbit", tags=["fitbit-webhook"])
logger = logging.getLogger(__name__)
FITBIT_SIGNATURE_HEADER = "X-Fitbit-Signature"


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


@router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def ingest_fitbit_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    webhook_ingestion_service: Annotated[
        FitbitWebhookIngestionService,
        Depends(get_fitbit_webhook_ingestion_service),
    ],
) -> Response:
    request_id = str(uuid.uuid4())
    raw_body = getattr(request.state, "raw_body", b"")
    if not isinstance(raw_body, bytes):
        raw_body = b""
    if not raw_body:
        raw_body = await request.body()
    if not raw_body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty request body",
        )

    signature = request.headers.get(FITBIT_SIGNATURE_HEADER, "").strip()
    if not signature:
        logger.warning(
            "Fitbit webhook rejected: missing signature.",
            extra={"request_id": request_id, "verified": False, "event_count": 0},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature",
        )

    verifier = FitbitWebhookSignatureVerifier(
        webhook_secret=get_settings().FITBIT_WEBHOOK_SECRET,
    )
    if not verifier.is_configured():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fitbit webhook signing secret is not configured",
        )

    if not verifier.verify(raw_body=raw_body, provided_signature=signature):
        logger.warning(
            "Fitbit webhook rejected: invalid signature.",
            extra={"request_id": request_id, "verified": False, "event_count": 0},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature",
        )

    payload = await request.json()
    if not isinstance(payload, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload must be a JSON array",
        )

    logger.debug(
        "Fitbit webhook received.",
        extra={"request_id": request_id, "verified": True, "event_count": len(payload)},
    )
    background_tasks.add_task(
        webhook_ingestion_service.enqueue_events,
        payload_events=payload,
        request_id=request_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
