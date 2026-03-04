from __future__ import annotations

from app.services.worker_runtime import WorkerRuntime


def test_runtime_stops_when_shutdown_requested() -> None:
    call_count = 0

    def run_once() -> int:
        nonlocal call_count
        call_count += 1
        runtime.request_shutdown()
        return 1

    runtime = WorkerRuntime(run_once_fn=run_once, base_idle_sleep_seconds=0.01)
    runtime.run_forever()

    assert call_count == 1
    assert runtime.shutdown_requested is True
    assert runtime.in_flight is False
    assert runtime.last_loop_at is not None


def test_runtime_idles_when_no_work() -> None:
    call_count = 0
    sleep_calls: list[float] = []

    def run_once() -> int:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            runtime.request_shutdown()
        return 0

    runtime = WorkerRuntime(
        run_once_fn=run_once,
        base_idle_sleep_seconds=0.25,
        max_idle_sleep_seconds=1.0,
        sleep_fn=lambda seconds: sleep_calls.append(seconds),
    )
    runtime.run_forever()

    assert call_count == 2
    assert sleep_calls == [0.25]


def test_runtime_applies_exponential_idle_backoff() -> None:
    call_count = 0
    sleep_calls: list[float] = []

    def run_once() -> int:
        nonlocal call_count
        call_count += 1
        if call_count == 4:
            runtime.request_shutdown()
        return 0

    runtime = WorkerRuntime(
        run_once_fn=run_once,
        base_idle_sleep_seconds=0.5,
        max_idle_sleep_seconds=2.0,
        backoff_multiplier=2.0,
        sleep_fn=lambda seconds: sleep_calls.append(seconds),
    )
    runtime.run_forever()

    assert call_count == 4
    assert sleep_calls == [0.5, 1.0, 2.0]
