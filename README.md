# agent-eval-platform

**Cost-aware eval and observability infrastructure for production LLM agents.**

Most multi-agent systems do not fail on capability. They fail on production economics. This is the layer that fixes that.

## Why this exists

I built a multi-agent GTM system. Five specialized agents under a chief of staff orchestrator, custom MCP server, provisional patent filed on the architecture. Ran it in production.

A few months in, AI labs changed pricing models and forced me back onto API pricing. Rising costs meant it was time for a solution.

I paused the system and started building the layer that resolves it. That layer is this repo.

## The four pillars

1. **Cost observability.** Every run, every step, every tool call attributed to a dollar amount. Aggregated by agent, by model, by task type. This is the headline metric on the dashboard, not a secondary field.
2. **Eval-driven model routing.** Default to the cheapest model that passes the golden dataset for a given task. Escalate to a more capable model only when the eval signal says it is needed.
3. **Prompt caching as a first-class concern.** Cacheable system prompts and shared context across multi-agent runs are configured by default, not as an afterthought.
4. **Eval gates on every prompt change.** No prompt edit ships without passing the golden dataset. This makes cost optimization safe instead of reckless.

Existing tools (LangSmith, Langfuse, Helicone, Braintrust) each solve part of this. None solve the combination for the multi-agent plus tool use plus MCP shape I actually run.

## Tech stack

| Layer | Choice |
|---|---|
| LLM primary | Claude API (Sonnet 4.6 default, Haiku 4.5 for the cheap tier) |
| LLM secondary | OpenAI API |
| Agent patterns | Raw Claude API tool use, structured outputs, prompt caching |
| Orchestration | None in Phase 1. Frameworkless on purpose. Adding a framework before the primitives are understood forfeits the ability to reason about them. |
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| DB | PostgreSQL with SQLAlchemy and Alembic |
| Cache and queue | Redis |
| Frontend | React, Vite, Tailwind, Recharts |
| Dev env | Docker Compose, local only |

## Phase 1 — shipped

Working local-only platform doing these end to end:

| # | Deliverable | Status |
|---|---|---|
| 1 | Provider abstraction with normalized response shape carrying token usage and dollar cost. Claude provider enables prompt caching by default. | ✅ Shipped |
| 2 | Centralized cost computation. Pricing tables, cache discount math, and itemized breakdown live in one place. | ✅ Shipped |
| 3 | Eval pipeline with golden datasets, three deterministic scorers (regex, JSON schema, substring), and LLM-as-judge with structured rubric. | ✅ Shipped |
| 4 | Trace capture — every LLM call writes to Postgres with input, model, system prompt, tool calls, results, per-step latency, token counts, cost. | ✅ Shipped |
| 5 | Market Researcher dogfood agent ported from Agentic GTM Infrastructure with full cost attribution. | ✅ Shipped |
| 6 | React dashboard — 5 KPI stat cards (runs, pass rate, spend, traces, avg latency), cost-over-time area chart, runs list with pass-rate badges, run detail with per-case scorer verdicts, traces view with cache hit highlighting. | ✅ Shipped |
| 7 | FastAPI backend with 7 API endpoints (`/api/runs`, `/api/traces`, `/api/dashboard/stats`, `/api/dashboard/cost-over-time`, `/api/dashboard/runs-over-time`, `/api/runs/{id}`, `/api/agents/market-research`). | ✅ Shipped |
| 8 | Alembic migrations — initial migration creating `Trace`, `EvalRun`, and `EvalCaseResult` tables. Every table carries `tenant_id` from day one. | ✅ Shipped |
| 9 | Docker Compose for one-command local startup: Postgres + Redis + backend + frontend. | ✅ Shipped |

## Repo layout

```
backend/
  src/
    providers/   Claude and OpenAI behind one normalized response shape
    traces/      Cost computation (pricing tables, cache discount math) + trace capture
    evals/       Datasets, deterministic scorers, LLM-as-judge, runner
    agents/      Market Researcher dogfood agent with tool use
    db/          SQLAlchemy models + Alembic migrations
    api/         FastAPI app + route modules
  alembic/       Migration env + version scripts
  tests/         Pytest contract and unit tests
frontend/        React + Vite dashboard (StatsCards, CostChart, RunsList, RunDetail, TracesView)
eval_datasets/   Golden datasets in YAML (json_extraction included)
```

## Quickstart

```bash
cp .env.example .env
# add ANTHROPIC_API_KEY (and optionally OPENAI_API_KEY)
docker compose up
```

Brings up Postgres, Redis, the FastAPI backend (with Alembic auto-migrate on start), and the Vite dev server. Dashboard at `http://localhost:5173`.

**Without Docker** (backend and frontend already running):

```bash
# Terminal 1 — backend
cd backend
DATABASE_URL=postgresql+psycopg2://agenteval:agenteval@localhost:5432/agenteval \
  python -m alembic upgrade head
DATABASE_URL=postgresql+psycopg2://agenteval:agenteval@localhost:5432/agenteval \
  python -m uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm install && npm run dev
```

## Status

Phase 1 complete. Single tenant. Local only. Phase 2 next: real model routing, multi-agent trace stitching, and CI eval gates.

## License

MIT. The patent-protected multi-agent design lives in a separate repo. This is the eval and economics layer.
