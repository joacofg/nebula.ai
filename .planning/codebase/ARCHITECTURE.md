# Architecture

**Analysis Date:** 2026-03-15

## Pattern Overview

**Overall:** Layered FastAPI gateway for multi-provider chat routing, semantic caching, and tenant governance

**Key Characteristics:**
- Single deployable ASGI application rooted at `src/nebula/main.py`
- Runtime wiring happens through one `ServiceContainer` in `src/nebula/core/container.py`
- Request handling is mostly stateless, with persistent state limited to SQLite governance tables and Qdrant cache entries
- Provider selection is policy- and heuristic-driven, with local-to-premium fallback handled inside the chat service

## Layers

**API Layer:**
- Purpose: Accept HTTP requests, validate payloads, and translate service metadata into HTTP responses
- Contains: `src/nebula/api/routes/chat.py`, `src/nebula/api/routes/admin.py`, `src/nebula/api/dependencies.py`
- Depends on: `ServiceContainer`, Pydantic models, FastAPI dependency injection
- Used by: Incoming HTTP requests under `/v1/*`

**Service Layer:**
- Purpose: Implement routing, policy enforcement, auth, caching, governance persistence, and provider orchestration
- Contains: `src/nebula/services/chat_service.py`, `router_service.py`, `policy_service.py`, `auth_service.py`, `semantic_cache_service.py`, `governance_store.py`
- Depends on: Providers, settings, models, observability helpers
- Used by: API routes and benchmark runner indirectly through the app

**Provider Layer:**
- Purpose: Isolate upstream completion implementations behind a common interface
- Contains: `src/nebula/providers/base.py`, `ollama.py`, `openai_compatible.py`, `mock_premium.py`, `src/nebula/services/provider_registry.py`
- Depends on: HTTPX and request/response models
- Used by: `ChatService`

**Model Layer:**
- Purpose: Define request, response, and governance schemas
- Contains: `src/nebula/models/openai.py`, `src/nebula/models/governance.py`
- Depends on: Pydantic
- Used by: API routes, services, providers, and tests

**Observability Layer:**
- Purpose: Request IDs, structured-enough logs, and Prometheus counters/histograms
- Contains: `src/nebula/observability/middleware.py`, `logging.py`, `metrics.py`
- Depends on: Starlette middleware and `prometheus_client`
- Used by: `create_app()` and `ChatService`

## Data Flow

**Chat Completion Request:**

1. `src/nebula/main.py` creates the FastAPI app and attaches `RequestContextMiddleware`
2. `src/nebula/api/routes/chat.py` validates `ChatCompletionRequest` and resolves `AuthenticatedTenantContext`
3. `src/nebula/services/chat_service.py` extracts the latest user prompt and asks `PolicyService` for a `PolicyResolution`
4. `SemanticCacheService` checks Qdrant for a semantic hit when cache is enabled
5. `RouterService` and tenant policy determine local vs premium execution
6. The selected provider in `ProviderRegistry` executes the request; local failures can fall back to premium
7. `ChatService` records usage in `GovernanceStore`, updates cache when allowed, and returns OpenAI-style payloads plus `X-Nebula-*` metadata headers

**Admin Governance Request:**

1. `src/nebula/api/routes/admin.py` gates access with `require_admin()`
2. Route handlers call `GovernanceStore` methods directly for tenant, API key, policy, and ledger CRUD
3. Pydantic models in `src/nebula/models/governance.py` shape request and response bodies

**Benchmark Run:**

1. `python -m nebula.benchmarking.run` executes `src/nebula/benchmarking/run.py`
2. The runner either targets an existing base URL or spawns managed Uvicorn subprocesses
3. Scenario requests are sent through the public `/v1/chat/completions` API and evaluated from HTTP headers/body
4. Reports are written to `artifacts/benchmarks/<timestamp>/`

**State Management:**
- SQLite state: tenants, policies, API keys, and usage ledger
- Qdrant state: semantic cache embeddings and cached responses
- In-memory runtime state: one container instance per app process, with long-lived HTTP clients per provider service

## Key Abstractions

**ServiceContainer:**
- Purpose: Central composition root
- Examples: `src/nebula/core/container.py`
- Pattern: Manual dependency injection / service locator attached to `app.state`

**PolicyResolution:**
- Purpose: Bundle the routing decision with cache, fallback, budget, and policy outcome flags
- Examples: `src/nebula/services/policy_service.py`
- Pattern: Immutable dataclass passed through service methods

**CompletionProvider:**
- Purpose: Normalize local, premium, and mock provider behavior
- Examples: `src/nebula/providers/base.py`, `ollama.py`, `openai_compatible.py`
- Pattern: Strategy interface with completion and streaming methods

## Entry Points

**ASGI App:**
- Location: `src/nebula/main.py`
- Triggers: Uvicorn startup or imports from tests
- Responsibilities: Initialize settings, container, middleware, routers, and `/health` plus optional `/metrics`

**Benchmark CLI:**
- Location: `src/nebula/benchmarking/run.py`
- Triggers: `make benchmark` or `python -m nebula.benchmarking.run`
- Responsibilities: Load datasets, manage benchmark servers, collect report artifacts

## Error Handling

**Strategy:** Raise typed domain/provider errors in lower layers, convert them to `HTTPException` at service or route boundaries

**Patterns:**
- Auth and policy failures raise `HTTPException` in `AuthService` and `PolicyService`
- Provider transport errors are wrapped as `ProviderError` in `src/nebula/providers/*.py`
- `ChatService` catches provider failures, records usage ledger outcomes, and emits HTTP 502 when recovery is not possible
- Cache failures are generally downgraded to warnings and a cache miss path instead of bubbling

## Cross-Cutting Concerns

**Logging:**
- Request ID context is set in `src/nebula/observability/middleware.py`
- Route decisions, provider completions, fallback selection, and cache failures are logged from `ChatService` and cache services

**Validation:**
- FastAPI + Pydantic validate all external request bodies
- `Settings` performs startup validation for premium provider configuration

**Authentication:**
- Client and admin auth are header-based and backed by SQLite state
- Tenant policy is resolved per request and influences routing, cache, and fallback behavior

---

*Architecture analysis: 2026-03-15*
*Update when major patterns change*
