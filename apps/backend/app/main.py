from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.moods import router as moods_router

app = FastAPI(title="Mood Platform API")
app.include_router(health_router)
app.include_router(moods_router)
