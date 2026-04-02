---
estimated_steps: 5
estimated_files: 10
skills_used: []
---

# T03: Add the bounded tenant calibrated-routing rollout control

Ship the small tenant-scoped control from D032/D033 as a rollout and safety valve, but keep it narrow: an explicit calibrated-routing enable/disable control, not a tuning surface. Persist it through governance models and admin APIs, keep simulation/runtime semantics aligned, and prove the new field works without widening console scope in this slice.

Steps:
1. Add a single bounded calibrated-routing control field to `TenantPolicy` plus its persistence path in `src/nebula/db/models.py`, `src/nebula/services/governance_store.py`, and a new Alembic revision under `migrations/versions/`.
2. Surface the field through admin policy options and policy read/write APIs in `src/nebula/api/routes/admin.py`, then update focused governance tests to prove runtime and simulation both respect the same on/off semantics.
3. Update the policy form/admin client types and focused console tests only as needed to keep the existing tenant policy surface truthful and writable, without adding new calibration analytics UI.

## Inputs

- ``src/nebula/models/governance.py``
- ``src/nebula/db/models.py``
- ``src/nebula/services/governance_store.py``
- ``src/nebula/api/routes/admin.py``
- ``tests/test_governance_api.py``
- ``console/src/lib/admin-api.ts``
- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``

## Expected Output

- ``src/nebula/models/governance.py``
- ``src/nebula/db/models.py``
- ``src/nebula/services/governance_store.py``
- ``src/nebula/api/routes/admin.py``
- ``migrations/versions/``
- ``tests/test_governance_api.py``
- ``console/src/lib/admin-api.ts``
- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``

## Verification

./.venv/bin/alembic upgrade head && ./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation or route_reason" -x && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx

## Observability Impact

Makes calibrated-routing rollout state inspectable through the existing policy surfaces and guarantees runtime/simulation both expose whether calibrated scoring was active or deliberately gated off for the tenant.
