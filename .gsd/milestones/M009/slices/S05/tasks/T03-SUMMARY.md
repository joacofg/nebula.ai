---
id: T03
parent: S05
milestone: M009
key_files:
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-04-27T21:45:40.455Z
blocker_discovered: false
---

# T03: Hardened degraded request-first console proof with focused hierarchy assertions in ledger detail and observability tests.

**Hardened degraded request-first console proof with focused hierarchy assertions in ledger detail and observability tests.**

## What Happened

I kept the task scoped to the existing console proof seams and did not change shipped UI copy or add new operator flows. After reviewing the current request-detail and Observability tests, I identified that most of the needed request-first degraded wording was already present in the runtime UI. I first tried to add a degraded-path Observability page test, but repeated verification showed the cross-page async setup was a brittle place to prove the hierarchy. I then moved the new degraded-proof assertion into the deterministic request-detail suite, where both degraded row-level routing and degraded calibration summary render together. The final change adds coverage that the request-detail section remains the primary proof surface while degraded tenant calibration text explicitly stays supporting context, and it preserves the broader Observability framing tests unchanged apart from removing the flaky experiment. No blocker or plan-invalidating mismatch was discovered.

## Verification

Ran the task verification suite for the three console seams. The ledger request-detail Vitest suite passed with the new degraded-authority assertion, the top-level observability page test passed, and the Observability page composition suite passed after leaving degraded hierarchy proof in the deterministic component test. This verifies the selected-request-first wording remains intact and that degraded evidence still keeps the selected request row authoritative while tenant calibration context remains supporting only.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'` | 0 | ✅ pass | 914ms |
| 2 | `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'` | 0 | ✅ pass | 572ms |
| 3 | `npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'` | 0 | ✅ pass | 702ms |

## Deviations

I initially attempted to prove degraded hierarchy through a new Observability page integration test, but verification showed that approach was brittle because of async page composition timing. I removed that flaky addition and instead placed the degraded-authority proof in the existing request-detail component suite, which still satisfies the task goal while keeping the verification seam stable.

## Known Issues

None.

## Files Created/Modified

- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
