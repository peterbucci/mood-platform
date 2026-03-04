from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import FeatureRequest

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
