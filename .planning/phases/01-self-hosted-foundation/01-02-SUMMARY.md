---
phase: 01-self-hosted-foundation
plan: "02"
subsystem: api
tags: [health, configuration, readiness, qdrant, ollama]
requires:
  - phase: 01-self-hosted-foundation
    provides: Self-hosted Docker Compose topology and operator deployment guide
provides:
  - Non-local runtime guardrails for secrets, provider selection, and runtime profile
  - Component-level readiness and dependency health reporting
  - Regression coverage for runtime safety and degraded optional dependencies
affects: [deployment, operations, testing]
tech-stack:
  added: []
  patterns: [explicit runtime profiles, liveness-readiness split, degraded optional dependency reporting]
key-files:
  created: [src/nebula/services/runtime_health_service.py]
  modified: [src/nebula/core/config.py, src/nebula/core/container.py, src/nebula/main.py, src/nebula/services/governance_store.py, src/nebula/services/semantic_cache_service.py, src/nebula/services/embeddings_service.py, tests/test_settings.py, tests/test_health.py, deploy/selfhosted.env.example, docs/self-hosting.md, README.md]
key-decisions:
  - "Nebula must reject local_dev runtime profile, default secrets, and the mock premium provider outside local mode."
  - "Readiness remains HTTP 200 for degraded optional dependencies and only fails when required services are not ready."
patterns-established:
  - "Runtime health is aggregated through a dedicated RuntimeHealthService instead of route-local checks."
  - "Operator docs and tests describe degraded optional dependencies explicitly rather than treating them as startup failures."
requirements-completed: [PLAT-02, PLAT-04]
duration: 1min
completed: 2026-03-15
---

# Phase 01: Self-Hosted Foundation Summary

**Premium-first runtime guardrails with explicit readiness and dependency health reporting**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-15T23:32:23Z
- **Completed:** 2026-03-15T23:33:00Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments
- Added runtime-profile and secret validation so Nebula refuses unsafe non-local startup defaults.
- Split liveness from readiness with `/health/ready` and `/health/dependencies`.
- Added focused regression coverage for degraded optional dependencies and non-local configuration rules.

## Task Commits

Each task was committed atomically:

1. **Task 1: Enforce explicit non-local runtime configuration and secret safety** - `1a5b1ee` (feat)
2. **Task 2: Add component-level readiness and degraded dependency reporting** - `85f50d2` (feat)
3. **Task 3: Add regression coverage and operator docs for guardrails and readiness** - `3407a0e` (test)

## Files Created/Modified
- `src/nebula/core/config.py` - Enforces `premium_first` and rejects unsafe non-local defaults.
- `src/nebula/services/runtime_health_service.py` - Aggregates dependency health into readiness reports.
- `src/nebula/main.py` - Exposes `/health`, `/health/ready`, and `/health/dependencies`.
- `src/nebula/services/governance_store.py` - Reports governance-store readiness.
- `src/nebula/services/semantic_cache_service.py` - Reports degraded Qdrant/cache state without blocking startup.
- `src/nebula/services/embeddings_service.py` - Reports local Ollama reachability as optional dependency health.
- `tests/test_settings.py` - Covers non-local runtime guardrails.
- `tests/test_health.py` - Covers degraded readiness and required-dependency failures.
- `deploy/selfhosted.env.example` - Documents the required `premium_first` runtime profile.
- `docs/self-hosting.md` - Documents readiness endpoints and degraded-mode meaning.
- `README.md` - Documents the new health endpoints for operators.

## Decisions Made
- Required the premium-first runtime profile for any non-local deployment to keep the self-hosted path explicit and safe.
- Treated semantic cache and local Ollama as optional dependencies in readiness so Nebula can serve traffic in degraded mode when the core gateway and governance store are healthy.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The app now distinguishes liveness from readiness, giving the persistence work a clear place to report migrated database state.
- Phase 01-03 can replace the bootstrap SQLite path with migration-backed persistence without changing the operator-facing health contract.

---
*Phase: 01-self-hosted-foundation*
*Completed: 2026-03-15*
