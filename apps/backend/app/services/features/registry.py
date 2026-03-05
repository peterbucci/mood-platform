from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FeatureFieldSpec:
    path: str
    required_if_inputs_present: bool
    missing_note: str
    description: str


class FeatureRegistry:
    """Declarative registry for required/optional feature outputs and notes."""

    def __init__(self, *, fields: list[FeatureFieldSpec]) -> None:
        self._fields = fields

    @property
    def fields(self) -> list[FeatureFieldSpec]:
        return list(self._fields)

    def append_missing_notes(
        self,
        *,
        payload: dict[str, Any],
        notes: list[str],
    ) -> None:
        for field in self._fields:
            if not field.required_if_inputs_present:
                continue
            if _value_at_path(payload, field.path) is not None:
                continue
            if field.missing_note not in notes:
                notes.append(field.missing_note)


FEATURE_REGISTRY = FeatureRegistry(
    fields=[
        FeatureFieldSpec(
            path="derived.stepsLast60m",
            required_if_inputs_present=True,
            missing_note="missing_intraday_steps",
            description="Last-60m steps should be present when intraday steps are available.",
        ),
        FeatureFieldSpec(
            path="derived.hrNow",
            required_if_inputs_present=True,
            missing_note="missing_intraday_heart",
            description="Current HR should be present when intraday HR is available.",
        ),
        FeatureFieldSpec(
            path="derived.azmLast60m",
            required_if_inputs_present=True,
            missing_note="missing_intraday_azm",
            description="AZM windows should be present when intraday AZM is available.",
        ),
        FeatureFieldSpec(
            path="derived.caloriesOutLast3h",
            required_if_inputs_present=True,
            missing_note="missing_intraday_calories",
            description="Calorie windows should be present when intraday calories are available.",
        ),
    ]
)


def _value_at_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for token in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(token)
    return current
