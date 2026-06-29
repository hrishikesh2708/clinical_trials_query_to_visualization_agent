"""Transform registry and public entrypoint."""

from __future__ import annotations

from collections.abc import Callable

from app.core.schemas.visualization import Visualization
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.services.transform.base import TransformContext
from app.services.transform.comparison import map_comparison
from app.services.transform.distribution import map_distribution
from app.services.transform.geographic import map_geographic
from app.services.transform.network import map_network
from app.services.transform.time_trend import map_time_trend
from app.validation.viz_compatibility import (
    validate_post_transform,
    validate_pre_transform,
)

_MAPPER: dict[
    tuple[Horizon, VisualizationType],
    Callable[[TransformContext], Visualization],
] = {
    (Horizon.TIME_TREND, VisualizationType.TIME_SERIES): map_time_trend,
    (Horizon.DISTRIBUTION, VisualizationType.BAR_CHART): map_distribution,
    (Horizon.DISTRIBUTION, VisualizationType.HISTOGRAM): map_distribution,
    (Horizon.COMPARISON, VisualizationType.GROUPED_BAR_CHART): map_comparison,
    (Horizon.COMPARISON, VisualizationType.BAR_CHART): map_comparison,
    (Horizon.GEOGRAPHIC, VisualizationType.BAR_CHART): map_geographic,
    (Horizon.NETWORK, VisualizationType.NETWORK_GRAPH): map_network,
}


def transform_studies(context: TransformContext) -> Visualization:
    validate_pre_transform(context)
    mapper = _MAPPER[(context.horizon, context.viz_type)]
    viz = mapper(context)
    validate_post_transform(context, viz)
    return viz
