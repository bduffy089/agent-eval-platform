"""Eval runner.

Given a dataset and a provider+model, run every case, apply every scorer, and produce
an EvalRunResult with pass rate and aggregate cost. The runner is intentionally
provider-agnostic; it speaks to the Provider abstraction, never to a vendor SDK.
"""

from __future__ import annotations

from typing import List, Tuple

from ..providers.base import Provider
from .models import (
    CaseResult,
    EvalCase,
    EvalDataset,
    EvalRunResult,
    ScorerSpec,
    ScoreResult,
)
from .scorers.deterministic import score_contains, score_json_schema, score_regex
from .scorers.judge import score_judge


async def _apply_scorer(output: str, spec: ScorerSpec) -> ScoreResult:
    if spec.kind == "regex":
        return score_regex(output, spec.params)
    if spec.kind == "contains":
        return score_contains(output, spec.params)
    if spec.kind == "json_schema":
        return score_json_schema(output, spec.params)
    if spec.kind == "judge":
        return await score_judge(output, spec.params)
    raise ValueError(f"unknown scorer kind: {spec.kind}")


async def run_case(provider: Provider, model: str, case: EvalCase) -> Tuple[CaseResult, float]:
    """Run one case end to end. Returns the case result and its dollar cost."""
    response = await provider.complete(
        model=model,
        messages=[{"role": "user", "content": case.input}],
        max_tokens=512,
    )
    scores = [await _apply_scorer(response.content, s) for s in case.scorers]
    return (
        CaseResult(
            case_id=case.id,
            output=response.content,
            passed=all(s.passed for s in scores),
            scores=scores,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
        ),
        response.cost_usd,
    )


async def run_dataset(provider: Provider, model: str, dataset: EvalDataset) -> EvalRunResult:
    """Run every case in the dataset and aggregate the verdict."""
    case_results: List[CaseResult] = []
    total_cost = 0.0
    total_latency = 0
    for case in dataset.cases:
        result, cost = await run_case(provider, model, case)
        case_results.append(result)
        total_cost += cost
        total_latency += result.latency_ms

    passed = sum(1 for r in case_results if r.passed)
    total = len(case_results)
    return EvalRunResult(
        dataset_name=dataset.name,
        provider=provider.name,
        model=model,
        total_cases=total,
        passed_cases=passed,
        pass_rate=round(passed / total, 4) if total else 0.0,
        total_cost_usd=round(total_cost, 6),
        total_latency_ms=total_latency,
        case_results=case_results,
    )
