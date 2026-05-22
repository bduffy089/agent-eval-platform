"""Pydantic models for the eval pipeline.

A golden dataset is a list of EvalCase. Each case has an input prompt and one or more
scorers that decide pass or fail. A scorer can be deterministic (regex, schema match,
substring) or LLM-as-judge (a rubric scored by a model).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ScorerKind = Literal["regex", "json_schema", "contains", "judge"]


class ScorerSpec(BaseModel):
    """Configuration for a single scorer applied to a model output."""

    kind: ScorerKind
    # Free-form params per scorer kind. Examples:
    #   regex:       {"pattern": "^[A-Z].*"}
    #   json_schema: {"schema": {...}}
    #   contains:    {"substring": "foo", "case_sensitive": false}
    #   judge:       {"rubric": "...", "judge_model": "claude-sonnet-4-6", "pass_threshold": 0.7}
    params: dict[str, Any] = Field(default_factory=dict)


class EvalCase(BaseModel):
    """One input and the scorers that judge the output."""

    id: str
    input: str
    description: str | None = None
    scorers: list[ScorerSpec]
    # Optional reference output. Used by some scorers (for example a judge that
    # compares to a known good answer) and ignored by others.
    expected: str | None = None
    tags: list[str] = Field(default_factory=list)


class EvalDataset(BaseModel):
    """A named bundle of cases that test one task type."""

    name: str
    description: str | None = None
    cases: list[EvalCase]


class ScoreResult(BaseModel):
    """Output of a single scorer applied to a single case."""

    scorer: ScorerKind
    passed: bool
    score: float  # 0.0 to 1.0. Deterministic scorers report 0 or 1.
    reason: str | None = None


class CaseResult(BaseModel):
    """Aggregate of all scorers on one case. Passes when every scorer passes."""

    case_id: str
    output: str
    passed: bool
    scores: list[ScoreResult]


class EvalRunResult(BaseModel):
    """Outcome of running a dataset against a provider and model."""

    dataset: str
    provider: str
    model: str
    total: int
    passed: int
    pass_rate: float
    total_cost_usd: float
    cases: list[CaseResult]
