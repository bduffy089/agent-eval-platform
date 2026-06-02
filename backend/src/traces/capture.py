"""Trace capture — writes every LLM call to Postgres."""

from __future__ import annotations

import logging
from typing import Any

from ..config import get_settings
from ..db.session import db_session
from ..providers.base import CompletionResponse

logger = logging.getLogger(__name__)


def capture_trace(
    response: CompletionResponse,
    *,
    system_prompt: str | None = None,
    input_messages: list[dict[str, Any]] | None = None,
    agent_name: str | None = None,
    run_id: str | None = None,
) -> str | None:
    """Persist a CompletionResponse to the traces table. Returns the trace ID or None on failure."""
    from ..db.models import Trace

    tenant_id = get_settings().tenant_id
    try:
        with db_session() as session:
            trace = Trace(
                tenant_id=tenant_id,
                agent_name=agent_name,
                run_id=run_id,
                provider=response.provider,
                model=response.model,
                system_prompt=system_prompt,
                input_messages=input_messages,
                output=response.content,
                tool_calls=[tc.model_dump() for tc in response.tool_calls] if response.tool_calls else None,
                latency_ms=response.latency_ms,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                cache_read_tokens=response.usage.cache_read_tokens,
                cache_write_tokens=response.usage.cache_write_tokens,
                cost_usd=response.cost_usd,
                raw_response=response.raw,
            )
            session.add(trace)
            session.flush()
            trace_id = trace.id
        return trace_id
    except Exception as exc:
        # Never crash a caller because of trace capture failure.
        logger.warning("trace capture failed: %s", exc)
        return None
