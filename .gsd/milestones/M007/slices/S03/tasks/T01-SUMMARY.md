---
id: T01
parent: S03
milestone: M007
provides: []
requires: []
affects: []
key_files: ["console/src/app/(console)/observability/page.tsx", "console/src/app/(console)/observability/page.test.tsx", "console/src/app/(console)/observability/observability-page.test.tsx", ".gsd/KNOWLEDGE.md"]
key_decisions: ["Grouped calibration, cache, and dependency health under a policy-preview follow-up column so the page reads as one request-led investigation rather than parallel dashboard cards.", "Kept LedgerRequestDetail unchanged as the authoritative persisted-evidence seam and fixed hierarchy drift through page composition and scoped tests instead of widening shared contracts."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the focused console Vitest suite covering Observability page composition, integrated page hierarchy, ledger request detail behavior, and runtime health cards. Final run passed with 21/21 tests after tightening assertions around intentionally duplicated request IDs and scoped supporting-card text."
completed_at: 2026-04-03T02:32:55.992Z
blocker_discovered: false
---

# T01: Reworked Observability into a selected-request-first investigation flow with explicit policy-preview follow-up sections and hierarchy-locking tests.

> Reworked Observability into a selected-request-first investigation flow with explicit policy-preview follow-up sections and hierarchy-locking tests.

## What Happened
---
id: T01
parent: S03
milestone: M007
key_files:
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Grouped calibration, cache, and dependency health under a policy-preview follow-up column so the page reads as one request-led investigation rather than parallel dashboard cards.
  - Kept LedgerRequestDetail unchanged as the authoritative persisted-evidence seam and fixed hierarchy drift through page composition and scoped tests instead of widening shared contracts.
duration: ""
verification_result: passed
completed_at: 2026-04-03T02:32:55.993Z
blocker_discovered: false
---

# T01: Reworked Observability into a selected-request-first investigation flow with explicit policy-preview follow-up sections and hierarchy-locking tests.

**Reworked Observability into a selected-request-first investigation flow with explicit policy-preview follow-up sections and hierarchy-locking tests.**

## What Happened

Recomposed the Observability page so operators encounter one selected persisted ledger row as the clear lead investigation object, then read recommendations, calibration, cache posture, and dependency health as subordinate follow-up context for that same request. Kept LedgerRequestDetail authoritative and preserved existing data sources while moving dependency health into the policy-preview follow-up track so the layout reads as one investigation plus one next-step column. Updated both focused Observability page test files to lock top-level DOM order, scoped supporting-card hierarchy, policy-preview cues, and anti-drift guards, and recorded the repeated-request-ID test pattern in project knowledge.

## Verification

Ran the focused console Vitest suite covering Observability page composition, integrated page hierarchy, ledger request detail behavior, and runtime health cards. Final run passed with 21/21 tests after tightening assertions around intentionally duplicated request IDs and scoped supporting-card text.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx` | 0 | ✅ pass | 7500ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `.gsd/KNOWLEDGE.md`


## Deviations
None.

## Known Issues
None.
