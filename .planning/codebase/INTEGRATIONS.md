# External Integrations

**Analysis Date:** 2026-03-15

## APIs & External Services

**Local LLM Runtime:**
- Ollama - Local chat completions and embeddings
  - SDK/Client: `httpx.AsyncClient` in `src/nebula/providers/ollama.py` and `src/nebula/services/embeddings_service.py`
  - Auth: none detected
  - Endpoints used: `POST /api/chat` for completions, `POST /api/embed` for embeddings

**Premium LLM Provider:**
- OpenAI-compatible API - Premium completions and fallback target
  - Integration method: REST calls in `src/nebula/providers/openai_compatible.py`
  - Auth: `Authorization: Bearer <NEBULA_PREMIUM_API_KEY>`
  - Base URL: `NEBULA_PREMIUM_BASE_URL`, defaulting to `https://api.openai.com/v1` when unset

**Mock Premium Provider:**
- In-process mock provider - Local development and tests without external spend
  - Implementation: `src/nebula/providers/mock_premium.py`
  - Auth: not applicable
  - Use when: `NEBULA_PREMIUM_PROVIDER=mock`

## Data Storage

**Databases:**
- SQLite - Governance, tenants, API keys, policies, and usage ledger
  - Connection: `NEBULA_DATA_STORE_PATH`
  - Client: Python `sqlite3` via `src/nebula/services/governance_store.py`
  - Migrations: no standalone migration system; schema is created imperatively in `GovernanceStore.initialize()`

**Vector Storage:**
- Qdrant - Semantic response cache
  - Connection: `NEBULA_QDRANT_URL`
  - Client: `qdrant-client` via `AsyncQdrantClient` in `src/nebula/services/semantic_cache_service.py`
  - Collection: `NEBULA_SEMANTIC_CACHE_COLLECTION`

**File Storage:**
- Local filesystem - Benchmark artifacts and local SQLite database
  - Artifacts: `artifacts/benchmarks/<timestamp>/report.json` and `report.md`
  - DB path default: `.nebula/nebula.db`

## Authentication & Identity

**Auth Provider:**
- Custom API-key and tenant resolution - Implemented in `src/nebula/services/auth_service.py`
  - Client auth header: `X-Nebula-API-Key`
  - Tenant scoping header: `X-Nebula-Tenant-ID`
  - Session management: stateless per-request resolution against SQLite-backed key records

**Admin Authentication:**
- Static admin key - Guard for operator routes
  - Header: `X-Nebula-Admin-Key`
  - Source: `NEBULA_ADMIN_API_KEY`

## Monitoring & Observability

**Metrics:**
- Prometheus - Exposes `/metrics` when `NEBULA_ENABLE_METRICS=true`
  - Integration: `prometheus_client.make_asgi_app()` in `src/nebula/main.py`
  - Metrics definitions: `src/nebula/observability/metrics.py`

**Logs:**
- Standard library logging to process output
  - Integration: `src/nebula/observability/logging.py` and middleware/service loggers
  - Request correlation: `X-Request-ID` support in `src/nebula/observability/middleware.py`

## CI/CD & Deployment

**Hosting:**
- Not detected in-repo
  - No Dockerfile, Kubernetes manifests, or platform config checked in
  - Current repo only provides app code plus local development infrastructure

**CI Pipeline:**
- Not detected in-repo
  - No `.github/workflows/` or equivalent CI configuration present in the mapped files

## Environment Configuration

**Development:**
- Required services: Ollama and Qdrant for the full local path
- Local bootstrap credentials and tenant defaults are provided through `Settings` defaults and `.env.example`
- Smoke command: `make smoke-openrouter` or `make smoke-fallback`

**Staging:**
- Not explicitly defined
  - Use env-var substitution for provider endpoints, keys, and datastore path

**Production:**
- Secrets management is external to the repo
- `Settings` allows either mock or real premium provider wiring, but secure secret injection must be handled by the runtime platform

## Webhooks & Callbacks

**Incoming:**
- Not detected

**Outgoing:**
- Not detected beyond direct synchronous provider API calls

---

*Integration audit: 2026-03-15*
*Update when adding/removing external services*
