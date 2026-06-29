"""Geographic mapper: country-level trial counts."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.core.schemas.visualization import BarChartDataRow, BarChartVisualization
from app.domain import models as study_models
from app.services.citation_engine import attach_citations_per_bucket, excerpt_country
from app.services.transform.base import TransformContext


def map_geographic(context: TransformContext) -> BarChartVisualization:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for study in context.studies:
        for country in study_models.unique_countries(study):
            buckets[country].append(study)

    citations_by_country = attach_citations_per_bucket(
        buckets,
        excerpt_builder=lambda study, country: excerpt_country(study, country),
    )

    rows = [
        BarChartDataRow(
            country=country,
            count=len(studies),
            citations=citations_by_country[country],
        )
        for country, studies in buckets.items()
    ]
    rows.sort(key=lambda row: row.count, reverse=True)

    return BarChartVisualization(
        encoding={"x": "country", "y": "count"},
        data=rows,
    )
