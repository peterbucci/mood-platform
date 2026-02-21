import os

import psycopg
from redis import Redis


class HealthService:
    def get_liveness(self) -> dict[str, str]:
        return {"status": "alive"}

    def get_readiness(self) -> tuple[bool, dict[str, str]]:
        database_url = os.getenv("DATABASE_URL", "").strip()
        redis_url = os.getenv("REDIS_URL", "").strip()

        checks: dict[str, str] = {}

        if not database_url:
            checks["postgres"] = "DATABASE_URL is not set"
        else:
            checks["postgres"] = self._check_postgres(database_url)

        if not redis_url:
            checks["redis"] = "REDIS_URL is not set"
        else:
            checks["redis"] = self._check_redis(redis_url)

        is_ready = checks.get("postgres") == "ok" and checks.get("redis") == "ok"
        return is_ready, checks

    def _check_postgres(self, database_url: str) -> str:
        try:
            with psycopg.connect(database_url, connect_timeout=3) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            return "ok"
        except Exception as exc:
            return f"postgres check failed: {exc}"

    def _check_redis(self, redis_url: str) -> str:
        try:
            client = Redis.from_url(redis_url, socket_connect_timeout=3, socket_timeout=3)
            try:
                client.ping()
            finally:
                client.close()
            return "ok"
        except Exception as exc:
            return f"redis check failed: {exc}"
