---
id: T01
parent: S03
milestone: M005
provides: []
requires: []
affects: []
key_files: ["src/nebula/models/governance.py", "src/nebula/db/models.py", "src/nebula/services/governance_store.py", "src/nebula/api/routes/admin.py", "migrations/versions/20260328_0007_hard_budget_guardrails.py", "console/src/lib/admin-api.ts", "console/src/components/policy/policy-form.tsx", "tests/test_governance_api.py", "console/src/components/policy/policy-form.test.tsx", "console/src/components/policy/policy-page.test.tsx", "console/e2e/policy.spec.ts"]
key_decisions: ["Represented hard cumulative budget policy with explicit `hard_budget_limit_usd` and `hard_budget_enforcement` fields instead of mutating `soft_budget_usd`.", "Used `/v1/admin/policy/options` metadata as the observability and UI contract for classifying hard-budget controls as runtime-enforced while keeping `soft_budget_usd` advisory-only."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x` and confirmed 6 selected governance policy-option/simulation tests passed, including runtime field metadata and persisted policy round-trip coverage. Ran `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` and confirmed 10 console policy tests passed, including metadata-driven runtime grouping and rendering of the new hard-budget controls."
completed_at: 2026-03-28T03:30:14.752Z
blocker_discovered: false
---

# T01: Added explicit hard cumulative budget policy fields across backend persistence, admin metadata, and console policy contracts while keeping soft budget advisory-only.

> Added explicit hard cumulative budget policy fields across backend persistence, admin metadata, and console policy contracts while keeping soft budget advisory-only.

## What Happened
---
id: T01
parent: S03
milestone: M005
key_files:
  - src/nebula/models/governance.py
  - src/nebula/db/models.py
  - src/nebula/services/governance_store.py
  - src/nebula/api/routes/admin.py
  - migrations/versions/20260328_0007_hard_budget_guardrails.py
  - console/src/lib/admin-api.ts
  - console/src/components/policy/policy-form.tsx
  - tests/test_governance_api.py
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - console/e2e/policy.spec.ts
key_decisions:
  - Represented hard cumulative budget policy with explicit `hard_budget_limit_usd` and `hard_budget_enforcement` fields instead of mutating `soft_budget_usd`.
  - Used `/v1/admin/policy/options` metadata as the observability and UI contract for classifying hard-budget controls as runtime-enforced while keeping `soft_budget_usd` advisory-only.
duration: ""
verification_result: passed
completed_at: 2026-03-28T03:30:14.753Z
blocker_discovered: false
---

# T01: Added explicit hard cumulative budget policy fields across backend persistence, admin metadata, and console policy contracts while keeping soft budget advisory-only.

**Added explicit hard cumulative budget policy fields across backend persistence, admin metadata, and console policy contracts while keeping soft budget advisory-only.**

## What Happened

Extended the shared tenant policy contract with `hard_budget_limit_usd` and `hard_budget_enforcement`, added matching SQLAlchemy columns and a new Alembic migration, and wired GovernanceStore read/write hydration so admin policy round-trips preserve the new values. Updated `/v1/admin/policy/options` so the new controls are classified as runtime-enforced while `soft_budget_usd` remains advisory/soft-signal only. Mirrored the contract in console admin typings, updated policy page/form fixtures, and rendered the new runtime-enforced inputs in the metadata-driven policy form. During verification I corrected stale test expectations plus a real persistence bug in `upsert_policy()` that initially dropped the new fields.

## Verification

Ran `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x` and confirmed 6 selected governance policy-option/simulation tests passed, including runtime field metadata and persisted policy round-trip coverage. Ran `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` and confirmed 10 console policy tests passed, including metadata-driven runtime grouping and rendering of the new hard-budget controls.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x` | 0 | ✅ pass | 910ms |
| 2 | `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` | 0 | ✅ pass | 880ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/models/governance.py`
- `src/nebula/db/models.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/api/routes/admin.py`
- `migrations/versions/20260328_0007_hard_budget_guardrails.py`
- `console/src/lib/admin-api.ts`
- `console/src/components/policy/policy-form.tsx`
- `tests/test_governance_api.py`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `console/e2e/policy.spec.ts`


## Deviations
None.

## Known Issues
None.
