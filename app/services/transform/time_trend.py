"""Time-trend mapper: study start dates bucketed over time."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from typing import Any

from app.core.schemas.visualization import TimeSeriesDataRow, TimeSeriesVisualization
from app.domain import models as study_models
from app.domain.visualization import TimeGranularity, assert_never
from app.services.citation_engine import attach_citations, excerpt_start_date
from app.services.transform.base import TransformContext

_DATE_YEAR = re.compile(r"^(\d{4})")
_DATE_YEAR_MONTH = re.compile(r"^(\d{4})-(\d{2})")
_DATE_FULL = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def _date_priority(study: dict[str, Any]) -> int | None:
    struct = study_models.start_date_struct(study)
    if struct is None:
        return None
    date_value = struct.get("date")
    if not isinstance(date_value, str) or not date_value:
        return None
    date_type = struct.get("type")
    if date_type == "ACTUAL":
        return 2
    if date_type == "ESTIMATED" or date_type is None:
        return 1
    return None


def _parse_bucket(date_value: str, granularity: TimeGranularity) -> str | int | None:
    full_match = _DATE_FULL.match(date_value)
    if full_match:
        year, month, day = map(int, full_match.groups())
        parsed = date(year, month, day)
    else:
        month_match = _DATE_YEAR_MONTH.match(date_value)
        if month_match:
            year, month = map(int, month_match.groups())
            parsed = date(year, month, 1)
        else:
            year_match = _DATE_YEAR.match(date_value)
            if not year_match:
                return None
            parsed = date(int(year_match.group(1)), 1, 1)

    match granularity:
        case TimeGranularity.YEAR:
            return parsed.year
        case TimeGranularity.MONTH:
            return f"{parsed.year}-{parsed.month:02d}"
        case TimeGranularity.QUARTER:
            quarter = (parsed.month - 1) // 3 + 1
            return f"{parsed.year}-Q{quarter}"
        case TimeGranularity.DAY:
            return parsed.isoformat()
        case _ as unreachable:
            assert_never(unreachable)


def _eligible_studies(studies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    for study in studies:
        if _date_priority(study) is not None:
            eligible.append(study)
    return eligible


def map_time_trend(context: TransformContext) -> TimeSeriesVisualization:
    buckets: dict[str | int, list[dict[str, Any]]] = defaultdict(list)

    for study in _eligible_studies(context.studies):
        struct = study_models.start_date_struct(study)
        assert struct is not None
        date_value = struct["date"]
        assert isinstance(date_value, str)
        bucket = _parse_bucket(date_value, context.time_granularity)
        if bucket is None:
            continue
        buckets[bucket].append(study)

    citations_by_bucket = attach_citations(
        buckets,
        excerpt_builder=excerpt_start_date,
    )

    rows: list[TimeSeriesDataRow] = []
    for bucket in sorted(buckets, key=lambda value: str(value)):
        studies = buckets[bucket]
        rows.append(
            TimeSeriesDataRow(
                year=bucket,
                count=len(studies),
                citations=citations_by_bucket[bucket],
            )
        )

    return TimeSeriesVisualization(
        encoding={"x": "year", "y": "count"},
        data=rows,
    )
