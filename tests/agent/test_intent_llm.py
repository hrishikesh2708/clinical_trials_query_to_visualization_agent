"""Tests for intent parser LLM integration (mocked)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest
from pydantic import BaseModel

from app.agent.exceptions import AgentError
from app.agent.intent_parser import parse_intent
from app.agent.llm import parse_structured
from app.agent.types import Intent, ResolvedFilters
from app.core.schemas.request import VisualizeRequest
from app.domain.horizons import Horizon
from app.domain.visualization import VisualizationType


class _Shape(BaseModel):
    value: str


@pytest.fixture
def time_trend_intent() -> Intent:
    return Intent(
        horizon=Horizon.TIME_TREND,
        filters=ResolvedFilters(drug_name="Pembrolizumab", start_year=2015),
        suggested_viz_type=VisualizationType.TIME_SERIES,
        assumptions=["Using study start date."],
    )


def test_parse_intent_returns_merged_and_gated_intent(
    time_trend_intent: Intent,
) -> None:
    request = VisualizeRequest(
        query="Trials per year for pembrolizumab since 2015",
        drug_name="Pembrolizumab",
        start_year=2015,
    )
    client = AsyncMock()

    with patch(
        "app.agent.intent_parser.parse_structured",
        new_callable=AsyncMock,
        return_value=time_trend_intent,
    ) as mock_parse:
        result = asyncio.run(parse_intent(request, client=client, model="gpt-4o-mini"))

    mock_parse.assert_awaited_once()
    assert result.horizon is Horizon.TIME_TREND
    assert result.filters.drug_name == "Pembrolizumab"
    assert result.filters.start_year == 2015
    assert result.bucket_field is None


def _completion_with_parsed(parsed: BaseModel) -> MagicMock:
    message = MagicMock()
    message.parsed = parsed
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    return completion


def test_parse_structured_forwards_temperature() -> None:
    client = AsyncMock()
    client.beta.chat.completions.parse = AsyncMock(
        return_value=_completion_with_parsed(_Shape(value="ok")),
    )

    asyncio.run(
        parse_structured(
            client,
            model="gpt-4o-mini",
            system_prompt="sys",
            user_content="user",
            response_format=_Shape,
            temperature=0.0,
        )
    )

    call_kwargs = client.beta.chat.completions.parse.await_args.kwargs
    assert call_kwargs["temperature"] == 0.0


def test_parse_structured_retries_once_on_openai_error() -> None:
    client = AsyncMock()
    client.beta.chat.completions.parse = AsyncMock(
        side_effect=[
            openai.APIError("rate limited", request=MagicMock(), body=None),
            _completion_with_parsed(_Shape(value="ok")),
        ]
    )

    result = asyncio.run(
        parse_structured(
            client,
            model="gpt-4o-mini",
            system_prompt="sys",
            user_content="user",
            response_format=_Shape,
        )
    )
    assert result.value == "ok"
    assert client.beta.chat.completions.parse.await_count == 2


def test_parse_structured_raises_llm_error_after_retry() -> None:
    client = AsyncMock()
    client.beta.chat.completions.parse = AsyncMock(
        side_effect=openai.APIError("down", request=MagicMock(), body=None),
    )

    with pytest.raises(AgentError) as exc_info:
        asyncio.run(
            parse_structured(
                client,
                model="gpt-4o-mini",
                system_prompt="sys",
                user_content="user",
                response_format=_Shape,
            )
        )

    assert exc_info.value.code == "llm_error"
    assert client.beta.chat.completions.parse.await_count == 2
