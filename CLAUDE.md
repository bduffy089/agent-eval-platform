# Agent Eval Platform

## Project Context

I'm building **cost-aware eval and observability infrastructure for production LLM agents**. This is a portfolio project for the Anthropic Applied AI Architect role, and it needs to be defensible under technical interview probing.

**The origin story (use this in interviews):** I built a multi-agent GTM system (https://github.com/bduffy089/Agentic-GTM-Infrastructure), five specialized agents under a Chief of Staff orchestrator, custom MCP server, provisional patent filed on the architecture. Ran it in production. About four months in I hit a wall I had not designed for: API costs scaled faster than the value the agents were producing, and I had no infrastructure to do anything about it intelligently. No per-agent cost attribution, no eval signal telling me which model was overkill for which task, no disciplined prompt caching. I paused the system and started building the layer that resolves it.

**That layer is this project.** It is the production economics infrastructure for multi-agent systems.

## Product Thesis (Lead With This)

Most multi-agent systems do not fail on capability. They fail on production economics. The four pillars of this platform address that directly:

1. **Cost observability.** Every run, every step, every tool call attributed to a dollar amount. Aggregated by agent, by model, by task type. **This is the headline metric on the dashboard, not a secondary field.**
2. **Eval-driven model routing.** Default to the cheapest model that passes the golden dataset for a given task. Escalate to more capable models only when eval signal says it is needed.
3. **Prompt caching as a first-class concern.** Cacheable system prompts and shared context across multi-agent runs are configured by default, not as afterthought.
4. **Eval gates on every prompt change.** No prompt edit ships without passing the golden dataset. This makes the cost optimization safe rather than reckless.

Existing tools (LangSmith, Langfuse, Helicone, Braintrust) each solve part of this. None solve the combination for the multi-agent + tool use + MCP shape I actually run.

## Non-Goals for Phase 1 (Push Back If I Ask for These)

- Multi-tenancy or user auth beyond a single API key
- Cloud deployment, Terraform, IaC of any kind
- Production-grade RAG
- A LangGraph-based orchestration layer (Phase 2)
- Custom MCP server (already exists in Agentic GTM repo)
- Marketplace, templates library, onboarding flow
- "Just one more provider" beyond Claude and OpenAI
- Vector DB or retrieval until an agent actually needs it

If a feature is on this list, default to "no" and ask me first.

## Tech Stack

| Layer | Choice | Why |
| :-- | :-- | :-- |
| LLM primary | Claude API (Sonnet 4.6 default, Haiku 4.5 for cheap tier) | Target role at Anthropic. Lead with Claude. |
| LLM secondary | OpenAI API (GPT-5, o-series) | Multi-provider enables head-to-head evals |
| Agent patterns | Raw Claude API tool use, structured outputs, **prompt caching** | Phase 1 stays close to primitives |
| Orchestration | None in Phase 1. LangGraph in Phase 2. | Frameworkless to start, per Anthropic's "Building effective agents" guidance |
| Backend | Python 3.11+, FastAPI, Pydantic v2 | Standard async |
| DB | PostgreSQL with SQLAlchemy + Alembic | Traces, evals, runs |
| Cache and queue | Redis | Rate limiting, eval job queue |
| Frontend | React + Vite + Tailwind | One dashboard page, no router yet |
| Dev env | Docker Compose | Local only |

## On LangGraph (Read This Before Suggesting It)

LangGraph is currently hyped. We are NOT using it in Phase 1, on purpose:

1. Anthropic's December 2024 "Building effective agents" post explicitly recommends starting frameworkless and adding complexity only when earned. The interviewers know this post.
2. Phase 1 needs a clean foundation on raw Claude API: tool use, structured outputs, prompt caching, streaming. Burying those under a framework forfeits the ability to speak to them.
3. LangGraph shines for multi-step state-machine flows with conditional branching. Phase 1 does not need that yet.
4. **Phase 2 will introduce LangGraph for one specific use case:** orchestrating multi-step eval pipelines (run agent, grade output, branch on grade, maybe re-run with adjusted prompt, log). That is genuine state-machine territory and gives a defensible "I evaluated framework vs no framework" interview answer.

If you catch yourself reaching for LangGraph in Phase 1, stop. Ask.

## Phase 1 MVP Deliverables (2-3 Weeks)

Working local-only platform doing these end to end:

1. **Provider abstraction.** `providers/base.py` (abstract), `providers/claude.py`, `providers/openai.py`. Each exposes async `complete(messages, tools, **kwargs)` returning a normalized response with token usage AND **dollar cost** populated. Claude provider has prompt caching enabled by default.
2. **Agent runtime.** Single-agent task config: which provider, which model, which tools, which prompts. Cheap-first routing: declare a primary model AND a fallback. Escalate only when eval fails (Phase 1: stub the routing logic, real eval-driven routing is Phase 2).
3. **Trace capture.** Every run writes to Postgres: input, model, system prompt, tool calls, tool results, final output, per-step latency, token counts, **cost in dollars, cache hit/miss for Claude.**
4. **Eval pipeline.** Golden dataset format (JSON or YAML files in `eval_datasets/`). Two scorer types: deterministic (regex, JSON schema, contains-x) and LLM-as-judge (Claude as default judge, structured rubric output). Eval runs produce pass/fail plus rubric scores stored in Postgres.
5. **Dogfood agent.** Port the Market Researcher from Agentic-GTM-Infrastructure into the platform. Goal: run it end to end at meaningfully lower cost than the original implementation, with eval gate confirming quality holds.
6. **Dashboard.** One React page with three views:
   - Recent runs (timestamp, agent, model, latency, **cost**, eval pass/fail)
   - Run detail (full trace + scoring + cost breakdown by step)
   - **Cost over time** (line chart by day, broken down by agent and model). This is the headline view.
7. **Docker Compose.** One command brings up backend + Postgres + Redis + frontend.

## Repo Structure

```
agent-eval-platform/
├── CLAUDE.md
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   ├── src/
│   │   ├── api/
│   │   ├── agents/
│   │   ├── providers/         # claude.py, openai.py, base.py
│   │   ├── evals/             # datasets loader, scorers, judge prompts
│   │   ├── traces/            # capture, storage, cost computation
│   │   ├── db/
│   │   └── config.py
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── pages/Dashboard.tsx
│       ├── components/
│       └── lib/api.ts
└── eval_datasets/
```

## Coding Conventions

- **Python:** Type hints everywhere. Pydantic v2 for all data models. Ruff + Black. No bare exceptions.
- **TypeScript:** Strict mode. No `any`.
- **NO em dashes anywhere.** Code comments, docs, UI copy, commit messages. Personal style rule, applies repo-wide.
- **Commits:** Conventional Commits. `feat:`, `fix:`, `chore:`, `docs:`. Atomic.
- **Tests:** Pytest for backend. Cover the provider abstraction, eval scorers, trace + cost computation. UI tests not in Phase 1.
- **Secrets:** `.env` gitignored. `.env.example` shows keys without values.
- **License:** MIT. The patent-protected design lives in Agentic-GTM-Infrastructure. This repo is the eval layer, not the agent IP.
- **Tenant ID column on every table** from day one. Hardcode to `"britney"` for the whole MVP. Cheap insurance for freelance multi-tenancy later.

## Anti-Patterns to Reject

Push back if I drift toward:

- LangGraph in Phase 1
- Vector DB / RAG before an agent actually needs retrieval
- Custom auth (one user in Phase 1: me)
- Mocking LLM calls with fake responses in tests (use recorded cassettes or real eval dataset runs)
- A third provider beyond Claude and OpenAI in Phase 1
- Speculative abstractions for "future flexibility"
- Generic agent loops before the dogfood agent works end to end

## First Task: Bootstrap the Repo

Do this and stop. Show me what you built before moving on.

1. Initialize the repo structure above. Empty `__init__.py` files, placeholder README, working `docker-compose.yml` with **Postgres + Redis only** (no backend or frontend yet).
2. `pyproject.toml` with: fastapi, uvicorn, pydantic, sqlalchemy, alembic, psycopg2-binary, redis, anthropic, openai, python-dotenv, ruff, black, pytest, pytest-asyncio.
3. `.env.example` with: ANTHROPIC_API_KEY, OPENAI_API_KEY, DATABASE_URL, REDIS_URL.
4. `.gitignore` covering Python, Node, env files, .venv, node_modules, .DS_Store.
5. Build the provider abstraction: `providers/base.py` (ABC with normalized response model including `cost_usd`), `providers/claude.py`, `providers/openai.py`. Each provider's `complete()` returns the same normalized shape: `{content, tool_calls, usage: {input_tokens, output_tokens, cache_read_tokens, cache_write_tokens}, cost_usd, latency_ms}`. Claude provider enables prompt caching on system prompts by default.
6. Contract tests in `tests/test_providers.py`. Both providers must pass the same contract given the same input.

**Stop after that. Do not write more.** Bootstrapping cleanly is worth more than a half-built feature.

## How to Talk to Me

I am still building my Python and systems intuition. When you make a non-obvious choice, explain it in one sentence in the commit message or code comment. I want to learn the why.

Before destructive actions (drop tables, rewrite files, install heavy deps), ask.

If I ask for something that contradicts this CLAUDE.md, push back. Name the rule it contradicts and ask if I want to update the rule or back off the request.
