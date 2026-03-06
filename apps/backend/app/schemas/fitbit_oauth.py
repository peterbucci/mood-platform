from datetime import datetime

from pydantic import BaseModel


class FitbitOAuthCallbackResponse(BaseModel):
    connected: bool
    expiresAt: datetime


class FitbitOAuthStatusResponse(BaseModel):
    connected: bool
    expiresAt: datetime | None
    fitbitUserId: str | None = None
    scopes: list[str] | None = None
    lastSyncAt: datetime | None = None
    message: str | None = None


class FitbitOAuthUnlinkResponse(BaseModel):
    success: bool
