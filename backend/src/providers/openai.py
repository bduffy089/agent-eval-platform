"""OpenAI provider.

Uses the Responses API style via the chat.completions interface for Phase 1.
OpenAI does not expose explicit prompt-cache token counts the way Anthropic does,
so `cache_read_tokens` and `cache_write_tokens` always return 0 here. The dashboard
can still render the columns; they will just be empty for OpenAI runs.
"""

from __future__ import annotations

import json
import time
from typing import Any

from openai import AsyncOpenAI

from ..config import get_settings
from .base import CompletionResponse, Provider, TokenUsage, ToolCall

OPENAI_PRICING: dict[str, dict[str, float]] = {
    "gpt-5": {"input": 5.00, "output": 15.00},
    "gpt-5-mini": {"input": 1.00, "output": 4.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "o3": {"input": 10.00, "output": 40.00},
    "o3-mini": {"input": 1.10, "output": 4.40},
}


def _price_lookup(model: str) -> dict[str, float]:
    if model in OPENAI_PRICING:
        return OPENAI_PRICING[model]
    for key, prices in OPENAI_PRICING.items():
        if model.startswith(key):
            return prices
    return {"input": 2.50, "output": 10.00}


def compute_cost_usd(model: str, usage: TokenUsage) -> float:
    p = _price_lookup(model)
    input_dollars = (usage.input_tokens * p["input"]) / 1_000_000
    output_dollars = (usage.output_tokens * p["output"]) / 1_000_000
    return round(input_dollars + output_dollars, 6)


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or get_settings().openai_api_key
        self._client = AsyncOpenAI(api_key=key) if key else None

    async def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> CompletionResponse:
        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY not configured")

        chat_messages: list[dict[str, Any]] = []
        if system:
            chat_messages.append({"role": "system", "content": system})
        chat_messages.extend(messages)

        request: dict[str, Any] = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
        }
        if tools:
            request["tools"] = tools
        request.update(kwargs)

        start = time.perf_counter()
        resp = await self._client.chat.completions.create(**request)
        latency_ms = int((time.perf_counter() - start) * 1000)

        choice = resp.choices[0]
        message = choice.message
        content = message.content or ""

        tool_calls: list[ToolCall] = []
        for tc in message.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            except json.JSONDecodeError:
                args = {"_raw": tc.function.arguments}
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        u = resp.usage
        usage = TokenUsage(
            input_tokens=getattr(u, "prompt_tokens", 0) or 0,
            output_tokens=getattr(u, "completion_tokens", 0) or 0,
            cache_read_tokens=0,
            cache_write_tokens=0,
        )

        return CompletionResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            cost_usd=compute_cost_usd(model, usage),
            latency_ms=latency_ms,
            model=model,
            provider=self.name,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else None,
        )
