from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from app.repositories.fitbit_token_repository import (
    FitbitTokenRepository,
    FitbitTokenRepositoryError,
)
from app.repositories.webhook_job_repository import WebhookJobRepository, WebhookJobRepositoryError
from app.settings import Settings

DEFAULT_WEBHOOK_JOB_TYPE = "fitbit_webhook_ingest"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookEnqueueResult:
    enqueued_count: int
    skipped_count: int


class FitbitWebhookIngestionService:
    def __init__(
        self,
        *,
        fitbit_token_repository: FitbitTokenRepository,
        webhook_job_repository: WebhookJobRepository,
        settings: Settings,
    ) -> None:
        self._fitbit_token_repository = fitbit_token_repository
        self._webhook_job_repository = webhook_job_repository
        self._settings = settings

    def enqueue_events(
        self,
        *,
        payload_events: list[dict[str, Any]],
        request_id: str,
    ) -> WebhookEnqueueResult:
        events_by_fitbit_user_id = self._group_events_by_fitbit_user_id(
            payload_events=payload_events
        )
        enqueued_count = 0
        skipped_count = 0

        for fitbit_user_id, grouped_events in events_by_fitbit_user_id.items():
            try:
                internal_user_id = self._fitbit_token_repository.get_user_id_by_fitbit_user_id(
                    fitbit_user_id=fitbit_user_id
                )
            except FitbitTokenRepositoryError:
                logger.exception(
                    "Failed to resolve internal user from Fitbit id during webhook enqueue.",
                    extra={"request_id": request_id},
                )
                skipped_count += 1
                continue

            if internal_user_id is None:
                skipped_count += 1
                continue

            try:
                was_enqueued = self._webhook_job_repository.enqueue_job(
                    user_id=internal_user_id,
                    fitbit_user_id=fitbit_user_id,
                    payload_json=json.dumps(grouped_events),
                    job_type=DEFAULT_WEBHOOK_JOB_TYPE,
                    coalesce_seconds=self._settings.FITBIT_WEBHOOK_COALESCE_SECONDS,
                )
            except WebhookJobRepositoryError:
                logger.exception(
                    "Failed to enqueue Fitbit webhook job.",
                    extra={"request_id": request_id},
                )
                skipped_count += 1
                continue

            if was_enqueued:
                enqueued_count += 1
            else:
                skipped_count += 1

        logger.info(
            "Fitbit webhook enqueue summary.",
            extra={
                "request_id": request_id,
                "enqueued_count": enqueued_count,
                "skipped_count": skipped_count,
            },
        )
        return WebhookEnqueueResult(enqueued_count=enqueued_count, skipped_count=skipped_count)

    @staticmethod
    def _group_events_by_fitbit_user_id(
        *,
        payload_events: Iterable[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        grouped_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in payload_events:
            owner_id = event.get("ownerId")
            if not isinstance(owner_id, str):
                continue
            normalized_owner_id = owner_id.strip()
            if not normalized_owner_id:
                continue
            grouped_events[normalized_owner_id].append(event)
        return dict(grouped_events)
