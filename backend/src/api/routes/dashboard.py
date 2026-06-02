"""Dashboard stats routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...config import get_settings
from ...db.models import EvalRun, Trace
from ...db.session import get_db

router = APIRouter()


@router.get("/dashboard/stats")
def get_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    tenant_id = get_settings().tenant_id

    total_runs = db.query(func.count(EvalRun.id)).filter(EvalRun.tenant_id == tenant_id).scalar() or 0

    avg_pass_rate = (
        db.query(func.avg(EvalRun.pass_rate)).filter(EvalRun.tenant_id == tenant_id).scalar() or 0.0
    )

    total_cost = (
        db.query(func.sum(Trace.cost_usd)).filter(Trace.tenant_id == tenant_id).scalar() or 0.0
    )

    total_traces = (
        db.query(func.count(Trace.id)).filter(Trace.tenant_id == tenant_id).scalar() or 0
    )

    avg_latency = (
        db.query(func.avg(Trace.latency_ms)).filter(Trace.tenant_id == tenant_id).scalar() or 0.0
    )

    return {
        "total_runs": total_runs,
        "avg_pass_rate": round(float(avg_pass_rate), 4),
        "total_cost_usd": round(float(total_cost), 6),
        "total_traces": total_traces,
        "avg_latency_ms": round(float(avg_latency), 1),
    }


@router.get("/dashboard/cost-over-time")
def cost_over_time(days: int = 30, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Daily cost breakdown for the past N days."""
    tenant_id = get_settings().tenant_id

    rows = (
        db.query(
            func.date(Trace.created_at).label("day"),
            func.sum(Trace.cost_usd).label("cost_usd"),
            func.count(Trace.id).label("calls"),
            func.sum(Trace.input_tokens).label("input_tokens"),
            func.sum(Trace.output_tokens).label("output_tokens"),
            func.sum(Trace.cache_read_tokens).label("cache_read_tokens"),
        )
        .filter(Trace.tenant_id == tenant_id)
        .group_by(func.date(Trace.created_at))
        .order_by(func.date(Trace.created_at).desc())
        .limit(days)
        .all()
    )

    return [
        {
            "day": str(r.day),
            "cost_usd": round(float(r.cost_usd or 0), 6),
            "calls": r.calls,
            "input_tokens": r.input_tokens or 0,
            "output_tokens": r.output_tokens or 0,
            "cache_read_tokens": r.cache_read_tokens or 0,
        }
        for r in rows
    ]


@router.get("/dashboard/runs-over-time")
def runs_over_time(days: int = 30, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    tenant_id = get_settings().tenant_id

    rows = (
        db.query(
            func.date(EvalRun.created_at).label("day"),
            func.count(EvalRun.id).label("runs"),
            func.avg(EvalRun.pass_rate).label("avg_pass_rate"),
        )
        .filter(EvalRun.tenant_id == tenant_id)
        .group_by(func.date(EvalRun.created_at))
        .order_by(func.date(EvalRun.created_at).desc())
        .limit(days)
        .all()
    )

    return [
        {
            "day": str(r.day),
            "runs": r.runs,
            "avg_pass_rate": round(float(r.avg_pass_rate or 0), 4),
        }
        for r in rows
    ]
