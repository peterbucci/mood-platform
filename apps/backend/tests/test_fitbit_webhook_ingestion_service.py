from __future__ import annotations

import uuid

from app.services.fitbit_webhook_ingestion_service import FitbitWebhookIngestionService


class _FakeFitbitTokenRepository:
    def __init__(self, user_by_fitbit_id: dict[str, uuid.UUID | None]) -> None:
        self._user_by_fitbit_id = user_by_fitbit_id

    def get_user_id_by_fitbit_user_id(self, *, fitbit_user_id: str) -> uuid.UUID | None:
        return self._user_by_fitbit_id.get(fitbit_user_id)


class _FakeWebhookCoalescer:
    def __init__(self, outcomes_by_user: dict[str, str]) -> None:
        self._outcomes_by_user = outcomes_by_user
        self.scheduled_user_ids: list[str] = []

    def schedule(self, user_id: str) -> str:
        self.scheduled_user_ids.append(user_id)
        return self._outcomes_by_user[user_id]


def test_enqueue_events_groups_by_owner_and_schedules_once_per_user() -> None:
    internal_user_id = uuid.UUID("00000000-0000-0000-0000-00000000ab01")
    coalescer = _FakeWebhookCoalescer(outcomes_by_user={str(internal_user_id): "scheduled"})
    service = FitbitWebhookIngestionService(
        fitbit_token_repository=_FakeFitbitTokenRepository(
            user_by_fitbit_id={"fitbit-1": internal_user_id}
        ),
        webhook_coalescer=coalescer,
    )

    result = service.enqueue_events(
        payload_events=[
            {"ownerId": "fitbit-1", "collectionType": "sleep"},
            {"ownerId": "fitbit-1", "collectionType": "activities"},
        ],
        request_id="request-1",
    )

    assert coalescer.scheduled_user_ids == [str(internal_user_id)]
    assert result.scheduled_count == 1
    assert result.extended_count == 0
    assert result.skipped_count == 0


def test_enqueue_events_counts_extended_and_skipped_outcomes() -> None:
    user_a = uuid.UUID("00000000-0000-0000-0000-00000000ab02")
    user_b = uuid.UUID("00000000-0000-0000-0000-00000000ab03")
    coalescer = _FakeWebhookCoalescer(
        outcomes_by_user={
            str(user_a): "extended",
            str(user_b): "skipped",
        }
    )
    service = FitbitWebhookIngestionService(
        fitbit_token_repository=_FakeFitbitTokenRepository(
            user_by_fitbit_id={
                "fitbit-a": user_a,
                "fitbit-b": user_b,
                "fitbit-missing": None,
            }
        ),
        webhook_coalescer=coalescer,
    )

    result = service.enqueue_events(
        payload_events=[
            {"ownerId": "fitbit-a"},
            {"ownerId": "fitbit-b"},
            {"ownerId": "fitbit-missing"},
            {"ownerId": ""},
            {"collectionType": "sleep"},
        ],
        request_id="request-2",
    )

    assert coalescer.scheduled_user_ids == [str(user_a), str(user_b)]
    assert result.scheduled_count == 0
    assert result.extended_count == 1
    assert result.skipped_count == 2
