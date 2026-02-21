from fastapi import APIRouter, Response, status

from app.repositories.postgres import PostgresRepository
from app.repositories.redis import RedisRepository
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["health"])
health_service = HealthService(
    postgres_repository=PostgresRepository(),
    redis_repository=RedisRepository(),
)


@router.get("/live")
def health_live() -> dict[str, str]:
    return health_service.get_liveness()


@router.get("/ready")
def health_ready(response: Response) -> dict[str, object]:
    is_ready, checks = health_service.get_readiness()
    if is_ready:
        return {"status": "ready", "checks": checks}

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "not_ready", "checks": checks}
