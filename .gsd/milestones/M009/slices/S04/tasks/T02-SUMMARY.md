---
id: T02
parent: S04
milestone: M009
key_files:
  - console/src/app/(console)/observability/observability-page.test.tsx
key_decisions:
  - Repaired the broader observability page fixture to use the current UsageLedgerRecord contract, including governed metadata suppression and grounded route-signals evidence, instead of weakening request-detail assertions.
  - Proved request-first hierarchy at the page level by asserting selected-request section order and scoped selected-row evidence, while treating follow-up calibration/cache/dependency cards as subordinate context for the same request.
duration: 
verification_result: passed
completed_at: 2026-04-27T21:26:45.453Z
blocker_discovered: false
---

# T02: Repaired observability page fixtures and proved selected-request-first hierarchy in the page-level Vitest suites.

**Repaired observability page fixtures and proved selected-request-first hierarchy in the page-level Vitest suites.**

## What Happened

Updated the broader observability page regression suite so it exercises the current selected-request contract established in T01. The stale page-level ledger fixture now includes governed retention/minimization fields plus grounded route-signals data, which prevents request-detail from falling back to incomplete legacy shapes. Tightened assertions to prove the Observability page still leads with the selected ledger row and request detail, then presents follow-up calibration, cache, and dependency cards as subordinate context for the same investigation. No production page copy changes were required because the existing page wording already matched the grounded/thin/stale/degraded vocabulary and request-first architecture.

## Verification

Ran the two required focused Vitest suites for the observability page. `src/app/(console)/observability/page.test.tsx` passed 1/1, confirming the top-level page framing still presents the selected request section before follow-up context and keeps supporting cards subordinate. `src/app/(console)/observability/observability-page.test.tsx` passed 4/4 after fixture repair, confirming the broader page suite now uses up-to-date UsageLedgerRecord fields, renders governed metadata suppression safely, and verifies grounded/thin/stale/rollout-disabled supporting states without overriding selected-request evidence.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'` | 0 | ✅ pass | 546ms |
| 2 | `npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'` | 0 | ✅ pass | 665ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/app/(console)/observability/observability-page.test.tsx`
