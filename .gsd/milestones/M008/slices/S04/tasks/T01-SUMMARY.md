---
id: T01
parent: S04
milestone: M008
key_files:
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - console/src/lib/hosted-contract.ts
key_decisions:
  - Reused shared hosted-contract copy for the hosted export exclusion sentence so policy, hosted trust-boundary, and future request-detail surfaces stay aligned to one metadata-only contract.
duration: 
verification_result: passed
completed_at: 2026-04-12T17:09:11.666Z
blocker_discovered: false
---

# T01: Added policy-side effective evidence boundary guidance driven by retention/minimization controls and shared hosted export limits.

**Added policy-side effective evidence boundary guidance driven by retention/minimization controls and shared hosted export limits.**

## What Happened

Updated `console/src/components/policy/policy-form.tsx` to render a subordinate “Effective evidence boundary” panel inside the existing runtime-enforced controls section. The panel derives operator-facing guidance from the live `evidence_retention_window` and `metadata_minimization_level` form values, making it explicit what governed ledger metadata remains inspectable while retained, what strict minimization suppresses at write time, and that hosted export still excludes raw usage-ledger rows. To keep hosted wording aligned with the metadata-only contract instead of duplicating ad hoc copy, I extended `console/src/lib/hosted-contract.ts` with a shared `hostedExportExclusion` string and consumed it from the policy form. I then updated `console/src/components/policy/policy-form.test.tsx` and `console/src/components/policy/policy-page.test.tsx` to lock the new boundary vocabulary, verify the strict-minimization variant, and preserve the runtime-enforced versus advisory distinction already present on the page.

## Verification

Ran the focused console Vitest command from the task plan: `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`. The suite passed with 17/17 tests green, confirming the new policy-side evidence-boundary copy, the strict-minimization branch, the shared hosted export exclusion wording, and the existing runtime-enforced/advisory separation.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 0 | ✅ pass | 1490ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `console/src/lib/hosted-contract.ts`
