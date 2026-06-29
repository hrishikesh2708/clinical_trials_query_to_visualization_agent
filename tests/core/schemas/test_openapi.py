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


def test_visualize_endpoint_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/visualize" in paths
    post = paths["/api/v1/visualize"]["post"]
    assert post["requestBody"]["content"]["application/json"]["schema"][
        "$ref"
    ] == "#/components/schemas/VisualizeRequest"
    assert post["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ] == "#/components/schemas/VisualizeResponse"
