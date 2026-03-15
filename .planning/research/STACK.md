# Stack Research

**Domain:** B2B LLM gateway and operator platform
**Researched:** 2026-03-15
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI | 0.115.x+ | Gateway API, admin API, service composition | Matches the current codebase, gives strong typed HTTP boundaries, and is already proving the core routing path |
| Next.js | 16.x | Operator dashboard and playground UI | Current stable major release, strong React app-router stack, and well-suited for a polished admin surface |
| PostgreSQL | 18.x current / 17.x acceptable | Durable governance store, ledger, migrations | Better long-term fit than SQLite for multi-user operator workflows and safer schema evolution |
| Qdrant | current cloud/self-hosted release | Semantic cache vector store | Already aligned with the product’s cache path and purpose-built for vector similarity workloads |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy + Alembic | current stable | Database access and migrations | Use when replacing the single-file SQLite repository with a production-safe persistence layer |
| OpenTelemetry | current stable | Traces and structured telemetry | Use when moving beyond basic counters/logging into customer-facing operational diagnostics |
| Redis | 8.x | Ephemeral cache, sessions, rate limiting, background coordination | Use if operator UI auth/session state or hot-path caching needs outgrow in-process simplicity |
| TanStack Query | current stable | Dashboard data fetching and mutation state | Use in the Next.js console for admin CRUD and ledger views |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Ruff | Python linting | Already configured in `pyproject.toml`; keep it as the Python quality baseline |
| Pytest | Backend verification | Existing suite covers gateway flows and should stay the backend test spine |
| Playwright | UI and end-to-end verification | Add once the operator console exists; useful for demo-critical workflows |

## Installation

```bash
# Existing backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

# Recommended frontend (when Phase 2 starts)
npx create-next-app@latest nebula-console

# Local services
docker compose up -d qdrant
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Next.js 16.x | FastAPI-served templates | Only use templates if the UI stays extremely small and intentionally temporary |
| PostgreSQL | SQLite | SQLite is fine for local development and demos; move when concurrency, migrations, and durability matter |
| OpenTelemetry + Prometheus | Logs only | Logs only are acceptable in very early local development, not for a serious operator product |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Building the operator UI inside ad-hoc server-rendered Python templates | Slows UI iteration and lowers perceived product quality | Next.js 16.x |
| Committing to hosted SaaS infrastructure before self-hosted product maturity | Creates ops and security scope before the product wedge is validated | Self-hosted first, hosted demo mode later |
| Treating SQLite bootstrap DDL as the long-term migration story | Fragile for evolving B2B governance schemas | PostgreSQL with explicit migrations |

## Stack Patterns by Variant

**If staying self-hosted for v1:**
- Keep FastAPI + Qdrant + local/managed Postgres
- Because the goal is a deployable customer-pilot package, not control-plane scale

**If adding a hosted demo later:**
- Keep the same FastAPI/Next.js split, but disable assumptions that require local Ollama
- Because free/cheap hosting works better with premium-only routing and externalized state

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Next.js 16.x | React 19.2 features per official release notes | Good fit for a modern admin console |
| PostgreSQL 18 current | Prior supported majors 17/16 | Official policy recommends running the current minor of a supported major |
| Redis 8.x | AI/vector-adjacent workloads | Useful if Nebula later needs session/rate-limit infrastructure in addition to Qdrant |

## Sources

- [Next.js 16 official release](https://nextjs.org/blog/next-16) — verified current major release direction
- [PostgreSQL documentation and versioning policy](https://www.postgresql.org/docs/) — verified current supported majors and upgrade guidance
- [Redis 8.0 docs](https://redis.io/docs/latest/develop/whats-new/8-0/) — verified current Redis release direction for supporting infrastructure
- [Qdrant Cloud docs](https://qdrant.tech/documentation/cloud/create-cluster/) — verified free-tier and deployment options

---
*Stack research for: B2B LLM gateway and operator platform*
*Researched: 2026-03-15*
