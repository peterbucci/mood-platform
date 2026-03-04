from __future__ import annotations

import json
import logging
import os
import signal
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_database_url_from_env
from app.repositories.feature_request_repository import FeatureRequestRepository
from app.services.request_fulfillment_service import FitbitClientProtocol, RequestFulfillmentService
from app.services.worker_runtime import WorkerRuntime

logger = logging.getLogger(__name__)

DEFAULT_WORKER_IDLE_SLEEP_SECONDS = 1.0
DEFAULT_WORKER_BATCH_SIZE = 100


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
    batch_size: int,
) -> int:
    with session_factory() as session:
        repository = FeatureRequestRepository(session=session)
        service = RequestFulfillmentService(
            repository=repository,
            fitbit_client=fitbit_client,
        )
        stats = service.process_pending_requests(limit=batch_size)
        logger.info(
            "Worker iteration completed: processed=%s fulfilled=%s skipped=%s failed=%s",
            stats.processed,
            stats.fulfilled,
            stats.skipped,
            stats.failed,
        )
        return stats.processed


def run_worker(
    *,
    session_factory: sessionmaker[Session],
    fitbit_client: FitbitClientProtocol,
    idle_sleep_seconds: float = DEFAULT_WORKER_IDLE_SLEEP_SECONDS,
    batch_size: int = DEFAULT_WORKER_BATCH_SIZE,
) -> None:
    runtime = WorkerRuntime(
        run_once_fn=lambda: process_pending_once(
            session_factory=session_factory,
            fitbit_client=fitbit_client,
            batch_size=batch_size,
        ),
        idle_sleep_seconds=idle_sleep_seconds,
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


def main() -> int:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    run_worker(
        session_factory=build_session_factory(),
        fitbit_client=StaticFitbitClient(),
        idle_sleep_seconds=_parse_env_float(
            name="WORKER_IDLE_SLEEP_SECONDS",
            default=DEFAULT_WORKER_IDLE_SLEEP_SECONDS,
        ),
        batch_size=_parse_env_int(
            name="WORKER_BATCH_SIZE",
            default=DEFAULT_WORKER_BATCH_SIZE,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
