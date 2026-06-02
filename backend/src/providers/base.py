"""Provider abstraction.

Every LLM provider in this platform returns the SAME normalized response shape so the
agent runtime, trace capture, and cost dashboard never branch on provider identity.

The non-obvious choice: `cost_usd` is populated by the provider itself, not by a
downstream cost calculator. Each provider knows its own pricing table and cache
discount math, so the trace layer just records what it gets. This keeps cost truth
co-located with the API call that produced it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token counts normalized across providers.

    `cache_read_tokens` and `cache_write_tokens` are Claude-specific today but live on
    the shared model so the dashboard can render them without provider branching.
    OpenAI providers report 0 for both until OpenAI ships an equivalent surface.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


class ToolCall(BaseModel):
    """Normalized tool call. Providers map their native shape into this."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class CompletionResponse(BaseModel):
    """The single shape returned by every provider's `complete()`.

    Contract tests in tests/test_providers.py enforce that both providers produce a
    response that validates against this model given the same input.
    """

    content: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    usage: TokenUsage
    cost_usd: float
    latency_ms: int
    model: str
    provider: str
    raw: Optional[Dict[str, Any]] = None


class Provider(ABC):
    """Abstract provider. Implementations live in claude.py and openai.py."""

    name: str

    @abstractmethod
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
        """Run a single completion and return the normalized response.

        Claude implementations must enable prompt caching on the system prompt by
        default. OpenAI implementations report zero cache tokens until OpenAI
        exposes an equivalent surface.
        """
        raise NotImplementedError
