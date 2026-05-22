"""Tests for the eval framework.

Scorer tests are deterministic and run without any LLM call.
Runner tests use a fake provider to keep the suite hermetic; the real eval pipeline
will run against live models with recorded cassettes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.evals.datasets import load_dataset
from src.evals.models import EvalCase, EvalDataset, ScorerSpec
from src.evals.runner import run_dataset
from src.evals.scorers.deterministic import (
    score_contains,
    score_json_schema,
    score_regex,
)
from src.providers.base import CompletionResponse, Provider, TokenUsage


class FakeProvider(Provider):
    """A canned provider for hermetic runner tests."""

    name = "fake"

    def __init__(self, response_text: str = '{"name": "Acme", "industry": "robotics"}') -> None:
        self._response_text = response_text

    async def complete(self, **kwargs: Any) -> CompletionResponse:
        return CompletionResponse(
            content=self._response_text,
            tool_calls=[],
            usage=TokenUsage(input_tokens=10, output_tokens=10),
            cost_usd=0.0001,
            latency_ms=1,
            model=kwargs.get("model", "fake-1"),
            provider=self.name,
        )


def test_regex_pass() -> None:
    r = score_regex("hello world", {"pattern": "^hello"})
    assert r.passed and r.score == 1.0


def test_regex_fail() -> None:
    r = score_regex("hello world", {"pattern": "^goodbye"})
    assert not r.passed and r.score == 0.0
    assert r.reason is not None


def test_contains_case_insensitive() -> None:
    r = score_contains("Hello World", {"substring": "WORLD", "case_sensitive": False})
    assert r.passed


def test_contains_case_sensitive_fail() -> None:
    r = score_contains("Hello World", {"substring": "world", "case_sensitive": True})
    assert not r.passed


def test_json_schema_pass() -> None:
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {"name": {"type": "string"}},
    }
    r = score_json_schema('{"name": "Acme"}', {"schema": schema})
    assert r.passed


def test_json_schema_invalid_json() -> None:
    r = score_json_schema("not json", {"schema": {"type": "object"}})
    assert not r.passed
    assert r.reason is not None and "not valid JSON" in r.reason


def test_json_schema_violates_schema() -> None:
    schema = {"type": "object", "required": ["name"]}
    r = score_json_schema('{"industry": "robotics"}', {"schema": schema})
    assert not r.passed
    assert r.reason is not None and "did not match" in r.reason


def test_load_yaml_dataset() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "eval_datasets" / "json_extraction.yaml"
    dataset = load_dataset(path)
    assert dataset.name == "json_extraction"
    assert len(dataset.cases) == 2
    assert all(c.scorers for c in dataset.cases)


async def test_runner_passes_when_all_scorers_pass() -> None:
    dataset = EvalDataset(
        name="t",
        cases=[
            EvalCase(
                id="c1",
                input="anything",
                scorers=[
                    ScorerSpec(
                        kind="json_schema",
                        params={"schema": {"type": "object", "required": ["name"]}},
                    ),
                    ScorerSpec(kind="contains", params={"substring": "Acme"}),
                ],
            )
        ],
    )
    result = await run_dataset(FakeProvider(), "fake-1", dataset)
    assert result.total == 1
    assert result.passed == 1
    assert result.pass_rate == 1.0
    assert result.total_cost_usd > 0


async def test_runner_fails_when_any_scorer_fails() -> None:
    dataset = EvalDataset(
        name="t",
        cases=[
            EvalCase(
                id="c1",
                input="anything",
                scorers=[
                    ScorerSpec(kind="contains", params={"substring": "missing-token"}),
                ],
            )
        ],
    )
    result = await run_dataset(FakeProvider(), "fake-1", dataset)
    assert result.passed == 0
    assert result.pass_rate == 0.0
