from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.visualization import VisualizationType, assert_never

# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------


class Citation(BaseModel):
    nct_id: str = Field(..., min_length=1)
    excerpt: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Encoding models (field-name mappings into data rows)
# ---------------------------------------------------------------------------


class BarChartEncoding(BaseModel):
    x: str
    y: str


class GroupedBarChartEncoding(BaseModel):
    x: str
    y: str
    series: str


class TimeSeriesEncoding(BaseModel):
    x: str
    y: str
    series: str | None = None


class HistogramEncoding(BaseModel):
    x: str
    y: str


class ScatterPlotEncoding(BaseModel):
    x: str
    y: str
    color: str | None = None
    label: str | None = None


class NetworkGraphEncoding(BaseModel):
    nodes: str
    edges: str


# ---------------------------------------------------------------------------
# Data row models
# ---------------------------------------------------------------------------


class TabularDataRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    citations: list[Citation] = Field(default_factory=list)


class BarChartDataRow(TabularDataRow):
    pass


class GroupedBarChartDataRow(TabularDataRow):
    pass


class TimeSeriesDataRow(TabularDataRow):
    pass


class HistogramDataRow(TabularDataRow):
    pass


class ScatterPlotDataRow(TabularDataRow):
    pass


class NetworkNode(BaseModel):
    id: str
    label: str | None = None
    citations: list[Citation] = Field(default_factory=list)


class NetworkEdge(BaseModel):
    source: str
    target: str
    label: str | None = None
    citations: list[Citation] = Field(default_factory=list)


class NetworkGraphData(BaseModel):
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]


# ---------------------------------------------------------------------------
# Per-type visualization models
# ---------------------------------------------------------------------------


class BarChartVisualization(BaseModel):
    type: Literal[VisualizationType.BAR_CHART] = VisualizationType.BAR_CHART
    encoding: BarChartEncoding
    data: list[BarChartDataRow]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "bar_chart",
                    "encoding": {"x": "phase", "y": "count"},
                    "data": [
                        {
                            "phase": "Phase 2",
                            "count": 42,
                            "citations": [
                                {
                                    "nct_id": "NCT01234567",
                                    "excerpt": "Phase 2 study of pembrolizumab.",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    )


class GroupedBarChartVisualization(BaseModel):
    type: Literal[VisualizationType.GROUPED_BAR_CHART] = (
        VisualizationType.GROUPED_BAR_CHART
    )
    encoding: GroupedBarChartEncoding
    data: list[GroupedBarChartDataRow]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "grouped_bar_chart",
                    "encoding": {"x": "phase", "y": "count", "series": "status"},
                    "data": [
                        {
                            "phase": "Phase 2",
                            "status": "Recruiting",
                            "count": 12,
                            "citations": [],
                        }
                    ],
                }
            ]
        }
    )


class TimeSeriesVisualization(BaseModel):
    type: Literal[VisualizationType.TIME_SERIES] = VisualizationType.TIME_SERIES
    encoding: TimeSeriesEncoding
    data: list[TimeSeriesDataRow]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "time_series",
                    "encoding": {"x": "year", "y": "count", "series": "drug"},
                    "data": [
                        {
                            "year": 2015,
                            "drug": "Pembrolizumab",
                            "count": 8,
                            "citations": [
                                {
                                    "nct_id": "NCT01234567",
                                    "excerpt": "Study start date: 2015-03-01.",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    )


class HistogramVisualization(BaseModel):
    type: Literal[VisualizationType.HISTOGRAM] = VisualizationType.HISTOGRAM
    encoding: HistogramEncoding
    data: list[HistogramDataRow]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "histogram",
                    "encoding": {"x": "enrollment_bin", "y": "count"},
                    "data": [
                        {
                            "enrollment_bin": "0-50",
                            "count": 15,
                            "citations": [],
                        }
                    ],
                }
            ]
        }
    )


class ScatterPlotVisualization(BaseModel):
    type: Literal[VisualizationType.SCATTER_PLOT] = VisualizationType.SCATTER_PLOT
    encoding: ScatterPlotEncoding
    data: list[ScatterPlotDataRow]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "scatter_plot",
                    "encoding": {
                        "x": "enrollment",
                        "y": "duration_months",
                        "color": "phase",
                        "label": "nct_id",
                    },
                    "data": [
                        {
                            "enrollment": 120,
                            "duration_months": 24,
                            "phase": "Phase 3",
                            "nct_id": "NCT01234567",
                            "citations": [
                                {
                                    "nct_id": "NCT01234567",
                                    "excerpt": "Enrollment: 120 participants.",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    )


class NetworkGraphVisualization(BaseModel):
    type: Literal[VisualizationType.NETWORK_GRAPH] = VisualizationType.NETWORK_GRAPH
    encoding: NetworkGraphEncoding
    data: NetworkGraphData

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "network_graph",
                    "encoding": {"nodes": "nodes", "edges": "edges"},
                    "data": {
                        "nodes": [
                            {
                                "id": "pembrolizumab",
                                "label": "Pembrolizumab",
                                "citations": [
                                    {
                                        "nct_id": "NCT01234567",
                                        "excerpt": "Intervention: Pembrolizumab.",
                                    }
                                ],
                            },
                            {
                                "id": "melanoma",
                                "label": "Melanoma",
                                "citations": [],
                            },
                        ],
                        "edges": [
                            {
                                "source": "pembrolizumab",
                                "target": "melanoma",
                                "label": "studied_in",
                                "citations": [
                                    {
                                        "nct_id": "NCT01234567",
                                        "excerpt": "Condition: Melanoma.",
                                    }
                                ],
                            }
                        ],
                    },
                }
            ]
        }
    )


Visualization = Annotated[
    BarChartVisualization
    | GroupedBarChartVisualization
    | TimeSeriesVisualization
    | HistogramVisualization
    | ScatterPlotVisualization
    | NetworkGraphVisualization,
    Field(discriminator="type"),
]


def visualization_data_keys(viz: Visualization) -> dict[str, Any]:
    """Return encoding field mappings for a visualization."""
    match viz:
        case BarChartVisualization(encoding=encoding):
            return {"x": encoding.x, "y": encoding.y}
        case GroupedBarChartVisualization(encoding=encoding):
            return {
                "x": encoding.x,
                "y": encoding.y,
                "series": encoding.series,
            }
        case TimeSeriesVisualization(encoding=encoding):
            keys: dict[str, Any] = {"x": encoding.x, "y": encoding.y}
            if encoding.series is not None:
                keys["series"] = encoding.series
            return keys
        case HistogramVisualization(encoding=encoding):
            return {"x": encoding.x, "y": encoding.y}
        case ScatterPlotVisualization(encoding=encoding):
            keys = {"x": encoding.x, "y": encoding.y}
            if encoding.color is not None:
                keys["color"] = encoding.color
            if encoding.label is not None:
                keys["label"] = encoding.label
            return keys
        case NetworkGraphVisualization(encoding=encoding):
            return {"nodes": encoding.nodes, "edges": encoding.edges}
        case _ as unreachable:
            assert_never(unreachable)
