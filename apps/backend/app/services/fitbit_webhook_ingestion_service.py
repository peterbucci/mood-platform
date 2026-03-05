from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from app.repositories.fitbit_token_repository import (
    FitbitTokenRepository,
    FitbitTokenRepositoryError,
)
from app.services.webhook_coalescer import WebhookCoalescer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookEnqueueResult:
    scheduled_count: int
    extended_count: int
    skipped_count: int


class FitbitWebhookIngestionService:
    def __init__(
        self,
        *,
        fitbit_token_repository: FitbitTokenRepository,
        webhook_coalescer: WebhookCoalescer,
    ) -> None:
        self._fitbit_token_repository = fitbit_token_repository
        self._webhook_coalescer = webhook_coalescer

    def enqueue_events(
        self,
        *,
        payload_events: list[dict[str, Any]],
        request_id: str,
    ) -> WebhookEnqueueResult:
        events_by_fitbit_user_id = self._group_events_by_fitbit_user_id(
            payload_events=payload_events
        )
        scheduled_count = 0
        extended_count = 0
        skipped_count = 0

        for fitbit_user_id, _grouped_events in events_by_fitbit_user_id.items():
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

            schedule_outcome = self._webhook_coalescer.schedule(str(internal_user_id))
            if schedule_outcome == "scheduled":
                scheduled_count += 1
            elif schedule_outcome == "extended":
                extended_count += 1
            else:
                skipped_count += 1

        logger.info(
            "Fitbit webhook enqueue summary.",
            extra={
                "request_id": request_id,
                "scheduled_count": scheduled_count,
                "extended_count": extended_count,
                "skipped_count": skipped_count,
            },
        )
        return WebhookEnqueueResult(
            scheduled_count=scheduled_count,
            extended_count=extended_count,
            skipped_count=skipped_count,
        )

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
