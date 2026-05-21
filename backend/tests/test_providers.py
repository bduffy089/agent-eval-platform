"""Contract tests for the provider abstraction.

Every provider's `complete()` must return a `CompletionResponse` with the same shape.
These tests do NOT call real APIs. Per CLAUDE.md, we do not mock LLM calls with fake
responses for behavior tests; that rule is about behavior validation in the eval
layer. Provider-shape contract tests are different: they verify the adapter wires raw
SDK responses into the normalized shape correctly, which is exactly what fixtures are
for. We patch the SDK client with a stub that returns a recorded response shape.

When the eval pipeline lands in a later phase, it will exercise providers against
real models using recorded cassettes from golden datasets.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from src.providers.base import CompletionResponse
from src.providers.claude import ClaudeProvider, compute_cost_usd as claude_cost
from src.providers.openai import OpenAIProvider, compute_cost_usd as openai_cost
from src.providers.base import TokenUsage


class _FakeAnthropicMessages:
    async def create(self, **kwargs: Any) -> Any:
        # Verify the Claude provider attached cache_control to the system prompt by
        # default. This is the contract enforcement for pillar 3.
        system = kwargs.get("system")
        assert isinstance(system, list)
        assert system[0]["cache_control"] == {"type": "ephemeral"}

        return SimpleNamespace(
            content=[
                SimpleNamespace(type="text", text="hello world"),
                SimpleNamespace(
                    type="tool_use", id="t_1", name="echo", input={"value": "hi"}
                ),
            ],
            usage=SimpleNamespace(
                input_tokens=100,
                output_tokens=20,
                cache_read_input_tokens=50,
                cache_creation_input_tokens=10,
            ),
            model_dump=lambda: {"id": "msg_test"},
        )


class _FakeAnthropicClient:
    def __init__(self) -> None:
        self.messages = _FakeAnthropicMessages()


class _FakeOpenAICompletions:
    async def create(self, **kwargs: Any) -> Any:
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="hello world",
                        tool_calls=[
                            SimpleNamespace(
                                id="t_1",
                                function=SimpleNamespace(
                                    name="echo", arguments='{"value": "hi"}'
                                ),
                            )
                        ],
                    )
                )
            ],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20),
            model_dump=lambda: {"id": "resp_test"},
        )


class _FakeOpenAIChat:
    def __init__(self) -> None:
        self.completions = _FakeOpenAICompletions()


class _FakeOpenAIClient:
    def __init__(self) -> None:
        self.chat = _FakeOpenAIChat()


@pytest.fixture
def claude_provider() -> ClaudeProvider:
    p = ClaudeProvider(api_key="test")
    p._client = _FakeAnthropicClient()  # type: ignore[assignment]
    return p


@pytest.fixture
def openai_provider() -> OpenAIProvider:
    p = OpenAIProvider(api_key="test")
    p._client = _FakeOpenAIClient()  # type: ignore[assignment]
    return p


def _assert_contract(resp: CompletionResponse) -> None:
    assert isinstance(resp, CompletionResponse)
    assert isinstance(resp.content, str) and resp.content
    assert resp.usage.input_tokens > 0
    assert resp.usage.output_tokens > 0
    assert resp.cost_usd > 0
    assert resp.latency_ms >= 0
    assert resp.provider in {"claude", "openai"}
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "echo"
    assert resp.tool_calls[0].arguments == {"value": "hi"}


async def test_claude_contract(claude_provider: ClaudeProvider) -> None:
    resp = await claude_provider.complete(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "hi"}],
        system="you are helpful",
    )
    _assert_contract(resp)
    assert resp.provider == "claude"
    assert resp.usage.cache_read_tokens == 50
    assert resp.usage.cache_write_tokens == 10


async def test_openai_contract(openai_provider: OpenAIProvider) -> None:
    resp = await openai_provider.complete(
        model="gpt-5",
        messages=[{"role": "user", "content": "hi"}],
        system="you are helpful",
    )
    _assert_contract(resp)
    assert resp.provider == "openai"
    # OpenAI does not surface cache tokens in Phase 1.
    assert resp.usage.cache_read_tokens == 0
    assert resp.usage.cache_write_tokens == 0


def test_claude_cost_includes_cache_discount() -> None:
    usage = TokenUsage(
        input_tokens=1_000_000,
        output_tokens=0,
        cache_read_tokens=1_000_000,
        cache_write_tokens=0,
    )
    # 1M input at $3 + 1M cache reads at 0.1x = $3.00 + $0.30 = $3.30
    assert claude_cost("claude-sonnet-4-6", usage) == 3.30


def test_openai_cost_basic() -> None:
    usage = TokenUsage(input_tokens=1_000_000, output_tokens=1_000_000)
    # gpt-5: $5 in + $15 out per 1M
    assert openai_cost("gpt-5", usage) == 20.0
