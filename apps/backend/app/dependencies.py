import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import session as db_session
from app.db.session import get_db_session
from app.repositories.feature_repository import FeatureRepository
from app.repositories.feature_request_repository import FeatureRequestRepository
from app.repositories.feature_set_repository import FeatureSetRepository
from app.repositories.fitbit_oauth_repository import FitbitOAuthRepository
from app.repositories.fitbit_token_repository import FitbitTokenRepository
from app.repositories.mood_entry_repository import MoodEntryRepository
from app.repositories.postgres import PostgresRepository
from app.repositories.redis import RedisRepository
from app.repositories.webhook_job_repository import WebhookJobRepository
from app.services.feature_request_service import FeatureRequestService
from app.services.feature_service import FeatureService
from app.services.fitbit_data_client import build_fitbit_client
from app.services.fitbit_oauth_service import FitbitOAuthService
from app.services.fitbit_token_service import FitbitTokenService
from app.services.fitbit_webhook_ingestion_service import FitbitWebhookIngestionService
from app.services.health_service import HealthService
from app.services.mood_entry_service import MoodEntryService, get_owner_user_id
from app.services.request_fulfillment_service import RequestFulfillmentService
from app.services.webhook_coalescer import WebhookCoalescer
from app.settings import get_settings

logger = logging.getLogger(__name__)


def get_postgres_repository() -> PostgresRepository:
    return PostgresRepository()


def get_redis_repository() -> RedisRepository:
    return RedisRepository()


def get_health_service(
    postgres_repository: Annotated[PostgresRepository, Depends(get_postgres_repository)],
    redis_repository: Annotated[RedisRepository, Depends(get_redis_repository)],
) -> HealthService:
    return HealthService(
        postgres_repository=postgres_repository,
        redis_repository=redis_repository,
    )


def get_mood_entry_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> MoodEntryRepository:
    return MoodEntryRepository(session=db_session)


def get_feature_set_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> FeatureSetRepository:
    return FeatureSetRepository(session=db_session)


def get_feature_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> FeatureRepository:
    return FeatureRepository(session=db_session)


def get_feature_request_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> FeatureRequestRepository:
    return FeatureRequestRepository(session=db_session)


def get_fitbit_oauth_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> FitbitOAuthRepository:
    return FitbitOAuthRepository(session=db_session)


def get_fitbit_token_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> FitbitTokenRepository:
    return FitbitTokenRepository(session=db_session)


def get_webhook_job_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> WebhookJobRepository:
    return WebhookJobRepository(session=db_session)


def _get_webhook_coalesce_seconds() -> int:
    return get_settings().FITBIT_WEBHOOK_COALESCE_SECONDS


def _has_pending_requests_for_user(user_id: str) -> bool:
    session_factory = db_session._session_factory()
    with session_factory() as session:
        repository = FeatureRequestRepository(session=session)
        return repository.has_pending_requests_for_user(user_id=user_id)


def _trigger_fulfillment_for_user(user_id: str) -> None:
    session_factory = db_session._session_factory()
    fitbit_client = build_fitbit_client(session_factory=session_factory)
    with session_factory() as session:
        repository = FeatureRequestRepository(session=session)
        service = RequestFulfillmentService(
            repository=repository,
            fitbit_client=fitbit_client,
        )
        stats = service.process_pending_requests_for_user(user_id=user_id)
        logger.debug(
            "Webhook coalescer fulfillment run completed.",
            extra={
                "user_id": user_id,
                "processed": stats.processed,
                "fulfilled": stats.fulfilled,
                "skipped": stats.skipped,
                "failed": stats.failed,
            },
        )


@lru_cache
def get_webhook_coalescer() -> WebhookCoalescer:
    return WebhookCoalescer(
        coalesce_seconds_provider=_get_webhook_coalesce_seconds,
        has_pending_requests=_has_pending_requests_for_user,
        trigger_fulfillment=_trigger_fulfillment_for_user,
    )


def get_feature_request_service(
    feature_request_repository: Annotated[
        FeatureRequestRepository, Depends(get_feature_request_repository)
    ],
) -> FeatureRequestService:
    return FeatureRequestService(
        repository=feature_request_repository,
        owner_user_id=get_owner_user_id(),
    )


def get_feature_service(
    feature_repository: Annotated[FeatureRepository, Depends(get_feature_repository)],
) -> FeatureService:
    return FeatureService(
        repository=feature_repository,
        owner_user_id=get_owner_user_id(),
    )


def get_mood_entry_service(
    mood_entry_repository: Annotated[MoodEntryRepository, Depends(get_mood_entry_repository)],
) -> MoodEntryService:
    return MoodEntryService(
        repository=mood_entry_repository,
        owner_user_id=get_owner_user_id(),
    )


def get_fitbit_token_service(
    fitbit_token_repository: Annotated[FitbitTokenRepository, Depends(get_fitbit_token_repository)],
) -> FitbitTokenService:
    return FitbitTokenService(
        repository=fitbit_token_repository,
        settings=get_settings(),
    )


def get_fitbit_oauth_service(
    fitbit_oauth_repository: Annotated[FitbitOAuthRepository, Depends(get_fitbit_oauth_repository)],
    fitbit_token_service: Annotated[FitbitTokenService, Depends(get_fitbit_token_service)],
) -> FitbitOAuthService:
    return FitbitOAuthService(
        state_repository=fitbit_oauth_repository,
        token_service=fitbit_token_service,
        settings=get_settings(),
    )


def get_fitbit_webhook_ingestion_service(
    fitbit_token_repository: Annotated[FitbitTokenRepository, Depends(get_fitbit_token_repository)],
    webhook_coalescer: Annotated[WebhookCoalescer, Depends(get_webhook_coalescer)],
) -> FitbitWebhookIngestionService:
    return FitbitWebhookIngestionService(
        fitbit_token_repository=fitbit_token_repository,
        webhook_coalescer=webhook_coalescer,
    )
