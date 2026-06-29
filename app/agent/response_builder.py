"""Step 6: LLM response narrative and VisualizeResponse assembly."""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.agent.llm import parse_structured
from app.agent.prompts import load_prompt
from app.agent.types import FetchResult, Intent, ResponseNarrative
from app.core.schemas.response import AppliedFilters, ResponseMeta, VisualizeResponse
from app.core.schemas.visualization import NetworkGraphVisualization, Visualization
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType, assert_never


def _visualization_summary(viz: Visualization) -> dict[str, Any]:
    match viz.type:
        case VisualizationType.NETWORK_GRAPH:
            assert isinstance(viz, NetworkGraphVisualization)
            return {
                "node_count": len(viz.data.nodes),
                "edge_count": len(viz.data.edges),
            }
        case (
            VisualizationType.BAR_CHART
            | VisualizationType.GROUPED_BAR_CHART
            | VisualizationType.TIME_SERIES
            | VisualizationType.HISTOGRAM
            | VisualizationType.SCATTER_PLOT
        ):
            return {"row_count": len(viz.data)}
        case _ as unreachable:
            assert_never(unreachable)


def build_response_user_message(
    intent: Intent,
    viz: Visualization,
    viz_type: VisualizationType,
    fetched: FetchResult,
) -> str:
    payload = {
        "horizon": intent.horizon.value,
        "bucket_field": intent.bucket_field,
        "time_granularity": intent.time_granularity.value,
        "comparison_arm_labels": list(intent.comparison_arm_labels),
        "viz_type": viz_type.value,
        "encoding": viz.encoding.model_dump(),
        "visualization_summary": _visualization_summary(viz),
        "total_studies_fetched": sum(
            len(studies) for studies in fetched.studies_per_search
        ),
        "assumptions": intent.assumptions,
    }
    return json.dumps(payload, indent=2)


async def build_response_narrative(
    intent: Intent,
    viz: Visualization,
    viz_type: VisualizationType,
    fetched: FetchResult,
    *,
    client: AsyncOpenAI,
    model: str,
    temperature: float = 0.0,
) -> ResponseNarrative:
    system_prompt = load_prompt("response")
    user_content = build_response_user_message(intent, viz, viz_type, fetched)
    return await parse_structured(
        client,
        model=model,
        system_prompt=system_prompt,
        user_content=user_content,
        response_format=ResponseNarrative,
        temperature=temperature,
    )


def assemble_visualize_response(
    intent: Intent,
    viz: Visualization,
    narrative: ResponseNarrative,
    fetched: FetchResult,
) -> VisualizeResponse:
    return VisualizeResponse(
        visualization=viz,
        meta=ResponseMeta(
            title=narrative.title,
            filters=AppliedFilters(**intent.filters.model_dump()),
            assumptions=intent.assumptions + narrative.additional_assumptions,
            time_granularity=(
                intent.time_granularity
                if intent.horizon is Horizon.TIME_TREND
                else None
            ),
            total_studies_fetched=sum(
                len(studies) for studies in fetched.studies_per_search
            ),
            interpretation_notes=narrative.interpretation_notes,
        ),
    )


async def build_visualize_response(
    intent: Intent,
    viz: Visualization,
    viz_type: VisualizationType,
    fetched: FetchResult,
    *,
    client: AsyncOpenAI,
    model: str,
    temperature: float = 0.0,
) -> VisualizeResponse:
    narrative = await build_response_narrative(
        intent,
        viz,
        viz_type,
        fetched,
        client=client,
        model=model,
        temperature=temperature,
    )
    return assemble_visualize_response(intent, viz, narrative, fetched)
