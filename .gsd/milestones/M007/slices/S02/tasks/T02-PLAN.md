---
estimated_steps: 5
estimated_files: 8
skills_used: []
---

# T02: Tighten policy preview and Observability supporting seams

Consume the aligned contracts in the console by making policy preview and Observability more explicit about the operator’s next comparison or follow-up action while preserving the S01 authority hierarchy. Extend existing components locally; do not add a new surface, summary dashboard, or alternate request authority path.

Steps:
1. Refine `PolicyForm` / policy page rendering so preview reads as baseline-vs-simulated decision evidence with explicit bounded samples, save-explicit semantics, and cache-control/runtime wording grounded in the aligned policy-options contract.
2. Refine Observability supporting-context seams so recommendation, calibration, cache, and dependency cards point more clearly back to the selected request investigation while keeping `LedgerRequestDetail` authoritative and avoiding tenant-summary takeover.
3. Tighten focused Vitest coverage with DOM-order and scoped assertions (`within(...)`) for duplicate labels, comparison-first preview semantics, and negative checks against dashboard/routing-studio/analytics drift.

## Inputs

- ``console/src/app/(console)/policy/page.tsx``
- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/src/app/(console)/observability/page.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``
- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/lib/admin-api.ts``

## Expected Output

- ``console/src/app/(console)/policy/page.tsx``
- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/src/app/(console)/observability/page.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``
- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``

## Verification

npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx

## Observability Impact

Keeps failure diagnosis local to the operator surfaces: focused Vitest assertions identify whether drift came from preview framing, selected-request hierarchy, or scoped supporting cards.
