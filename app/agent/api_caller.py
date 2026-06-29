"""Step 3: fetch studies from ClinicalTrials.gov and build FetchPreview."""

from __future__ import annotations

from typing import Any

from app.agent.exceptions import AgentError
from app.agent.types import (
    APIQueryPlan,
    FetchPreview,
    FetchResult,
    SearchPreview,
)
from app.domain.horizons import allowed_visualization_types
from app.infrastructure.ctgov.client import CtgovClient


def build_fetch_preview(
    plan: APIQueryPlan,
    studies_per_search: list[list[dict[str, Any]]],
    total_counts: list[int | None],
) -> FetchPreview:
    allowed = sorted(
        allowed_visualization_types(plan.horizon),
        key=lambda viz_type: viz_type.value,
    )
    searches = [
        SearchPreview(
            label=search.label,
            studies_fetched=len(studies),
            total_count=total_count,
        )
        for search, studies, total_count in zip(
            plan.searches,
            studies_per_search,
            total_counts,
            strict=True,
        )
    ]
    return FetchPreview(searches=searches, allowed_viz_types=allowed)


def fetch_studies(plan: APIQueryPlan, client: CtgovClient) -> FetchResult:
    studies_per_search: list[list[dict[str, Any]]] = []
    total_counts: list[int | None] = []

    for search in plan.searches:
        studies, total_count = client.fetch_search_studies(search.params)
        if not studies:
            label = search.label or "cohort"
            raise AgentError(
                "empty_api_results",
                f"Search for {label!r} returned zero studies.",
            )
        studies_per_search.append(studies)
        total_counts.append(total_count)

    preview = build_fetch_preview(plan, studies_per_search, total_counts)
    return FetchResult(
        studies_per_search=studies_per_search,
        preview=preview,
    )
