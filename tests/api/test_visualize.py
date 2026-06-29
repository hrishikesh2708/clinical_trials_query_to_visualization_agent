"""HTTP integration tests for POST /api/v1/visualize."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.agent.exceptions import AgentError
from app.validation.viz_compatibility import VizValidationError
from tests.api.horizon_mocks import (
    ALL_SCENARIOS,
    HorizonScenario,
    patched_pipeline_steps,
)


def _assert_response_has_citations(body: dict) -> None:
    viz = body["visualization"]
    viz_type = viz["type"]
    if viz_type == "network_graph":
        assert all(node.get("citations") for node in viz["data"]["nodes"])
        assert all(edge.get("citations") for edge in viz["data"]["edges"])
        return
    rows_with_counts = [
        row
        for row in viz["data"]
        if isinstance(row.get("count"), int) and row["count"] > 0
    ]
    assert rows_with_counts, "Expected at least one non-zero data row"
    assert all(row.get("citations") for row in rows_with_counts)


@pytest.mark.parametrize(
    "scenario",
    ALL_SCENARIOS,
    ids=[scenario.name for scenario in ALL_SCENARIOS],
)
def test_visualize_horizon_returns_200(
    client: TestClient, scenario: HorizonScenario
) -> None:
    with patched_pipeline_steps(scenario):
        response = client.post(
            "/api/v1/visualize",
            json=scenario.request.model_dump(mode="json"),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["visualization"]["type"] == scenario.viz_type.value
    assert body["meta"]["title"] == scenario.narrative.title
    assert body["meta"]["total_studies_fetched"] == sum(
        len(studies) for studies in scenario.fetched.studies_per_search
    )
    _assert_response_has_citations(body)


def test_visualize_agent_error_returns_422(client: TestClient) -> None:
    scenario = ALL_SCENARIOS[0]
    with (
        patched_pipeline_steps(scenario),
        patch(
            "app.agent.pipeline.fetch_studies",
            side_effect=AgentError("empty_api_results", "No studies matched query"),
        ),
    ):
        response = client.post(
            "/api/v1/visualize",
            json=scenario.request.model_dump(mode="json"),
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "empty_api_results"
    assert detail["message"] == "No studies matched query"


def test_visualize_viz_validation_error_returns_422(client: TestClient) -> None:
    scenario = ALL_SCENARIOS[0]
    with (
        patched_pipeline_steps(scenario),
        patch(
            "app.agent.pipeline.run_transform",
            side_effect=VizValidationError(
                "incompatible_horizon_viz",
                "Visualization 'bar_chart' is not allowed for horizon 'time_trend'",
            ),
        ),
    ):
        response = client.post(
            "/api/v1/visualize",
            json=scenario.request.model_dump(mode="json"),
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "incompatible_horizon_viz"
    assert "time_trend" in detail["message"]
