from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Feature, FeatureRequest

PENDING_STATUS = "pending"
PHONE_SOURCE = "phone"


class FeatureRequestWriteError(Exception):
    pass


class FeatureRequestFulfillmentError(Exception):
    pass


class FeatureRequestRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_request(self, *, user_id: str) -> tuple[str, str]:
        request_id = str(uuid.uuid4())
        created_at = int(datetime.now(tz=UTC).timestamp())
        request = FeatureRequest(
            id=request_id,
            user_id=user_id,
            created_at=created_at,
            status=PENDING_STATUS,
            source=PHONE_SOURCE,
        )

        try:
            self._session.add(request)
            self._session.commit()
            return request.id, request.status
        except IntegrityError as exc:
            self._session.rollback()
            raise FeatureRequestWriteError("Failed to create feature request.") from exc

    def list_requests(
        self,
        *,
        user_id: str,
        limit: int,
        offset: int,
    ) -> list[tuple[FeatureRequest, Feature | None]]:
        result = self._session.execute(
            sa.select(FeatureRequest, Feature)
            .outerjoin(
                Feature,
                sa.and_(
                    Feature.id == FeatureRequest.feature_id,
                    Feature.user_id == FeatureRequest.user_id,
                ),
            )
            .where(FeatureRequest.user_id == user_id)
            .order_by(FeatureRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [(row[0], row[1]) for row in result.all()]

    def list_pending_requests(self, *, limit: int = 100) -> list[FeatureRequest]:
        result = self._session.execute(
            sa.select(FeatureRequest)
            .where(
                FeatureRequest.status == PENDING_STATUS,
                FeatureRequest.feature_id.is_(None),
            )
            .order_by(FeatureRequest.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    def list_pending_user_ids(self, *, limit: int = 100) -> list[str]:
        result = self._session.execute(
            sa.select(FeatureRequest.user_id)
            .where(
                FeatureRequest.status == PENDING_STATUS,
                FeatureRequest.feature_id.is_(None),
            )
            .group_by(FeatureRequest.user_id)
            .order_by(sa.func.min(FeatureRequest.created_at).asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    def list_pending_requests_by_user(
        self, *, user_id: str, limit: int = 100
    ) -> list[FeatureRequest]:
        result = self._session.execute(
            sa.select(FeatureRequest)
            .where(
                FeatureRequest.user_id == user_id,
                FeatureRequest.status == PENDING_STATUS,
                FeatureRequest.feature_id.is_(None),
            )
            .order_by(FeatureRequest.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    def get_request_by_id(self, *, request_id: str) -> FeatureRequest | None:
        result = self._session.execute(
            sa.select(FeatureRequest).where(FeatureRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    def fulfill_request_if_pending(
        self,
        *,
        request_id: str,
        user_id: str,
        feature_source: str,
        feature_payload: dict[str, Any],
    ) -> str | None:
        feature_id = str(uuid.uuid4())
        created_at = int(datetime.now(tz=UTC).timestamp())
        feature = Feature(
            id=feature_id,
            user_id=user_id,
            created_at=created_at,
            source=feature_source,
            data=json.dumps(feature_payload),
        )

        try:
            self._session.add(feature)
            update_result = self._session.execute(
                sa.update(FeatureRequest)
                .where(
                    FeatureRequest.id == request_id,
                    FeatureRequest.user_id == user_id,
                    FeatureRequest.status == PENDING_STATUS,
                    FeatureRequest.feature_id.is_(None),
                )
                .values(status="fulfilled", feature_id=feature_id)
            )
            if update_result.rowcount != 1:
                self._session.rollback()
                return None

            self._session.commit()
            return feature_id
        except IntegrityError as exc:
            self._session.rollback()
            raise FeatureRequestFulfillmentError("Failed to fulfill feature request.") from exc
