---
estimated_steps: 1
estimated_files: 4
skills_used: []
---

# T01: Add policy-side effective evidence boundary guidance

Add a bounded operator-facing explanation to the policy surface that synthesizes the runtime-enforced governance controls already present in `console/src/components/policy/policy-form.tsx`. Reuse the existing `evidence_retention_window` and `metadata_minimization_level` values plus the shared hosted contract copy from `console/src/lib/hosted-contract.ts` to explain, in explicit operator language, what evidence remains inspectable while a row exists, what strict minimization suppresses today, and that hosted export still excludes raw usage-ledger rows. Keep this explanatory surface subordinate to the existing runtime-enforced controls rather than turning the page into a second observability/dashboard seam. Update focused policy tests to lock the new boundary vocabulary and verify that the page still distinguishes runtime-enforced controls from advisory capture settings.

## Inputs

- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/src/lib/hosted-contract.ts``
- ``console/src/lib/admin-api.ts``

## Expected Output

- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/src/lib/hosted-contract.ts``

## Verification

npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx

## Observability Impact

Makes policy-page UI itself the inspection surface for configured evidence boundary truth: future failures are localized by boundary-card copy/tests rather than inferred from scattered helper text.
