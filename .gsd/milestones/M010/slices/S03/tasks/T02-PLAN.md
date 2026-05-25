---
estimated_steps: 3
estimated_files: 5
skills_used: []
---

# T02: Prove request-first observability surfaces expose outage and recovery truth

Why: S03 is only complete if operators can actually inspect dependency-specific outage and recovery state on existing Observability surfaces without displacing the selected request evidence hierarchy established in M009.

Do: Update `console/src/app/(console)/observability/page.tsx` typing only as needed so the runtime health query accepts the richer dependency payload without narrowing fields away. Extend unit/page tests in `console/src/app/(console)/observability/page.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` to cover governance fail-closed, semantic-cache degraded-serving, and recovering metadata examples while reasserting request-first wording and anti-dashboard boundaries. Refresh the browser proof in `console/e2e/observability.spec.ts` to stub typed runtime health payloads and verify an operator can see failed dependency identity, degraded serving semantics, and recovery evidence on the existing page.

Done when: Page and e2e verification prove the selected request remains primary, dependency-health cards show typed outage/recovery metadata on the current Observability page, and `/api/runtime/health` passthrough assumptions are preserved without requiring new backend work.

## Inputs

- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/e2e/observability.spec.ts`
- `console/src/app/api/runtime/health/route.ts`
- `console/src/components/health/runtime-health-cards.tsx`
- `console/src/components/health/runtime-health-cards.test.tsx`
- `tests/test_health.py`
- `tests/test_phase10_outage_safety.py`
- `.gsd/milestones/M010/slices/S01/S01-SUMMARY.md`
- `.gsd/milestones/M010/slices/S02/S02-SUMMARY.md`

## Expected Output

- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/e2e/observability.spec.ts`

## Verification

npm --prefix console run test -- --run src/app/(console)/observability/page.test.tsx src/app/(console)/observability/observability-page.test.tsx

## Observability Impact

Locks request-first operator inspection proof around governance, semantic-cache, and recovering dependency states on the existing Observability page and browser flow.
