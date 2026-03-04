from __future__ import annotations

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Feature, FeatureRequest

PENDING_STATUS = "pending"
PHONE_SOURCE = "phone"


class FeatureRequestWriteError(Exception):
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
