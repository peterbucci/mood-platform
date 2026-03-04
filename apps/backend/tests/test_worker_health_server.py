from __future__ import annotations

import json
from urllib.request import urlopen

from app.services.worker_runtime import WorkerRuntime
from app.worker import WorkerHealthServer


def test_worker_health_server_exposes_loop_state() -> None:
    runtime = WorkerRuntime(run_once_fn=lambda: 0)
    health_server = WorkerHealthServer(runtime=runtime, host="127.0.0.1", port=0)
    health_server.start()

    try:
        runtime.run_once()
        with urlopen(  # noqa: S310
            f"http://127.0.0.1:{health_server.bound_port}/healthz",
            timeout=2,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))

        assert response.status == 200
        assert payload["status"] == "ok"
        assert payload["shutting_down"] is False
        assert payload["in_flight"] is False
        assert payload["last_loop_at"] is not None

        runtime.request_shutdown()
        with urlopen(  # noqa: S310
            f"http://127.0.0.1:{health_server.bound_port}/healthz",
            timeout=2,
        ) as response:
            shutting_down_payload = json.loads(response.read().decode("utf-8"))

        assert response.status == 200
        assert shutting_down_payload["status"] == "shutting_down"
        assert shutting_down_payload["shutting_down"] is True
    finally:
        health_server.stop()
