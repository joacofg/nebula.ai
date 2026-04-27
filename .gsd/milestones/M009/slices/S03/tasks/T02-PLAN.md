---
estimated_steps: 6
estimated_files: 4
skills_used: []
---

# T02: Prove admin replay parity and repair console type drift

Close the public replay boundary and keep the request-first console contract aligned with the backend semantics.

Steps:
1. Extend admin API coverage so `POST /v1/admin/tenants/{tenant_id}/policy/simulate` proves replay uses the same outcome-grounded semantics as runtime for the same tenant traffic class, including changed-request route score/mode parity and honest degraded behavior when persisted route signals are incomplete.
2. Keep the simulation non-mutating and bounded by asserting saved tenant policy is unchanged, no provider execution side effects are introduced, and the returned tenant-window `calibration_summary` matches the replay window semantics.
3. Update `console/src/lib/admin-api.ts` so `CalibrationEvidenceSummary.state` includes `"degraded"`, then adjust policy-form tests only as needed to keep the request-first preview resilient when degraded replay evidence becomes visible more often.
4. Verify the backend API contract and the console type/test seam separately so future regressions localize quickly to either replay semantics or UI typing/rendering drift.

## Inputs

- ``tests/test_governance_api.py``
- ``src/nebula/api/routes/admin.py``
- ``src/nebula/models/governance.py``
- ``console/src/lib/admin-api.ts``
- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``

## Expected Output

- ``tests/test_governance_api.py``
- ``console/src/lib/admin-api.ts``
- ``console/src/components/policy/policy-form.test.tsx``

## Verification

./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or hard_budget)" && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx

## Observability Impact

Preserves the operator-visible replay diagnostics surface by ensuring the admin payload and preview types can carry degraded evidence-state vocabulary without crashing or silently dropping parity clues.
