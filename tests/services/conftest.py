"""Shared fixtures for service-layer tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.core.schemas.visualization import (
    BarChartVisualization,
    GroupedBarChartVisualization,
    HistogramVisualization,
    NetworkGraphVisualization,
    TimeSeriesVisualization,
    Visualization,
)
from app.infrastructure.ctgov.enums import CtgovEnums

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VIZ_DIR = PROJECT_ROOT / "tests" / "fixtures" / "expected_viz"

ENUMS_FIXTURE = [
    {
        "type": "Phase",
        "pieces": ["Phase"],
        "values": [
            {"value": "NA", "legacyValue": "Not Applicable"},
            {"value": "EARLY_PHASE1", "legacyValue": "Early Phase 1"},
            {"value": "PHASE1", "legacyValue": "Phase 1"},
            {"value": "PHASE2", "legacyValue": "Phase 2"},
            {"value": "PHASE3", "legacyValue": "Phase 3"},
            {"value": "PHASE4", "legacyValue": "Phase 4"},
        ],
    },
    {
        "type": "Status",
        "pieces": ["OverallStatus"],
        "values": [
            {"value": "RECRUITING", "legacyValue": "Recruiting"},
            {"value": "COMPLETED", "legacyValue": "Completed"},
            {"value": "TERMINATED", "legacyValue": "Terminated"},
        ],
    },
]


@pytest.fixture
def ctgov_enums() -> CtgovEnums:
    return CtgovEnums.from_api(ENUMS_FIXTURE)


def load_expected_viz(stem: str) -> dict[str, Any]:
    path = EXPECTED_VIZ_DIR / f"{stem}.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def assert_excerpts_in_source(
    studies: list[dict[str, Any]],
    citations: list[dict[str, Any]],
) -> None:
    serialized = [json.dumps(study, ensure_ascii=False) for study in studies]
    for citation in citations:
        excerpt = citation["excerpt"]
        nct_id = citation["nct_id"]
        source = next(
            (
                study_json
                for study_json in serialized
                if nct_id in study_json
            ),
            None,
        )
        assert source is not None
        assert excerpt in source


def assert_all_rows_have_citations(viz: Visualization) -> None:
    match viz:
        case BarChartVisualization() | GroupedBarChartVisualization() | (
            TimeSeriesVisualization()
        ) | HistogramVisualization():
            for row in viz.data:
                count = row.model_dump().get("count", 0)
                if isinstance(count, int) and count > 0:
                    assert row.citations, "Expected citations on non-zero row"
        case NetworkGraphVisualization():
            pass
        case _:
            pytest.fail(f"Unexpected visualization type: {type(viz)!r}")


def assert_all_network_citations(viz: NetworkGraphVisualization) -> None:
    assert all(node.citations for node in viz.data.nodes), "Node missing citations"
    assert all(edge.citations for edge in viz.data.edges), "Edge missing citations"


def assert_all_excerpts_in_source(
    studies: list[dict[str, Any]],
    viz: Visualization,
) -> None:
    match viz:
        case BarChartVisualization() | GroupedBarChartVisualization() | (
            TimeSeriesVisualization()
        ) | HistogramVisualization():
            for row in viz.data:
                if row.citations:
                    assert_excerpts_in_source(
                        studies,
                        [citation.model_dump() for citation in row.citations],
                    )
        case NetworkGraphVisualization():
            for node in viz.data.nodes:
                if node.citations:
                    assert_excerpts_in_source(
                        studies,
                        [citation.model_dump() for citation in node.citations],
                    )
            for edge in viz.data.edges:
                if edge.citations:
                    assert_excerpts_in_source(
                        studies,
                        [citation.model_dump() for citation in edge.citations],
                    )
        case _:
            pytest.fail(f"Unexpected visualization type: {type(viz)!r}")
