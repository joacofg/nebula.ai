---
phase: 07-deployment-enrollment-and-identity
plan: "02"
subsystem: api
tags: [fastapi, sqlalchemy, alembic, pydantic, enrollment, httpx, gateway, identity]

# Dependency graph
requires:
  - phase: 07-01
    provides: DeploymentModel, EnrollmentTokenModel, EnrollmentService, EnrollmentExchangeRequest/Response Pydantic models
provides:
  - consume_enrollment_token method on EnrollmentService (atomic SHA-256 lock, nbdc_ credential)
  - POST /v1/enrollment/exchange endpoint (no auth required, gateway-facing)
  - LocalHostedIdentityModel ORM class and local_hosted_identity DB table
  - GatewayEnrollmentService with attempt_enrollment, get_local_identity, clear_local_identity
  - Startup hook in main.py lifespan that triggers enrollment from NEBULA_ENROLLMENT_TOKEN
  - Migration 20260321_0002 extended with local_hosted_identity table
affects:
  - 07-03 (identity and linking builds on LocalHostedIdentityModel and GatewayEnrollmentService)
  - Phase 8 (first heartbeat stub logged; actual heartbeat delivery deferred)

# Tech tracking
tech-stack:
  added:
    - httpx (outbound async HTTP client for enrollment exchange; already a transitive dep)
  patterns:
    - Pessimistic SELECT ... FOR UPDATE lock on EnrollmentTokenModel prevents double-consumption
    - GatewayEnrollmentService accepts optional http_transport for ASGI-based testing without a real server
    - Enrollment failure in lifespan is wrapped in try/except — non-fatal by design
    - Local identity stored as SHA-256 credential hash + 12-char prefix, same as enrollment token pattern

key-files:
  created:
    - src/nebula/services/gateway_enrollment_service.py
    - tests/test_gateway_enrollment.py
  modified:
    - src/nebula/services/enrollment_service.py (consume_enrollment_token added)
    - src/nebula/api/routes/enrollment.py (exchange_router and enrollment_exchange endpoint added)
    - src/nebula/db/models.py (LocalHostedIdentityModel added)
    - migrations/versions/20260321_0002_deployments.py (local_hosted_identity table added)
    - src/nebula/core/container.py (GatewayEnrollmentService registered)
    - src/nebula/main.py (exchange_router mounted; enrollment startup hook added)
    - tests/test_enrollment_api.py (exchange success/expired/consumed tests + 409 test upgraded)

key-decisions:
  - "GatewayEnrollmentService accepts optional http_transport parameter to enable httpx.ASGITransport injection in tests, avoiding the need for a real server while testing the outbound call pattern"
  - "Exchange endpoint has no auth (by design — enrollment token IS the auth credential)"
  - "Enrollment failure in lifespan wrapped in broad try/except to guarantee gateway always starts"
  - "SELECT FOR UPDATE used on EnrollmentTokenModel to prevent race-condition double-consumption"

patterns-established:
  - "GatewayEnrollmentService pattern: outbound httpx call with injected transport for testability"
  - "Non-fatal startup hooks: wrap in try/except, log error, continue"

requirements-completed:
  - ENRL-02

# Metrics
duration: 6min
completed: 2026-03-21
---

# Phase 07 Plan 02: Enrollment Exchange and Gateway Identity Summary

**Outbound-only enrollment exchange endpoint with atomic token consumption, steady-state credential generation, local identity persistence, and non-fatal gateway startup hook**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-03-21T23:05:01Z
- **Completed:** 2026-03-21T23:11:00Z
- **Tasks:** 2 (each with TDD RED + GREEN)
- **Files modified:** 8

## Accomplishments

