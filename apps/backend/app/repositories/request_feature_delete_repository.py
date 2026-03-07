from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Feature, FeatureRequest, Label


class RequestFeatureDeleteWriteError(Exception):
    pass


@dataclass(frozen=True)
class RequestFeatureDeleteResult:
    deleted_feature_id: str | None
    deleted_request_ids: tuple[str, ...]


@dataclass(frozen=True)
class _DeletePlan:
    feature_id: str | None
    request_ids: tuple[str, ...]


class RequestFeatureDeleteRepository:
    """Delete one connected request/feature/label unit in a single transaction.

    The policy is intentionally symmetric:
    - deleting a request deletes its linked feature snapshot and labels
    - deleting a feature deletes its linked request rows and labels
    - legacy cases with multiple requests linked to one feature are cleaned up as one unit
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def delete_unit_by_request_id(
        self,
        *,
        user_id: str,
        request_id: str,
        commit: bool = True,
    ) -> RequestFeatureDeleteResult | None:
        """Delete the connected unit reached from a request id, or return None if missing."""
        plan = self._build_delete_plan_for_request(user_id=user_id, request_id=request_id)
        if plan is None:
            return None

        return self._execute_delete_plan(user_id=user_id, plan=plan, commit=commit)

    def delete_unit_by_feature_id(
        self,
        *,
        user_id: str,
        feature_id: str,
        commit: bool = True,
    ) -> RequestFeatureDeleteResult | None:
        """Delete the connected unit reached from a feature id, or return None if missing."""
        plan = self._build_delete_plan_for_feature(user_id=user_id, feature_id=feature_id)
        if plan is None:
            return None

        return self._execute_delete_plan(user_id=user_id, plan=plan, commit=commit)

    def _build_delete_plan_for_request(
        self,
        *,
        user_id: str,
        request_id: str,
    ) -> _DeletePlan | None:
        request_row = self._session.execute(
            sa.select(FeatureRequest.id, FeatureRequest.feature_id)
            .where(
                FeatureRequest.user_id == user_id,
                FeatureRequest.id == request_id,
            )
            .with_for_update()
        ).one_or_none()
        if request_row is None:
            return None

        feature_id = request_row.feature_id
        if feature_id is None:
            return _DeletePlan(feature_id=None, request_ids=(request_row.id,))

        request_ids = self._load_request_ids_for_feature(user_id=user_id, feature_id=feature_id)
        if request_row.id not in request_ids:
            request_ids = (*request_ids, request_row.id)

        return _DeletePlan(feature_id=feature_id, request_ids=tuple(sorted(set(request_ids))))

    def _build_delete_plan_for_feature(
        self,
        *,
        user_id: str,
        feature_id: str,
    ) -> _DeletePlan | None:
        feature_row = self._session.execute(
            sa.select(Feature.id)
            .where(
                Feature.user_id == user_id,
                Feature.id == feature_id,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if feature_row is None:
            return None

        request_ids = self._load_request_ids_for_feature(user_id=user_id, feature_id=feature_id)
        return _DeletePlan(feature_id=feature_id, request_ids=request_ids)

    def _load_request_ids_for_feature(self, *, user_id: str, feature_id: str) -> tuple[str, ...]:
        result = self._session.execute(
            sa.select(FeatureRequest.id)
            .where(
                FeatureRequest.user_id == user_id,
                FeatureRequest.feature_id == feature_id,
            )
            .with_for_update()
        )
        return tuple(result.scalars().all())

    def _execute_delete_plan(
        self,
        *,
        user_id: str,
        plan: _DeletePlan,
        commit: bool,
    ) -> RequestFeatureDeleteResult:
        label_filters: list[sa.ColumnElement[bool]] = []
        if plan.request_ids:
            label_filters.append(Label.request_id.in_(plan.request_ids))
        if plan.feature_id is not None:
            label_filters.append(Label.feature_id == plan.feature_id)

        try:
            if label_filters:
                self._session.execute(
                    sa.delete(Label).where(
                        Label.user_id == user_id,
                        sa.or_(*label_filters),
                    )
                )

            if plan.request_ids:
                self._session.execute(
                    sa.delete(FeatureRequest).where(
                        FeatureRequest.user_id == user_id,
                        FeatureRequest.id.in_(plan.request_ids),
                    )
                )

            if plan.feature_id is not None:
                self._session.execute(
                    sa.delete(Feature).where(
                        Feature.user_id == user_id,
                        Feature.id == plan.feature_id,
                    )
                )

            if commit:
                self._session.commit()

            return RequestFeatureDeleteResult(
                deleted_feature_id=plan.feature_id,
                deleted_request_ids=plan.request_ids,
            )
        except IntegrityError as exc:
            self._session.rollback()
            raise RequestFeatureDeleteWriteError(
                "Failed to delete linked request/feature records."
            ) from exc
