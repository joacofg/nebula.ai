# Phase 1 Research: Self-Hosted Foundation

**Phase:** 1
**Researched:** 2026-03-15
**Confidence:** HIGH

## Executive Summary

Phase 1 should harden Nebula around one opinionated self-hosted story instead of expanding feature scope. The most credible path for this repo is a premium-first Docker Compose deployment with three managed services: the FastAPI app, PostgreSQL for governance and usage ledger persistence, and Qdrant for semantic cache state. Local Ollama remains supported, but it is reported as an optional optimization rather than a deployment prerequisite.

The existing code already has the right seams for this work: `src/nebula/core/config.py` owns runtime configuration, `src/nebula/core/container.py` is the composition root, `src/nebula/main.py` already exposes liveness, and `src/nebula/services/governance_store.py` is the place to replace bootstrap DDL with a migration-backed persistence layer.

## Current Baseline

### Deployment

- The repo only ships `docker-compose.yml` for Qdrant.
- There is no container image, self-hosted compose stack, or operator-facing deployment guide.
- The README documents local development, not a production-shaped path.

### Runtime Safety

- `src/nebula/core/config.py` uses local-only defaults for admin and bootstrap credentials.
- Startup validation only checks premium provider credentials when `NEBULA_PREMIUM_PROVIDER=openai_compatible`.
- `src/nebula/main.py` exposes only `GET /health`, which currently returns `status` plus a cache-enabled flag.

### Persistence

- `src/nebula/services/governance_store.py` creates the SQLite schema at runtime with `CREATE TABLE IF NOT EXISTS`.
- The governance store bootstraps tenant and API key records during app initialization.
- There is no migration framework, no durable Postgres path, and no schema-version health check.

## Recommended Implementation Direction

### 1. Canonical Self-Hosted Topology

Adopt a premium-first Compose stack with these concrete artifacts:

- `Dockerfile` for the FastAPI app on Python 3.12 slim
- `.dockerignore` to keep the image lean
- `docker-compose.selfhosted.yml` with services `nebula`, `postgres`, and `qdrant`
- `deploy/selfhosted.env.example` for the supported runtime profile
- `docs/self-hosting.md` as the operator runbook

Use the current `uvicorn nebula.main:app` entrypoint first, then update the app service in the persistence plan to run `alembic upgrade head` before startup.

### 2. Runtime Profile and Secret Guardrails

Introduce an explicit runtime-profile boundary:

- `local_dev` for current local workflows
- `premium_first` for the canonical self-hosted deployment path

For non-local environments, Nebula should fail fast when any of the following remain true:

- `NEBULA_ADMIN_API_KEY=nebula-admin-key`
- `NEBULA_BOOTSTRAP_API_KEY=nebula-dev-key`
- `NEBULA_PREMIUM_PROVIDER=mock`
- the runtime profile is not explicitly set

That keeps the current dev ergonomics while enforcing explicit configuration for any serious deployment.

### 3. Readiness and Dependency Detail

Keep `/health` as a liveness endpoint and add two operator-facing endpoints:

- `GET /health/ready`
- `GET /health/dependencies`

Use this readiness contract:

- `gateway` and `governance_store` are required
- `semantic_cache` is optional and can report `degraded`
- `local_ollama` is optional in `premium_first` mode and can report `degraded`

`/health/ready` should return HTTP 200 when required dependencies are ready, even if optional dependencies are degraded, and HTTP 503 only when the gateway cannot safely serve traffic. The body should include a `status` field with `ready`, `degraded`, or `not_ready`, plus a component map that tells operators what is required versus optional.

### 4. Durable Persistence and Migrations

Move governance persistence to a migration-backed database layer:

- Add `sqlalchemy`, `alembic`, and `psycopg[binary]` to `pyproject.toml`
- Add `NEBULA_DATABASE_URL` as the primary persistence setting
- Keep SQLite available for local dev via a SQLite URL, but route both SQLite and Postgres through the same Alembic migration path
- Stop creating tables in `GovernanceStore.initialize()`
- Keep bootstrap tenant and API key creation, but only after the schema already exists

The minimal brownfield-safe structure is:

- `src/nebula/db/session.py` for engine and session factory creation
- `src/nebula/db/models.py` for the governance and usage-ledger tables
- `migrations/env.py` plus a baseline migration under `migrations/versions/`

This preserves the current repository-style service API while replacing the implicit schema bootstrap behavior underneath it.

## Plan Split Recommendation

### Plan 01

Define the self-hosted packaging and runtime topology:

- container image
- self-hosted compose stack
- env template
- deployment guide
- Makefile helpers

### Plan 02

Harden configuration, secrets, and health/readiness behavior:

- non-local default-secret rejection
- explicit runtime profile checks
- readiness and dependency-detail endpoints
- degraded-mode visibility for cache and local optimization

### Plan 03

Introduce the durable persistence and migration path:

- Alembic scaffold
- database URL configuration
- migration-backed governance store
- updated tests and deployment docs

## Validation Architecture

Phase 1 already has a fast pytest baseline, so no Wave 0 framework installation is needed.

- Quick command: `./.venv/bin/pytest tests/test_settings.py tests/test_health.py -q`
- Full command: `./.venv/bin/pytest -q`
- Current observed quick runtime: about 1.3 seconds wall-clock
- Current observed full runtime: about 1.1 seconds wall-clock

Coverage to add while executing this phase:

- `tests/test_settings.py` for non-local startup guardrails
- `tests/test_health.py` for readiness and degraded dependency reporting
- migration-backed persistence coverage in `tests/test_governance_api.py` and test app bootstrapping helpers

## Risks to Avoid

- Do not make Ollama or Qdrant required for the premium-first deployment path.
- Do not leave the old runtime `CREATE TABLE IF NOT EXISTS` path in place after Alembic lands.
- Do not split deployment documentation across multiple equal paths; the phase needs one supported operator story.
- Do not let readiness remain a boolean cache flag; operators need component-level visibility.

## Research Inputs

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/01-self-hosted-foundation/01-CONTEXT.md`
- `.planning/codebase/STACK.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONCERNS.md`
- `README.md`
- `docker-compose.yml`
- `src/nebula/core/config.py`
- `src/nebula/core/container.py`
- `src/nebula/main.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/semantic_cache_service.py`
- `tests/test_settings.py`
- `tests/test_health.py`

---
*Phase research completed: 2026-03-15*
*Ready for planning: yes*
