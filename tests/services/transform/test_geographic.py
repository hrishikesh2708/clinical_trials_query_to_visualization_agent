from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.services.fetch import load_fixture_studies
from app.services.transform import transform_studies
from app.services.transform.base import TransformContext
from tests.services.conftest import load_expected_viz


def test_geographic_country_dedup_matches_golden() -> None:
    viz = transform_studies(
        TransformContext(
            horizon=Horizon.GEOGRAPHIC,
            viz_type=VisualizationType.BAR_CHART,
            studies=load_fixture_studies("geographic_pembrolizumab_countries"),
        )
    )
    expected = load_expected_viz("geographic_pembrolizumab_countries")

    assert viz.encoding.model_dump() == expected["encoding"]
    actual_rows = [
        {
            "country": row.country,
            "count": row.count,
            "has_citations": bool(row.citations),
        }
        for row in viz.data
    ]
    assert actual_rows == expected["data"]
