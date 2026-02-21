import os

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis import Redis

app = FastAPI(title="Mood Platform API")


def check_postgres(database_url: str) -> tuple[bool, str]:
    try:
        with psycopg.connect(database_url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return True, "ok"
    except Exception as exc:
        return False, f"postgres check failed: {exc}"


def check_redis(redis_url: str) -> tuple[bool, str]:
    try:
        client = Redis.from_url(redis_url, socket_connect_timeout=3, socket_timeout=3)
        try:
            client.ping()
        finally:
            client.close()
        return True, "ok"
    except Exception as exc:
        return False, f"redis check failed: {exc}"


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def health_ready() -> JSONResponse | dict[str, object]:
    database_url = os.getenv("DATABASE_URL", "").strip()
    redis_url = os.getenv("REDIS_URL", "").strip()

    checks: dict[str, str] = {}

    if not database_url:
        checks["postgres"] = "DATABASE_URL is not set"
    else:
        postgres_ok, postgres_details = check_postgres(database_url)
        checks["postgres"] = postgres_details

    if not redis_url:
        checks["redis"] = "REDIS_URL is not set"
    else:
        redis_ok, redis_details = check_redis(redis_url)
        checks["redis"] = redis_details

    is_ready = checks.get("postgres") == "ok" and checks.get("redis") == "ok"
    if is_ready:
        return {"status": "ready", "checks": checks}

    return JSONResponse(status_code=503, content={"status": "not_ready", "checks": checks})
