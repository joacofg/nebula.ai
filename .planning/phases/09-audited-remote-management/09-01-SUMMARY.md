---
phase: 09-audited-remote-management
plan: 01
subsystem: api
tags: [fastapi, sqlalchemy, alembic, pydantic, remote-management]
requires:
  - phase: 08-fleet-inventory-and-freshness-visibility
    provides: deployment identity, freshness state, and hosted admin deployment surfaces
provides:
  - typed hosted remote-action queue contracts for rotate_deployment_credential
  - durable deployment_remote_actions persistence with live-action uniqueness protection
  - admin queue and history APIs for hosted remote-management requests
affects: [09-02-PLAN, 09-03-PLAN, remote-management, audit-history]
tech-stack:
  added: []
  patterns: [partial unique live-action guard, service-owned duplicate suppression, admin remote action endpoints]
key-files:
  created: [.planning/phases/09-audited-remote-management/09-01-SUMMARY.md, migrations/versions/20260322_0005_remote_actions.py, tests/test_remote_management_api.py]
  modified: [src/nebula/models/deployment.py, src/nebula/db/models.py, src/nebula/services/enrollment_service.py, src/nebula/api/routes/admin.py]
key-decisions:
  - "Remote-action queue/history endpoints live on the admin router under /v1/admin/deployments so existing enrollment routes can stay in place."
  - "The live-action uniqueness guard is a partial unique index limited to queued and in_progress rows, with sqlite and postgres predicates kept aligned."
patterns-established:
  - "Remote-management queueing is service-owned: validate deployment state, trim note, lock existing live row, then return or create one action record."
  - "Hosted remote-action contracts use string-serialized timestamps in API models to match the existing deployment/enrollment response style."
requirements-completed: [RMGT-01, RMGT-03]
duration: 4min
completed: 2026-03-23
---

# Phase 9 Plan 01: Audited Remote Management Summary

**Hosted rotate_deployment_credential queue contracts, durable action persistence, and audited admin queue/history APIs**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-23T00:01:30Z
- **Completed:** 2026-03-23T00:05:56Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added typed remote-action contracts to the hosted deployment models, including queue requests, action records, failure reasons, and action summary shape.
- Added the `deployment_remote_actions` ORM model and Alembic migration with a live-action uniqueness guard for queued and in-progress actions.
- Implemented admin queue/history APIs with deployment-state validation, duplicate live-action suppression, and regression coverage for success, invalid-state, and history-order behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define remote-action models, ORM state, and migration** - `b20391a` (feat)
2. **Task 2: Implement hosted queue/history APIs and queue-contract tests** - `8e9bf8b` (feat)

## Files Created/Modified
- `src/nebula/models/deployment.py` - Remote action API models and deployment summary contract.
- `src/nebula/db/models.py` - `DeploymentRemoteActionModel` plus live-action partial unique index metadata.
- `migrations/versions/20260322_0005_remote_actions.py` - Idempotent queue-table migration and live-action index creation.
- `src/nebula/services/enrollment_service.py` - Queue creation, duplicate suppression, and remote-action history reads.
- `src/nebula/api/routes/admin.py` - Hosted admin queue and history endpoints under `/v1/admin/deployments/...`.
- `tests/test_remote_management_api.py` - Contract and API regression coverage for queue and history behavior.

## Decisions Made
- Kept the new remote-action endpoints on the shared admin router so the deployed path matches the plan without moving the existing enrollment route module.
- Matched test and production semantics for the live-action uniqueness guard by defining partial-index predicates for both SQLite and PostgreSQL.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed unconditional uniqueness on SQLite remote-action history**
- **Found during:** Task 2 (Implement hosted queue/history APIs and queue-contract tests)
- **Issue:** The live-action uniqueness guard behaved as a full unique index in SQLite, blocking historical `applied` rows from being followed by a new queued action.
- **Fix:** Added the same queued/in_progress predicate to the SQLite index definition in ORM and migration code.
- **Files modified:** `src/nebula/db/models.py`, `migrations/versions/20260322_0005_remote_actions.py`
- **Verification:** `.venv/bin/pytest tests/test_remote_management_api.py -x`
- **Committed in:** `8e9bf8b` (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Required for correctness in the repo's SQLite-backed integration tests and to keep history semantics aligned with production intent.

## Issues Encountered
- `pytest` was not on `PATH`; execution continued with `.venv/bin/pytest` from the project environment.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Hosted-side queue contracts, persistence, and admin APIs are ready for outbound polling and local apply logic in `09-02-PLAN`.
- Later phases can build audit rollups and UI history surfaces on the stable `RemoteActionRecord` and `/remote-actions` contract.

## Self-Check: PASSED

---
*Phase: 09-audited-remote-management*
*Completed: 2026-03-23*
