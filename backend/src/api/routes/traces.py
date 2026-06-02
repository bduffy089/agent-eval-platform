"""Trace routes."""

from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...config import get_settings
from ...db.models import Trace
from ...db.session import get_db

router = APIRouter()


@router.get("/traces")
def list_traces(
    limit: int = 50,
    agent_name: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[dict]:
    tenant_id = get_settings().tenant_id
    q = db.query(Trace).filter(Trace.tenant_id == tenant_id)
    if agent_name:
        q = q.filter(Trace.agent_name == agent_name)
    traces = q.order_by(Trace.created_at.desc()).limit(limit).all()
    return [
        {
            "id": t.id,
            "created_at": t.created_at.isoformat(),
            "agent_name": t.agent_name,
            "run_id": t.run_id,
            "provider": t.provider,
            "model": t.model,
            "latency_ms": t.latency_ms,
            "input_tokens": t.input_tokens,
            "output_tokens": t.output_tokens,
            "cache_read_tokens": t.cache_read_tokens,
            "cache_write_tokens": t.cache_write_tokens,
            "cost_usd": t.cost_usd,
        }
        for t in traces
    ]
