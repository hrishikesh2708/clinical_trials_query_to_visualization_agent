"""Distribution mapper: categorical bar charts and enrollment histograms."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.core.schemas.visualization import (
    BarChartDataRow,
    BarChartVisualization,
    HistogramDataRow,
    HistogramVisualization,
)
from app.domain import models as study_models
from app.domain.visualization import VisualizationType, assert_never
from app.infrastructure.ctgov.enums import CtgovEnums
from app.services.citation_engine import (
    attach_citations,
    excerpt_enrollment,
    excerpt_overall_status,
    excerpt_phase_for_study,
)
from app.services.transform.base import TransformContext

ENROLLMENT_BIN_WIDTH = 50
UNKNOWN_PHASE_LABEL = "Unknown"


def _phase_label(enums: CtgovEnums | None, phase_code: str) -> str:
    if enums is None:
        return phase_code
    try:
        return enums.label_for("Phase", phase_code)
    except (KeyError, ValueError):
        return phase_code


def _status_label(enums: CtgovEnums | None, status_code: str) -> str:
    if enums is None:
        return status_code
    try:
        return enums.label_for("Status", status_code)
    except (KeyError, ValueError):
        return status_code


def _enrollment_bin(count: int) -> str:
    lower = (count // ENROLLMENT_BIN_WIDTH) * ENROLLMENT_BIN_WIDTH
    upper = lower + ENROLLMENT_BIN_WIDTH - 1
    return f"{lower}-{upper}"


def _phase_buckets(
    studies: list[dict[str, Any]],
    enums: CtgovEnums | None,
) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for study in studies:
        phase_codes = study_models.phases(study)
        if not phase_codes:
            buckets[UNKNOWN_PHASE_LABEL].append(study)
            continue
        for phase_code in phase_codes:
            label = _phase_label(enums, phase_code)
            buckets[label].append(study)
    return buckets


def _status_buckets(
    studies: list[dict[str, Any]],
    enums: CtgovEnums | None,
) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for study in studies:
        status = study_models.overall_status(study)
        if status is None:
            continue
        label = _status_label(enums, status)
        buckets[label].append(study)
    return buckets


def _enrollment_buckets(
    studies: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for study in studies:
        count = study_models.enrollment_count(study)
        if count is None:
            continue
        buckets[_enrollment_bin(count)].append(study)
    return buckets


def _bar_chart_from_buckets(
    buckets: dict[str, list[dict[str, Any]]],
    *,
    x_field: str,
    excerpt_builder,
) -> BarChartVisualization:
    citations_by_bucket = attach_citations(buckets, excerpt_builder=excerpt_builder)
    rows = [
        BarChartDataRow(
            **{
                x_field: bucket,
                "count": len(studies),
                "citations": citations_by_bucket[bucket],
            }
        )
        for bucket, studies in buckets.items()
    ]
    rows.sort(key=lambda row: row.model_dump()["count"], reverse=True)
    return BarChartVisualization(
        encoding={"x": x_field, "y": "count"},
        data=rows,
    )


def map_distribution(
    context: TransformContext,
) -> BarChartVisualization | HistogramVisualization:
    match context.viz_type:
        case VisualizationType.BAR_CHART:
            if context.bucket_field == "overall_status":
                buckets = _status_buckets(context.studies, context.enums)
                return _bar_chart_from_buckets(
                    buckets,
                    x_field="status",
                    excerpt_builder=excerpt_overall_status,
                )
            buckets = _phase_buckets(context.studies, context.enums)
            return _bar_chart_from_buckets(
                buckets,
                x_field="phase",
                excerpt_builder=excerpt_phase_for_study,
            )
        case VisualizationType.HISTOGRAM:
            buckets = _enrollment_buckets(context.studies)
            citations_by_bucket = attach_citations(
                buckets,
                excerpt_builder=excerpt_enrollment,
            )
            rows = [
                HistogramDataRow(
                    enrollment_bin=bucket,
                    count=len(studies),
                    citations=citations_by_bucket[bucket],
                )
                for bucket, studies in sorted(
                    buckets.items(),
                    key=lambda item: int(item[0].split("-")[0]),
                )
            ]
            return HistogramVisualization(
                encoding={"x": "enrollment_bin", "y": "count"},
                data=rows,
            )
        case _ as unreachable:
            assert_never(unreachable)
