"""Assert all submission examples include valid citation structure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_ROOT / "examples"

EXAMPLE_FILES = sorted(EXAMPLES_DIR.glob("*.json"))


def _load_example(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _assert_citation_shape(citation: dict, *, context: str) -> None:
    assert "nct_id" in citation, f"{context}: missing nct_id"
    assert "excerpt" in citation, f"{context}: missing excerpt"
    assert citation["nct_id"], f"{context}: empty nct_id"
    assert citation["excerpt"], f"{context}: empty excerpt"


@pytest.mark.parametrize("example_path", EXAMPLE_FILES, ids=lambda p: p.name)
def test_example_has_citations_on_all_data(example_path: Path) -> None:
    payload = _load_example(example_path)
    viz = payload["visualization"]
    viz_type = viz["type"]

    if viz_type == "network_graph":
        nodes = viz["data"]["nodes"]
        edges = viz["data"]["edges"]
        for index, node in enumerate(nodes):
            assert node.get("citations"), f"node[{index}] missing citations"
            for citation in node["citations"]:
                _assert_citation_shape(citation, context=f"node[{index}]")
        for index, edge in enumerate(edges):
            assert edge.get("citations"), f"edge[{index}] missing citations"
            for citation in edge["citations"]:
                _assert_citation_shape(citation, context=f"edge[{index}]")
        return

    for index, row in enumerate(viz["data"]):
        count = row.get("count", 0)
        if isinstance(count, int) and count > 0:
            assert row.get("citations"), f"row[{index}] missing citations"
            for citation in row["citations"]:
                _assert_citation_shape(citation, context=f"row[{index}]")
