# S03: Hard budget guardrails

**Goal:** Add hard tenant spend guardrails that enforce cumulative premium budget behavior through explicit downgrade-versus-deny decisions, preserve shared runtime/simulation semantics, and expose explainable budget outcomes to operators without widening Nebula beyond the existing decisioning control-plane scope.
**Demo:** After this: Tenant policy can enforce hard spend limits with explicit downgrade or denial behavior and explainable recorded outcomes.

## Tasks
- [x] **T01: Added explicit hard cumulative budget policy fields across backend persistence, admin metadata, and console policy contracts while keeping soft budget advisory-only.** — Extend the tenant policy contract with explicit hard cumulative spend guardrail fields instead of mutating `soft_budget_usd`, then carry those fields through SQLAlchemy/Alembic, governance-store hydration, admin options metadata, and console admin typings so every downstream runtime and UI surface reads the same policy shape.

Steps:
1. Add the new hard-budget fields to `TenantPolicy`, `TenantPolicyModel`, and a new Alembic migration, preserving `soft_budget_usd` as advisory-only.
2. Update `GovernanceStore` read/write hydration plus `/v1/admin/policy/options` grouping so the backend classifies hard-budget controls as runtime-enforced and keeps soft-budget copy distinct.
3. Mirror the new fields in `console/src/lib/admin-api.ts` and adjust policy-form tests/fixtures so the frontend contract stays type-safe before behavior work lands.

Must-haves:
- [ ] New hard-budget fields are explicit and cumulative-budget-oriented, not a semantic rewrite of `soft_budget_usd`.
- [ ] DB model, migration, store write path, and store read hydration stay in lockstep so admin reads cannot silently drop the new fields.
- [ ] Policy options metadata exposes the new controls to the console as runtime-enforced fields while `soft_budget_usd` remains advisory/soft-signal only.
  - Estimate: 1.5h
  - Files: src/nebula/models/governance.py, src/nebula/db/models.py, src/nebula/services/governance_store.py, src/nebula/api/routes/admin.py, migrations/versions/20260328_0007_hard_budget_guardrails.py, console/src/lib/admin-api.ts, tests/test_governance_api.py, console/src/components/policy/policy-form.test.tsx, console/src/components/policy/policy-page.test.tsx, console/e2e/policy.spec.ts
  - Verify: ./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx
- [x] **T02: Centralized hard-budget downgrade and denial behavior in PolicyService and aligned simulation replay semantics.** — Implement the real hard-budget behavior in `PolicyService.evaluate()` so runtime requests and simulation replays share one decision path for cumulative spend caps, downgrade-to-local when allowed, deny when premium is required, and persist explainable outcomes that preserve S01's override-route-signal discipline.

Steps:
1. Add focused runtime/service tests that cover cumulative spend exhaustion, local downgrade eligibility, explicit premium denial, and replay-window spend calculations using `before_timestamp`.
2. Update `PolicyService.evaluate()` (and only the minimum adjacent runtime plumbing it truly needs) to compute spend-cap state from `tenant_spend_total`, choose downgrade vs deny deterministically, and emit stable `policy_outcome` / budget evidence.
3. Confirm simulation replay inherits the exact same semantics through `PolicySimulationService` without introducing a second budget engine.

Must-haves:
- [ ] Runtime and simulation both rely on `PolicyService.evaluate()` for hard-budget decisions.
- [ ] When cumulative spend cap is exhausted, auto-routed traffic downgrades to local when compatible instead of failing ambiguously.
- [ ] Explicit premium or premium-only cases deny with exact operator-readable detail when downgrade is impossible or disallowed.
- [ ] Soft-budget advisory behavior remains non-blocking and distinct from the new hard guardrails.
  - Estimate: 2h
  - Files: src/nebula/services/policy_service.py, src/nebula/services/policy_simulation_service.py, src/nebula/services/router_service.py, tests/test_governance_runtime_hardening.py, tests/test_service_flows.py, tests/test_governance_api.py
  - Verify: ./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "budget or simulation or runtime_policy" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "guardrail or policy_denied or simulation" -x
- [ ] **T03: Expose hard-budget explanations in operator policy and ledger surfaces** — Finish the operator loop by updating the policy UI, simulation copy, and ledger request detail to explain hard cumulative budget behavior in plain language, showing the new controls and recorded outcomes without raw JSON spelunking or scope drift beyond the existing decisioning control plane.

Steps:
1. Update `console/src/components/policy/policy-form.tsx` and related tests/E2E fixtures so the policy page distinguishes runtime-enforced hard guardrails from advisory soft-budget signals.
2. Extend `console/src/components/ledger/ledger-request-detail.tsx` (and tests) to render any new budget evidence or clearer policy outcome language using the stable labeled-field pattern established in S01.
3. Refresh route-decision / budget docs so operators and downstream slices have one stable explanation vocabulary for the new hard-budget outcomes.

Must-haves:
- [ ] The policy page explains the new hard guardrails as runtime-enforced controls and preserves `soft_budget_usd` as advisory-only.
- [ ] Observability request detail makes hard-budget downgrade/deny evidence inspectable through labeled fields, not raw JSON.
- [ ] Docs stay within R044 scope discipline and describe explainable operator-visible budget outcomes rather than a new analytics/billing subsystem.
  - Estimate: 1.5h
  - Files: console/src/components/policy/policy-form.tsx, console/src/components/policy/policy-form.test.tsx, console/src/components/policy/policy-page.test.tsx, console/e2e/policy.spec.ts, console/src/components/ledger/ledger-request-detail.tsx, console/src/components/ledger/ledger-request-detail.test.tsx, docs/route-decision-vocabulary.md, docs/policy-guardrails.md
  - Verify: npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx && test -f docs/policy-guardrails.md
