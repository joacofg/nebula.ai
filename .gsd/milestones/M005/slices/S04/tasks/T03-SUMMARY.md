---
id: T03
parent: S04
milestone: M005
provides: []
requires: []
affects: []
key_files: ["console/src/app/(console)/observability/page.tsx", "console/src/components/policy/policy-form.tsx", "console/src/lib/admin-api.ts", "console/src/lib/query-keys.ts", "console/src/app/(console)/observability/page.test.tsx", "console/src/app/(console)/observability/observability-page.test.tsx", "console/src/components/policy/policy-form.test.tsx", "console/src/components/policy/policy-page.test.tsx", ".gsd/milestones/M005/slices/S04/tasks/T03-SUMMARY.md"]
key_decisions: ["Kept recommendation rendering inside the existing Observability page and made cache tuning inspection-only there, with editing confined to the existing policy save/preview flow.", "Extended the shared console TenantPolicy contract with the two backend cache-tuning knobs so preview and save semantics stay typed end to end instead of relying on ad-hoc UI state."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` three times. The first run failed due to async observability test timing and a test-file syntax regression introduced during editing. The second run narrowed the remaining issue to a duplicate `168 hours` assertion in observability coverage. The final rerun passed all 14 tests across the four targeted files, proving recommendation cards, cache insight context, and cache-control save/preview semantics render on the intended surfaces."
completed_at: 2026-03-28T04:10:50.097Z
blocker_discovered: false
---

# T03: Rendered grounded observability recommendations and semantic-cache tuning controls inside the existing console surfaces.

> Rendered grounded observability recommendations and semantic-cache tuning controls inside the existing console surfaces.

## What Happened
---
id: T03
parent: S04
milestone: M005
key_files:
  - console/src/app/(console)/observability/page.tsx
  - console/src/components/policy/policy-form.tsx
  - console/src/lib/admin-api.ts
  - console/src/lib/query-keys.ts
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/milestones/M005/slices/S04/tasks/T03-SUMMARY.md
key_decisions:
  - Kept recommendation rendering inside the existing Observability page and made cache tuning inspection-only there, with editing confined to the existing policy save/preview flow.
  - Extended the shared console TenantPolicy contract with the two backend cache-tuning knobs so preview and save semantics stay typed end to end instead of relying on ad-hoc UI state.
duration: ""
verification_result: mixed
completed_at: 2026-03-28T04:10:50.098Z
blocker_discovered: false
---

# T03: Rendered grounded observability recommendations and semantic-cache tuning controls inside the existing console surfaces.

**Rendered grounded observability recommendations and semantic-cache tuning controls inside the existing console surfaces.**

## What Happened

Updated the console observability page to fetch tenant recommendations together with usage-ledger and runtime-health data, then render bounded recommendation cards and cache-effectiveness context with explicit wording that the guidance comes from recent ledger-backed traffic plus supporting runtime context rather than black-box optimization. Kept cache tuning inspection-only on the observability page and confined editing to the existing policy editor. Extended the shared console TenantPolicy contract with semantic cache similarity threshold and max entry age fields, added a dedicated tenant recommendations query key, and updated the policy form so semantic-cache controls remain inside runtime-enforced controls with explicit preview/save semantics and bound validation. Refreshed focused Vitest coverage for observability and policy surfaces to assert recommendation framing, cache insight visibility, typed preview/save payloads, and invalid cache tuning behavior.

## Verification

Ran `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` three times. The first run failed due to async observability test timing and a test-file syntax regression introduced during editing. The second run narrowed the remaining issue to a duplicate `168 hours` assertion in observability coverage. The final rerun passed all 14 tests across the four targeted files, proving recommendation cards, cache insight context, and cache-control save/preview semantics render on the intended surfaces.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 1 | ❌ fail | 24400ms |
| 2 | `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 1 | ❌ fail | 3600ms |
| 3 | `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 0 | ✅ pass | 2500ms |


## Deviations

Added `console/src/lib/query-keys.ts` and extended `console/src/lib/admin-api.ts` beyond the listed output files so the tenant recommendation query remained isolated and the console TenantPolicy contract matched the backend cache-tuning fields introduced earlier in the slice.

## Known Issues

None.

## Files Created/Modified

- `console/src/app/(console)/observability/page.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/lib/admin-api.ts`
- `console/src/lib/query-keys.ts`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `.gsd/milestones/M005/slices/S04/tasks/T03-SUMMARY.md`


## Deviations
Added `console/src/lib/query-keys.ts` and extended `console/src/lib/admin-api.ts` beyond the listed output files so the tenant recommendation query remained isolated and the console TenantPolicy contract matched the backend cache-tuning fields introduced earlier in the slice.

## Known Issues
None.
