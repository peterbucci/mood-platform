from pydantic import BaseModel


class FeatureRequestResponse(BaseModel):
    requestId: str
    status: str
