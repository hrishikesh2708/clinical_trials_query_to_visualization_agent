"""Tests for Step 6 response builder."""

import asyncio
from unittest.mock import AsyncMock, patch

from app.agent.response_builder import (
    assemble_visualize_response,
    build_visualize_response,
)
from app.agent.types import (
    FetchPreview,
    FetchResult,
    Intent,
    ResolvedFilters,
    ResponseNarrative,
    SearchPreview,
)
from app.core.schemas.visualization import TimeSeriesVisualization
from app.domain.horizons import Horizon
from app.domain.visualization import TimeGranularity, VisualizationType
from app.services.fetch import load_fixture_studies
from tests.services.conftest import load_expected_viz


def _time_trend_viz() -> TimeSeriesVisualization:
    return TimeSeriesVisualization.model_validate(
        load_expected_viz("time_trend_pembrolizumab")
    )


def test_assemble_visualize_response() -> None:
    studies = load_fixture_studies("time_trend_pembrolizumab")
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(drug_name="Pembrolizumab", start_year=2015),
        assumptions=["Using study start date."],
        time_granularity=TimeGranularity.YEAR,
    )
    fetched = FetchResult(
        studies_per_search=[studies],
        preview=FetchPreview(
            searches=[
                SearchPreview(
                    label=None,
                    studies_fetched=len(studies),
                    total_count=42,
                )
            ],
            allowed_viz_types=[VisualizationType.TIME_SERIES],
        ),
    )
    narrative = ResponseNarrative(
        title="Pembrolizumab trials started per year since 2015",
        interpretation_notes="Counts rose after 2015.",
        additional_assumptions=["Dates may be estimated."],
    )

    response = assemble_visualize_response(
        intent,
        _time_trend_viz(),
        narrative,
        fetched,
    )

    assert response.meta.title == narrative.title
    assert response.meta.filters.drug_name == "Pembrolizumab"
    assert response.meta.filters.start_year == 2015
    assert response.meta.assumptions == [
        "Using study start date.",
        "Dates may be estimated.",
    ]
    assert response.meta.time_granularity is TimeGranularity.YEAR
    assert response.meta.total_studies_fetched == len(studies)
    assert response.meta.interpretation_notes == narrative.interpretation_notes


def test_assemble_visualize_response_omits_time_granularity_for_distribution() -> None:
    studies = load_fixture_studies("distribution_breast_cancer_phase")
    intent = Intent(
        horizon=Horizon.DISTRIBUTION,
        filters=ResolvedFilters(condition="breast cancer"),
        bucket_field="phase",
        time_granularity=TimeGranularity.YEAR,
    )
    fetched = FetchResult(
        studies_per_search=[studies],
        preview=FetchPreview(
            searches=[
                SearchPreview(
                    label=None,
                    studies_fetched=len(studies),
                    total_count=10,
                )
            ],
            allowed_viz_types=[VisualizationType.BAR_CHART],
        ),
    )
    narrative = ResponseNarrative(title="Breast cancer trials by phase")

    response = assemble_visualize_response(
        intent,
        _time_trend_viz(),
        narrative,
        fetched,
    )

    assert response.meta.time_granularity is None


def test_build_visualize_response_mocked_llm() -> None:
    studies = load_fixture_studies("time_trend_pembrolizumab")
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(drug_name="Pembrolizumab", start_year=2015),
        assumptions=["Using study start date."],
    )
    fetched = FetchResult(
        studies_per_search=[studies],
        preview=FetchPreview(
            searches=[
                SearchPreview(
                    label=None,
                    studies_fetched=len(studies),
                    total_count=42,
                )
            ],
            allowed_viz_types=[VisualizationType.TIME_SERIES],
        ),
    )
    narrative = ResponseNarrative(
        title="Pembrolizumab trials started per year since 2015",
        interpretation_notes="Steady growth.",
    )
    client = AsyncMock()

    with patch(
        "app.agent.response_builder.parse_structured",
        new_callable=AsyncMock,
        return_value=narrative,
    ) as mock_parse:
        response = asyncio.run(
            build_visualize_response(
                intent,
                _time_trend_viz(),
                VisualizationType.TIME_SERIES,
                fetched,
                client=client,
                model="gpt-4o-mini",
            )
        )

    mock_parse.assert_awaited_once()
    assert response.visualization.type == VisualizationType.TIME_SERIES
    assert response.meta.title == narrative.title
    assert response.meta.total_studies_fetched == len(studies)
