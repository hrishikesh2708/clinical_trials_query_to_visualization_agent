from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.services.fetch import load_fixture_studies
from app.services.transform import transform_studies
from app.services.transform.base import ComparisonArm, TransformContext
from tests.services.conftest import (
    assert_all_excerpts_in_source,
    assert_all_rows_have_citations,
    load_expected_viz,
)


def test_comparison_grouped_bar_matches_golden(ctgov_enums) -> None:
    context = TransformContext(
        horizon=Horizon.COMPARISON,
        viz_type=VisualizationType.GROUPED_BAR_CHART,
        comparison_arms=(
            ComparisonArm(
                "Pembrolizumab",
                load_fixture_studies("comparison_pembrolizumab_arm"),
            ),
            ComparisonArm(
                "Nivolumab",
                load_fixture_studies("comparison_nivolumab_arm"),
            ),
        ),
        enums=ctgov_enums,
    )
    viz = transform_studies(context)
    expected = load_expected_viz("comparison_pembrolizumab_vs_nivolumab")

    assert viz.encoding.model_dump() == expected["encoding"]
    actual_rows = [
        {
            "phase": row.phase,
            "series": row.series,
            "count": row.count,
            "has_citations": bool(row.citations),
        }
        for row in viz.data
    ]
    assert actual_rows == expected["data"]
    assert_all_rows_have_citations(viz)
    studies = [
        *load_fixture_studies("comparison_pembrolizumab_arm"),
        *load_fixture_studies("comparison_nivolumab_arm"),
    ]
    assert_all_excerpts_in_source(studies, viz)
