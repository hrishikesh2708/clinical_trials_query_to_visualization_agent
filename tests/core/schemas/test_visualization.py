from typing import Any

import pytest
from pydantic import TypeAdapter

from app.core.schemas.visualization import (
    BarChartVisualization,
    GroupedBarChartVisualization,
    HistogramVisualization,
    NetworkGraphVisualization,
    ScatterPlotVisualization,
    TimeSeriesVisualization,
    Visualization,
    visualization_data_keys,
)
from app.domain.visualization import VisualizationType, visualization_type_label

VisualizationAdapter = TypeAdapter(Visualization)

BAR_CHART_PAYLOAD: dict[str, Any] = {
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

GROUPED_BAR_CHART_PAYLOAD: dict[str, Any] = {
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

TIME_SERIES_PAYLOAD: dict[str, Any] = {
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

HISTOGRAM_PAYLOAD: dict[str, Any] = {
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

SCATTER_PLOT_PAYLOAD: dict[str, Any] = {
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

NETWORK_GRAPH_PAYLOAD: dict[str, Any] = {
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
            {"id": "melanoma", "label": "Melanoma", "citations": []},
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

ALL_VIZ_PAYLOADS = [
    (BarChartVisualization, BAR_CHART_PAYLOAD),
    (GroupedBarChartVisualization, GROUPED_BAR_CHART_PAYLOAD),
    (TimeSeriesVisualization, TIME_SERIES_PAYLOAD),
    (HistogramVisualization, HISTOGRAM_PAYLOAD),
    (ScatterPlotVisualization, SCATTER_PLOT_PAYLOAD),
    (NetworkGraphVisualization, NETWORK_GRAPH_PAYLOAD),
]


@pytest.mark.parametrize(("model_cls", "payload"), ALL_VIZ_PAYLOADS)
def test_visualization_round_trip_per_type(
    model_cls: type, payload: dict[str, Any]
) -> None:
    original = model_cls.model_validate(payload)
    json_str = original.model_dump_json()
    restored = model_cls.model_validate_json(json_str)
    assert restored == original


@pytest.mark.parametrize(("model_cls", "payload"), ALL_VIZ_PAYLOADS)
def test_discriminated_union_parses_per_type(
    model_cls: type, payload: dict[str, Any]
) -> None:
    parsed = VisualizationAdapter.validate_python(payload)
    assert isinstance(parsed, model_cls)


def test_network_graph_citations_on_nodes_and_edges() -> None:
    viz = NetworkGraphVisualization.model_validate(NETWORK_GRAPH_PAYLOAD)
    assert viz.data.nodes[0].citations[0].nct_id == "NCT01234567"
    assert viz.data.edges[0].citations[0].excerpt == "Condition: Melanoma."


def test_tabular_row_preserves_extra_encoding_fields() -> None:
    viz = BarChartVisualization.model_validate(BAR_CHART_PAYLOAD)
    row = viz.data[0]
    assert row.phase == "Phase 2"  # type: ignore[attr-defined]
    assert row.count == 42  # type: ignore[attr-defined]


@pytest.mark.parametrize(("viz_type", "expected_label"), [
    (VisualizationType.BAR_CHART, "Bar Chart"),
    (VisualizationType.GROUPED_BAR_CHART, "Grouped Bar Chart"),
    (VisualizationType.TIME_SERIES, "Time Series"),
    (VisualizationType.HISTOGRAM, "Histogram"),
    (VisualizationType.SCATTER_PLOT, "Scatter Plot"),
    (VisualizationType.NETWORK_GRAPH, "Network Graph"),
])
def test_visualization_type_label_exhaustive(
    viz_type: VisualizationType, expected_label: str
) -> None:
    assert visualization_type_label(viz_type) == expected_label


@pytest.mark.parametrize("payload", [
    BAR_CHART_PAYLOAD,
    GROUPED_BAR_CHART_PAYLOAD,
    TIME_SERIES_PAYLOAD,
    HISTOGRAM_PAYLOAD,
    SCATTER_PLOT_PAYLOAD,
    NETWORK_GRAPH_PAYLOAD,
])
def test_visualization_data_keys_exhaustive(payload: dict[str, Any]) -> None:
    viz = VisualizationAdapter.validate_python(payload)
    keys = visualization_data_keys(viz)
    assert isinstance(keys, dict)
    assert len(keys) >= 2
