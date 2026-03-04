from __future__ import annotations

from dataclasses import dataclass

from app.settings import Settings


class FitbitOAuthConfigurationError(Exception):
    pass


class FitbitOAuthExchangeError(Exception):
    pass


@dataclass(frozen=True)
class FitbitTokenPayload:
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str
    user_id: str


class FitbitOAuthService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_authorization_url(self, *, state: str) -> str:
        self._assert_oauth_configured()
        query = self._settings.fitbit_authorization_query(state=state)
        return f"{self._settings.FITBIT_AUTH_BASE_URL}?{query}"

    def exchange_authorization_code(self, *, code: str) -> FitbitTokenPayload:
        raise NotImplementedError("Token exchange will be implemented in a follow-up commit.")

    @staticmethod
    def parse_token_payload(payload: dict[str, object]) -> FitbitTokenPayload:
        try:
            access_token = str(payload["access_token"])
            refresh_token = str(payload["refresh_token"])
            expires_in = int(payload["expires_in"])
            scope = str(payload["scope"])
            user_id = str(payload["user_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise FitbitOAuthExchangeError("Invalid token payload returned by Fitbit.") from exc

        if not access_token or not refresh_token or not user_id:
            raise FitbitOAuthExchangeError("Token payload is missing required token values.")

        return FitbitTokenPayload(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            scope=scope,
            user_id=user_id,
        )

    def _assert_oauth_configured(self) -> None:
        if (
            not self._settings.FITBIT_CLIENT_ID
            or not self._settings.FITBIT_CLIENT_SECRET
            or not self._settings.FITBIT_REDIRECT_URI
        ):
            raise FitbitOAuthConfigurationError(
                "Fitbit OAuth is not configured. Set FITBIT_CLIENT_ID, "
                "FITBIT_CLIENT_SECRET, and FITBIT_REDIRECT_URI."
            )
