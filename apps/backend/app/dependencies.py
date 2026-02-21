from typing import Annotated

from fastapi import Depends

from app.repositories.postgres import PostgresRepository
from app.repositories.redis import RedisRepository
from app.services.health_service import HealthService


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
