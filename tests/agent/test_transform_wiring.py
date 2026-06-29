"""Tests for Step 5 transform wiring."""

from app.agent.transform_wiring import build_transform_context, run_transform
from app.agent.types import (
    APIQueryPlan,
    FetchPreview,
    FetchResult,
    Intent,
    PlannedSearch,
    ResolvedFilters,
    SearchPreview,
)
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.infrastructure.ctgov.models import StudiesSearchParams
from app.services.fetch import load_fixture_studies
from tests.agent.conftest import enums_from_fixture
from tests.services.conftest import load_expected_viz


def test_build_transform_context_time_trend() -> None:
    ctgov_enums = enums_from_fixture()
    studies = load_fixture_studies("time_trend_pembrolizumab")
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(drug_name="Pembrolizumab", start_year=2015),
        bucket_field="phase",
    )
    plan = APIQueryPlan(
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

    context = build_transform_context(
        intent,
        plan,
        fetched,
        VisualizationType.TIME_SERIES,
        ctgov_enums,
    )

    assert context.horizon is Horizon.TIME_TREND
    assert context.studies == studies
    assert context.bucket_field == "phase"
    assert context.enums is ctgov_enums
    assert context.comparison_arms == ()


def test_build_transform_context_comparison() -> None:
    ctgov_enums = enums_from_fixture()
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
                ),
                fields=["NCTId", "Phase"],
            ),
            PlannedSearch(
                label="Nivolumab",
                params=StudiesSearchParams(
                    query_intr="Nivolumab",
                    count_total=True,
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

    context = build_transform_context(
        intent,
        plan,
        fetched,
        VisualizationType.GROUPED_BAR_CHART,
        ctgov_enums,
    )

    assert context.horizon is Horizon.COMPARISON
    assert len(context.comparison_arms) == 2
    assert context.comparison_arms[0].label == "Pembrolizumab"
    assert context.comparison_arms[0].studies == pembrolizumab
    assert context.comparison_arms[1].label == "Nivolumab"
    assert context.comparison_arms[1].studies == nivolumab
    assert context.bucket_field == "phase"
    assert context.enums is ctgov_enums


def test_run_transform_time_trend_matches_golden() -> None:
    ctgov_enums = enums_from_fixture()
    studies = load_fixture_studies("time_trend_pembrolizumab")
    intent = Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(drug_name="Pembrolizumab", start_year=2015),
    )
    plan = APIQueryPlan(
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

    viz = run_transform(
        intent,
        plan,
        fetched,
        VisualizationType.TIME_SERIES,
        ctgov_enums,
    )
    expected = load_expected_viz("time_trend_pembrolizumab")

    assert viz.type == expected["type"]
    assert viz.encoding.model_dump() == expected["encoding"]
    assert len(viz.data) == len(expected["data"])
    assert viz.data[0].year == expected["data"][0]["year"]
    assert viz.data[0].count == expected["data"][0]["count"]
