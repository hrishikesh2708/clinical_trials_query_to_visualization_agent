import pytest

from app.domain.horizons import (
    Horizon,
    allowed_visualization_types,
    horizon_spec,
    is_visualization_compatible,
)
from app.domain.visualization import VisualizationType

_EXPECTED_ALLOWED: dict[Horizon, frozenset[VisualizationType]] = {
    Horizon.TIME_TREND: frozenset({VisualizationType.TIME_SERIES}),
    Horizon.DISTRIBUTION: frozenset(
        {VisualizationType.BAR_CHART, VisualizationType.HISTOGRAM}
    ),
    Horizon.COMPARISON: frozenset(
        {VisualizationType.GROUPED_BAR_CHART, VisualizationType.BAR_CHART}
    ),
    Horizon.GEOGRAPHIC: frozenset({VisualizationType.BAR_CHART}),
    Horizon.NETWORK: frozenset({VisualizationType.NETWORK_GRAPH}),
}

_ALL_VIZ_TYPES = frozenset(VisualizationType)


@pytest.mark.parametrize("horizon", list(Horizon))
def test_allowed_visualization_types_matches_matrix(horizon: Horizon) -> None:
    assert allowed_visualization_types(horizon) == _EXPECTED_ALLOWED[horizon]


@pytest.mark.parametrize("horizon", list(Horizon))
def test_each_horizon_has_at_least_one_allowed_viz(horizon: Horizon) -> None:
    assert len(allowed_visualization_types(horizon)) >= 1


@pytest.mark.parametrize(
    ("horizon", "viz_type"),
    [
        (Horizon.TIME_TREND, VisualizationType.TIME_SERIES),
        (Horizon.DISTRIBUTION, VisualizationType.BAR_CHART),
        (Horizon.DISTRIBUTION, VisualizationType.HISTOGRAM),
        (Horizon.COMPARISON, VisualizationType.GROUPED_BAR_CHART),
        (Horizon.COMPARISON, VisualizationType.BAR_CHART),
        (Horizon.GEOGRAPHIC, VisualizationType.BAR_CHART),
        (Horizon.NETWORK, VisualizationType.NETWORK_GRAPH),
    ],
)
def test_compatible_pairs(horizon: Horizon, viz_type: VisualizationType) -> None:
    assert is_visualization_compatible(horizon, viz_type) is True


@pytest.mark.parametrize(
    ("horizon", "viz_type"),
    [
        (Horizon.TIME_TREND, VisualizationType.NETWORK_GRAPH),
        (Horizon.TIME_TREND, VisualizationType.SCATTER_PLOT),
        (Horizon.TIME_TREND, VisualizationType.BAR_CHART),
        (Horizon.DISTRIBUTION, VisualizationType.TIME_SERIES),
        (Horizon.DISTRIBUTION, VisualizationType.NETWORK_GRAPH),
        (Horizon.DISTRIBUTION, VisualizationType.GROUPED_BAR_CHART),
        (Horizon.COMPARISON, VisualizationType.TIME_SERIES),
        (Horizon.COMPARISON, VisualizationType.HISTOGRAM),
        (Horizon.COMPARISON, VisualizationType.NETWORK_GRAPH),
        (Horizon.GEOGRAPHIC, VisualizationType.TIME_SERIES),
        (Horizon.GEOGRAPHIC, VisualizationType.NETWORK_GRAPH),
        (Horizon.GEOGRAPHIC, VisualizationType.HISTOGRAM),
        (Horizon.NETWORK, VisualizationType.TIME_SERIES),
        (Horizon.NETWORK, VisualizationType.BAR_CHART),
        (Horizon.NETWORK, VisualizationType.HISTOGRAM),
    ],
)
def test_forbidden_pairs(horizon: Horizon, viz_type: VisualizationType) -> None:
    assert is_visualization_compatible(horizon, viz_type) is False


@pytest.mark.parametrize("horizon", list(Horizon))
def test_scatter_plot_incompatible_with_every_horizon(horizon: Horizon) -> None:
    assert is_visualization_compatible(horizon, VisualizationType.SCATTER_PLOT) is False


@pytest.mark.parametrize("horizon", list(Horizon))
def test_forbidden_types_are_complement_of_allowed(horizon: Horizon) -> None:
    allowed = allowed_visualization_types(horizon)
    forbidden = _ALL_VIZ_TYPES - allowed
    for viz_type in forbidden:
        assert is_visualization_compatible(horizon, viz_type) is False


@pytest.mark.parametrize("horizon", list(Horizon))
def test_horizon_spec_aligns_with_allowed_viz(horizon: Horizon) -> None:
    spec = horizon_spec(horizon)
    assert spec.horizon == horizon
    assert spec.allowed_viz == allowed_visualization_types(horizon)
    assert len(spec.canonical_json_paths) >= 1
    assert len(spec.fields_pieces) >= 1
