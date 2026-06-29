from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.services.fetch import load_fixture_studies
from app.services.transform import transform_studies
from app.services.transform.base import TransformContext
from tests.services.conftest import (
    assert_all_excerpts_in_source,
    assert_all_rows_have_citations,
    load_expected_viz,
)


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
    assert_all_rows_have_citations(viz)
    assert_all_excerpts_in_source(
        load_fixture_studies("distribution_breast_cancer_phase"),
        viz,
    )


def test_distribution_enrollment_histogram_has_citations() -> None:
    studies = [
        {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT00000001"},
                "designModule": {"enrollmentInfo": {"count": 25}},
            }
        },
        {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT00000002"},
                "designModule": {"enrollmentInfo": {"count": 75}},
            }
        },
        {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT00000003"},
                "designModule": {"enrollmentInfo": {"count": 120}},
            }
        },
    ]
    viz = transform_studies(
        TransformContext(
            horizon=Horizon.DISTRIBUTION,
            viz_type=VisualizationType.HISTOGRAM,
            studies=studies,
            bucket_field="enrollment",
        )
    )
    assert_all_rows_have_citations(viz)
    assert_all_excerpts_in_source(studies, viz)
