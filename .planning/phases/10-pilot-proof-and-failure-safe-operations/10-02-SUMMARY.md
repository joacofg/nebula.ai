---
phase: 10-pilot-proof-and-failure-safe-operations
plan: 02
subsystem: ui
tags: [nextjs, react, vitest, docs, trust-boundary, hosted-control-plane]
requires:
  - phase: 10-01
    provides: "Outage-safe hosted-control-plane proof and stale/offline visibility semantics"
provides:
  - "Schema-backed pilot trust-boundary copy for onboarding, outage behavior, and remote-management limits"
  - "Public trust-boundary page sections that repeat the hosted visibility-only narrative"
  - "Pilot docs and demo materials aligned to outbound-only enrollment and one audited remote action"
affects: [pilot-docs, self-hosting, demo-flow, trust-boundary-page]
tech-stack:
  added: []
  patterns: [schema-backed UI copy, canonical pilot narrative reuse]
key-files:
  created: []
  modified:
    - console/src/lib/hosted-contract.ts
    - console/src/lib/hosted-contract.test.ts
    - console/src/app/trust-boundary/page.tsx
    - console/src/app/trust-boundary/page.test.tsx
    - docs/self-hosting.md
    - docs/demo-script.md
    - docs/pilot-checklist.md
key-decisions:
  - "Kept hosted onboarding, outage, and remote-limit language in console/src/lib/hosted-contract.ts as the single schema-backed UI content source."
  - "Updated pilot docs to repeat the exact metadata-and-intent and visibility-only wording instead of introducing a second trust-boundary narrative."
patterns-established:
  - "Public hosted-trust messaging should flow from the schema-backed content module into page-level rendering and regression tests."
  - "Pilot-facing docs should reuse the same bounded hosted claims: outbound-only enrollment, fleet visibility, and one audited rotate_deployment_credential action."
requirements-completed: [TRST-03]
duration: 3min
completed: 2026-03-23
---

# Phase 10 Plan 02: Pilot Trust Narrative Summary

**Schema-backed hosted onboarding, outage, and rotate_deployment_credential limits now align across the public trust page and pilot docs**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-23T16:43:17Z
- **Completed:** 2026-03-23T16:46:46Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Extended the hosted contract copy with exact pilot wording for onboarding flow, outage behavior, and remote-management safety limits.
- Rendered the new narrative on the public trust-boundary page and locked it with Vitest regression coverage.
- Updated self-hosting, demo, and pilot-checklist docs so they repeat the same visibility-only and metadata-and-intent claims.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend schema-backed trust-boundary copy with onboarding, outage, and safety-limit narrative** - `3d360d9` (feat)
2. **Task 2: Update canonical pilot docs and demo materials to match the shipped hosted-control-plane story** - `af59b1b` (docs)

## Files Created/Modified
- `console/src/lib/hosted-contract.ts` - Added the canonical pilot copy strings for onboarding, outage handling, and remote-management limits.
- `console/src/lib/hosted-contract.test.ts` - Asserted every required copy string and kept schema/freshness parity coverage intact.
- `console/src/app/trust-boundary/page.tsx` - Rendered the exact outage sentence and new pilot narrative sections from the shared content module.
- `console/src/app/trust-boundary/page.test.tsx` - Verified the public page renders the new headings and exact hosted copy.
- `docs/self-hosting.md` - Added the hosted pilot workflow section tied to the schema contract and bounded hosted capabilities.
- `docs/demo-script.md` - Replaced the old hosted caveat with a concrete hosted pilot proof talk track.
- `docs/pilot-checklist.md` - Added presenter checklist items for outbound-only onboarding, visibility-only outage behavior, and the audited remote-action limit.

## Decisions Made
- Kept the new hosted narrative in the existing schema-backed content module instead of creating a second copy source for the public page.
- Expressed the pilot docs with the same bounded claims as the UI so pilot reviews cannot drift into unsupported hosted authority or remote powers.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- A transient `git` index lock blocked the first task commit attempt; retrying after the stale lock cleared succeeded without code changes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- TRST-03 is now backed by exact tested copy and matching pilot docs.
- The next phase can rely on the public page and docs as the canonical hosted trust-boundary narrative.

## Self-Check: PASSED

- FOUND: `.planning/phases/10-pilot-proof-and-failure-safe-operations/10-02-SUMMARY.md`
- FOUND: `3d360d9`
- FOUND: `af59b1b`

---
*Phase: 10-pilot-proof-and-failure-safe-operations*
*Completed: 2026-03-23*
