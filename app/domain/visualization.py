from enum import StrEnum
from typing import Never, TypeVar

T = TypeVar("T")


class VisualizationType(StrEnum):
    BAR_CHART = "bar_chart"
    GROUPED_BAR_CHART = "grouped_bar_chart"
    TIME_SERIES = "time_series"
    HISTOGRAM = "histogram"
    SCATTER_PLOT = "scatter_plot"
    NETWORK_GRAPH = "network_graph"


class TimeGranularity(StrEnum):
    YEAR = "year"
    MONTH = "month"
    QUARTER = "quarter"
    DAY = "day"


class DataSource(StrEnum):
    CLINICALTRIALS_GOV = "clinicaltrials.gov"


def visualization_type_label(viz_type: VisualizationType) -> str:
    """Return a human-readable label for each visualization type."""
    match viz_type:
        case VisualizationType.BAR_CHART:
            return "Bar Chart"
        case VisualizationType.GROUPED_BAR_CHART:
            return "Grouped Bar Chart"
        case VisualizationType.TIME_SERIES:
            return "Time Series"
        case VisualizationType.HISTOGRAM:
            return "Histogram"
        case VisualizationType.SCATTER_PLOT:
            return "Scatter Plot"
        case VisualizationType.NETWORK_GRAPH:
            return "Network Graph"
        case _ as unreachable:
            assert_never(unreachable)


def assert_never(value: Never) -> Never:
    raise AssertionError(f"Unhandled value: {value!r}")