- `consume_enrollment_token` added to EnrollmentService: SHA-256 token lookup with `SELECT ... FOR UPDATE` pessimistic lock, atomic state transition to "active", `nbdc_`-prefixed steady-state credential generation
- `POST /v1/enrollment/exchange` endpoint created on a separate `exchange_router` (no auth required — token IS the auth)
- `LocalHostedIdentityModel` ORM class added with `local_hosted_identity` table in migration 20260321_0002
- `GatewayEnrollmentService` created with `attempt_enrollment` (outbound httpx), `get_local_identity`, `clear_local_identity`
- Injectable `http_transport` parameter enables ASGI-based testing without an actual running server
- Startup hook in `main.py` lifespan: if `NEBULA_ENROLLMENT_TOKEN` is set, calls `attempt_enrollment`; failure is non-fatal
- Warning logged when `NEBULA_ENROLLMENT_TOKEN` remains in env after successful enrollment
- First heartbeat stub logged post-enrollment (Phase 8 delivers actual heartbeat)
- 11 exchange + gateway tests pass; full 69-test suite green with no regressions

## Task Commits

1. **TDD RED: Failing exchange endpoint tests** — `c437b56` (test)
2. **Task 1: Exchange endpoint and atomic token consumption** — `cabe56d` (feat)
3. **TDD RED: Failing gateway enrollment tests** — `b8ba38a` (test)
4. **Task 2: GatewayEnrollmentService and startup hook** — `369ab69` (feat)

## Files Created/Modified

- `src/nebula/services/enrollment_service.py` — Added `consume_enrollment_token` with SELECT FOR UPDATE
- `src/nebula/api/routes/enrollment.py` — Added `exchange_router` and `enrollment_exchange` endpoint
- `src/nebula/db/models.py` — Added `LocalHostedIdentityModel`
- `migrations/versions/20260321_0002_deployments.py` — Extended with `local_hosted_identity` table
- `src/nebula/services/gateway_enrollment_service.py` — New: GatewayEnrollmentService
- `src/nebula/core/container.py` — GatewayEnrollmentService registered
- `src/nebula/main.py` — exchange_router mounted; enrollment startup hook added
- `tests/test_enrollment_api.py` — Exchange success/expired/consumed tests; 409 test completed
- `tests/test_gateway_enrollment.py` — New: 4 gateway enrollment integration tests

## Decisions Made

- GatewayEnrollmentService accepts `http_transport: httpx.AsyncBaseTransport | None` to inject `httpx.ASGITransport` in tests. This allows the outbound exchange call to route through the same FastAPI app without needing a real running server, matching the codebase's TestClient-based test pattern.
- Exchange endpoint at `/v1/enrollment/exchange` has no `require_admin` dependency — the enrollment token itself is the authentication mechanism. A separate `exchange_router` was used to isolate it from admin routes.
- Enrollment failure in the lifespan startup hook is wrapped in `try/except Exception` to guarantee the gateway always starts — per RESEARCH Pitfall 2.
- `SELECT ... FOR UPDATE` on `EnrollmentTokenModel` prevents concurrent double-consumption race conditions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Test strategy] GatewayEnrollmentService uses injectable http_transport instead of hardcoded httpx**

- **Found during:** Task 2 (writing tests)
- **Issue:** The plan specified testing via `configured_app` with `NEBULA_ENROLLMENT_TOKEN` set, expecting the lifespan to call the exchange endpoint on the same app. But TestClient's `http://testserver` URL is not reachable from outbound httpx calls made during lifespan (outside the client context).
- **Fix:** Added `http_transport: httpx.AsyncBaseTransport | None = None` parameter to `GatewayEnrollmentService.__init__`. Tests inject `httpx.ASGITransport(app=app)` to route the outbound call through the ASGI app directly.
- **Files modified:** `src/nebula/services/gateway_enrollment_service.py`, `tests/test_gateway_enrollment.py`
- **Commit:** `369ab69`

## Known Stubs

- `attempt_enrollment` logs "Sending first heartbeat (stub — Phase 8 delivers actual heartbeat implementation)" at line ~75 of `gateway_enrollment_service.py`. This is intentional — Phase 8 will implement the actual heartbeat ping.

## Self-Check: PASSED
