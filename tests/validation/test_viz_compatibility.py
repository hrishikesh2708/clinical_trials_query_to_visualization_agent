import pytest

from app.core.schemas.visualization import (
    BarChartDataRow,
    BarChartEncoding,
    BarChartVisualization,
    NetworkEdge,
    NetworkGraphData,
    NetworkGraphEncoding,
    NetworkGraphVisualization,
    NetworkNode,
    TimeSeriesDataRow,
    TimeSeriesEncoding,
    TimeSeriesVisualization,
)
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.services.fetch import load_fixture_studies
from app.services.transform import transform_studies
from app.services.transform.base import TransformContext
from app.validation.viz_compatibility import (
    VizValidationError,
    validate_post_transform,
    validate_pre_transform,
)


@pytest.mark.parametrize(
    ("horizon", "viz_type"),
    [
        (Horizon.TIME_TREND, VisualizationType.BAR_CHART),
        (Horizon.TIME_TREND, VisualizationType.SCATTER_PLOT),
        (Horizon.DISTRIBUTION, VisualizationType.TIME_SERIES),
        (Horizon.COMPARISON, VisualizationType.HISTOGRAM),
        (Horizon.GEOGRAPHIC, VisualizationType.NETWORK_GRAPH),
        (Horizon.NETWORK, VisualizationType.BAR_CHART),
    ],
)
def test_pre_transform_rejects_forbidden_pairs(horizon, viz_type) -> None:
    context = TransformContext(
        horizon=horizon,
        viz_type=viz_type,
        studies=load_fixture_studies("studies_single"),
    )
    with pytest.raises(VizValidationError) as exc_info:
        validate_pre_transform(context)
    assert exc_info.value.code in {
        "incompatible_horizon_viz",
        "forbidden_viz_type",
        "bucket_viz_mismatch",
    }


def test_pre_transform_rejects_empty_studies() -> None:
    context = TransformContext(
        horizon=Horizon.TIME_TREND,
        viz_type=VisualizationType.TIME_SERIES,
        studies=load_fixture_studies("studies_empty"),
    )
    with pytest.raises(VizValidationError) as exc_info:
        validate_pre_transform(context)
    assert exc_info.value.code == "empty_studies"


def test_pre_transform_rejects_comparison_without_arms() -> None:
    context = TransformContext(
        horizon=Horizon.COMPARISON,
        viz_type=VisualizationType.GROUPED_BAR_CHART,
        studies=load_fixture_studies("studies_single"),
    )
    with pytest.raises(VizValidationError, match="comparison_arms"):
        validate_pre_transform(context)


def test_transform_rejects_empty_studies_before_mapping() -> None:
    context = TransformContext(
        horizon=Horizon.DISTRIBUTION,
        viz_type=VisualizationType.BAR_CHART,
        studies=load_fixture_studies("studies_empty"),
    )
    with pytest.raises(VizValidationError) as exc_info:
        transform_studies(context)
    assert exc_info.value.code == "empty_studies"


def test_distribution_enrollment_requires_histogram() -> None:
    context = TransformContext(
        horizon=Horizon.DISTRIBUTION,
        viz_type=VisualizationType.BAR_CHART,
        studies=load_fixture_studies("studies_single"),
        bucket_field="enrollment",
    )
    with pytest.raises(VizValidationError) as exc_info:
        validate_pre_transform(context)
    assert exc_info.value.code == "bucket_viz_mismatch"


def test_post_transform_rejects_missing_tabular_citations() -> None:
    context = TransformContext(
        horizon=Horizon.TIME_TREND,
        viz_type=VisualizationType.TIME_SERIES,
        studies=load_fixture_studies("studies_single"),
    )
    viz = TimeSeriesVisualization(
        encoding=TimeSeriesEncoding(x="year", y="count"),
        data=[TimeSeriesDataRow(year=2020, count=1, citations=[])],
    )
    with pytest.raises(VizValidationError) as exc_info:
        validate_post_transform(context, viz)
    assert exc_info.value.code == "missing_citations"


def test_post_transform_rejects_missing_network_node_citations() -> None:
    context = TransformContext(
        horizon=Horizon.NETWORK,
        viz_type=VisualizationType.NETWORK_GRAPH,
        studies=load_fixture_studies("studies_single"),
    )
    viz = NetworkGraphVisualization(
        encoding=NetworkGraphEncoding(nodes="nodes", edges="edges"),
        data=NetworkGraphData(
            nodes=[NetworkNode(id="a", label="A", citations=[])],
            edges=[
                NetworkEdge(
                    source="a",
                    target="b",
                    label="sponsored_by",
                    citations=[],
                )
            ],
        ),
    )
    with pytest.raises(VizValidationError) as exc_info:
        validate_post_transform(context, viz)
    assert exc_info.value.code == "missing_citations"


def test_post_transform_rejects_missing_network_edge_citations() -> None:
    context = TransformContext(
        horizon=Horizon.NETWORK,
        viz_type=VisualizationType.NETWORK_GRAPH,
        studies=load_fixture_studies("studies_single"),
    )
    viz = NetworkGraphVisualization(
        encoding=NetworkGraphEncoding(nodes="nodes", edges="edges"),
        data=NetworkGraphData(
            nodes=[
                NetworkNode(
                    id="a",
                    label="A",
                    citations=[{"nct_id": "NCT05071014", "excerpt": "x"}],
                )
            ],
            edges=[
                NetworkEdge(
                    source="a",
                    target="b",
                    label="sponsored_by",
                    citations=[],
                )
            ],
        ),
    )
    with pytest.raises(VizValidationError) as exc_info:
        validate_post_transform(context, viz)
    assert exc_info.value.code == "missing_citations"


def test_post_transform_allows_zero_count_without_citations() -> None:
    context = TransformContext(
        horizon=Horizon.DISTRIBUTION,
        viz_type=VisualizationType.BAR_CHART,
        studies=load_fixture_studies("studies_single"),
    )
    viz = BarChartVisualization(
        encoding=BarChartEncoding(x="phase", y="count"),
        data=[BarChartDataRow(phase="Phase 1", count=0, citations=[])],
    )
    validate_post_transform(context, viz)
