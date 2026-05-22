"""Cost computation for provider responses.

This is the single source of truth for token-to-dollar conversion in the platform.
Pricing tables, cache discount math, and per-model lookups all live here. Providers
import `compute_cost_usd` rather than duplicating pricing.

Pillar 1 of the platform thesis: cost is a first-class metric, not a derived field.
Centralizing the computation here means there is exactly one place to update when a
lab changes pricing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from ..providers.base import TokenUsage

ProviderName = Literal["claude", "openai"]


# Per-million-token pricing in USD. Update when labs change pricing.
# Claude cache reads bill at 0.1x input; cache writes at 1.25x input.
CLAUDE_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00},
}

OPENAI_PRICING: dict[str, dict[str, float]] = {
    "gpt-5": {"input": 5.00, "output": 15.00},
    "gpt-5-mini": {"input": 1.00, "output": 4.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "o3": {"input": 10.00, "output": 40.00},
    "o3-mini": {"input": 1.10, "output": 4.40},
}

CACHE_READ_DISCOUNT = 0.10  # Claude charges 10% of input price for cache reads.
CACHE_WRITE_PREMIUM = 1.25  # Claude charges 125% of input price for cache writes.


class CostBreakdown(BaseModel):
    """Itemized cost so the dashboard can show where the dollars went."""

    input_usd: float
    output_usd: float
    cache_read_usd: float
    cache_write_usd: float
    total_usd: float


def _lookup(provider: ProviderName, model: str) -> dict[str, float]:
    table = CLAUDE_PRICING if provider == "claude" else OPENAI_PRICING
    if model in table:
        return table[model]
    # Family-prefix fallback so we keep working through point releases.
    for key, prices in table.items():
        if model.startswith(key):
            return prices
    # Conservative default if pricing is unknown so cost is never reported as zero.
    return {"input": 5.00, "output": 15.00}


def compute_cost_breakdown(
    provider: ProviderName, model: str, usage: TokenUsage
) -> CostBreakdown:
    """Return the itemized cost for a single completion."""
    p = _lookup(provider, model)
    input_usd = (usage.input_tokens * p["input"]) / 1_000_000
    output_usd = (usage.output_tokens * p["output"]) / 1_000_000

    if provider == "claude":
        cache_read_usd = (usage.cache_read_tokens * p["input"] * CACHE_READ_DISCOUNT) / 1_000_000
        cache_write_usd = (
            usage.cache_write_tokens * p["input"] * CACHE_WRITE_PREMIUM
        ) / 1_000_000
    else:
        cache_read_usd = 0.0
        cache_write_usd = 0.0

    total = input_usd + output_usd + cache_read_usd + cache_write_usd
    return CostBreakdown(
        input_usd=round(input_usd, 6),
        output_usd=round(output_usd, 6),
        cache_read_usd=round(cache_read_usd, 6),
        cache_write_usd=round(cache_write_usd, 6),
        total_usd=round(total, 6),
    )


def compute_cost_usd(provider: ProviderName, model: str, usage: TokenUsage) -> float:
    """Convenience wrapper: total dollars only."""
    return compute_cost_breakdown(provider, model, usage).total_usd
