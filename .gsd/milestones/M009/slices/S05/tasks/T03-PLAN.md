---
estimated_steps: 1
estimated_files: 3
skills_used: []
---

# T03: Harden request-first console proof for degraded inspection

Tighten the request-first console proof so the final walkthrough can point to exact operator seams for both grounded and degraded review paths. Reuse the current request-detail and Observability suites; add only the assertions needed to prove the degraded path still keeps the selected request row authoritative while tenant calibration summary remains supporting context. Do not add a new dashboard/workflow or browser-only proof path.

## Inputs

- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``
- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/app/(console)/observability/page.tsx``
- ``docs/m009-integrated-proof.md``

## Expected Output

- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``

## Verification

npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx' && npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx' && npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'

## Observability Impact

Preserves and hardens the selected-request-first UI wording/operators seams so degraded evidence remains inspectable without a summary-first analytics drift.
