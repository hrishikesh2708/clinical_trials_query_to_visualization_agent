"""End-to-end visualize pipeline tests with mocked LLM and fetch."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.agent.pipeline import VisualizePipeline
from app.agent.types import (
    APIQueryPlan,
    FetchPreview,
    FetchResult,
    Intent,
    PlannedSearch,
    ResolvedFilters,
    ResponseNarrative,
    SearchPreview,
)
from app.core.config import Settings
from app.core.schemas.request import VisualizeRequest
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.infrastructure.ctgov.models import StudiesSearchParams
from app.services.fetch import load_fixture_studies
from tests.agent.conftest import enums_from_fixture


def _pipeline(settings: Settings) -> VisualizePipeline:
    pipeline = VisualizePipeline(settings, openai_client=AsyncMock())
    pipeline._enums_loader = MagicMock()
    pipeline._enums_loader.load.return_value = enums_from_fixture()
    return pipeline


def test_pipeline_e2e_time_trend() -> None:
    settings = Settings()
    pipeline = _pipeline(settings)
    request = VisualizeRequest(
        query="Trials per year for pembrolizumab since 2015",
        drug_name="Pembrolizumab",
        start_year=2015,
    )
    studies = load_fixture_studies("time_trend_pembrolizumab")
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(drug_name="Pembrolizumab", start_year=2015),
        assumptions=["Using study start date."],
    )
    plan = APIQueryPlan(
        horizon=Horizon.TIME_TREND,
        searches=[
            PlannedSearch(
                params=StudiesSearchParams(
                    query_intr="Pembrolizumab",
                    filter_advanced="AREA[StartDate]2015",
                    count_total=True,
                    fields=["NCTId", "StartDateStruct"],
                ),
                fields=["NCTId", "StartDateStruct"],
            )
        ],
    )
    fetched = FetchResult(
        studies_per_search=[studies],
        preview=FetchPreview(
            searches=[
                SearchPreview(
                    label=None,
                    studies_fetched=len(studies),
                    total_count=120,
                )
            ],
            allowed_viz_types=[VisualizationType.TIME_SERIES],
        ),
    )
    narrative = ResponseNarrative(
        title="Pembrolizumab trials started per year since 2015",
        interpretation_notes="Trial starts clustered in 2015 for this fixture.",
    )

    with (
        patch(
            "app.agent.pipeline.parse_intent",
            new_callable=AsyncMock,
            return_value=intent,
        ),
        patch(
            "app.agent.pipeline.plan_query",
            new_callable=AsyncMock,
            return_value=plan,
        ),
        patch(
            "app.agent.pipeline.fetch_studies",
            return_value=fetched,
        ),
        patch(
            "app.agent.pipeline.select_viz",
            new_callable=AsyncMock,
            return_value=VisualizationType.TIME_SERIES,
        ),
        patch(
            "app.agent.response_builder.parse_structured",
            new_callable=AsyncMock,
            return_value=narrative,
        ),
    ):
        response = asyncio.run(pipeline.run(request))

    assert response.visualization.type == VisualizationType.TIME_SERIES
    assert response.meta.title == narrative.title
    assert response.meta.total_studies_fetched == len(studies)


def test_pipeline_e2e_comparison() -> None:
    settings = Settings()
    pipeline = _pipeline(settings)
    request = VisualizeRequest(query="Compare pembrolizumab vs nivolumab by phase")
    pembrolizumab = load_fixture_studies("comparison_pembrolizumab_arm")
    nivolumab = load_fixture_studies("comparison_nivolumab_arm")
    intent = Intent(
        horizon=Horizon.COMPARISON,
        filters=ResolvedFilters(),
        comparison_arm_labels=("Pembrolizumab", "Nivolumab"),
    )
    plan = APIQueryPlan(
        horizon=Horizon.COMPARISON,
        searches=[
            PlannedSearch(
                label="Pembrolizumab",
                params=StudiesSearchParams(
                    query_intr="Pembrolizumab",
                    count_total=True,
                    fields=["NCTId", "Phase"],
                ),
                fields=["NCTId", "Phase"],
            ),
            PlannedSearch(
                label="Nivolumab",
                params=StudiesSearchParams(
                    query_intr="Nivolumab",
                    count_total=True,
                    fields=["NCTId", "Phase"],
                ),
                fields=["NCTId", "Phase"],
            ),
        ],
    )
    fetched = FetchResult(
        studies_per_search=[pembrolizumab, nivolumab],
        preview=FetchPreview(
            searches=[
                SearchPreview(
                    label="Pembrolizumab",
                    studies_fetched=len(pembrolizumab),
                    total_count=50,
                ),
                SearchPreview(
                    label="Nivolumab",
                    studies_fetched=len(nivolumab),
                    total_count=40,
                ),
            ],
            allowed_viz_types=[VisualizationType.GROUPED_BAR_CHART],
        ),
    )
    narrative = ResponseNarrative(
        title="Pembrolizumab vs nivolumab trials by phase",
    )

    with (
        patch(
            "app.agent.pipeline.parse_intent",
            new_callable=AsyncMock,
            return_value=intent,
        ),
        patch(
            "app.agent.pipeline.plan_query",
            new_callable=AsyncMock,
            return_value=plan,
        ),
        patch(
            "app.agent.pipeline.fetch_studies",
            return_value=fetched,
        ),
        patch(
            "app.agent.pipeline.select_viz",
            new_callable=AsyncMock,
            return_value=VisualizationType.GROUPED_BAR_CHART,
        ),
        patch(
            "app.agent.response_builder.parse_structured",
            new_callable=AsyncMock,
            return_value=narrative,
        ),
    ):
        response = asyncio.run(pipeline.run(request))

    assert response.visualization.type == VisualizationType.GROUPED_BAR_CHART
    assert response.meta.title == narrative.title
