"""finalize request/feature delete policy with explicit linked cleanup

Revision ID: 20260307_000016
Revises: 20260305_000015
Create Date: 2026-03-07 00:00:16.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260307_000016"
down_revision: str | None = "20260305_000015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM requests
        WHERE "featureId" IS NOT NULL
          AND NOT EXISTS (
            SELECT 1
            FROM features
            WHERE features.id = requests."featureId"
          )
        """
    )

    op.drop_constraint("ck_requests_feature_id_consistency", "requests", type_="check")
    op.create_check_constraint(
        "ck_requests_feature_id_consistency",
        "requests",
        "(status != 'pending' OR \"featureId\" IS NULL) "
        "AND (status != 'fulfilled' OR \"featureId\" IS NOT NULL) "
        "AND (status != 'canceled' OR \"featureId\" IS NULL)",
    )
    op.create_index("ix_requests_feature_id", "requests", ["featureId"], unique=False)
    op.create_foreign_key(
        "fk_requests_feature_id_features",
        "requests",
        "features",
        ["featureId"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_requests_feature_id_features", "requests", type_="foreignkey")
    op.drop_index("ix_requests_feature_id", table_name="requests")
    op.drop_constraint("ck_requests_feature_id_consistency", "requests", type_="check")
    op.create_check_constraint(
        "ck_requests_feature_id_consistency",
        "requests",
        "(status != 'pending' OR \"featureId\" IS NULL) "
        "AND (status != 'canceled' OR \"featureId\" IS NULL)",
    )
