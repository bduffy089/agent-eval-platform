"""OpenAI provider.

Uses the chat.completions interface for Phase 1. OpenAI does not expose explicit
prompt-cache token counts the way Anthropic does, so `cache_read_tokens` and
`cache_write_tokens` always return 0 here. The dashboard can still render the
columns; they will just be empty for OpenAI runs.
"""

from __future__ import annotations

import json
import time
from typing import Any

from openai import AsyncOpenAI

from ..config import get_settings
from ..traces.cost import compute_cost_usd
from .base import CompletionResponse, Provider, TokenUsage, ToolCall


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
            cost_usd=compute_cost_usd("openai", model, usage),
            latency_ms=latency_ms,
            model=model,
            provider=self.name,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else None,
        )
