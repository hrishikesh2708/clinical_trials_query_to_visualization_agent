"""Shared transform context and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.horizons import Horizon
from app.domain.visualization import TimeGranularity, VisualizationType
from app.infrastructure.ctgov.enums import CtgovEnums


@dataclass(frozen=True, slots=True)
class ComparisonArm:
    label: str
    studies: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class TransformContext:
    horizon: Horizon
    viz_type: VisualizationType
    studies: list[dict[str, Any]] = field(default_factory=list)
    comparison_arms: tuple[ComparisonArm, ...] = ()
    bucket_field: str = "phase"
    time_granularity: TimeGranularity = TimeGranularity.YEAR
    enums: CtgovEnums | None = None

    def effective_studies(self) -> list[dict[str, Any]]:
        return self.studies
