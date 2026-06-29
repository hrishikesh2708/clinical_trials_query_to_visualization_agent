"""Network mapper: sponsor, drug, and condition co-occurrence graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

from app.core.schemas.visualization import (
    NetworkEdge,
    NetworkGraphData,
    NetworkGraphVisualization,
    NetworkNode,
)
from app.domain import models as study_models
from app.services.citation_engine import (
    build_citations_for_studies,
    excerpt_condition,
    excerpt_intervention,
    excerpt_sponsor,
    slug_id,
)
from app.services.transform.base import TransformContext


@dataclass
class _MutableNode:
    node_id: str
    label: str
    studies: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class _MutableEdge:
    source: str
    target: str
    label: str
    studies: list[dict[str, Any]] = field(default_factory=list)


def _add_node(
    nodes: dict[str, _MutableNode],
    label: str,
    study: dict[str, Any],
) -> str:
    node_id = slug_id(label)
    if node_id not in nodes:
        nodes[node_id] = _MutableNode(node_id=node_id, label=label)
    nodes[node_id].studies.append(study)
    return node_id


def _add_edge(
    edges: dict[tuple[str, str, str], _MutableEdge],
    source: str,
    target: str,
    label: str,
    study: dict[str, Any],
) -> None:
    if source == target:
        return
    left, right = sorted((source, target))
    key = (left, right, label)
    if key not in edges:
        edges[key] = _MutableEdge(source=left, target=right, label=label)
    edges[key].studies.append(study)


def map_network(context: TransformContext) -> NetworkGraphVisualization:
    nodes: dict[str, _MutableNode] = {}
    edges: dict[tuple[str, str, str], _MutableEdge] = {}

    for study in context.studies:
        sponsor = study_models.lead_sponsor_name(study)
        drugs = study_models.intervention_names(study)
        conditions = study_models.conditions(study)

        sponsor_id: str | None = None
        if sponsor is not None:
            sponsor_id = _add_node(nodes, sponsor, study)

        drug_ids = [_add_node(nodes, drug, study) for drug in drugs]
        condition_ids = [
            _add_node(nodes, condition, study) for condition in conditions
        ]

        if sponsor_id is not None:
            for drug_id in drug_ids:
                _add_edge(edges, sponsor_id, drug_id, "sponsored_by", study)

        for drug_id in drug_ids:
            for condition_id in condition_ids:
                _add_edge(edges, drug_id, condition_id, "studied_in", study)

        for left_id, right_id in combinations(sorted(set(drug_ids)), 2):
            _add_edge(edges, left_id, right_id, "co_intervention", study)

    node_models = [
        NetworkNode(
            id=node.node_id,
            label=node.label,
            citations=build_citations_for_studies(
                node.studies,
                excerpt_builder=lambda study, label=node.label: (
                    excerpt_sponsor(study)
                    if study_models.lead_sponsor_name(study) == label
                    else excerpt_intervention(study, label)
                    if label in study_models.intervention_names(study)
                    else excerpt_condition(study, label)
                ),
            ),
        )
        for node in nodes.values()
    ]

    edge_models = [
        NetworkEdge(
            source=edge.source,
            target=edge.target,
            label=edge.label,
            citations=build_citations_for_studies(
                edge.studies,
                excerpt_builder=lambda study, edge=edge, nodes=nodes: (
                    excerpt_sponsor(study)
                    if edge.label == "sponsored_by"
                    else excerpt_condition(study, nodes[edge.target].label)
                    if edge.label == "studied_in"
                    else excerpt_intervention(study, nodes[edge.source].label)
                ),
            ),
        )
        for edge in edges.values()
    ]

    return NetworkGraphVisualization(
        encoding={"nodes": "nodes", "edges": "edges"},
        data=NetworkGraphData(nodes=node_models, edges=edge_models),
    )
