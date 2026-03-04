from fastapi import FastAPI

from app.api.feature_requests import router as feature_requests_router
from app.api.features import router as features_router
from app.api.health import router as health_router
from app.api.moods import router as moods_router

app = FastAPI(title="Mood Platform API")
app.include_router(health_router)
app.include_router(moods_router)
app.include_router(feature_requests_router)
app.include_router(features_router)
