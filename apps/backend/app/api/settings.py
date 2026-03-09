from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_fitbit_integration_settings_service
from app.schemas.fitbit_settings import FitbitSettingsResponse, FitbitSettingsUpdateRequest
from app.services.fitbit_integration_settings_service import (
    FitbitIntegrationSettingsService,
    FitbitIntegrationSettingsServiceError,
    FitbitIntegrationSettingsValidationError,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/fitbit", response_model=FitbitSettingsResponse)
def get_fitbit_settings(
    fitbit_settings_service: Annotated[
        FitbitIntegrationSettingsService, Depends(get_fitbit_integration_settings_service)
    ],
) -> FitbitSettingsResponse:
    try:
        settings_view = fitbit_settings_service.get_settings_view()
    except FitbitIntegrationSettingsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return FitbitSettingsResponse(
        clientId=settings_view.client_id,
        clientSecretMasked=settings_view.client_secret_masked,
        redirectUri=settings_view.redirect_uri,
        scope=settings_view.scope,
        subscriberId=settings_view.subscriber_id,
        webhookSecretMasked=settings_view.webhook_secret_masked,
        hasClientSecret=settings_view.has_client_secret,
        hasWebhookSecret=settings_view.has_webhook_secret,
    )


@router.put("/fitbit", response_model=FitbitSettingsResponse)
def update_fitbit_settings(
    payload: FitbitSettingsUpdateRequest,
    fitbit_settings_service: Annotated[
        FitbitIntegrationSettingsService, Depends(get_fitbit_integration_settings_service)
    ],
) -> FitbitSettingsResponse:
    try:
        settings_view = fitbit_settings_service.upsert_settings(
            client_id=payload.clientId,
            client_secret=payload.clientSecret,
            redirect_uri=payload.redirectUri,
            scope=payload.scope,
            subscriber_id=payload.subscriberId,
            webhook_secret=payload.webhookSecret,
        )
    except FitbitIntegrationSettingsValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "Invalid Fitbit integration settings.",
                "errors": exc.errors,
            },
        ) from exc
    except FitbitIntegrationSettingsServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return FitbitSettingsResponse(
        clientId=settings_view.client_id,
        clientSecretMasked=settings_view.client_secret_masked,
        redirectUri=settings_view.redirect_uri,
        scope=settings_view.scope,
        subscriberId=settings_view.subscriber_id,
        webhookSecretMasked=settings_view.webhook_secret_masked,
        hasClientSecret=settings_view.has_client_secret,
        hasWebhookSecret=settings_view.has_webhook_secret,
    )
