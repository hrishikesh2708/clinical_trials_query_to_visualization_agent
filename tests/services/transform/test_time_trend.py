from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.services.fetch import load_fixture_studies
from app.services.transform import transform_studies
from app.services.transform.base import TransformContext
from tests.services.conftest import assert_excerpts_in_source, load_expected_viz


def test_time_trend_matches_golden_summary() -> None:
    studies = load_fixture_studies("time_trend_pembrolizumab")
    context = TransformContext(
        horizon=Horizon.TIME_TREND,
        viz_type=VisualizationType.TIME_SERIES,
        studies=studies,
    )
    viz = transform_studies(context)
    expected = load_expected_viz("time_trend_pembrolizumab")

    assert viz.type == expected["type"]
    assert viz.encoding.model_dump() == expected["encoding"]
    assert len(viz.data) == len(expected["data"])
    assert viz.data[0].year == expected["data"][0]["year"]
    assert viz.data[0].count == expected["data"][0]["count"]
    assert viz.data[0].citations
    assert_excerpts_in_source(
        studies,
        [citation.model_dump() for citation in viz.data[0].citations],
    )


def test_time_trend_buckets_all_fixture_studies_in_2015() -> None:
    studies = load_fixture_studies("time_trend_pembrolizumab")
    viz = transform_studies(
        TransformContext(
            horizon=Horizon.TIME_TREND,
            viz_type=VisualizationType.TIME_SERIES,
            studies=studies,
        )
    )
    assert len(viz.data) == 1
    assert viz.data[0].year == 2015
    assert viz.data[0].count == len(studies)
