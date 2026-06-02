"""Agent invocation routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class MarketResearchRequest(BaseModel):
    topic: str
    model: str = "claude-sonnet-4-6"


@router.post("/agents/market-research")
async def run_market_research(req: MarketResearchRequest) -> dict[str, Any]:
    from ...agents.market_researcher import run

    try:
        result = await run(req.topic, model=req.model)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
