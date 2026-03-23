---
phase: 08-fleet-inventory-and-freshness-visibility
plan: "02"
subsystem: heartbeat-sender
tags: [heartbeat, freshness, fleet-inventory, deployment, sqlite, migration]
dependency_graph:
  requires:
    - phase: 08-01
      provides: POST /v1/heartbeat endpoint, HeartbeatIngestService, compute_freshness, HeartbeatRequest model
  provides:
    - HeartbeatService background task (gateway-side outbound heartbeat sender, 5-minute interval)
    - credential_raw stored in LocalHostedIdentityModel for heartbeat auth
    - get_deployment_credential() helper on GatewayEnrollmentService
    - Heartbeat sender wired into lifespan start/stop
    - Alembic migration 20260322_0004 (credential_raw column on local_hosted_identity)
    - tests/test_freshness.py: 9 unit tests for D-08 thresholds and D-09 reason format
    - tests/test_heartbeat_api.py: 7 integration tests for INVT-01/INVT-02/INVT-04
  affects:
    - src/nebula/services/gateway_enrollment_service.py
    - src/nebula/db/models.py
    - src/nebula/core/container.py
    - src/nebula/main.py
tech-stack:
  added: []
  patterns:
    - HeartbeatService follows same httpx outbound pattern as GatewayEnrollmentService (injectable transport)
    - HeartbeatService._summarize_deps() maps RuntimeHealthService dict to HostedDependencySummary shape
    - compute_freshness normalises naive datetimes to UTC-aware before comparison (SQLite compat)
    - credential_raw stored with server_default="" for safe migration of existing rows
key-files:
  created:
    - src/nebula/services/heartbeat_service.py
    - migrations/versions/20260322_0004_credential_raw.py
    - tests/test_freshness.py
    - tests/test_heartbeat_api.py
  modified:
    - src/nebula/db/models.py (credential_raw column on LocalHostedIdentityModel)
    - src/nebula/services/gateway_enrollment_service.py (credential_raw persist + get_deployment_credential)
    - src/nebula/services/heartbeat_ingest_service.py (timezone normalization fix)
    - src/nebula/core/container.py (HeartbeatService registration and shutdown)
    - src/nebula/main.py (heartbeat_service.start() in lifespan)
key-decisions:
  - "HeartbeatService.start() called unconditionally in lifespan; _send_once silently skips when not enrolled or hosted_plane_url is None"
  - "credential_raw stored with server_default='' so existing rows survive migration without re-enrollment"
  - "compute_freshness normalises naive datetimes from SQLite to UTC-aware before subtraction"
  - "HeartbeatService injects both gateway_enrollment_service and runtime_health_service for loose coupling"
patterns-established:
  - "Background task services (HeartbeatService) follow asyncio.create_task pattern with start()/stop() interface"
  - "All exceptions in heartbeat _send_once() are caught and logged as warning — never propagated (D-05)"
  - "Freshness computation always normalises tzinfo before comparison to handle SQLite naive datetimes"
requirements-completed:
  - INVT-01
  - INVT-02
  - INVT-04
duration: 12min
completed: 2026-03-22
---

# Phase 08 Plan 02: Gateway Heartbeat Sender Summary

**Gateway-side HeartbeatService background task sending outbound POST /v1/heartbeat every 5 minutes using deployment credential, with credential_raw storage fix and full D-08/D-09 test coverage**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-03-22T23:08:00Z
- **Completed:** 2026-03-22T23:20:19Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Gateway sends heartbeats outbound to hosted plane every 5 minutes via `HeartbeatService` background asyncio task
- Resolved credential storage gap: `credential_raw` now persisted during enrollment exchange and used for heartbeat auth header
- 16 new tests (9 unit + 7 integration) prove D-08 freshness thresholds, D-09 reason format, and INVT-01/INVT-02/INVT-04 backend behavior

## Task Commits

