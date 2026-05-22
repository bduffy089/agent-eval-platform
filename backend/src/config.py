"""Runtime config loaded from environment."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

# Single-tenant MVP. Every table carries a tenant_id column from day one, hardcoded to
# this value through Phase 1. Cheap insurance for a real multi-tenant layer later.
DEFAULT_TENANT_ID = "britney"


class Settings(BaseModel):
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    database_url: str = "postgresql+psycopg2://agenteval:agenteval@localhost:5432/agenteval"
    redis_url: str = "redis://localhost:6379/0"
    tenant_id: str = DEFAULT_TENANT_ID


@lru_cache
def get_settings() -> Settings:
    return Settings(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        database_url=os.getenv("DATABASE_URL", Settings().database_url),
        redis_url=os.getenv("REDIS_URL", Settings().redis_url),
    )
