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


def _intervention_for_label(study: dict[str, Any], label: str) -> str | None:
    for name in study_models.intervention_names(study):
        if slug_id(name) == slug_id(label):
            return name
    return None


def _condition_for_label(study: dict[str, Any], label: str) -> str | None:
    for name in study_models.conditions(study):
        if slug_id(name) == slug_id(label):
            return name
    return None


def _sponsor_matches_label(study: dict[str, Any], label: str) -> bool:
    sponsor = study_models.lead_sponsor_name(study)
    return sponsor is not None and slug_id(sponsor) == slug_id(label)


def _node_excerpt(study: dict[str, Any], label: str) -> str:
    if _sponsor_matches_label(study, label):
        return excerpt_sponsor(study)
    if intervention := _intervention_for_label(study, label):
        return excerpt_intervention(study, intervention)
    if condition := _condition_for_label(study, label):
        return excerpt_condition(study, condition)
    raise ValueError(f"No network node field match for label {label!r}")


def _edge_excerpt(
    study: dict[str, Any],
    edge: _MutableEdge,
    nodes: dict[str, _MutableNode],
) -> str:
    src_label = nodes[edge.source].label
    tgt_label = nodes[edge.target].label

    match edge.label:
        case "sponsored_by":
            return excerpt_sponsor(study)
        case "studied_in":
            if condition := _condition_for_label(study, tgt_label):
                return excerpt_condition(study, condition)
            if condition := _condition_for_label(study, src_label):
                return excerpt_condition(study, condition)
            raise ValueError(
                "No condition endpoint for studied_in edge "
                f"{src_label!r} -> {tgt_label!r}"
            )
        case "co_intervention":
            if intervention := _intervention_for_label(study, src_label):
                return excerpt_intervention(study, intervention)
            if intervention := _intervention_for_label(study, tgt_label):
                return excerpt_intervention(study, intervention)
            raise ValueError(
                "No drug endpoint for co_intervention edge "
                f"{src_label!r} -> {tgt_label!r}"
            )
        case _:
            raise ValueError(f"Unknown network edge label: {edge.label!r}")


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
                excerpt_builder=lambda study, label=node.label: _node_excerpt(
                    study, label
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
                excerpt_builder=lambda study, edge=edge, nodes=nodes: _edge_excerpt(
                    study, edge, nodes
                ),
            ),
        )
        for edge in edges.values()
    ]

    return NetworkGraphVisualization(
        encoding={"nodes": "nodes", "edges": "edges"},
        data=NetworkGraphData(nodes=node_models, edges=edge_models),
    )
