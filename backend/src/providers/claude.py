"""Claude provider.

Prompt caching is enabled on the system prompt by default. We attach
`cache_control={"type": "ephemeral"}` to the system block, which means Claude serves
cached tokens at 0.1x input price on repeat calls within the 5-minute window. Caching
is a first-class concern in this platform, not opt-in.
"""

from __future__ import annotations

import time
from typing import Any

from anthropic import AsyncAnthropic

from ..config import get_settings
from ..traces.cost import compute_cost_usd
from .base import CompletionResponse, Provider, TokenUsage, ToolCall


class ClaudeProvider(Provider):
    name = "claude"

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or get_settings().anthropic_api_key
        self._client = AsyncAnthropic(api_key=key) if key else None

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
            raise RuntimeError("ANTHROPIC_API_KEY not configured")

        # Wrap system prompt with ephemeral cache_control. Default behavior for this
        # provider so cost gains from caching are not opt-in.
        system_param: Any = None
        if system:
            system_param = [
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ]

        request: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if system_param is not None:
            request["system"] = system_param
        if tools:
            request["tools"] = tools
        request.update(kwargs)

        start = time.perf_counter()
        resp = await self._client.messages.create(**request)
        latency_ms = int((time.perf_counter() - start) * 1000)

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
            elif getattr(block, "type", None) == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=dict(block.input or {}))
                )

        u = resp.usage
        usage = TokenUsage(
            input_tokens=getattr(u, "input_tokens", 0) or 0,
            output_tokens=getattr(u, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
        )

        return CompletionResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            usage=usage,
            cost_usd=compute_cost_usd("claude", model, usage),
            latency_ms=latency_ms,
            model=model,
            provider=self.name,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else None,
        )
