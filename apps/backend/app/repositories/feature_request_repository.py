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
FULFILLED_STATUS = "fulfilled"
PHONE_SOURCE = "phone"


class FeatureRequestWriteError(Exception):
    pass


class FeatureRequestFulfillmentError(Exception):
    pass


class FeatureRequestRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def has_pending_requests_for_user(self, *, user_id: str) -> bool:
        pending_ready_filter = self._pending_ready_filter()
        pending_request = self._session.execute(
            sa.select(FeatureRequest.id)
            .where(
                FeatureRequest.user_id == user_id,
                FeatureRequest.status == PENDING_STATUS,
                FeatureRequest.feature_id.is_(None),
                pending_ready_filter,
            )
            .limit(1)
        ).scalar_one_or_none()
        return pending_request is not None

    def create_request(self, *, user_id: str) -> tuple[str, str]:
        return self.create_request_with_client_features(user_id=user_id, client_features=None)

    def create_request_with_client_features(
        self,
        *,
        user_id: str,
        client_features: dict[str, Any] | None,
    ) -> tuple[str, str]:
        request_id = str(uuid.uuid4())
        created_at = int(datetime.now(tz=UTC).timestamp())
        client_features_json = None
        if isinstance(client_features, dict):
            client_features_json = json.dumps(client_features)
        request = FeatureRequest(
            id=request_id,
            user_id=user_id,
            created_at=created_at,
            status=PENDING_STATUS,
            source=PHONE_SOURCE,
            client_features_json=client_features_json,
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
        pending_ready_filter = self._pending_ready_filter()
        result = self._session.execute(
            sa.select(FeatureRequest)
            .where(
                FeatureRequest.status == PENDING_STATUS,
                FeatureRequest.feature_id.is_(None),
                pending_ready_filter,
            )
            .order_by(FeatureRequest.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    def list_pending_user_ids(self, *, limit: int = 100) -> list[str]:
        pending_ready_filter = self._pending_ready_filter()
        result = self._session.execute(
            sa.select(FeatureRequest.user_id)
            .where(
                FeatureRequest.status == PENDING_STATUS,
                FeatureRequest.feature_id.is_(None),
                pending_ready_filter,
            )
            .group_by(FeatureRequest.user_id)
            .order_by(sa.func.min(FeatureRequest.created_at).asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    def list_pending_requests_by_user(
        self, *, user_id: str, limit: int = 100
    ) -> list[FeatureRequest]:
        pending_ready_filter = self._pending_ready_filter()
        result = self._session.execute(
            sa.select(FeatureRequest)
            .where(
                FeatureRequest.user_id == user_id,
                FeatureRequest.status == PENDING_STATUS,
                FeatureRequest.feature_id.is_(None),
                pending_ready_filter,
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

    def get_request_by_id_for_user(self, *, user_id: str, request_id: str) -> FeatureRequest | None:
        result = self._session.execute(
            sa.select(FeatureRequest).where(
                FeatureRequest.id == request_id,
                FeatureRequest.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    def count_pending_requests(self, *, user_id: str | None = None) -> int:
        query = (
            sa.select(sa.func.count())
            .select_from(FeatureRequest)
            .where(FeatureRequest.status == PENDING_STATUS)
        )
        if user_id is not None:
            query = query.where(FeatureRequest.user_id == user_id)
        count = self._session.execute(query).scalar_one()
        return int(count or 0)

    def fulfill_request_if_pending(
        self,
        *,
        request_id: str,
        user_id: str,
        feature_source: str,
        feature_payload: dict[str, Any],
        source_timezone: str | None = None,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
    ) -> str | None:
        feature_id = str(uuid.uuid4())
        created_at = int(datetime.now(tz=UTC).timestamp())
        feature = Feature(
            id=feature_id,
            user_id=user_id,
            created_at=created_at,
            source=feature_source,
            data=json.dumps(feature_payload),
            source_timezone=source_timezone,
            window_start=window_start,
            window_end=window_end,
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
                .values(
                    status=FULFILLED_STATUS,
                    feature_id=feature_id,
                    attempts=0,
                    next_attempt_at=None,
                    last_error_code=None,
                    last_error_signal=None,
                )
            )
            if update_result.rowcount != 1:
                self._session.rollback()
                return None

            self._session.commit()
            return feature_id
        except IntegrityError as exc:
            self._session.rollback()
            raise FeatureRequestFulfillmentError("Failed to fulfill feature request.") from exc

    def schedule_retry_if_pending(
        self,
        *,
        request_id: str,
        user_id: str,
        delay_seconds: float,
        error_code: int | None,
        error_signal: str | None,
    ) -> bool:
        now_ts = int(datetime.now(tz=UTC).timestamp())
        clamped_delay_seconds = max(1, int(delay_seconds))
        next_attempt_at = now_ts + clamped_delay_seconds

        try:
            update_result = self._session.execute(
                sa.update(FeatureRequest)
                .where(
                    FeatureRequest.id == request_id,
                    FeatureRequest.user_id == user_id,
                    FeatureRequest.status == PENDING_STATUS,
                    FeatureRequest.feature_id.is_(None),
                )
                .values(
                    attempts=sa.func.coalesce(FeatureRequest.attempts, 0) + 1,
                    next_attempt_at=next_attempt_at,
                    last_error_code=error_code,
                    last_error_signal=error_signal,
                )
            )
            self._session.commit()
            return update_result.rowcount == 1
        except IntegrityError as exc:
            self._session.rollback()
            raise FeatureRequestFulfillmentError("Failed to schedule request retry.") from exc

    @staticmethod
    def _pending_ready_filter() -> sa.ColumnElement[bool]:
        now_ts = int(datetime.now(tz=UTC).timestamp())
        return sa.or_(
            FeatureRequest.next_attempt_at.is_(None),
            FeatureRequest.next_attempt_at <= now_ts,
        )
