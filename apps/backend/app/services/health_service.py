import os
from typing import Protocol


class PostgresReadinessRepository(Protocol):
    def check_connection(self, database_url: str) -> str: ...


class RedisReadinessRepository(Protocol):
    def check_connection(self, redis_url: str) -> str: ...


class HealthService:
    def __init__(
        self,
        postgres_repository: PostgresReadinessRepository,
        redis_repository: RedisReadinessRepository,
    ) -> None:
        self._postgres_repository = postgres_repository
        self._redis_repository = redis_repository

    def get_liveness(self) -> dict[str, str]:
        return {"status": "alive"}

    def get_readiness(self) -> tuple[bool, dict[str, str]]:
        database_url = os.getenv("DATABASE_URL", "").strip()
        redis_url = os.getenv("REDIS_URL", "").strip()

        checks: dict[str, str] = {}

        if not database_url:
            checks["postgres"] = "DATABASE_URL is not set"
        else:
            checks["postgres"] = self._postgres_repository.check_connection(database_url)

        if not redis_url:
            checks["redis"] = "REDIS_URL is not set"
        else:
            checks["redis"] = self._redis_repository.check_connection(redis_url)

        is_ready = checks.get("postgres") == "ok" and checks.get("redis") == "ok"
        return is_ready, checks
