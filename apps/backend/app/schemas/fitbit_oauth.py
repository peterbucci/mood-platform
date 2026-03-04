from datetime import datetime

from pydantic import BaseModel


class FitbitOAuthCallbackResponse(BaseModel):
    connected: bool
    expiresAt: datetime


class FitbitOAuthStatusResponse(BaseModel):
    connected: bool
    expiresAt: datetime | None


class FitbitOAuthUnlinkResponse(BaseModel):
    success: bool
