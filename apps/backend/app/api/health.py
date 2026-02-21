from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_health_service
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def health_live(
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> dict[str, str]:
    return health_service.get_liveness()


@router.get("/ready")
def health_ready(
    response: Response,
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> dict[str, object]:
    is_ready, checks = health_service.get_readiness()
    if is_ready:
        return {"status": "ready", "checks": checks}

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "not_ready", "checks": checks}
