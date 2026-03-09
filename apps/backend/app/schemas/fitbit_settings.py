from pydantic import BaseModel


class FitbitSettingsResponse(BaseModel):
    clientId: str
    clientSecretMasked: str | None = None
    redirectUri: str
    scope: str
    subscriberId: str
    webhookSecretMasked: str | None = None
    hasClientSecret: bool = False
    hasWebhookSecret: bool = False


class FitbitSettingsUpdateRequest(BaseModel):
    clientId: str
    clientSecret: str | None = None
    redirectUri: str
    scope: str | None = None
    subscriberId: str | None = None
    webhookSecret: str | None = None
