"""Claude provider.

Prompt caching is enabled on the system prompt by default. This is non-obvious: we
attach `cache_control={"type": "ephemeral"}` to the system block, which means Claude
will serve cached tokens at 0.1x input price on repeat calls within the 5-minute
window. CLAUDE.md pillar 3 demands this be the default, not opt-in.
"""

from __future__ import annotations

import time
from typing import Any

from anthropic import AsyncAnthropic

from ..config import get_settings
from .base import CompletionResponse, Provider, TokenUsage, ToolCall

# Per-million-token pricing in USD. Update when Anthropic changes pricing.
# Cache reads bill at 0.1x input; cache writes at 1.25x input.
CLAUDE_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00},
}


def _price_lookup(model: str) -> dict[str, float]:
    if model in CLAUDE_PRICING:
        return CLAUDE_PRICING[model]
    # Fall back to nearest family prefix. Keeps things working when Anthropic ships a
    # point release before we update the table.
    for key, prices in CLAUDE_PRICING.items():
        if model.startswith(key):
            return prices
    return {"input": 3.00, "output": 15.00}


def compute_cost_usd(model: str, usage: TokenUsage) -> float:
    p = _price_lookup(model)
    input_dollars = (usage.input_tokens * p["input"]) / 1_000_000
    output_dollars = (usage.output_tokens * p["output"]) / 1_000_000
    cache_read_dollars = (usage.cache_read_tokens * p["input"] * 0.10) / 1_000_000
    cache_write_dollars = (usage.cache_write_tokens * p["input"] * 1.25) / 1_000_000
    return round(input_dollars + output_dollars + cache_read_dollars + cache_write_dollars, 6)


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

        # Wrap system prompt with ephemeral cache_control. This is the default behavior
        # for this provider per CLAUDE.md pillar 3.
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
            cost_usd=compute_cost_usd(model, usage),
            latency_ms=latency_ms,
            model=model,
            provider=self.name,
            raw=resp.model_dump() if hasattr(resp, "model_dump") else None,
        )
