"""Tests for VisualizePipeline scaffolding."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.agent.pipeline import VisualizePipeline
from app.agent.types import (
    APIQueryPlan,
    FetchPreview,
    FetchResult,
    Intent,
    PlannedSearch,
    ResolvedFilters,
    SearchPreview,
)
from app.core.config import Settings
from app.core.schemas.request import VisualizeRequest
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.infrastructure.ctgov.models import StudiesSearchParams


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def pipeline(settings: Settings) -> VisualizePipeline:
    return VisualizePipeline(settings)


def test_pipeline_run_raises_at_step5_when_steps1_through_4_succeed(
    pipeline: VisualizePipeline,
) -> None:
    request = VisualizeRequest(query="Trials for pembrolizumab since 2015")
    stub_intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(),
    )
    stub_plan = APIQueryPlan(
        horizon=Horizon.TIME_TREND,
        searches=[
            PlannedSearch(
                params=StudiesSearchParams(
                    query_intr="Pembrolizumab",
                    count_total=True,
                ),
                fields=["NCTId", "StartDateStruct"],
            )
        ],
    )
    stub_fetched = FetchResult(
        studies_per_search=[[{"protocolSection": {}}]],
        preview=FetchPreview(
            searches=[
                SearchPreview(label=None, studies_fetched=1, total_count=10),
            ],
            allowed_viz_types=[VisualizationType.TIME_SERIES],
        ),
    )

    with (
        patch(
            "app.agent.pipeline.parse_intent",
            new_callable=AsyncMock,
            return_value=stub_intent,
        ),
        patch(
            "app.agent.pipeline.plan_query",
            new_callable=AsyncMock,
            return_value=stub_plan,
        ),
        patch(
            "app.agent.pipeline.fetch_studies",
            return_value=stub_fetched,
        ),
        patch(
            "app.agent.pipeline.select_viz",
            new_callable=AsyncMock,
            return_value=VisualizationType.TIME_SERIES,
        ),
    ):
        with pytest.raises(NotImplementedError, match="Stage 8e"):
            asyncio.run(pipeline.run(request))


def test_pipeline_constructs_with_defaults(settings: Settings) -> None:
    pipeline = VisualizePipeline(settings)
    assert pipeline._ctgov is not None
    assert pipeline._openai is not None
    assert pipeline._enums_loader is not None
