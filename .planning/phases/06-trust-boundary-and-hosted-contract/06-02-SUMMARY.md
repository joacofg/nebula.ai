---
phase: 06-trust-boundary-and-hosted-contract
plan: "02"
subsystem: ui
tags: [react, next.js, trust-boundary, hosted-contract, vitest, playwright]

# Dependency graph
requires:
  - phase: 06-trust-boundary-and-hosted-contract/01
    provides: "Backend hosted-default-export.schema.json artifact and Pydantic contract model"
provides:
  - "Schema-backed hosted-contract.ts content module with getHostedContractContent helper"
  - "TrustBoundaryCard reusable disclosure component"
  - "Public /trust-boundary route accessible before auth"
  - "Pre-auth link on login page to trust-boundary"
  - "E2E and unit test coverage for trust-boundary surfaces"
affects: [07-deployment-identity, 08-fleet-inventory, 10-pilot-docs]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Schema-backed UI content sourced from canonical JSON artifact"]

key-files:
  created:
    - console/src/lib/hosted-contract.ts
    - console/src/lib/hosted-contract.test.ts
    - console/src/components/hosted/trust-boundary-card.tsx
    - console/src/components/hosted/trust-boundary-card.test.tsx
    - console/src/app/trust-boundary/page.tsx
    - console/src/app/trust-boundary/page.test.tsx
    - console/e2e/trust-boundary.spec.ts
  modified:
    - console/src/components/auth/login-page-client.tsx

key-decisions:
  - "Schema-backed content module reads hosted-default-export.schema.json directly instead of duplicating field lists"
  - "Trust boundary page is a static public Next.js route outside the (console) auth group"

patterns-established:
  - "Schema-parity pattern: UI content modules import the JSON schema artifact and fail fast on drift"
  - "Public disclosure routes: pages outside auth boundary for trust/compliance information"

requirements-completed: [TRST-01]

# Metrics
duration: 3min
completed: 2026-03-21
---

# Phase 06 Plan 02: Trust-Boundary UI Summary

**Schema-backed trust-boundary disclosure page with public route, reusable card component, and pre-auth login link**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T15:47:49Z
- **Completed:** 2026-03-21T15:50:25Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Schema-backed content module (`getHostedContractContent`) that reads the canonical JSON schema artifact with parity checks
- Reusable `TrustBoundaryCard` component rendering all 12 exported fields, 6 excluded data classes, freshness states, and exact copy strings
- Public `/trust-boundary` route accessible before authentication with pilot-oriented intro
- Pre-auth "Review hosted trust boundary" link added to login page
- 20 unit tests and 2 E2E specs covering all trust-boundary surfaces

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the shared trust-boundary content module and reusable disclosure card** - `4e2b3c2` (feat)
2. **Task 2: Publish the public trust-boundary route and pre-auth entry link** - `9debd1f` (feat)

## Files Created/Modified
- `console/src/lib/hosted-contract.ts` - Schema-backed content module with getHostedContractContent, excludedByDefault, freshnessStates, and copy strings
- `console/src/lib/hosted-contract.test.ts` - 6 tests for schema parity, field count, freshness enum, excluded data classes
- `console/src/components/hosted/trust-boundary-card.tsx` - Reusable disclosure card consuming the content module
- `console/src/components/hosted/trust-boundary-card.test.tsx` - 7 tests for rendered headings, labels, excluded items, freshness states
- `console/src/app/trust-boundary/page.tsx` - Public trust-boundary page with intro and card
- `console/src/app/trust-boundary/page.test.tsx` - 7 tests for page rendering
- `console/e2e/trust-boundary.spec.ts` - 2 E2E specs for public access and login link navigation
- `console/src/components/auth/login-page-client.tsx` - Added pre-auth trust-boundary link

## Decisions Made
- Schema-backed content module reads `hosted-default-export.schema.json` directly and fails fast if schema keys drift, ensuring UI stays in sync with the backend contract
- Trust boundary page is a static public route outside the auth boundary so operators can review the data contract before signing in

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The `TrustBoundaryCard` is reusable and ready for embedding in future hosted surfaces (fleet inventory, enrollment)
- The `getHostedContractContent` helper is available for any downstream component that needs hosted contract data
- E2E coverage ensures the public disclosure route survives refactors

---
*Phase: 06-trust-boundary-and-hosted-contract*
*Completed: 2026-03-21*
