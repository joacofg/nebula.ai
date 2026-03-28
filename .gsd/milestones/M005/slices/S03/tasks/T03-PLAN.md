---
estimated_steps: 9
estimated_files: 8
skills_used: []
---

# T03: Expose hard-budget explanations in operator policy and ledger surfaces

Finish the operator loop by updating the policy UI, simulation copy, and ledger request detail to explain hard cumulative budget behavior in plain language, showing the new controls and recorded outcomes without raw JSON spelunking or scope drift beyond the existing decisioning control plane.

Steps:
1. Update `console/src/components/policy/policy-form.tsx` and related tests/E2E fixtures so the policy page distinguishes runtime-enforced hard guardrails from advisory soft-budget signals.
2. Extend `console/src/components/ledger/ledger-request-detail.tsx` (and tests) to render any new budget evidence or clearer policy outcome language using the stable labeled-field pattern established in S01.
3. Refresh route-decision / budget docs so operators and downstream slices have one stable explanation vocabulary for the new hard-budget outcomes.

Must-haves:
- [ ] The policy page explains the new hard guardrails as runtime-enforced controls and preserves `soft_budget_usd` as advisory-only.
- [ ] Observability request detail makes hard-budget downgrade/deny evidence inspectable through labeled fields, not raw JSON.
- [ ] Docs stay within R044 scope discipline and describe explainable operator-visible budget outcomes rather than a new analytics/billing subsystem.

## Inputs

- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/e2e/policy.spec.ts``
- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``docs/route-decision-vocabulary.md``

## Expected Output

- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/e2e/policy.spec.ts``
- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``docs/route-decision-vocabulary.md``
- ``docs/policy-guardrails.md``

## Verification

npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx && test -f docs/policy-guardrails.md

## Observability Impact

- Signals added/changed: operator-visible labels/copy for hard-budget policy outcomes and budget-related route evidence.
- How a future agent inspects this: open the Policy page and Observability request drawer or run the focused Vitest suite for those surfaces.
- Failure state exposed: missing/broken explanation paths show up as absent labels, stale copy, or failed drawer/policy component assertions.
