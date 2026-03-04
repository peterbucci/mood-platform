"""Compatibility module so `uvicorn main:app` still works."""

from app.main import app

__all__ = ["app"]