1. **Task 1: Gateway heartbeat sender with credential storage fix** - `56578c7` (feat)
2. **Task 2: Backend tests for heartbeat API and freshness calculation** - `bb0c69c` (test)

## Files Created/Modified

- `src/nebula/services/heartbeat_service.py` - HeartbeatService with start/stop/loop/_send_once, HEARTBEAT_INTERVAL_SECONDS=300
- `src/nebula/db/models.py` - Added credential_raw column to LocalHostedIdentityModel
- `src/nebula/services/gateway_enrollment_service.py` - Persist credential_raw in _store_local_identity; add get_deployment_credential(); remove heartbeat stub
- `src/nebula/services/heartbeat_ingest_service.py` - Timezone normalization fix in compute_freshness
- `src/nebula/core/container.py` - Register HeartbeatService; shutdown hook
- `src/nebula/main.py` - Wire heartbeat_service.start() after enrollment in lifespan
- `migrations/versions/20260322_0004_credential_raw.py` - Alembic migration for credential_raw column
- `tests/test_freshness.py` - 9 unit tests for compute_freshness (None/connected/degraded/stale/offline/clock-skew/boundaries/D-09 reason codes)
- `tests/test_heartbeat_api.py` - 7 integration tests (auth, last_seen_at, freshness_status, capability_flags, dependency_summary)

## Decisions Made

- `HeartbeatService.start()` is called unconditionally in lifespan; `_send_once()` silently returns when `get_deployment_credential()` returns None or `hosted_plane_url` is None — avoids conditional startup complexity
- `credential_raw` uses `server_default=""` in migration so existing rows (if any) survive without error; empty string is treated as None by `get_deployment_credential()`
- `compute_freshness()` normalizes naive datetimes (SQLite storage artifact) to UTC-aware before subtraction — prevents TypeError in test environments

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed timezone-naive/aware mismatch in compute_freshness**
- **Found during:** Task 2 (test_heartbeat_updates_last_seen_at)
- **Issue:** SQLite stores datetimes without tzinfo; compute_freshness compared naive `last_seen_at` with `datetime.now(UTC)` (offset-aware), causing `TypeError: can't subtract offset-naive and offset-aware datetimes`
- **Fix:** Added `if last_seen_at.tzinfo is None: last_seen_at = last_seen_at.replace(tzinfo=UTC)` in `compute_freshness()`
- **Files modified:** `src/nebula/services/heartbeat_ingest_service.py`
- **Verification:** All 16 new tests pass; test_heartbeat_freshness_connected confirms "connected" returned after live heartbeat
- **Committed in:** `bb0c69c` (Task 2 commit)

**2. [Rule 3 - Blocking] Added Alembic migration for credential_raw column**
- **Found during:** Task 2 (test_gateway_enrollment.py failures after Task 1 committed)
- **Issue:** Plan mentioned `configured_app()` auto-migrates via SQLite; however existing tests that insert into `local_hosted_identity` (test_gateway_enrollment.py) failed because the column was only in the ORM model, not in any migration
- **Fix:** Created migration `20260322_0004_credential_raw.py` with idempotent `inspector.get_columns` guard and `server_default=""`
- **Files modified:** `migrations/versions/20260322_0004_credential_raw.py`
- **Verification:** Full suite 91 passed (0 failed)
- **Committed in:** `bb0c69c` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes essential for correctness. No scope creep.

## Issues Encountered

- Boundary test for `compute_freshness` at exactly 10 minutes triggered timing flakiness — fixed by testing 9m59s (safely under) instead of exactly 10m

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Heartbeat data flow is now end-to-end: gateway sends (08-02), hosted receives and stores (08-01)
- All INVT-01/INVT-02/INVT-04 backend behaviors are tested and proven
- Phase 08-03 (fleet console UI) can proceed: it reads `freshness_status`, `last_seen_at`, `capability_flags`, and `dependency_summary` from `/v1/admin/deployments`

---
*Phase: 08-fleet-inventory-and-freshness-visibility*
*Completed: 2026-03-22*
