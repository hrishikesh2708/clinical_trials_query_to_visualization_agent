"""Shared mocked pipeline scenarios for API and example generation tests."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
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
from app.core.schemas.response import VisualizeResponse
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.infrastructure.ctgov.models import StudiesSearchParams
from app.services.fetch import load_fixture_studies
from tests.agent.conftest import enums_from_fixture


@dataclass(frozen=True)
class HorizonScenario:
    name: str
    request: VisualizeRequest
    intent: Intent
    plan: APIQueryPlan
    fetched: FetchResult
    viz_type: VisualizationType
    narrative: ResponseNarrative


def build_mock_pipeline(settings: Settings | None = None) -> VisualizePipeline:
    resolved_settings = settings or Settings()
    pipeline = VisualizePipeline(resolved_settings, openai_client=AsyncMock())
    pipeline._enums_loader = MagicMock()
    pipeline._enums_loader.load.return_value = enums_from_fixture()
    return pipeline


@contextmanager
def patched_pipeline_steps(scenario: HorizonScenario) -> Iterator[None]:
    with (
        patch(
            "app.agent.pipeline.parse_intent",
            new_callable=AsyncMock,
            return_value=scenario.intent,
        ),
        patch(
            "app.agent.pipeline.plan_query",
            new_callable=AsyncMock,
            return_value=scenario.plan,
        ),
        patch(
            "app.agent.pipeline.fetch_studies",
            return_value=scenario.fetched,
        ),
        patch(
            "app.agent.pipeline.select_viz",
            new_callable=AsyncMock,
            return_value=scenario.viz_type,
        ),
        patch(
            "app.agent.response_builder.parse_structured",
            new_callable=AsyncMock,
            return_value=scenario.narrative,
        ),
    ):
        yield


async def run_scenario(
    scenario: HorizonScenario,
    settings: Settings | None = None,
) -> VisualizeResponse:
    pipeline = build_mock_pipeline(settings)
    with patched_pipeline_steps(scenario):
        return await pipeline.run(scenario.request)


def time_trend_scenario() -> HorizonScenario:
    studies = load_fixture_studies("time_trend_pembrolizumab")
    return HorizonScenario(
        name="time_trend_pembrolizumab",
        request=VisualizeRequest(
            query="Trials per year for pembrolizumab since 2015",
            drug_name="Pembrolizumab",
            start_year=2015,
        ),
        intent=Intent(
            horizon=Horizon.TIME_TREND,
            filters=ResolvedFilters(drug_name="Pembrolizumab", start_year=2015),
            assumptions=["Using study start date."],
        ),
        plan=APIQueryPlan(
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
        ),
        fetched=FetchResult(
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
        ),
        viz_type=VisualizationType.TIME_SERIES,
        narrative=ResponseNarrative(
            title="Pembrolizumab trials started per year since 2015",
            interpretation_notes="Trial starts clustered in 2015 for this fixture.",
        ),
    )


def distribution_scenario() -> HorizonScenario:
    studies = load_fixture_studies("distribution_breast_cancer_phase")
    return HorizonScenario(
        name="distribution_breast_cancer_phase",
        request=VisualizeRequest(
            query="Breast cancer trials by phase",
            condition="breast cancer",
        ),
        intent=Intent(
            horizon=Horizon.DISTRIBUTION,
            filters=ResolvedFilters(condition="breast cancer"),
            bucket_field="phase",
        ),
        plan=APIQueryPlan(
            horizon=Horizon.DISTRIBUTION,
            searches=[
                PlannedSearch(
                    params=StudiesSearchParams(
                        query_cond="breast cancer",
                        count_total=True,
                        fields=["NCTId", "Phase"],
                    ),
                    fields=["NCTId", "Phase"],
                )
            ],
        ),
        fetched=FetchResult(
            studies_per_search=[studies],
            preview=FetchPreview(
                searches=[
                    SearchPreview(
                        label=None,
                        studies_fetched=len(studies),
                        total_count=80,
                    )
                ],
                allowed_viz_types=[VisualizationType.BAR_CHART],
            ),
        ),
        viz_type=VisualizationType.BAR_CHART,
        narrative=ResponseNarrative(
            title="Breast cancer trials by phase",
        ),
    )


def comparison_scenario() -> HorizonScenario:
    pembrolizumab = load_fixture_studies("comparison_pembrolizumab_arm")
    nivolumab = load_fixture_studies("comparison_nivolumab_arm")
    return HorizonScenario(
        name="comparison_pembrolizumab_vs_nivolumab",
        request=VisualizeRequest(
            query="Pembrolizumab vs nivolumab trials by phase",
        ),
        intent=Intent(
            horizon=Horizon.COMPARISON,
            filters=ResolvedFilters(),
            comparison_arm_labels=("Pembrolizumab", "Nivolumab"),
        ),
        plan=APIQueryPlan(
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
        ),
        fetched=FetchResult(
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
        ),
        viz_type=VisualizationType.GROUPED_BAR_CHART,
        narrative=ResponseNarrative(
            title="Pembrolizumab vs nivolumab trials by phase",
        ),
    )


def geographic_scenario() -> HorizonScenario:
    studies = load_fixture_studies("geographic_pembrolizumab_countries")
    return HorizonScenario(
        name="geographic_lung_cancer_recruiting",
        request=VisualizeRequest(
            query="Recruiting lung cancer trials by country",
            condition="lung cancer",
            trial_phase="Recruiting",
        ),
        intent=Intent(
            horizon=Horizon.GEOGRAPHIC,
            filters=ResolvedFilters(
                condition="lung cancer",
                trial_phase="Recruiting",
            ),
        ),
        plan=APIQueryPlan(
            horizon=Horizon.GEOGRAPHIC,
            searches=[
                PlannedSearch(
                    params=StudiesSearchParams(
                        query_cond="lung cancer",
                        filter_overall_status=["RECRUITING"],
                        count_total=True,
                        fields=["NCTId", "LocationCountry"],
                    ),
                    fields=["NCTId", "LocationCountry"],
                )
            ],
        ),
        fetched=FetchResult(
            studies_per_search=[studies],
            preview=FetchPreview(
                searches=[
                    SearchPreview(
                        label=None,
                        studies_fetched=len(studies),
                        total_count=35,
                    )
                ],
                allowed_viz_types=[VisualizationType.BAR_CHART],
            ),
        ),
        viz_type=VisualizationType.BAR_CHART,
        narrative=ResponseNarrative(
            title="Recruiting lung cancer trials by country",
        ),
    )


def network_scenario() -> HorizonScenario:
    studies = load_fixture_studies("network_diabetes_sponsor_drug")
    return HorizonScenario(
        name="network_diabetes_sponsor_drug",
        request=VisualizeRequest(
            query="Sponsor–drug network for diabetes trials",
            condition="diabetes",
        ),
        intent=Intent(
            horizon=Horizon.NETWORK,
            filters=ResolvedFilters(condition="diabetes"),
        ),
        plan=APIQueryPlan(
            horizon=Horizon.NETWORK,
            searches=[
                PlannedSearch(
                    params=StudiesSearchParams(
                        query_cond="diabetes",
                        count_total=True,
                        fields=[
                            "NCTId",
                            "InterventionName",
                            "LeadSponsorName",
                            "Condition",
                            "DerivedSection",
                        ],
                    ),
                    fields=[
                        "NCTId",
                        "InterventionName",
                        "LeadSponsorName",
                        "Condition",
                        "DerivedSection",
                    ],
                )
            ],
        ),
        fetched=FetchResult(
            studies_per_search=[studies],
            preview=FetchPreview(
                searches=[
                    SearchPreview(
                        label=None,
                        studies_fetched=len(studies),
                        total_count=25,
                    )
                ],
                allowed_viz_types=[VisualizationType.NETWORK_GRAPH],
            ),
        ),
        viz_type=VisualizationType.NETWORK_GRAPH,
        narrative=ResponseNarrative(
            title="Sponsor–drug network for diabetes trials",
        ),
    )


ALL_SCENARIOS = (
    time_trend_scenario(),
    distribution_scenario(),
    comparison_scenario(),
    geographic_scenario(),
    network_scenario(),
)

SCENARIO_BY_NAME = {scenario.name: scenario for scenario in ALL_SCENARIOS}
