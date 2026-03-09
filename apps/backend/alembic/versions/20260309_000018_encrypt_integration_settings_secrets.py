"""encrypt integration settings secrets at rest

Revision ID: 20260309_000018
Revises: 20260309_000017
Create Date: 2026-03-09 00:00:18.000000
"""

from __future__ import annotations

import os
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from cryptography.fernet import Fernet

revision: str = "20260309_000018"
down_revision: str | None = "20260309_000017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _normalize_secret(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    normalized_value = value.strip()
    if not normalized_value:
        return None

    return normalized_value


def _get_fernet(*, required: bool) -> Fernet | None:
    encryption_key = os.getenv("APP_SECRET_ENCRYPTION_KEY", "").strip()
    if not encryption_key:
        if required:
            raise RuntimeError(
                "APP_SECRET_ENCRYPTION_KEY is required to migrate encrypted integration secrets."
            )
        return None

    try:
        return Fernet(encryption_key.encode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise RuntimeError("APP_SECRET_ENCRYPTION_KEY must be a valid Fernet key.") from exc


def _encrypt_if_present(*, fernet: Fernet | None, value: object) -> str | None:
    normalized_value = _normalize_secret(value)
    if normalized_value is None:
        return None

    if fernet is None:
        raise RuntimeError(
            "APP_SECRET_ENCRYPTION_KEY is required to migrate encrypted integration secrets."
        )

    return fernet.encrypt(normalized_value.encode("utf-8")).decode("utf-8")


def upgrade() -> None:
    op.add_column(
        "integration_settings",
        sa.Column("fitbit_client_secret_encrypted", sa.Text(), nullable=True),
    )
    op.add_column(
        "integration_settings",
        sa.Column("fitbit_webhook_secret_encrypted", sa.Text(), nullable=True),
    )

    bind = op.get_bind()
    integration_settings = sa.table(
        "integration_settings",
        sa.column("id", sa.Integer()),
        sa.column("fitbit_client_secret", sa.Text()),
        sa.column("fitbit_webhook_secret", sa.Text()),
        sa.column("fitbit_client_secret_encrypted", sa.Text()),
        sa.column("fitbit_webhook_secret_encrypted", sa.Text()),
    )
    existing_rows = bind.execute(
        sa.select(
            integration_settings.c.id,
            integration_settings.c.fitbit_client_secret,
            integration_settings.c.fitbit_webhook_secret,
        )
    ).mappings()

    rows_to_encrypt = list(existing_rows)
    requires_key = any(
        _normalize_secret(row["fitbit_client_secret"])
        or _normalize_secret(row["fitbit_webhook_secret"])
        for row in rows_to_encrypt
    )
    fernet = _get_fernet(required=requires_key)

    for row in rows_to_encrypt:
        bind.execute(
            sa.update(integration_settings)
            .where(integration_settings.c.id == row["id"])
            .values(
                fitbit_client_secret_encrypted=_encrypt_if_present(
                    fernet=fernet,
                    value=row["fitbit_client_secret"],
                ),
                fitbit_webhook_secret_encrypted=_encrypt_if_present(
                    fernet=fernet,
                    value=row["fitbit_webhook_secret"],
                ),
            )
        )

    op.drop_column("integration_settings", "fitbit_client_secret")
    op.drop_column("integration_settings", "fitbit_webhook_secret")


def downgrade() -> None:
    op.add_column(
        "integration_settings",
        sa.Column("fitbit_webhook_secret", sa.Text(), nullable=True),
    )
    op.add_column(
        "integration_settings",
        sa.Column("fitbit_client_secret", sa.Text(), nullable=True),
    )

    bind = op.get_bind()
    integration_settings = sa.table(
        "integration_settings",
        sa.column("id", sa.Integer()),
        sa.column("fitbit_client_secret", sa.Text()),
        sa.column("fitbit_webhook_secret", sa.Text()),
        sa.column("fitbit_client_secret_encrypted", sa.Text()),
        sa.column("fitbit_webhook_secret_encrypted", sa.Text()),
    )
    existing_rows = bind.execute(
        sa.select(
            integration_settings.c.id,
            integration_settings.c.fitbit_client_secret_encrypted,
            integration_settings.c.fitbit_webhook_secret_encrypted,
        )
    ).mappings()

    rows_to_decrypt = list(existing_rows)
    requires_key = any(
        _normalize_secret(row["fitbit_client_secret_encrypted"])
        or _normalize_secret(row["fitbit_webhook_secret_encrypted"])
        for row in rows_to_decrypt
    )
    fernet = _get_fernet(required=requires_key)

    for row in rows_to_decrypt:
        client_secret = _normalize_secret(row["fitbit_client_secret_encrypted"])
        webhook_secret = _normalize_secret(row["fitbit_webhook_secret_encrypted"])
        bind.execute(
            sa.update(integration_settings)
            .where(integration_settings.c.id == row["id"])
            .values(
                fitbit_client_secret=(
                    fernet.decrypt(client_secret.encode("utf-8")).decode("utf-8")
                    if client_secret and fernet is not None
                    else None
                ),
                fitbit_webhook_secret=(
                    fernet.decrypt(webhook_secret.encode("utf-8")).decode("utf-8")
                    if webhook_secret and fernet is not None
                    else None
                ),
            )
        )

    op.drop_column("integration_settings", "fitbit_client_secret_encrypted")
    op.drop_column("integration_settings", "fitbit_webhook_secret_encrypted")
