from app.domain import models as study_models
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
    studies = load_fixture_studies("geographic_pembrolizumab_countries")
    assert_all_rows_have_citations(viz)
    assert_all_excerpts_in_source(studies, viz)


def test_geographic_multi_country_study_cites_bucket_country() -> None:
    studies = load_fixture_studies("geographic_pembrolizumab_countries")
    viz = transform_studies(
        TransformContext(
            horizon=Horizon.GEOGRAPHIC,
            viz_type=VisualizationType.BAR_CHART,
            studies=studies,
        )
    )
    multi_country_study = next(
        study
        for study in studies
        if len(study_models.unique_countries(study)) > 1
    )
    nct_id = study_models.nct_id(multi_country_study)
    assert nct_id is not None
    countries = study_models.unique_countries(multi_country_study)
    for country in countries:
        row = next(row for row in viz.data if row.country == country)
        matching = [c for c in row.citations if c.nct_id == nct_id]
        assert matching, f"Expected citation for {nct_id} in {country} bucket"
        assert any(c.excerpt == country for c in matching)
