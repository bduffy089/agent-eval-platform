# agent-eval-platform

Cost-aware eval and observability infrastructure for production LLM agents.

See [CLAUDE.md](CLAUDE.md) for the full project brief, product thesis, and Phase 1 deliverables.

## Status

Phase 1 bootstrap. Local-only. Single tenant (`britney`).

## Quickstart

```bash
cp .env.example .env
# fill in ANTHROPIC_API_KEY and OPENAI_API_KEY
docker compose up -d
```

That brings up Postgres and Redis. Backend and frontend land in subsequent commits.

## Layout

```
backend/         FastAPI service, providers, evals, traces
frontend/        React + Vite dashboard
eval_datasets/   Golden datasets (JSON/YAML)
```

## License

MIT.
