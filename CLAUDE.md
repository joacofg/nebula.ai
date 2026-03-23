# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Nebula.ai — self-hosted semantic AI gateway that reduces premium LLM spend while preserving operator control over routing, fallback behavior, and cost visibility. v1.0 shipped; v2.0 (Hosted Control Plane Validation) in progress.

## Commands

```bash
make setup              # Bootstrap Python 3.12 venv + install[dev]
make test               # Run all pytest tests
make lint               # ruff check (line-length 100, py312 target)
make run                # uvicorn with --reload
make benchmark          # Full scenario suite → artifacts/benchmarks/<timestamp>/
make benchmark-demo     # Smaller demo subset
make migrate            # alembic upgrade head
make selfhost-up        # Full production stack (docker-compose.selfhosted.yml)
make selfhost-down      # Teardown production stack
make console-dev        # npm run dev in console/
make console-test       # npm test in console/ (vitest)
make console-e2e        # Playwright E2E tests
```

Single test: `pytest tests/test_chat_completions.py -k test_name`

Console single test: `npm --prefix console run test -- --run src/path/to/test.test.ts`

## Architecture

**Request flow:** Client → `POST /v1/chat/completions` with `X-Nebula-API-Key` → tenant policy resolution → routing decision (local → cache → premium → fallback) → response with `X-Nebula-*` metadata headers → usage persisted to ledger.

**Backend** (FastAPI, Python 3.12): `src/nebula/`
- `main.py` — App factory with async lifespan
- `core/container.py` — ServiceContainer (DI pattern)
- `core/config.py` — Pydantic Settings; runtime profiles: `local_dev`, `premium_first`
- `services/chat_service.py` — Main orchestration: routing, policy check, fallback (largest service)
- `services/router_service.py` — Complexity-based routing (char count + keyword hints)
- `services/governance_store.py` — PostgreSQL ORM for tenants, keys, policies, ledger
- `services/policy_service.py` — Cost bounds, model allowlists, routing mode enforcement
- `services/semantic_cache_service.py` — Qdrant vector similarity
- `api/routes/chat.py` — Chat completions endpoint
- `api/routes/admin.py` — Governance admin APIs
- `providers/` — LLM adapters: `ollama.py` (local), `openai_compatible.py` (premium), `mock_premium.py` (test)

**Console** (Next.js 15, React 19, TypeScript): `console/`
- Operator UI: Playground, Observability, Policy Editor, Tenants, API Keys
- API routes proxy to gateway admin APIs

**Data stores:** PostgreSQL 16 (governance), Qdrant (semantic cache)

## Testing Patterns

- `configured_app()` — async context manager for test app setup
- `StubProvider` / `FakeCacheService` — isolation stubs
- `auth_headers()` — helper for authenticated requests
- All tests are async (`pytest-asyncio` in auto mode)
- 13 test modules covering chat, admin, governance, benchmarks, providers, health

## Code Conventions

- Async-first for all I/O
- Type-safe routing literals: `"local"` / `"premium"` / `"cache"` / `"denied"`
- Frozen dataclasses for value objects (RouteDecision, CompletionMetadata)
- Custom `X-Nebula-*` response headers for metadata contract
- Pydantic models for API schemas (OpenAI-compatible)
- Conventional commit prefixes: fix, feat, docs, chore, test

## Local Dev Setup

```bash
make setup
cp .env.example .env
docker compose up -d qdrant   # or: make qdrant-up
make run                       # gateway on :8000
make console-dev               # console on :3000
```

## Deployment

- **Self-hosted prod:** `docker compose -f docker-compose.selfhosted.yml up -d` — runs gateway, console, PostgreSQL, Qdrant; alembic migrations run at startup
- Runtime profile: `NEBULA_RUNTIME_PROFILE=premium_first` for production
- Premium providers configured via `NEBULA_PREMIUM_BASE_URL` + `NEBULA_PREMIUM_API_KEY`

## Observability

- Prometheus metrics at `/metrics`
- Health endpoints: `/health`, `/health/ready`, `/health/dependencies`
- Benchmark reports: `artifacts/benchmarks/<timestamp>/report.json` + `report.md`

## v2.0 Context

Hosted Control Plane Validation — phase 6 of 10. Planning artifacts in `.planning/` (PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md). Key constraint: hosted plane is metadata-only; local enforcement stays authoritative; no raw prompts/responses/credentials sent to hosted plane.
