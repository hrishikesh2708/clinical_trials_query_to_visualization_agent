from fastapi.testclient import TestClient

from app.main import app

EXPECTED_SCHEMA_NAMES = {
    "VisualizeRequest",
    "VisualizeResponse",
    "BarChartVisualization",
    "GroupedBarChartVisualization",
    "TimeSeriesVisualization",
    "HistogramVisualization",
    "ScatterPlotVisualization",
    "NetworkGraphVisualization",
    "Citation",
    "ResponseMeta",
    "AppliedFilters",
}


def test_openapi_contains_schema_components() -> None:
    schemas = app.openapi()["components"]["schemas"]
    missing = EXPECTED_SCHEMA_NAMES - set(schemas)
    assert not missing, f"Missing OpenAPI schemas: {missing}"


def test_visualize_stub_returns_501() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/visualize",
        json={"query": "How many trials are recruiting?"},
    )
    assert response.status_code == 501
    assert response.json()["detail"] == "Not implemented until Stage 9"
