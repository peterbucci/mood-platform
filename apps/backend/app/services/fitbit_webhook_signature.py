from __future__ import annotations

import hashlib
import hmac


class FitbitWebhookSignatureVerifier:
    def __init__(self, *, webhook_secret: str) -> None:
        self._webhook_secret = webhook_secret.strip()

    def is_configured(self) -> bool:
        return bool(self._webhook_secret)

    def verify(self, *, raw_body: bytes, provided_signature: str) -> bool:
        if not self.is_configured():
            return False
        if not provided_signature.strip():
            return False

        expected_signature = self.build_signature(raw_body=raw_body)
        normalized_provided = provided_signature.strip().lower()
        return hmac.compare_digest(expected_signature, normalized_provided)

    def build_signature(self, *, raw_body: bytes) -> str:
        digest = hmac.new(
            self._webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        )
        return digest.hexdigest()
