"""Shared OpenAI structured-output helper for pipeline steps."""

from __future__ import annotations

from typing import TypeVar

import openai
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.agent.exceptions import AgentError

T = TypeVar("T", bound=BaseModel)


async def parse_structured(
    client: AsyncOpenAI,
    *,
    model: str,
    system_prompt: str,
    user_content: str,
    response_format: type[T],
) -> T:
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            completion = await client.beta.chat.completions.parse(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format=response_format,
            )
            parsed = completion.choices[0].message.parsed
            if parsed is None:
                raise AgentError(
                    "llm_error",
                    "OpenAI returned no parsed structured output",
                )
            return parsed
        except AgentError:
            raise
        except openai.OpenAIError as exc:
            last_error = exc
            if attempt == 0:
                continue
            raise AgentError(
                "llm_error",
                f"OpenAI request failed after retry: {exc}",
            ) from exc

    raise AgentError(
        "llm_error",
        f"OpenAI request failed: {last_error}",
    ) from last_error
