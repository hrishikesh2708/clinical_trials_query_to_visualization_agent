"""Comparison mapper: merge independent arm searches."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.core.schemas.visualization import (
    BarChartDataRow,
    BarChartVisualization,
    GroupedBarChartDataRow,
    GroupedBarChartVisualization,
)
from app.domain import models as study_models
from app.domain.visualization import VisualizationType, assert_never
from app.infrastructure.ctgov.enums import CtgovEnums
from app.services.citation_engine import (
    attach_citations,
    attach_citations_per_bucket,
    excerpt_phase,
    excerpt_phase_for_study,
)
from app.services.transform.base import TransformContext

UNKNOWN_PHASE_LABEL = "Unknown"


def _phase_label(enums: CtgovEnums | None, phase_code: str) -> str:
    if enums is None:
        return phase_code
    try:
        return enums.label_for("Phase", phase_code)
    except (KeyError, ValueError):
        return phase_code


def _phase_code_for_label(
    study: dict[str, Any],
    phase_label: str,
    enums: CtgovEnums | None,
) -> str | None:
    for code in study_models.phases(study):
        if _phase_label(enums, code) == phase_label:
            return code
    return None


def _phase_excerpt_for_label(
    study: dict[str, Any],
    phase_label: str,
    enums: CtgovEnums | None,
) -> str:
    if phase_label == UNKNOWN_PHASE_LABEL:
        return excerpt_phase_for_study(study)
    phase_code = _phase_code_for_label(study, phase_label, enums)
    if phase_code is None:
        return excerpt_phase_for_study(study)
    return excerpt_phase(study, phase_code)


def _phase_rows_for_arm(
    arm_label: str,
    studies: list[dict[str, Any]],
    enums: CtgovEnums | None,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for study in studies:
        phase_codes = study_models.phases(study)
        if not phase_codes:
            buckets[(UNKNOWN_PHASE_LABEL, arm_label)].append(study)
            continue
        for phase_code in phase_codes:
            label = _phase_label(enums, phase_code)
            buckets[(label, arm_label)].append(study)
    return buckets


def map_comparison(
    context: TransformContext,
) -> GroupedBarChartVisualization | BarChartVisualization:
    match context.viz_type:
        case VisualizationType.GROUPED_BAR_CHART:
            buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
            for arm in context.comparison_arms:
                arm_buckets = _phase_rows_for_arm(
                    arm.label,
                    arm.studies,
                    context.enums,
                )
                for key, studies in arm_buckets.items():
                    buckets[key].extend(studies)

            flat_buckets: dict[tuple[str, str], list[dict[str, Any]]] = {
                key: studies for key, studies in buckets.items()
            }
            citations_by_key = attach_citations_per_bucket(
                flat_buckets,
                excerpt_builder=lambda study, key: _phase_excerpt_for_label(
                    study, key[0], context.enums
                ),
            )

            rows = [
                GroupedBarChartDataRow(
                    phase=phase,
                    series=arm_label,
                    count=len(studies),
                    citations=citations_by_key[(phase, arm_label)],
                )
                for (phase, arm_label), studies in sorted(flat_buckets.items())
            ]
            return GroupedBarChartVisualization(
                encoding={"x": "phase", "y": "count", "series": "series"},
                data=rows,
            )
        case VisualizationType.BAR_CHART:
            buckets = {
                arm.label: arm.studies for arm in context.comparison_arms
            }
            citations_by_arm = attach_citations(
                buckets,
                excerpt_builder=excerpt_phase_for_study,
            )
            rows = [
                BarChartDataRow(
                    arm=arm_label,
                    count=len(studies),
                    citations=citations_by_arm[arm_label],
                )
                for arm_label, studies in context.comparison_arms
            ]
            rows.sort(key=lambda row: row.count, reverse=True)
            return BarChartVisualization(
                encoding={"x": "arm", "y": "count"},
                data=rows,
            )
        case _ as unreachable:
            assert_never(unreachable)
