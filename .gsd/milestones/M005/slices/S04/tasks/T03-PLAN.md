---
estimated_steps: 27
estimated_files: 7
skills_used: []
---

# T03: Render observability recommendations and cache controls in existing operator surfaces

Why: S04 is only true when operators can actually see grounded next-best-action guidance and tune cache behavior intentionally through existing product surfaces, not just via backend contracts.

Steps:
1. Update `console/src/app/(console)/observability/page.tsx` to fetch the new tenant recommendation/cache summary alongside ledger/runtime health and render bounded recommendation cards plus cache-effectiveness context with copy grounded in ledger-backed evidence.
2. Extend `console/src/components/policy/policy-form.tsx` (and page wiring if needed) so cache tuning remains in the existing policy editor, with any new cache knobs grouped as runtime-enforced controls and evidence-oriented copy that avoids implying autosave or autonomous optimization.
3. Add/align focused Vitest coverage in `console/src/app/(console)/observability/page.test.tsx`, `console/src/app/(console)/observability/observability-page.test.tsx`, `console/src/components/policy/policy-form.test.tsx`, and `console/src/components/policy/policy-page.test.tsx` for recommendation framing, cache insight visibility, and cache-control save/preview behavior.

Must-haves:
- Observability copy must explicitly say recommendations are based on recent ledger-backed traffic and supporting runtime context, not black-box optimization.
- Policy-page work must keep cache tuning in the existing save/preview flow and avoid creating a separate cache-management area.
- Normalize the existing observability wording drift in tests while preserving the established persisted-evidence framing.

Verification:
- `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`
- UI tests prove recommendation cards, cache insight context, and cache-control save/preview semantics render on the intended surfaces.

Inputs:
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `console/src/lib/admin-api.ts`

Expected output:
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`

## Inputs

- ``console/src/app/(console)/observability/page.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``
- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/src/lib/admin-api.ts``

## Expected Output

- ``console/src/app/(console)/observability/page.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``
- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``

## Verification

npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx

## Observability Impact

Adds UI-level inspection of recommendation/cache evidence and keeps cache tuning diagnostics inside existing policy/observability flows where operators already investigate routing outcomes.
