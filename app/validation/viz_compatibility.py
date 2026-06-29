"""Visualization compatibility validation."""

from __future__ import annotations

from pydantic import TypeAdapter

from app.core.schemas.visualization import (
    BarChartVisualization,
    GroupedBarChartVisualization,
    HistogramVisualization,
    NetworkGraphVisualization,
    TimeSeriesVisualization,
    Visualization,
)
from app.domain.horizons import Horizon, is_visualization_compatible
from app.domain.visualization import VisualizationType, assert_never
from app.services.transform.base import TransformContext

VisualizationAdapter = TypeAdapter(Visualization)


class VizValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def validate_pre_transform(context: TransformContext) -> None:
    if not is_visualization_compatible(context.horizon, context.viz_type):
        raise VizValidationError(
            "incompatible_horizon_viz",
            (
                f"Visualization {context.viz_type.value!r} is not allowed for "
                f"horizon {context.horizon.value!r}"
            ),
        )

    if context.viz_type is VisualizationType.SCATTER_PLOT:
        raise VizValidationError(
            "forbidden_viz_type",
            "scatter_plot is not supported for any horizon",
        )

    match context.horizon:
        case Horizon.COMPARISON:
            if not context.comparison_arms:
                raise VizValidationError(
                    "missing_comparison_arms",
                    "Comparison horizon requires comparison_arms",
                )
        case _:
            if not context.studies:
                raise VizValidationError(
                    "empty_studies",
                    "At least one study is required for transformation",
                )

    if context.horizon is Horizon.DISTRIBUTION:
        if context.bucket_field == "enrollment":
            if context.viz_type is not VisualizationType.HISTOGRAM:
                raise VizValidationError(
                    "bucket_viz_mismatch",
                    "Enrollment distribution requires histogram visualization",
                )
        elif context.viz_type is VisualizationType.HISTOGRAM:
            raise VizValidationError(
                "bucket_viz_mismatch",
                "Histogram visualization requires enrollment bucket_field",
            )


def _assert_citations_present(viz: Visualization) -> None:
    match viz:
        case BarChartVisualization() | GroupedBarChartVisualization() | (
            TimeSeriesVisualization()
        ) | HistogramVisualization():
            for row in viz.data:
                count = row.model_dump().get("count", 0)
                if isinstance(count, int) and count > 0 and not row.citations:
                    raise VizValidationError(
                        "missing_citations",
                        "Data rows with count > 0 must include citations",
                    )
        case NetworkGraphVisualization():
            for node in viz.data.nodes:
                if not node.citations:
                    raise VizValidationError(
                        "missing_citations",
                        "Network nodes must include citations",
                    )
            for edge in viz.data.edges:
                if not edge.citations:
                    raise VizValidationError(
                        "missing_citations",
                        "Network edges must include citations",
                    )
        case _ as unreachable:
            assert_never(unreachable)


def validate_post_transform(context: TransformContext, viz: Visualization) -> None:
    validated = VisualizationAdapter.validate_python(viz.model_dump())

    if validated.type != context.viz_type:
        raise VizValidationError(
            "viz_type_mismatch",
            (
                f"Mapper produced {validated.type.value!r} but "
                f"{context.viz_type.value!r} was requested"
            ),
        )

    match validated:
        case BarChartVisualization() | GroupedBarChartVisualization() | (
            TimeSeriesVisualization()
        ) | HistogramVisualization():
            if not validated.data:
                raise VizValidationError(
                    "empty_data",
                    "Visualization has no data rows",
                )
        case NetworkGraphVisualization():
            if not validated.data.nodes and not validated.data.edges:
                raise VizValidationError(
                    "empty_data",
                    "Network visualization has no nodes or edges",
                )
        case _ as unreachable:
            assert_never(unreachable)

    _assert_citations_present(validated)
