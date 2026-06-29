"""Step 2: LLM query draft plus Python normalization."""

from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.agent.exceptions import AgentError
from app.agent.llm import parse_structured
from app.agent.prompts import load_prompt
from app.agent.query_normalizer import normalize_query_plan
from app.agent.types import APIQueryPlan, Intent, QueryPlanDraft
from app.infrastructure.ctgov.enums import CtgovEnumsLoader


def build_query_plan_user_message(intent: Intent) -> str:
    payload = {
        "horizon": intent.horizon.value,
        "filters": intent.filters.model_dump(),
        "bucket_field": intent.bucket_field,
        "comparison_arm_labels": list(intent.comparison_arm_labels),
        "time_granularity": intent.time_granularity.value,
        "assumptions": intent.assumptions,
    }
    return json.dumps(payload, indent=2)


async def plan_query(
    intent: Intent,
    *,
    client: AsyncOpenAI,
    model: str,
    enums_loader: CtgovEnumsLoader,
    page_size: int = 100,
) -> APIQueryPlan:
    system_prompt = load_prompt("query_plan")
    user_content = build_query_plan_user_message(intent)
    enums = enums_loader.load()
    last_error: AgentError | None = None

    for attempt in range(2):
        try:
            draft = await parse_structured(
                client,
                model=model,
                system_prompt=system_prompt,
                user_content=user_content,
                response_format=QueryPlanDraft,
            )
            return normalize_query_plan(
                intent,
                draft,
                enums=enums,
                page_size=page_size,
            )
        except AgentError as exc:
            if exc.code != "invalid_query_plan" or attempt == 1:
                raise
            last_error = exc
            user_content = (
                f"{build_query_plan_user_message(intent)}\n\n"
                f"Previous attempt failed validation:\n{exc.message}"
            )

    raise last_error  # pragma: no cover
