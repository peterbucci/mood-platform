from __future__ import annotations

import json
import logging
import os
import signal
import uuid
from datetime import UTC
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_database_url_from_env
from app.repositories.feature_request_repository import FeatureRequestRepository
from app.repositories.worker_lock_repository import WorkerLockRepository
from app.services.fitbit_data_client import build_fitbit_client
from app.services.request_fulfillment_service import FitbitClientProtocol, RequestFulfillmentService
from app.services.worker_runtime import WorkerRuntime

logger = logging.getLogger(__name__)

DEFAULT_WORKER_BASE_IDLE_SLEEP_SECONDS = 1.0
DEFAULT_WORKER_MAX_IDLE_SLEEP_SECONDS = 5.0
DEFAULT_WORKER_BACKOFF_MULTIPLIER = 2.0
DEFAULT_WORKER_USER_BATCH_SIZE = 100
DEFAULT_WORKER_REQUEST_BATCH_SIZE = 100
DEFAULT_WORKER_LOCK_TTL_SECONDS = 30.0
DEFAULT_WORKER_LOCK_PREFIX = "fulfillment_lock"
DEFAULT_WORKER_HEALTH_HOST = "0.0.0.0"
DEFAULT_WORKER_HEALTH_PORT = 3001


class WorkerHealthServer:
    def __init__(
        self,
        *,
        runtime: WorkerRuntime,
        host: str = DEFAULT_WORKER_HEALTH_HOST,
        port: int = DEFAULT_WORKER_HEALTH_PORT,
    ) -> None:
        self._runtime = runtime
        self._host = host
        self._port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def bound_port(self) -> int:
        if self._server is None:
            return self._port
        return int(self._server.server_address[1])

    def start(self) -> None:
        runtime = self._runtime

        class _HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path != "/healthz":
                    self.send_response(404)
                    self.end_headers()
                    return

                last_loop_at = runtime.last_loop_at
                payload = {
                    "status": "shutting_down" if runtime.shutdown_requested else "ok",
                    "shutting_down": runtime.shutdown_requested,
                    "in_flight": runtime.in_flight,
                    "last_loop_at": (
                        last_loop_at.astimezone(UTC).isoformat()
                        if last_loop_at is not None
                        else None
                    ),
                }
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format: str, *_args: Any) -> None:
                return

        self._server = ThreadingHTTPServer((self._host, self._port), _HealthHandler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info("Worker health server started on %s:%s", self._host, self.bound_port)

    def stop(self) -> None:
        if self._server is None:
            return

        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
        logger.info("Worker health server stopped.")
        self._server = None
        self._thread = None


def build_session_factory() -> sessionmaker[Session]:
    engine = create_engine(get_database_url_from_env(), pool_pre_ping=True)
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


def process_pending_once(
    *,
    session_factory: sessionmaker[Session],
    fitbit_client: FitbitClientProtocol,
    user_batch_size: int,
    request_batch_size: int,
    lock_owner_id: str,
    lock_ttl_seconds: float,
    lock_prefix: str,
) -> int:
    with session_factory() as discovery_session:
        discovery_repository = FeatureRequestRepository(session=discovery_session)
        pending_user_ids = discovery_repository.list_pending_user_ids(limit=user_batch_size)

    if not pending_user_ids:
        logger.debug("No users with pending requests found.")
        return 0

    total_processed_requests = 0
    for user_id in pending_user_ids:
        lock_key = f"{lock_prefix}:{user_id}"
        with session_factory() as lock_session:
            lock_repository = WorkerLockRepository(session=lock_session)
            acquired = lock_repository.try_acquire(
                lock_key=lock_key,
                owner_id=lock_owner_id,
                ttl_seconds=lock_ttl_seconds,
            )

        if not acquired:
            logger.info(
                "Skipping user %s because lock %s is already held by another worker.",
                user_id,
                lock_key,
            )
            continue

        try:
            with session_factory() as work_session:
                request_repository = FeatureRequestRepository(session=work_session)
                service = RequestFulfillmentService(
                    repository=request_repository,
                    fitbit_client=fitbit_client,
                )
                user_stats = service.process_pending_requests_for_user(
                    user_id=user_id,
                    limit=request_batch_size,
                )
                total_processed_requests += user_stats.processed
                logger.info(
                    (
                        "Processed pending requests for user %s: processed=%s "
                        "fulfilled=%s skipped=%s failed=%s"
                    ),
                    user_id,
                    user_stats.processed,
                    user_stats.fulfilled,
                    user_stats.skipped,
                    user_stats.failed,
                )
        finally:
            with session_factory() as release_session:
                release_repository = WorkerLockRepository(session=release_session)
                released = release_repository.release(
                    lock_key=lock_key,
                    owner_id=lock_owner_id,
                )
                if not released:
                    logger.warning(
                        "Worker %s did not release lock %s (already expired or transferred).",
                        lock_owner_id,
                        lock_key,
                    )

    logger.info(
        "Worker iteration summary: pending_users=%s processed_requests=%s",
        len(pending_user_ids),
        total_processed_requests,
    )
    return total_processed_requests


def run_worker(
    *,
    session_factory: sessionmaker[Session],
    fitbit_client: FitbitClientProtocol,
    base_idle_sleep_seconds: float = DEFAULT_WORKER_BASE_IDLE_SLEEP_SECONDS,
    max_idle_sleep_seconds: float = DEFAULT_WORKER_MAX_IDLE_SLEEP_SECONDS,
    backoff_multiplier: float = DEFAULT_WORKER_BACKOFF_MULTIPLIER,
    user_batch_size: int = DEFAULT_WORKER_USER_BATCH_SIZE,
    request_batch_size: int = DEFAULT_WORKER_REQUEST_BATCH_SIZE,
    lock_owner_id: str,
    lock_ttl_seconds: float = DEFAULT_WORKER_LOCK_TTL_SECONDS,
    lock_prefix: str = DEFAULT_WORKER_LOCK_PREFIX,
    health_host: str = DEFAULT_WORKER_HEALTH_HOST,
    health_port: int = DEFAULT_WORKER_HEALTH_PORT,
) -> None:
    runtime = WorkerRuntime(
        run_once_fn=lambda: process_pending_once(
            session_factory=session_factory,
            fitbit_client=fitbit_client,
            user_batch_size=user_batch_size,
            request_batch_size=request_batch_size,
            lock_owner_id=lock_owner_id,
            lock_ttl_seconds=lock_ttl_seconds,
            lock_prefix=lock_prefix,
        ),
        base_idle_sleep_seconds=base_idle_sleep_seconds,
        max_idle_sleep_seconds=max_idle_sleep_seconds,
        backoff_multiplier=backoff_multiplier,
    )
    health_server = WorkerHealthServer(
        runtime=runtime,
        host=health_host,
        port=health_port,
    )

    def _handle_signal(signum: int, _frame: Any) -> None:
        logger.info("Received signal %s. Worker will shut down after in-flight iteration.", signum)
        runtime.request_shutdown()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info("Starting fulfillment worker loop.")
    health_server.start()
    try:
        runtime.run_forever()
        logger.info("Fulfillment worker exited cleanly.")
    finally:
        health_server.stop()


def _parse_env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        return float(raw_value)
    except ValueError:
        logger.warning("Invalid %s value '%s'; using default %s.", name, raw_value, default)
        return default


def _parse_env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError:
        logger.warning("Invalid %s value '%s'; using default %s.", name, raw_value, default)
        return default


def _get_lock_owner_id() -> str:
    configured_owner_id = os.getenv("WORKER_OWNER_ID", "").strip()
    if configured_owner_id:
        return configured_owner_id
    return f"worker-{uuid.uuid4()}"


def main() -> int:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    session_factory = build_session_factory()
    run_worker(
        session_factory=session_factory,
        fitbit_client=build_fitbit_client(session_factory=session_factory),
        base_idle_sleep_seconds=_parse_env_float(
            name="WORKER_BASE_IDLE_SLEEP_SECONDS",
            default=DEFAULT_WORKER_BASE_IDLE_SLEEP_SECONDS,
        ),
        max_idle_sleep_seconds=_parse_env_float(
            name="WORKER_MAX_IDLE_SLEEP_SECONDS",
            default=DEFAULT_WORKER_MAX_IDLE_SLEEP_SECONDS,
        ),
        backoff_multiplier=_parse_env_float(
            name="WORKER_BACKOFF_MULTIPLIER",
            default=DEFAULT_WORKER_BACKOFF_MULTIPLIER,
        ),
        user_batch_size=_parse_env_int(
            name="WORKER_USER_BATCH_SIZE",
            default=DEFAULT_WORKER_USER_BATCH_SIZE,
        ),
        request_batch_size=_parse_env_int(
            name="WORKER_REQUEST_BATCH_SIZE",
            default=DEFAULT_WORKER_REQUEST_BATCH_SIZE,
        ),
        lock_owner_id=_get_lock_owner_id(),
        lock_ttl_seconds=_parse_env_float(
            name="WORKER_LOCK_TTL_SECONDS",
            default=DEFAULT_WORKER_LOCK_TTL_SECONDS,
        ),
        lock_prefix=os.getenv("WORKER_LOCK_PREFIX", DEFAULT_WORKER_LOCK_PREFIX),
        health_host=os.getenv("WORKER_HEALTH_HOST", DEFAULT_WORKER_HEALTH_HOST),
        health_port=_parse_env_int(
            name="WORKER_HEALTH_PORT",
            default=DEFAULT_WORKER_HEALTH_PORT,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
