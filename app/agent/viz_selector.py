"""Step 4: select visualization type from allowed set."""

from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.agent.exceptions import AgentError
from app.agent.llm import parse_structured
from app.agent.prompts import load_prompt
from app.agent.types import FetchPreview, Intent, VizSelection
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType, assert_never


def build_viz_select_user_message(intent: Intent, preview: FetchPreview) -> str:
    payload = {
        "horizon": intent.horizon.value,
        "bucket_field": intent.bucket_field,
        "suggested_viz_type": (
            intent.suggested_viz_type.value if intent.suggested_viz_type else None
        ),
        "preview": preview.model_dump(mode="json"),
    }
    return json.dumps(payload, indent=2)


def heuristic_viz_type(intent: Intent) -> VisualizationType | None:
    match intent.horizon:
        case Horizon.DISTRIBUTION:
            if intent.bucket_field == "enrollment":
                return VisualizationType.HISTOGRAM
            return VisualizationType.BAR_CHART
        case Horizon.COMPARISON:
            if intent.bucket_field == "phase":
                return VisualizationType.GROUPED_BAR_CHART
            return VisualizationType.BAR_CHART
        case Horizon.TIME_TREND:
            return VisualizationType.TIME_SERIES
        case Horizon.GEOGRAPHIC:
            return VisualizationType.BAR_CHART
        case Horizon.NETWORK:
            return VisualizationType.NETWORK_GRAPH
        case _ as unreachable:
            assert_never(unreachable)


def _resolve_with_fallbacks(
    intent: Intent,
    selection: VizSelection,
    preview: FetchPreview,
) -> VisualizationType:
    allowed = preview.allowed_viz_types
    if selection.viz_type in allowed:
        return selection.viz_type
    if len(allowed) == 1:
        return allowed[0]
    if (
        intent.suggested_viz_type is not None
        and intent.suggested_viz_type in allowed
    ):
        return intent.suggested_viz_type
    heuristic = heuristic_viz_type(intent)
    if heuristic is not None and heuristic in allowed:
        return heuristic
    allowed_values = ", ".join(viz.value for viz in allowed)
    raise AgentError(
        "incompatible_horizon_viz",
        (
            f"Visualization {selection.viz_type.value!r} is not allowed; "
            f"allowed: {allowed_values}"
        ),
    )


def apply_viz_gate(
    intent: Intent,
    selection: VizSelection,
    preview: FetchPreview,
) -> VisualizationType:
    return _resolve_with_fallbacks(intent, selection, preview)


async def select_viz(
    intent: Intent,
    preview: FetchPreview,
    *,
    client: AsyncOpenAI,
    model: str,
) -> VisualizationType:
    system_prompt = load_prompt("viz_select")
    user_content = build_viz_select_user_message(intent, preview)

    selection = await parse_structured(
        client,
        model=model,
        system_prompt=system_prompt,
        user_content=user_content,
        response_format=VizSelection,
    )
    if selection.viz_type in preview.allowed_viz_types:
        return selection.viz_type

    allowed_values = ", ".join(viz.value for viz in preview.allowed_viz_types)
    retry_content = (
        f"{user_content}\n\n"
        "Previous selection was not allowed. "
        f"You must pick exactly one of: {allowed_values}"
    )
    selection = await parse_structured(
        client,
        model=model,
        system_prompt=system_prompt,
        user_content=retry_content,
        response_format=VizSelection,
    )
    return _resolve_with_fallbacks(intent, selection, preview)
