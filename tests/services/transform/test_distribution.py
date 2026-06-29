from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.services.fetch import load_fixture_studies
from app.services.transform import transform_studies
from app.services.transform.base import TransformContext
from tests.services.conftest import load_expected_viz


def test_distribution_phase_bar_chart_matches_golden(ctgov_enums) -> None:
    context = TransformContext(
        horizon=Horizon.DISTRIBUTION,
        viz_type=VisualizationType.BAR_CHART,
        studies=load_fixture_studies("distribution_breast_cancer_phase"),
        enums=ctgov_enums,
    )
    viz = transform_studies(context)
    expected = load_expected_viz("distribution_breast_cancer_phase")

    assert viz.encoding.model_dump() == expected["encoding"]
    actual_rows = [
        {"phase": row.phase, "count": row.count, "has_citations": bool(row.citations)}
        for row in viz.data
    ]
    assert actual_rows == expected["data"]
