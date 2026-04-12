---
estimated_steps: 2
estimated_files: 10
skills_used: []
---

# T02: Tighten executable proof seams for integrated governance ordering

Use the new integrated proof doc to drive focused regression coverage across the shipped seams instead of broad feature churn. Run the targeted backend and console suites that already encode the M008 governance story, then only add or tighten assertions where integrated-proof drift is currently unguarded. Priority checks: request detail remains authoritative while a row exists; deletion semantics continue to reject soft-delete/recovery implications; observability/runtime-health stays supporting context rather than replacing ledger proof; and hosted trust-boundary surfaces keep the metadata-only evidence wording aligned with the shared contract. If the existing tests already cover a seam, keep it stable; if a missing order/copy expectation is needed to make the integrated proof executable, add the smallest focused assertion in the relevant test file.

Do not add new endpoints, dashboards, or exported data. This task closes R062/R063/R064 by ensuring the assembled story is mechanically verifiable from the real backend, health, and console seams the doc points to.

## Inputs

- ``docs/m008-integrated-proof.md``
- ``tests/test_governance_api.py``
- ``tests/test_retention_lifecycle_service.py``
- ``tests/test_health.py``
- ``tests/test_hosted_contract.py``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/components/health/runtime-health-cards.test.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/components/hosted/trust-boundary-card.test.tsx``
- ``console/src/app/trust-boundary/page.test.tsx``

## Expected Output

- ``tests/test_governance_api.py``
- ``tests/test_retention_lifecycle_service.py``
- ``tests/test_health.py``
- ``tests/test_hosted_contract.py``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/components/health/runtime-health-cards.test.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/components/hosted/trust-boundary-card.test.tsx``
- ``console/src/app/trust-boundary/page.test.tsx``

## Verification

./.venv/bin/pytest tests/test_governance_api.py tests/test_retention_lifecycle_service.py tests/test_health.py tests/test_hosted_contract.py -k "usage_ledger or retention or lifecycle or health or heartbeat" && npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx 'src/app/(console)/observability/page.test.tsx' src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx

## Observability Impact

This task preserves the real failure-diagnosis surfaces for the integrated proof: `/v1/admin/usage/ledger` visibility before/after cleanup, retention lifecycle health payloads, and console request-detail/hosted wording tests. Failures should surface as targeted test regressions that localize whether the drift is in persistence, deletion runtime state, or trust-boundary copy.
