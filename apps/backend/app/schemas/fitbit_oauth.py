from datetime import datetime

from pydantic import BaseModel


class FitbitOAuthCallbackResponse(BaseModel):
    connected: bool
    expiresAt: datetime
