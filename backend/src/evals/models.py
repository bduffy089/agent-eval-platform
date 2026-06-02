"""Pydantic models for the eval pipeline.

A golden dataset is a list of EvalCase. Each case has an input prompt and one or more
scorers that decide pass or fail. A scorer can be deterministic (regex, schema match,
substring) or LLM-as-judge (a rubric scored by a model).
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

ScorerKind = Literal["regex", "json_schema", "contains", "judge"]


class ScorerSpec(BaseModel):
    """Configuration for a single scorer applied to a model output."""

    kind: ScorerKind
    params: Dict[str, Any] = Field(default_factory=dict)


class EvalCase(BaseModel):
    """One input and the scorers that judge the output."""

    id: str
    input: str
    description: Optional[str] = None
    scorers: List[ScorerSpec]
    expected: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class EvalDataset(BaseModel):
    """A named bundle of cases that test one task type."""

    name: str
    description: Optional[str] = None
    cases: List[EvalCase]


class ScoreResult(BaseModel):
    """Output of a single scorer applied to a single case."""

    scorer: ScorerKind
    passed: bool
    score: float
    reason: Optional[str] = None


class CaseResult(BaseModel):
    """Aggregate of all scorers on one case. Passes when every scorer passes."""

    case_id: str
    output: str
    passed: bool
    scores: List[ScoreResult]
    cost_usd: float = 0.0
    latency_ms: int = 0


class EvalRunResult(BaseModel):
    """Outcome of running a dataset against a provider and model."""

    dataset_name: str
    provider: str
    model: str
    total_cases: int
    passed_cases: int
    pass_rate: float
    total_cost_usd: float
    total_latency_ms: int
    case_results: List[CaseResult]
