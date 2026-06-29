import pytest

from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.services.fetch import load_fixture_studies
from app.services.transform import transform_studies
from app.services.transform.base import TransformContext
from app.validation.viz_compatibility import VizValidationError, validate_pre_transform


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
