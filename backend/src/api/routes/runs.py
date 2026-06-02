"""Eval run routes."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...config import get_settings
from ...db.models import EvalCaseResult, EvalRun
from ...db.session import get_db
from ...evals.datasets import load_dataset
from ...evals.runner import run_dataset
from ...providers.claude import ClaudeProvider
from ...providers.openai import OpenAIProvider

router = APIRouter()


class RunRequest(BaseModel):
    dataset: str
    provider: str = "claude"
    model: str = "claude-haiku-4-5"


@router.post("/runs")
async def create_run(req: RunRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        dataset = load_dataset(req.dataset)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{req.dataset}' not found")

    provider = ClaudeProvider() if req.provider == "claude" else OpenAIProvider()

    result = await run_dataset(provider, req.model, dataset)

    run = EvalRun(
        id=str(uuid.uuid4()),
        tenant_id=get_settings().tenant_id,
        dataset_name=result.dataset_name,
        provider=req.provider,
        model=req.model,
        total_cases=result.total_cases,
        passed_cases=result.passed_cases,
        pass_rate=result.pass_rate,
        total_cost_usd=result.total_cost_usd,
        total_latency_ms=result.total_latency_ms,
    )
    db.add(run)
    db.flush()

    for cr in result.case_results:
        db.add(
            EvalCaseResult(
                id=str(uuid.uuid4()),
                run_id=run.id,
                tenant_id=get_settings().tenant_id,
                case_id=cr.case_id,
                output=cr.output,
                passed=cr.passed,
                scores=[s.model_dump() for s in cr.scores],
                cost_usd=cr.cost_usd,
                latency_ms=cr.latency_ms,
            )
        )

    db.commit()
    return {"run_id": run.id, "pass_rate": run.pass_rate, "total_cost_usd": run.total_cost_usd}


@router.get("/runs")
def list_runs(limit: int = 20, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    tenant_id = get_settings().tenant_id
    runs = (
        db.query(EvalRun)
        .filter(EvalRun.tenant_id == tenant_id)
        .order_by(EvalRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "dataset_name": r.dataset_name,
            "provider": r.provider,
            "model": r.model,
            "total_cases": r.total_cases,
            "passed_cases": r.passed_cases,
            "pass_rate": r.pass_rate,
            "total_cost_usd": r.total_cost_usd,
            "total_latency_ms": r.total_latency_ms,
        }
        for r in runs
    ]


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    run = db.query(EvalRun).filter(EvalRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    cases = db.query(EvalCaseResult).filter(EvalCaseResult.run_id == run_id).all()
    return {
        "id": run.id,
        "created_at": run.created_at.isoformat(),
        "dataset_name": run.dataset_name,
        "provider": run.provider,
        "model": run.model,
        "total_cases": run.total_cases,
        "passed_cases": run.passed_cases,
        "pass_rate": run.pass_rate,
        "total_cost_usd": run.total_cost_usd,
        "total_latency_ms": run.total_latency_ms,
        "cases": [
            {
                "case_id": c.case_id,
                "passed": c.passed,
                "output": c.output,
                "scores": c.scores,
                "cost_usd": c.cost_usd,
                "latency_ms": c.latency_ms,
            }
            for c in cases
        ],
    }
