from __future__ import annotations

import json
import logging
import os
import signal
import uuid
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_database_url_from_env
from app.repositories.feature_request_repository import FeatureRequestRepository
from app.repositories.worker_lock_repository import WorkerLockRepository
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


class StaticFitbitClient(FitbitClientProtocol):
    def __init__(self) -> None:
        raw_payload = os.getenv("FITBIT_STATIC_PAYLOAD", "").strip()
        if not raw_payload:
            self._payload: dict[str, Any] = {}
            return

        try:
            parsed_payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            logger.warning("Invalid FITBIT_STATIC_PAYLOAD JSON; using empty payload.")
            self._payload = {}
            return

        if not isinstance(parsed_payload, dict):
            logger.warning(
                "FITBIT_STATIC_PAYLOAD must deserialize to an object; using empty payload."
            )
            self._payload = {}
            return

        self._payload = parsed_payload

    def fetch_user_data(self, *, user_id: str) -> dict[str, Any]:
        return dict(self._payload)


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

    def _handle_signal(signum: int, _frame: Any) -> None:
        logger.info("Received signal %s. Worker will shut down after in-flight iteration.", signum)
        runtime.request_shutdown()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info("Starting fulfillment worker loop.")
    runtime.run_forever()
    logger.info("Fulfillment worker exited cleanly.")


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
    run_worker(
        session_factory=build_session_factory(),
        fitbit_client=StaticFitbitClient(),
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
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
