from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

logger = logging.getLogger(__name__)

ScheduleOutcome = Literal["scheduled", "extended", "skipped"]


class TimerHandle(Protocol):
    def start(self) -> None: ...

    def cancel(self) -> None: ...


TimerFactory = Callable[[float, Callable[[], None]], TimerHandle]
HasPendingRequestsFn = Callable[[str], bool]
TriggerFulfillmentFn = Callable[[str], None]
CoalesceSecondsProvider = Callable[[], int]


@dataclass
class _PendingTimer:
    generation: int
    timer: TimerHandle


def _default_timer_factory(delay_seconds: float, callback: Callable[[], None]) -> TimerHandle:
    timer = threading.Timer(delay_seconds, callback)
    timer.daemon = True
    return timer


class WebhookCoalescer:
    def __init__(
        self,
        *,
        coalesce_seconds_provider: CoalesceSecondsProvider,
        has_pending_requests: HasPendingRequestsFn,
        trigger_fulfillment: TriggerFulfillmentFn,
        timer_factory: TimerFactory = _default_timer_factory,
    ) -> None:
        self._coalesce_seconds_provider = coalesce_seconds_provider
        self._has_pending_requests = has_pending_requests
        self._trigger_fulfillment = trigger_fulfillment
        self._timer_factory = timer_factory
        self._lock = threading.RLock()
        self._pending_by_user: dict[str, _PendingTimer] = {}
        self._running_user_ids: set[str] = set()

    def schedule(self, user_id: str) -> ScheduleOutcome:
        normalized_user_id = user_id.strip()
        if not normalized_user_id:
            return "skipped"

        try:
            has_pending = self._has_pending_requests(normalized_user_id)
        except Exception:
            logger.exception(
                "Failed pending-request guard while scheduling webhook debounce.",
                extra={"user_id": normalized_user_id},
            )
            return "skipped"

        if not has_pending:
            logger.debug(
                "Skipping webhook debounce because user has no pending requests.",
                extra={"user_id": normalized_user_id},
            )
            return "skipped"

        with self._lock:
            existing_entry = self._pending_by_user.get(normalized_user_id)
            if existing_entry is None:
                self._schedule_locked(
                    user_id=normalized_user_id,
                    generation=1,
                    action="scheduled",
                )
                return "scheduled"

            self._extend_locked(user_id=normalized_user_id, entry=existing_entry)
            return "extended"

    def extend(self, user_id: str) -> ScheduleOutcome:
        normalized_user_id = user_id.strip()
        if not normalized_user_id:
            return "skipped"

        with self._lock:
            existing_entry = self._pending_by_user.get(normalized_user_id)
            if existing_entry is None:
                self._schedule_locked(
                    user_id=normalized_user_id,
                    generation=1,
                    action="scheduled",
                )
                return "scheduled"

            self._extend_locked(user_id=normalized_user_id, entry=existing_entry)
            return "extended"

    def run(self, user_id: str, *, expected_generation: int | None = None) -> None:
        normalized_user_id = user_id.strip()
        if not normalized_user_id:
            return

        with self._lock:
            current_entry = self._pending_by_user.get(normalized_user_id)
            if current_entry is None:
                return

            if expected_generation is not None and current_entry.generation != expected_generation:
                return

            self._pending_by_user.pop(normalized_user_id, None)
            if normalized_user_id in self._running_user_ids:
                logger.debug(
                    "Skipping webhook fulfillment trigger because a run is already in progress.",
                    extra={"user_id": normalized_user_id},
                )
                return
            self._running_user_ids.add(normalized_user_id)

        try:
            try:
                has_pending = self._has_pending_requests(normalized_user_id)
            except Exception:
                logger.exception(
                    "Failed pending-request guard while running webhook debounce.",
                    extra={"user_id": normalized_user_id},
                )
                return

            if not has_pending:
                logger.debug(
                    "Skipping webhook fulfillment trigger because user has no pending requests.",
                    extra={"user_id": normalized_user_id},
                )
                return

            logger.debug(
                "Webhook debounce fulfillment triggered.",
                extra={"user_id": normalized_user_id},
            )
            self._trigger_fulfillment(normalized_user_id)
        except Exception:
            logger.exception(
                "Webhook fulfillment trigger failed.",
                extra={"user_id": normalized_user_id},
            )
        finally:
            with self._lock:
                self._running_user_ids.discard(normalized_user_id)

    def _extend_locked(self, *, user_id: str, entry: _PendingTimer) -> None:
        entry.timer.cancel()
        self._schedule_locked(
            user_id=user_id,
            generation=entry.generation + 1,
            action="extended",
        )

    def _schedule_locked(self, *, user_id: str, generation: int, action: str) -> None:
        delay_seconds = self._coalesce_seconds()
        timer = self._timer_factory(
            delay_seconds,
            lambda: self.run(user_id, expected_generation=generation),
        )
        self._pending_by_user[user_id] = _PendingTimer(generation=generation, timer=timer)
        logger.debug(
            "Webhook debounce %s.",
            action,
            extra={
                "user_id": user_id,
                "coalesce_seconds": delay_seconds,
            },
        )
        timer.start()

    def _coalesce_seconds(self) -> float:
        configured_value: int
        try:
            configured_value = int(self._coalesce_seconds_provider())
        except Exception:
            configured_value = 1
        return float(max(1, configured_value))
