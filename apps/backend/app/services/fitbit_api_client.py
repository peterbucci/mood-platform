from __future__ import annotations

import uuid
from typing import Any

import httpx

from app.services.fitbit_token_service import FitbitTokenService


class FitbitApiClient:
    def __init__(
        self,
        *,
        token_service: FitbitTokenService,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._token_service = token_service
        self._http_client = http_client

    def fitbit_fetch(
        self,
        *,
        user_id: uuid.UUID,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        timeout: float = 10.0,
    ) -> httpx.Response:
        access_token = self._token_service.get_access_token(user_id=user_id)
        response = self._request(
            method=method,
            url=url,
            access_token=access_token,
            headers=headers,
            params=params,
            json_payload=json_payload,
            data=data,
            timeout=timeout,
        )
        if response.status_code != 401:
            return response

        self._token_service.refresh_token(user_id=user_id)
        refreshed_access_token = self._token_service.get_access_token(user_id=user_id)
        return self._request(
            method=method,
            url=url,
            access_token=refreshed_access_token,
            headers=headers,
            params=params,
            json_payload=json_payload,
            data=data,
            timeout=timeout,
        )

    # Compatibility helper matching the story contract naming.
    def fitbitFetch(  # noqa: N802
        self,
        *,
        user_id: uuid.UUID,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        timeout: float = 10.0,
    ) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=url,
            method=method,
            headers=headers,
            params=params,
            json_payload=json_payload,
            data=data,
            timeout=timeout,
        )

    def _request(
        self,
        *,
        method: str,
        url: str,
        access_token: str,
        headers: dict[str, str] | None,
        params: dict[str, Any] | None,
        json_payload: dict[str, Any] | None,
        data: dict[str, Any] | None,
        timeout: float,
    ) -> httpx.Response:
        request_headers = dict(headers or {})
        request_headers["Authorization"] = f"Bearer {access_token}"

        if self._http_client is not None:
            return self._http_client.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                json=json_payload,
                data=data,
                timeout=timeout,
            )

        with httpx.Client(timeout=timeout) as client:
            return client.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                json=json_payload,
                data=data,
            )
