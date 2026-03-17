---
phase: 04-governance-hardening
plan: "02"
subsystem: api
tags: [fastapi, governance, routing, testing, observability]
requires:
  - phase: 04-01
    provides: backend-authoritative governance contract and runtime hardening coverage
provides:
  - denied-path X-Nebula metadata for policy rejections and fallback-blocked provider failures
  - exact GOV-02 error-string coverage across chat and admin-playground entrypoints
  - request-id to ledger correlation for denied and provider-error governance paths
affects: [phase-04-03, governance, routing, admin-playground]
tech-stack:
  added: []
  patterns: [HTTPException headers carry route metadata, request-id ledger correlation for denied paths]
key-files:
  created: [.planning/phases/04-governance-hardening/04-02-SUMMARY.md]
  modified:
    - src/nebula/services/policy_service.py
    - src/nebula/services/chat_service.py
    - tests/test_response_headers.py
    - tests/test_service_flows.py
    - tests/test_governance_api.py
    - tests/test_admin_playground_api.py
key-decisions:
  - "Denied and fallback-blocked backend responses use HTTPException headers with the existing X-Nebula contract instead of a separate error envelope."
  - "ROUT-01 verification is pinned through X-Request-ID lookups against usage-ledger rows for denied and provider-error paths."
patterns-established:
  - "PolicyService raises route-aware 403s through _policy_denied so policy denials preserve attempted target and reason."
  - "ChatService records denied-path ledger metadata from exception headers rather than reconstructing partial context."
requirements-completed: [GOV-02, ROUT-01]
duration: 2m
completed: 2026-03-17
---

# Phase 4 Plan 02: Harden backend denied-path metadata, errors, and governance tests Summary

**Route-aware denial headers, blocked-fallback provider metadata, and exact governance error contracts across chat and admin-playground flows**

## Performance

- **Duration:** 2m
- **Started:** 2026-03-17T02:58:41Z
- **Completed:** 2026-03-17T03:00:57Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added route-aware denial metadata for policy rejections and fallback-blocked local provider failures without changing the public header contract.
- Preserved `route_reason` and policy outcome in usage-ledger rows for `policy_denied` and `provider_error` records.
- Locked down exact GOV-02 error strings and request-id ledger correlation across chat and admin-playground endpoints.

## Task Commits

Each task was committed atomically:

1. **Task 1: Attach route-aware denial metadata to policy rejections and fallback-blocked provider errors** - `8e3a6ca` (feat)
2. **Task 2: Lock down the GOV-02 and ROUT-01 error matrix across chat and admin-playground entrypoints** - `543be6e` (test)

## Files Created/Modified
- `src/nebula/services/policy_service.py` - Adds `_policy_denied(...)` so 403s carry attempted route metadata in `X-Nebula-*` headers.
- `src/nebula/services/chat_service.py` - Persists denied-path metadata from exception headers and marks blocked fallback failures with stable 502 details.
- `tests/test_response_headers.py` - Covers denied and fallback-blocked response-header metadata.
- `tests/test_service_flows.py` - Verifies blocked fallback provider errors keep ledger `route_reason` and `policy_outcome`.
- `tests/test_governance_api.py` - Pins exact auth/governance error strings and request-id ledger correlation.
- `tests/test_admin_playground_api.py` - Adds inactive-tenant playground coverage with no-successful-ledger assertion.

## Decisions Made
- Reused `HTTPException.headers` to carry denial metadata so normal chat and admin-playground routes inherit the same `X-Nebula-*` contract automatically.
- Used `X-Request-ID` as the authoritative join key for denied-path verification instead of adding a separate correlation mechanism.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Task 1 initially tested fallback-blocked behavior under `premium_only`, which bypassed the local provider path; the test setup was corrected to route through `local` before asserting blocked fallback behavior.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Backend denial-path semantics and ledger observability are now stable enough for console contract alignment in `04-03`.
- No blockers found for the remaining Phase 4 work.

## Self-Check: PASSED

---
*Phase: 04-governance-hardening*
*Completed: 2026-03-17*
