"""Geographic mapper: country-level trial counts."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.core.schemas.visualization import BarChartDataRow, BarChartVisualization
from app.domain import models as study_models
from app.services.citation_engine import attach_citations, excerpt_country
from app.services.transform.base import TransformContext


def map_geographic(context: TransformContext) -> BarChartVisualization:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for study in context.studies:
        for country in study_models.unique_countries(study):
            buckets[country].append(study)

    citations_by_country = attach_citations(
        buckets,
        excerpt_builder=lambda study: excerpt_country(
            study,
            study_models.unique_countries(study)[0],
        ),
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
