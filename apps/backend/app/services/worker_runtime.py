from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from time import sleep


class WorkerRuntime:
    def __init__(
        self,
        run_once_fn: Callable[[], int],
        *,
        idle_sleep_seconds: float = 1.0,
        sleep_fn: Callable[[float], None] = sleep,
    ) -> None:
        self._run_once_fn = run_once_fn
        self._idle_sleep_seconds = idle_sleep_seconds
        self._sleep = sleep_fn
        self._shutdown_requested = False
        self.in_flight = False
        self.last_loop_at: datetime | None = None

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    def request_shutdown(self) -> None:
        self._shutdown_requested = True

    def run_once(self) -> int:
        self.last_loop_at = datetime.now(tz=UTC)
        self.in_flight = True
        try:
            return self._run_once_fn()
        finally:
            self.in_flight = False

    def run_forever(self) -> None:
        while not self._shutdown_requested:
            processed_count = self.run_once()
            if self._shutdown_requested:
                break
            if processed_count == 0:
                self._sleep(self._idle_sleep_seconds)
