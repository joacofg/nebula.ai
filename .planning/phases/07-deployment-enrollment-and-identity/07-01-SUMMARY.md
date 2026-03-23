---
phase: 07-deployment-enrollment-and-identity
plan: "01"
subsystem: api
tags: [fastapi, sqlalchemy, alembic, pydantic, enrollment, deployment]

# Dependency graph
requires:
  - phase: 06-trust-boundary-and-hosted-contract
    provides: governance patterns, ORM patterns, session factory, admin API conventions
provides:
  - DeploymentModel and EnrollmentTokenModel ORM classes with SQLAlchemy
  - Migration 20260321_0002 creating deployments and enrollment_tokens tables
  - EnrollmentService with create_deployment_slot, generate_enrollment_token, list_deployments, get_deployment
  - Pydantic models for deployment API (DeploymentRecord, DeploymentCreateRequest, EnrollmentTokenResponse, EnrollmentExchangeRequest, EnrollmentExchangeResponse)
  - Admin API endpoints at /v1/admin/deployments for slot creation and token generation
  - enrollment_token and hosted_plane_url optional settings fields
affects:
  - 07-02 (exchange endpoint builds on DeploymentModel and EnrollmentTokenModel)
  - 07-03 (identity and linking builds on EnrollmentService and DeploymentRecord)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - EnrollmentService follows GovernanceStore session factory pattern (sessionmaker[Session])
    - Token stored as SHA-256 hash, raw token returned once only (nbet_ prefix)
    - Enrollment tokens use 1-hour TTL with expires_at field
    - ORM migration uses conditional table creation (inspector.get_table_names())

key-files:
  created:
    - src/nebula/db/models.py (DeploymentModel, EnrollmentTokenModel added)
    - src/nebula/models/deployment.py
    - src/nebula/services/enrollment_service.py
    - migrations/versions/20260321_0002_deployments.py
    - src/nebula/api/routes/enrollment.py
    - tests/test_enrollment_api.py
  modified:
    - src/nebula/core/config.py (enrollment_token, hosted_plane_url fields)
    - src/nebula/core/container.py (EnrollmentService registered)
    - src/nebula/main.py (enrollment_router mounted)

key-decisions:
  - "EnrollmentService gets its own session_factory instance via create_session_factory(settings), mirroring GovernanceStore pattern rather than sharing a factory"
  - "Token prefix is first 12 chars of raw token (including nbet_ prefix) for human-readable identification"
  - "generate_enrollment_token raises KeyError for missing deployments and ValueError for active state to allow distinct HTTP responses (404 vs 409)"
  - "Relink flow resets revoked/unlinked state back to pending when a new enrollment token is requested"

patterns-established:
  - "EnrollmentService pattern: service takes Settings + sessionmaker, uses _session() helper, raises exceptions for error cases"
  - "Enrollment routes use Depends(require_admin) for auth, returning container from dependency"
  - "Token generation returns raw token once; only hash + prefix stored in DB"

requirements-completed:
  - ENRL-01

# Metrics
duration: 8min
completed: 2026-03-21
---

# Phase 07 Plan 01: Deployment Enrollment Infrastructure Summary

**PostgreSQL-backed deployment slot registry with SHA-256-hashed enrollment tokens, admin CRUD API at /v1/admin/deployments, and 1-hour TTL single-use token generation**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-21T22:55:00Z
- **Completed:** 2026-03-21T23:03:00Z
- **Tasks:** 2 (+ TDD RED commit)
- **Files modified:** 9

## Accomplishments

- DeploymentModel and EnrollmentTokenModel ORM classes added to models.py with full schema coverage
- Alembic migration 20260321_0002 creates both tables with conditional pattern, FK ON DELETE CASCADE on enrollment_tokens
- EnrollmentService implements slot creation, enrollment token generation (SHA-256 hash, nbet_ prefix, 1h TTL), listing, and single-deployment lookup
- Admin API endpoints live at /v1/admin/deployments — POST to create, GET to list, GET /{id} for single, POST /{id}/enrollment-token to generate
- All 4 ENRL-01 integration tests pass; full 62-test suite green with no regressions

## Task Commits

Each task was committed atomically:

1. **TDD RED: Failing tests** - `55e6b52` (test)
2. **Task 1: DB models, Pydantic records, migration, enrollment service** - `06fcc87` (feat)
3. **Task 2: Wire enrollment API endpoints and register service** - `5972d72` (feat)

## Files Created/Modified

- `src/nebula/db/models.py` - Added DeploymentModel and EnrollmentTokenModel ORM classes
- `src/nebula/models/deployment.py` - Pydantic API shapes: DeploymentRecord, DeploymentCreateRequest, EnrollmentTokenResponse, EnrollmentExchangeRequest, EnrollmentExchangeResponse
- `src/nebula/services/enrollment_service.py` - EnrollmentService with create_deployment_slot, generate_enrollment_token, list_deployments, get_deployment
- `migrations/versions/20260321_0002_deployments.py` - Migration creating deployments and enrollment_tokens tables
- `src/nebula/api/routes/enrollment.py` - Admin deployment endpoints with require_admin auth
- `src/nebula/core/config.py` - Added enrollment_token and hosted_plane_url optional settings
- `src/nebula/core/container.py` - EnrollmentService registered in ServiceContainer
- `src/nebula/main.py` - enrollment_router mounted at /v1 prefix
- `tests/test_enrollment_api.py` - Integration tests for slot creation, listing, and token generation

## Decisions Made

- EnrollmentService gets its own session_factory instance via `create_session_factory(settings)`, mirroring the GovernanceStore pattern rather than sharing a factory instance. This keeps the two services independently lifecycle-managed.
- Token prefix stores first 12 chars of raw token (including "nbet_" prefix) for human-readable identification in logs.
- `generate_enrollment_token` raises `KeyError` for missing deployments and `ValueError` for the active-state guard, allowing the route to return distinct 404 vs 409 responses cleanly.
- Relink flow resets `revoked`/`unlinked` state back to `pending` when a fresh enrollment token is requested — per D-17 in plan context.

## Deviations from Plan

None - plan executed exactly as written.

Minor deviation: Test file initially used `asgi_lifespan.LifespanManager` (async pattern) but switched to `fastapi.testclient.TestClient` (synchronous) to match the established test conventions in this codebase. No functional change.

## Issues Encountered

- `asgi_lifespan` not installed — switched tests to use `TestClient` matching all other test modules in the project. Applied as Rule 3 auto-fix during RED phase.

## Next Phase Readiness

- Foundation complete for Plan 02: the enrollment exchange endpoint can now validate tokens against `EnrollmentTokenModel` and promote deployments from `pending` to `active`
- `EnrollmentExchangeRequest` and `EnrollmentExchangeResponse` Pydantic models are pre-defined and ready for Plan 02 route implementation
- 409 guard stub in `test_generate_token_for_active_deployment_returns_409` is ready to be filled in once the exchange endpoint exists

---
*Phase: 07-deployment-enrollment-and-identity*
*Completed: 2026-03-21*
