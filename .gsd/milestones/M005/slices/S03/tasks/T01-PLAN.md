---
estimated_steps: 9
estimated_files: 10
skills_used: []
---

# T01: Add hard cumulative budget policy fields and persistence plumbing

Extend the tenant policy contract with explicit hard cumulative spend guardrail fields instead of mutating `soft_budget_usd`, then carry those fields through SQLAlchemy/Alembic, governance-store hydration, admin options metadata, and console admin typings so every downstream runtime and UI surface reads the same policy shape.

Steps:
1. Add the new hard-budget fields to `TenantPolicy`, `TenantPolicyModel`, and a new Alembic migration, preserving `soft_budget_usd` as advisory-only.
2. Update `GovernanceStore` read/write hydration plus `/v1/admin/policy/options` grouping so the backend classifies hard-budget controls as runtime-enforced and keeps soft-budget copy distinct.
3. Mirror the new fields in `console/src/lib/admin-api.ts` and adjust policy-form tests/fixtures so the frontend contract stays type-safe before behavior work lands.

Must-haves:
- [ ] New hard-budget fields are explicit and cumulative-budget-oriented, not a semantic rewrite of `soft_budget_usd`.
- [ ] DB model, migration, store write path, and store read hydration stay in lockstep so admin reads cannot silently drop the new fields.
- [ ] Policy options metadata exposes the new controls to the console as runtime-enforced fields while `soft_budget_usd` remains advisory/soft-signal only.

## Inputs

- ``src/nebula/models/governance.py``
- ``src/nebula/db/models.py``
- ``src/nebula/services/governance_store.py``
- ``src/nebula/api/routes/admin.py``
- ``console/src/lib/admin-api.ts``
- ``tests/test_governance_api.py``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/e2e/policy.spec.ts``

## Expected Output

- ``src/nebula/models/governance.py``
- ``src/nebula/db/models.py``
- ``src/nebula/services/governance_store.py``
- ``src/nebula/api/routes/admin.py``
- ``migrations/versions/20260328_0007_hard_budget_guardrails.py``
- ``console/src/lib/admin-api.ts``
- ``tests/test_governance_api.py``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/e2e/policy.spec.ts``

## Verification

./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx

## Observability Impact

- Signals added/changed: policy options metadata should name the new runtime-enforced hard-budget fields.
- How a future agent inspects this: compare `GET /v1/admin/policy/options` payload with console policy-form rendering/tests.
- Failure state exposed: missing or misclassified policy fields become visible as absent controls or failing admin/console contract tests.
