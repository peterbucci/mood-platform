from __future__ import annotations

import pytest
from app.services.encryption_service import (
    EncryptionServiceConfigurationError,
    EncryptionServiceDecryptError,
    build_encryption_service,
    mask_secret,
)

TEST_ENCRYPTION_KEY = "Qv2K-KSS7eDYAf9H2JWzImrxNr7AWyP3w7k3TKTKuig="


def test_encryption_service_round_trips_plaintext() -> None:
    service = build_encryption_service(TEST_ENCRYPTION_KEY)

    ciphertext = service.encrypt_value("fitbit-secret-1234")

    assert ciphertext != "fitbit-secret-1234"
    assert service.decrypt_value(ciphertext) == "fitbit-secret-1234"


def test_encryption_service_rejects_missing_key() -> None:
    with pytest.raises(EncryptionServiceConfigurationError):
        build_encryption_service("")


def test_encryption_service_rejects_invalid_ciphertext() -> None:
    service = build_encryption_service(TEST_ENCRYPTION_KEY)

    with pytest.raises(EncryptionServiceDecryptError):
        service.decrypt_value("not-a-valid-fernet-token")


def test_mask_secret_only_exposes_last_four_chars() -> None:
    assert mask_secret("fitbit-secret-1234") == "********1234"
    assert mask_secret("1234") == "****"
    assert mask_secret("") is None
