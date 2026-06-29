"""Step 1: parse natural-language visualize requests into structured Intent."""

from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.agent.exceptions import AgentError
from app.agent.llm import parse_structured
from app.agent.prompts import load_prompt
from app.agent.types import Intent
from app.core.schemas.request import VisualizeRequest
from app.domain.horizons import Horizon, allowed_visualization_types
from app.domain.visualization import assert_never

_FILTER_FIELDS = (
    "drug_name",
    "condition",
    "trial_phase",
    "sponsor",
    "country",
    "start_year",
    "end_year",
)


def build_intent_user_message(request: VisualizeRequest) -> str:
    structured_filters = {
        field: getattr(request, field) for field in _FILTER_FIELDS
    }
    payload = {
        "query": request.query,
        "structured_filters": structured_filters,
    }
    return json.dumps(payload, indent=2)


def merge_request_filters(request: VisualizeRequest, llm_intent: Intent) -> Intent:
    filter_updates: dict[str, object] = {}
    for field in _FILTER_FIELDS:
        request_value = getattr(request, field)
        if request_value is not None:
            filter_updates[field] = request_value

    if not filter_updates:
        return llm_intent

    merged_filters = llm_intent.filters.model_copy(update=filter_updates)
    return llm_intent.model_copy(update={"filters": merged_filters})


def apply_intent_gates(intent: Intent) -> Intent:
    match intent.horizon:
        case Horizon.COMPARISON:
            if len(intent.comparison_arm_labels) < 2:
                raise AgentError(
                    "invalid_intent",
                    "Comparison horizon requires at least two comparison_arm_labels",
                )
            updates: dict[str, object] = {}
        case Horizon.DISTRIBUTION:
            updates = {}
            if intent.bucket_field is None:
                updates["bucket_field"] = "phase"
        case Horizon.TIME_TREND:
            updates = {"bucket_field": None}
        case Horizon.GEOGRAPHIC | Horizon.NETWORK:
            updates = {"bucket_field": None}
        case _ as unreachable:
            assert_never(unreachable)

    suggested_viz_type = intent.suggested_viz_type
    if (
        suggested_viz_type is not None
        and suggested_viz_type not in allowed_visualization_types(intent.horizon)
    ):
        updates["suggested_viz_type"] = None

    if not updates:
        return intent
    return intent.model_copy(update=updates)


async def parse_intent(
    request: VisualizeRequest,
    *,
    client: AsyncOpenAI,
    model: str,
) -> Intent:
    system_prompt = load_prompt("intent")
    user_content = build_intent_user_message(request)
    llm_intent = await parse_structured(
        client,
        model=model,
        system_prompt=system_prompt,
        user_content=user_content,
        response_format=Intent,
    )
    merged = merge_request_filters(request, llm_intent)
    return apply_intent_gates(merged)
