---
estimated_steps: 7
estimated_files: 6
skills_used: []
---

# T02: Align admin and request-detail surfaces with real evidence aging semantics

Carry the new retention lifecycle truth through the existing operator-facing read seams without inventing a new governance dashboard. Executors should load the `react-best-practices` and `test` skills before coding.

Steps:
1. If needed, expose a minimal admin/read-path seam that allows tests to prove cleanup effects through existing usage-ledger APIs rather than direct database inspection, keeping the surface local-authoritative and bounded.
2. Update request-detail and any mirrored admin types only as far as needed to explain that a persisted row is authoritative while it exists and may later disappear when governed retention cleanup deletes expired evidence. Do not imply soft-delete, archival recovery, or hosted raw export.
3. Add focused backend/UI verification covering the operator-facing contract: surviving rows still render persisted governance markers, and the request-detail copy remains consistent with actual deletion behavior introduced in T01.
4. Re-run the hosted-boundary regression suite to prove the slice did not widen the metadata-only export contract.

If no new backend route is necessary after T01, keep this task limited to read-path tests and UI/copy alignment rather than inventing extra API surface.

## Inputs

- ``src/nebula/api/routes/admin.py``
- ``tests/test_governance_api.py``
- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/lib/admin-api.ts``
- ``src/nebula/models/hosted_contract.py``
- ``tests/test_hosted_contract.py``

## Expected Output

- ``tests/test_governance_api.py``
- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``

## Verification

./.venv/bin/pytest tests/test_governance_api.py -k "usage_ledger or retention" && ./.venv/bin/pytest tests/test_hosted_contract.py && npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx

## Observability Impact

Preserves a trustworthy operator inspection path: `/v1/admin/usage/ledger` and request detail remain the places to determine whether governed evidence still exists, which write-time governance markers applied, and when disappearance is expected because retention cleanup has already removed the row.
