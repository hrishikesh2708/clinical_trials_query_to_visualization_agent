from app.core.schemas.response import AppliedFilters, ResponseMeta, VisualizeResponse
from app.core.schemas.visualization import BarChartVisualization
from app.domain.visualization import DataSource, TimeGranularity
from tests.core.schemas.test_visualization import BAR_CHART_PAYLOAD


def test_visualize_response_round_trip() -> None:
    visualization = BarChartVisualization.model_validate(BAR_CHART_PAYLOAD)
    original = VisualizeResponse(
        visualization=visualization,
        meta=ResponseMeta(
            title="Pembrolizumab trials started per year since 2015",
            filters=AppliedFilters(
                drug_name="Pembrolizumab",
                start_year=2015,
            ),
            assumptions=["Counted studies by primary completion year."],
            time_granularity=TimeGranularity.YEAR,
            units={"y": "study_count"},
            total_studies_fetched=42,
            interpretation_notes="Trial counts rose steadily after 2015.",
        ),
    )
    restored = VisualizeResponse.model_validate_json(original.model_dump_json())
    assert restored == original
    assert restored.meta.source == DataSource.CLINICALTRIALS_GOV
