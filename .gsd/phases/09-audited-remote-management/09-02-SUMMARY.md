---
phase: 09-audited-remote-management
plan: 02
subsystem: api
tags: [fastapi, remote-management, deployment-auth, polling, testing]
requires:
  - phase: 09-audited-remote-management
    provides: remote action queue records and hosted admin APIs from plan 09-01
provides:
  - deployment-authenticated poll and completion endpoints for hosted remote actions
  - gateway-side polling service that enforces local allowlist policy before applying actions
  - hosted and local credential rotation handshake for rotate_deployment_credential
  - integration coverage for disabled, failed-closed, and successful rotation paths
affects: [hosted-control-plane, enrollment, heartbeat, deployment-linking]
tech-stack:
  added: []
  patterns: [outbound deployment polling, shared capability derivation, hosted/local credential rotation handshake]
key-files:
  created: [src/nebula/api/routes/remote_management.py, src/nebula/services/remote_management_service.py, tests/test_remote_management_service.py]
  modified: [src/nebula/core/config.py, src/nebula/core/container.py, src/nebula/main.py, src/nebula/models/deployment.py, src/nebula/services/enrollment_service.py, src/nebula/services/gateway_enrollment_service.py, src/nebula/services/heartbeat_service.py]
key-decisions:
  - "Capability advertisement for remote rotation is derived once and reused for enrollment exchange plus heartbeat updates."
  - "Remote management starts unconditionally in app lifespan and fails closed inside the poller when enrollment, hosted URL, or local policy is missing."
patterns-established:
  - "Deployment-authenticated hosted control paths reuse X-Nebula-Deployment-Credential and rotate the credential only after hosted completion acknowledges success."
  - "Local remote-action authorization is allowlist-driven and reports stable failure reasons back to the hosted queue."
requirements-completed: [RMGT-02, RMGT-03]
duration: 8min
completed: 2026-03-23
---

# Phase 09 Plan 02: Audited Remote Management Summary

**Deployment-authenticated remote action polling with fail-closed local authorization and hosted/local credential rotation**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-23T00:08:29Z
- **Completed:** 2026-03-23T00:16:24Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Added hosted poll and completion endpoints for deployment-authenticated remote actions.
- Implemented gateway-side remote management polling, local allowlist enforcement, and credential replacement.
- Wired remote management into shared capability derivation and the FastAPI lifespan, with integration tests covering disabled, unauthorized, failed, and successful flows.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add deployment-authenticated poll and completion handshake** - `000b757` (test), `ee329ab` (feat)
2. **Task 2: Wire local authorization settings, polling lifecycle, and integration tests** - `5a661f6` (feat)

## Files Created/Modified
- `src/nebula/api/routes/remote_management.py` - Hosted poll and completion routes authenticated by deployment credential.
- `src/nebula/services/remote_management_service.py` - Gateway poll/apply loop, authorization, and completion handshake.
- `tests/test_remote_management_service.py` - ASGI integration coverage for disabled, unauthorized, failed, and rotated-credential flows.
- `src/nebula/services/enrollment_service.py` - Hosted claim/complete logic plus credential validation for deployment-authenticated actions.
- `src/nebula/services/gateway_enrollment_service.py` - Local credential replacement and shared capability advertisement during enrollment.
- `src/nebula/services/heartbeat_service.py` - Shared capability derivation extended with `remote_credential_rotation`.
- `src/nebula/core/config.py` - Remote management enablement, allowlist, and polling interval settings.
- `src/nebula/core/container.py` and `src/nebula/main.py` - Remote management service registration and lifespan startup/shutdown wiring.

## Decisions Made
- Shared capability derivation now feeds both enrollment exchange and heartbeat payloads so hosted state cannot drift between initial link and steady-state updates.
- The remote-management background service always starts with the app, but `_poll_once()` and `poll_and_apply_once()` no-op unless hosted URL, local credential, and enablement are present.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Normalized SQLite timestamps when claiming queued remote actions**
- **Found during:** Task 1 (Add deployment-authenticated poll and completion handshake)
- **Issue:** `expires_at` values loaded from SQLite were naive datetimes, causing claim-time comparisons to fail against UTC-aware `now`.
- **Fix:** Normalized queued-action expiry timestamps to UTC before evaluating expiration and claim eligibility.
- **Files modified:** `src/nebula/services/enrollment_service.py`
- **Verification:** `.venv/bin/pytest tests/test_remote_management_service.py -k 'poll or apply or failed' -x`
- **Committed in:** `ee329ab`

**2. [Rule 3 - Blocking] Replaced unavailable `asgi_lifespan` test dependency with native FastAPI lifespan handling**
- **Found during:** Task 1 (Add deployment-authenticated poll and completion handshake)
- **Issue:** The repo environment did not include `asgi_lifespan`, so the new async integration tests could not run.
- **Fix:** Switched the test harness to `app.router.lifespan_context(app)` and reused `httpx.ASGITransport` for in-process lifecycle-managed requests.
- **Files modified:** `tests/test_remote_management_service.py`
- **Verification:** `.venv/bin/pytest tests/test_remote_management_service.py -x`
- **Committed in:** `5a661f6`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes were required for the planned implementation to verify correctly. No architectural scope change.

## Issues Encountered
- `pytest` was not on shell `PATH`; execution used the repo virtualenv entrypoint `.venv/bin/pytest` instead.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Hosted and gateway sides now share a complete audited remote-action execution path for credential rotation.
- The next phase can build UI/operator workflows on top of stable action outcomes and capability-aware deployment state.

## Self-Check
PASSED

---
*Phase: 09-audited-remote-management*
*Completed: 2026-03-23*
