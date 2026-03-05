from __future__ import annotations

import random
import threading
import time
import uuid
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urljoin

import httpx

from app.services.fitbit_token_service import FitbitTokenService

DEFAULT_FITBIT_API_BASE_URL = "https://api.fitbit.com"


class FitbitApiClient:
    _throttle_lock = threading.Lock()
    _last_request_at_by_user: dict[str, float] = {}

    def __init__(
        self,
        *,
        token_service: FitbitTokenService,
        http_client: httpx.Client | None = None,
        api_base_url: str = DEFAULT_FITBIT_API_BASE_URL,
        min_fetch_interval_seconds: float = 0.0,
        max_retries: int = 0,
        backoff_base_seconds: float = 1.0,
        sleep_func=time.sleep,
        time_func=time.time,
        jitter_func=random.random,
    ) -> None:
        self._token_service = token_service
        self._http_client = http_client
        self._api_base_url = api_base_url.rstrip("/")
        self._min_fetch_interval_seconds = max(0.0, min_fetch_interval_seconds)
        self._max_retries = max(0, max_retries)
        self._backoff_base_seconds = max(0.1, backoff_base_seconds)
        self._sleep = sleep_func
        self._time = time_func
        self._jitter = jitter_func

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
        retried_401 = False
        retry_count = 0

        while True:
            self._throttle_for_user(user_id)
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
            if response.status_code == 401 and not retried_401:
                retried_401 = True
                self._token_service.refresh_token(user_id=user_id)
                access_token = self._token_service.get_access_token(user_id=user_id)
                continue

            if response.status_code != 429:
                return response

            if retry_count >= self._max_retries:
                return response
            retry_count += 1

            retry_delay = self._retry_delay_seconds(response=response, retry_count=retry_count)
            self._sleep(retry_delay)

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

    def fetch_activity_summary(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/activities/date/{date_iso}.json"),
        )

    def fetch_heart_rate(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/activities/heart/date/{date_iso}/1d.json"),
        )

    def fetch_sleep(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1.2/user/-/sleep/date/{date_iso}.json"),
        )

    def fetch_hrv(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/hrv/date/{date_iso}.json"),
        )

    def fetch_breathing_rate(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/br/date/{date_iso}.json"),
        )

    def fetch_spo2(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/spo2/date/{date_iso}.json"),
        )

    def fetch_skin_temperature(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/temp/skin/date/{date_iso}.json"),
        )

    def fetch_nutrition(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/foods/log/date/{date_iso}.json"),
        )

    def fetch_water_logs(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/foods/log/water/date/{date_iso}.json"),
        )

    def register_activity_subscription(
        self,
        *,
        user_id: uuid.UUID,
        subscription_id: str = "1",
        subscriber_id: str,
    ) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            method="POST",
            url=self._fitbit_url(f"/1/user/-/activities/apiSubscriptions/{subscription_id}.json"),
            headers={"X-Fitbit-Subscriber-Id": subscriber_id},
        )

    def fetch_intraday_steps(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/activities/steps/date/{date_iso}/1d/1min.json"),
        )

    def fetch_intraday_calories(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/activities/calories/date/{date_iso}/1d/1min.json"),
        )

    def fetch_intraday_active_zone_minutes(
        self,
        *,
        user_id: uuid.UUID,
        date_iso: str,
    ) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(
                f"/1/user/-/activities/active-zone-minutes/date/{date_iso}/1d/1min.json"
            ),
        )

    def fetch_intraday_heart_rate(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/activities/heart/date/{date_iso}/1d/1min.json"),
        )

    def fetch_latest_activity(
        self,
        *,
        user_id: uuid.UUID,
        before_date_iso: str,
    ) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url("/1/user/-/activities/list.json"),
            params={
                "beforeDate": before_date_iso,
                "sort": "desc",
                "offset": 0,
                "limit": 1,
            },
        )

    def fetch_steps_7d(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/activities/steps/date/{date_iso}/7d.json"),
        )

    def fetch_heart_rate_7d(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/activities/heart/date/{date_iso}/7d.json"),
        )

    def fetch_hrv_range(
        self,
        *,
        user_id: uuid.UUID,
        start_date_iso: str,
        end_date_iso: str,
    ) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/hrv/date/{start_date_iso}/{end_date_iso}.json"),
        )

    def fetch_hrv_all(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/hrv/date/{date_iso}/all.json"),
        )

    def fetch_sleep_range(
        self,
        *,
        user_id: uuid.UUID,
        start_date_iso: str,
        end_date_iso: str,
    ) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1.2/user/-/sleep/date/{start_date_iso}/{end_date_iso}.json"),
        )

    def fetch_breathing_rate_all(self, *, user_id: uuid.UUID, date_iso: str) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/br/date/{date_iso}/all.json"),
        )

    def fetch_breathing_rate_range(
        self,
        *,
        user_id: uuid.UUID,
        start_date_iso: str,
        end_date_iso: str,
    ) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/br/date/{start_date_iso}/{end_date_iso}.json"),
        )

    def fetch_spo2_range(
        self,
        *,
        user_id: uuid.UUID,
        start_date_iso: str,
        end_date_iso: str,
    ) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/spo2/date/{start_date_iso}/{end_date_iso}.json"),
        )

    def fetch_skin_temperature_range(
        self,
        *,
        user_id: uuid.UUID,
        start_date_iso: str,
        end_date_iso: str,
    ) -> httpx.Response:
        return self.fitbit_fetch(
            user_id=user_id,
            url=self._fitbit_url(f"/1/user/-/temp/skin/date/{start_date_iso}/{end_date_iso}.json"),
        )

    def _fitbit_url(self, path: str) -> str:
        return urljoin(f"{self._api_base_url}/", path.lstrip("/"))

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

    def _throttle_for_user(self, user_id: uuid.UUID) -> None:
        if self._min_fetch_interval_seconds <= 0:
            return

        user_key = str(user_id)
        with self._throttle_lock:
            now = self._time()
            last_request_at = self._last_request_at_by_user.get(user_key)
            if last_request_at is not None:
                elapsed = now - last_request_at
                remaining = self._min_fetch_interval_seconds - elapsed
                if remaining > 0:
                    self._sleep(remaining)
                    now = self._time()
            self._last_request_at_by_user[user_key] = now

    def _retry_delay_seconds(self, *, response: httpx.Response, retry_count: int) -> float:
        retry_after_delay = self._parse_retry_after_seconds(response=response)
        if retry_after_delay is not None:
            return retry_after_delay

        exponential_delay = self._backoff_base_seconds * (2 ** (retry_count - 1))
        jitter = self._jitter() * self._backoff_base_seconds
        return max(0.1, exponential_delay + jitter)

    def _parse_retry_after_seconds(self, *, response: httpx.Response) -> float | None:
        retry_after_value = response.headers.get("Retry-After")
        if not retry_after_value:
            return None

        retry_after_value = retry_after_value.strip()
        if not retry_after_value:
            return None

        try:
            seconds = float(retry_after_value)
            return max(0.0, seconds)
        except ValueError:
            pass

        try:
            retry_after_datetime = parsedate_to_datetime(retry_after_value)
        except (TypeError, ValueError):
            return None

        retry_after_timestamp = retry_after_datetime.timestamp()
        delay = retry_after_timestamp - self._time()
        return max(0.0, delay)
