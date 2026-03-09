from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken


class EncryptionServiceConfigurationError(Exception):
    pass


class EncryptionServiceDecryptError(Exception):
    pass


class EncryptionService:
    def __init__(self, *, encryption_key: str) -> None:
        normalized_key = encryption_key.strip()
        if not normalized_key:
            raise EncryptionServiceConfigurationError(
                "APP_SECRET_ENCRYPTION_KEY is required for encrypted integration settings."
            )

        try:
            self._fernet = Fernet(normalized_key.encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise EncryptionServiceConfigurationError(
                "APP_SECRET_ENCRYPTION_KEY must be a valid Fernet key."
            ) from exc

    def encrypt_value(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt_value(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except (InvalidToken, ValueError, TypeError) as exc:
            raise EncryptionServiceDecryptError(
                "Failed to decrypt encrypted integration secret."
            ) from exc


@lru_cache
def build_encryption_service(encryption_key: str) -> EncryptionService:
    return EncryptionService(encryption_key=encryption_key)


def mask_secret(secret: str | None) -> str | None:
    if not isinstance(secret, str):
        return None

    normalized_secret = secret.strip()
    if not normalized_secret:
        return None

    if len(normalized_secret) <= 4:
        return "*" * len(normalized_secret)

    return f"********{normalized_secret[-4:]}"
