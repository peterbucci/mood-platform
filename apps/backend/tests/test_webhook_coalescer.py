from __future__ import annotations

from app.services.webhook_coalescer import WebhookCoalescer


class _ManualTimer:
    def __init__(self, callback) -> None:
        self._callback = callback
        self.started = False
        self.cancelled = False

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        if self.cancelled:
            return
        self._callback()


class _ManualTimerFactory:
    def __init__(self) -> None:
        self.created_timers: list[_ManualTimer] = []

    def __call__(self, _delay_seconds: float, callback):
        timer = _ManualTimer(callback)
        self.created_timers.append(timer)
        return timer


def test_schedule_then_extend_triggers_fulfillment_once() -> None:
    pending_users = {"user-1"}
    fulfilled_users: list[str] = []
    timer_factory = _ManualTimerFactory()
    coalescer = WebhookCoalescer(
        coalesce_seconds_provider=lambda: 10,
        has_pending_requests=lambda user_id: user_id in pending_users,
        trigger_fulfillment=lambda user_id: fulfilled_users.append(user_id),
        timer_factory=timer_factory,
    )

    assert coalescer.schedule("user-1") == "scheduled"
    assert coalescer.schedule("user-1") == "extended"
    assert len(timer_factory.created_timers) == 2
    assert timer_factory.created_timers[0].cancelled is True

    timer_factory.created_timers[0].fire()
    assert fulfilled_users == []

    timer_factory.created_timers[1].fire()
    assert fulfilled_users == ["user-1"]


def test_schedule_skips_user_without_pending_requests() -> None:
    timer_factory = _ManualTimerFactory()
    fulfilled_users: list[str] = []
    coalescer = WebhookCoalescer(
        coalesce_seconds_provider=lambda: 10,
        has_pending_requests=lambda _user_id: False,
        trigger_fulfillment=lambda user_id: fulfilled_users.append(user_id),
        timer_factory=timer_factory,
    )

    assert coalescer.schedule("user-2") == "skipped"
    assert timer_factory.created_timers == []
    assert fulfilled_users == []


def test_extend_without_existing_timer_creates_new_schedule() -> None:
    timer_factory = _ManualTimerFactory()
    fulfilled_users: list[str] = []
    coalescer = WebhookCoalescer(
        coalesce_seconds_provider=lambda: 10,
        has_pending_requests=lambda _user_id: True,
        trigger_fulfillment=lambda user_id: fulfilled_users.append(user_id),
        timer_factory=timer_factory,
    )

    assert coalescer.extend("user-3") == "scheduled"
    assert len(timer_factory.created_timers) == 1
    assert fulfilled_users == []


def test_run_rechecks_pending_requests_before_triggering() -> None:
    pending_users = {"user-4"}
    timer_factory = _ManualTimerFactory()
    fulfilled_users: list[str] = []
    coalescer = WebhookCoalescer(
        coalesce_seconds_provider=lambda: 10,
        has_pending_requests=lambda user_id: user_id in pending_users,
        trigger_fulfillment=lambda user_id: fulfilled_users.append(user_id),
        timer_factory=timer_factory,
    )

    assert coalescer.schedule("user-4") == "scheduled"
    pending_users.clear()

    timer_factory.created_timers[0].fire()
    assert fulfilled_users == []
