from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories.feature_request_repository import FeatureRequestRepository
from app.repositories.feature_set_repository import FeatureSetRepository
from app.repositories.mood_entry_repository import MoodEntryRepository
from app.repositories.postgres import PostgresRepository
from app.repositories.redis import RedisRepository
from app.services.feature_request_service import FeatureRequestService
from app.services.health_service import HealthService
from app.services.mood_entry_service import MoodEntryService, get_owner_user_id


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


def get_feature_request_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> FeatureRequestRepository:
    return FeatureRequestRepository(session=db_session)


def get_feature_request_service(
    feature_request_repository: Annotated[
        FeatureRequestRepository, Depends(get_feature_request_repository)
    ],
) -> FeatureRequestService:
    return FeatureRequestService(
        repository=feature_request_repository,
        owner_user_id=get_owner_user_id(),
    )


def get_mood_entry_service(
    mood_entry_repository: Annotated[MoodEntryRepository, Depends(get_mood_entry_repository)],
) -> MoodEntryService:
    return MoodEntryService(
        repository=mood_entry_repository,
        owner_user_id=get_owner_user_id(),
    )
