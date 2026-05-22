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
| LLM primary | Claude API (Sonnet default, Haiku for the cheap tier) |
| LLM secondary | OpenAI API |
| Agent patterns | Raw Claude API tool use, structured outputs, prompt caching |
| Orchestration | None in Phase 1. Frameworkless on purpose. Adding a framework before the primitives are understood forfeits the ability to reason about them. |
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| DB | PostgreSQL with SQLAlchemy and Alembic |
| Cache and queue | Redis |
| Frontend | React, Vite, Tailwind |
| Dev env | Docker Compose, local only |

## Phase 1 scope (in progress)

Working local-only platform doing these end to end:

1. Provider abstraction with normalized response shape carrying token usage and dollar cost. Claude provider enables prompt caching by default.
2. Single-agent task runtime with cheap-first model routing.
3. Trace capture to Postgres: input, model, system prompt, tool calls, tool results, output, latency, tokens, cost, cache hit/miss.
4. Eval pipeline with golden datasets, deterministic scorers, and LLM-as-judge with structured rubric output.
5. Dogfood agent: porting a real production agent into the platform and measuring meaningful cost reduction with eval gates confirming quality holds.
6. Dashboard with three views: recent runs, run detail with cost breakdown, and cost-over-time as the headline view.
7. One-command bring-up via Docker Compose.

## Repo layout

```
backend/         FastAPI service, providers, evals, traces
frontend/        React + Vite dashboard
eval_datasets/   Golden datasets (JSON/YAML)
```

## Quickstart

```bash
cp .env.example .env
# fill in ANTHROPIC_API_KEY and OPENAI_API_KEY
docker compose up -d
```

That brings up Postgres and Redis. Backend and frontend land in subsequent commits.

## Status

Phase 1 bootstrap. Single tenant. Local only. Active build.

## License

MIT. The patent-protected multi-agent design lives in a separate repo. This is the eval and economics layer.
