---
phase: 09-audited-remote-management
plan: 03
subsystem: ui
tags: [remote-management, audit, react, fastapi, vitest, pytest]
requires:
  - phase: 09-audited-remote-management
    provides: "Remote action queue/history APIs plus polling and completion flow"
provides:
  - "TTL expiry transitions for queued and in-progress remote actions"
  - "Deployment remote_action_summary rollups projected into hosted deployment records"
  - "Hosted deployment drawer action card with note capture and recent history"
affects: [phase-10-pilot-proof, hosted-console, remote-management]
tech-stack:
  added: []
  patterns:
    [
      "EnrollmentService expires live remote actions before queue, poll, and deployment projection reads",
      "Hosted drawer actions stay fail-closed on stale, offline, revoked, unlinked, or unsupported deployments",
    ]
key-files:
  created:
    [
      "tests/test_remote_management_audit.py",
      "console/src/components/deployments/remote-action-card.tsx",
      "console/src/components/deployments/remote-action-card.test.tsx",
    ]
  modified:
    [
      "src/nebula/services/enrollment_service.py",
      "console/src/lib/admin-api.ts",
      "console/src/lib/admin-api.test.ts",
      "console/src/components/deployments/deployment-detail-drawer.tsx",
    ]
key-decisions:
  - "Expired live remote actions transition to failed with a single shared reason/detail string before any queue, poll, or deployment projection path."
  - "Deployment responses expose remote_action_summary from the backend so the hosted drawer can stay metadata-driven and fail closed."
  - "The hosted drawer confirms rotation intent explicitly and scopes the UI copy to hosted-link credential changes only."
patterns-established:
  - "Remote action audit rollups come from EnrollmentService, not ad hoc API serialization."
  - "Deployment detail drawer composes hosted remote-management UI above lifecycle controls."
requirements-completed: [RMGT-01, RMGT-03]
duration: 6 min
completed: 2026-03-23
---

# Phase 9 Plan 03: Audited Remote Management Summary

**Expiry-aware hosted remote-action audits with deployment summary rollups and a fail-closed drawer workflow for hosted-link credential rotation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-23T00:20:00Z
- **Completed:** 2026-03-23T00:26:04Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added centralized TTL expiry processing so stale queued and in-progress actions become visible failed audit records.
- Projected remote action summary counts and last-action timestamps into deployment records for hosted visibility surfaces.
- Added a hosted deployment drawer card for the one safe remote action, with required note capture, confirmation, recent history, and fail-closed gating.

## Task Commits

Each task was committed atomically:

1. **Task 1: Enforce expiry and project remote-action audit summary** - `2f3de42` (feat)
2. **Task 2: Add hosted deployment-detail action card, note capture, and recent-history UI** - `5d94284` (feat)

## Files Created/Modified

- `tests/test_remote_management_audit.py` - Backend regression coverage for expiry transitions, summary rollups, and duplicate queue behavior after expiry.
- `src/nebula/services/enrollment_service.py` - Shared expiry pass plus deployment-level remote action summary projection.
- `console/src/lib/admin-api.ts` - Remote action client types and hosted admin methods.
- `console/src/components/deployments/remote-action-card.tsx` - Hosted drawer action card, note validation, confirmation, and history rendering.
- `console/src/components/deployments/remote-action-card.test.tsx` - Component coverage for note validation, fail-closed gating, queue wiring, and history rendering.
- `console/src/components/deployments/deployment-detail-drawer.tsx` - Drawer integration for the hosted remote action card.

## Decisions Made

- Centralized expiry in `EnrollmentService` so live-action idempotency, polling, and deployment projections all observe the same failed-after-TTL state.
- Reused backend-projected `remote_action_summary` instead of computing drawer rollups in the console.
- Kept the hosted action surface intentionally narrow: one confirmed rotate-credential action with copy that reinforces the trust boundary.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The shell environment did not expose `pytest` on `PATH`, so verification used the repo-local `.venv/bin/pytest` target defined by the project Makefile.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 9 remote-management credibility work is complete and ready for Phase 10 outage-safe and pilot-proof validation.
- No execution blockers remain for this phase.

## Self-Check

PASSED

- Verified summary and key implementation files exist on disk.
- Verified task commits `2f3de42` and `5d94284` exist in git history.

---
*Phase: 09-audited-remote-management*
*Completed: 2026-03-23*
