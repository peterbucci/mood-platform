from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import WebhookJob

PENDING_WEBHOOK_JOB_STATUS = "pending"
PROCESSING_WEBHOOK_JOB_STATUS = "processing"


class WebhookJobRepositoryError(Exception):
    pass


class WebhookJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def enqueue_job(
        self,
        *,
        user_id: uuid.UUID,
        fitbit_user_id: str,
        payload_json: str,
        job_type: str,
        coalesce_seconds: int,
    ) -> bool:
        cutoff = datetime.now(tz=UTC) - timedelta(seconds=coalesce_seconds)
        try:
            existing_job_id = self._session.execute(
                sa.select(WebhookJob.id)
                .where(
                    WebhookJob.user_id == user_id,
                    WebhookJob.status.in_(
                        (PENDING_WEBHOOK_JOB_STATUS, PROCESSING_WEBHOOK_JOB_STATUS)
                    ),
                    WebhookJob.created_at >= cutoff,
                )
                .limit(1)
            ).scalar_one_or_none()
            if existing_job_id is not None:
                return False

            self._session.add(
                WebhookJob(
                    user_id=user_id,
                    fitbit_user_id=fitbit_user_id,
                    job_type=job_type,
                    payload_json=payload_json,
                    status=PENDING_WEBHOOK_JOB_STATUS,
                )
            )
            self._session.commit()
            return True
        except SQLAlchemyError as exc:
            self._session.rollback()
            raise WebhookJobRepositoryError("Failed to enqueue webhook job.") from exc
