"""Tests for Step 3 API caller."""

import json
from pathlib import Path

import pytest

from app.agent.api_caller import build_fetch_preview, fetch_studies
from app.agent.exceptions import AgentError
from app.agent.types import APIQueryPlan, PlannedSearch
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType
from app.infrastructure.ctgov.client import CtgovClient
from app.infrastructure.ctgov.models import StudiesSearchParams

BASE_URL = "https://clinicaltrials.gov/api/v2"
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "api"


def _client() -> CtgovClient:
    return CtgovClient(BASE_URL, timeout=5.0)


def _load_fixture(name: str) -> dict:
    with (FIXTURES_DIR / f"{name}.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _time_trend_plan() -> APIQueryPlan:
    return APIQueryPlan(
        horizon=Horizon.TIME_TREND,
        searches=[
            PlannedSearch(
                params=StudiesSearchParams(
                    query_intr="Pembrolizumab",
                    filter_advanced="AREA[StartDate]2015",
                    count_total=True,
                    fields=["NCTId", "StartDateStruct"],
                ),
                fields=["NCTId", "StartDateStruct"],
            )
        ],
    )


def _comparison_plan() -> APIQueryPlan:
    return APIQueryPlan(
        horizon=Horizon.COMPARISON,
        searches=[
            PlannedSearch(
                label="Pembrolizumab",
                params=StudiesSearchParams(
                    query_intr="Pembrolizumab",
                    count_total=True,
                    fields=["NCTId", "Phase", "InterventionName"],
                ),
                fields=["NCTId", "Phase", "InterventionName"],
            ),
            PlannedSearch(
                label="Nivolumab",
                params=StudiesSearchParams(
                    query_intr="Nivolumab",
                    count_total=True,
                    fields=["NCTId", "Phase", "InterventionName"],
                ),
                fields=["NCTId", "Phase", "InterventionName"],
            ),
        ],
    )


def test_build_fetch_preview_time_trend_allowed_types() -> None:
    plan = _time_trend_plan()
    studies = _load_fixture("time_trend_pembrolizumab")["studies"]
    preview = build_fetch_preview(plan, [studies], [42])
    assert preview.allowed_viz_types == [VisualizationType.TIME_SERIES]
    assert preview.searches[0].studies_fetched == len(studies)
    assert preview.searches[0].total_count == 42


def test_fetch_studies_single_search_success(httpx_mock) -> None:
    payload = _load_fixture("time_trend_pembrolizumab")
    payload = {**payload, "totalCount": 120}
    payload.pop("nextPageToken", None)
    httpx_mock.add_response(json=payload)

    result = fetch_studies(_time_trend_plan(), _client())

    assert len(result.studies_per_search) == 1
    assert len(result.studies_per_search[0]) == len(payload["studies"])
    assert result.preview.searches[0].total_count == 120
    assert result.preview.allowed_viz_types == [VisualizationType.TIME_SERIES]


def test_fetch_studies_comparison_two_sequential_searches(httpx_mock) -> None:
    pembrolizumab = {**_load_fixture("comparison_pembrolizumab_arm"), "totalCount": 50}
    nivolumab = {**_load_fixture("comparison_nivolumab_arm"), "totalCount": 40}
    pembrolizumab.pop("nextPageToken", None)
    nivolumab.pop("nextPageToken", None)
    httpx_mock.add_response(json=pembrolizumab)
    httpx_mock.add_response(json=nivolumab)

    result = fetch_studies(_comparison_plan(), _client())

    assert len(result.studies_per_search) == 2
    assert result.preview.searches[0].label == "Pembrolizumab"
    assert result.preview.searches[1].label == "Nivolumab"
    assert len(httpx_mock.get_requests()) == 2


def test_fetch_studies_empty_results_raises_empty_api_results(httpx_mock) -> None:
    httpx_mock.add_response(json=_load_fixture("studies_empty"))

    with pytest.raises(AgentError) as exc_info:
        fetch_studies(_time_trend_plan(), _client())

    assert exc_info.value.code == "empty_api_results"
