from fastapi import FastAPI

from app.api.feature_requests import router as feature_requests_router
from app.api.features import router as features_router
from app.api.fitbit_oauth import router as fitbit_oauth_router
from app.api.fitbit_webhook import router as fitbit_webhook_router
from app.api.health import router as health_router
from app.api.moods import router as moods_router
from app.api.requests import router as requests_router
from app.middleware.raw_body import RawBodyMiddleware

app = FastAPI(title="Mood Platform API")
app.add_middleware(RawBodyMiddleware)
app.include_router(health_router)
app.include_router(moods_router)
app.include_router(feature_requests_router)
app.include_router(features_router)
app.include_router(requests_router)
app.include_router(fitbit_oauth_router)
app.include_router(fitbit_webhook_router)
