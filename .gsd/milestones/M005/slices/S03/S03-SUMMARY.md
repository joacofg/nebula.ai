---
id: S03
parent: M005
milestone: M005
provides:
  - Explicit hard cumulative budget policy controls (`hard_budget_limit_usd`, `hard_budget_enforcement`) available across backend, admin APIs, and console contracts.
  - Shared runtime and simulation hard-budget enforcement that downgrades compatible auto-routed traffic to local when caps are exhausted and denies explicit premium requests when downgrade is not allowed.
  - Operator-visible budget evidence and stable vocabulary in policy editing, ledger request detail, simulation outputs, and documentation.
requires:
  - slice: S01
    provides: S01's route-decision vocabulary and ledger evidence pattern that S03 reused for stable policy outcomes and operator-visible explanation surfaces.
affects:
  - S04
  - S05
key_files:
  - src/nebula/models/governance.py
  - src/nebula/db/models.py
  - src/nebula/services/governance_store.py
  - src/nebula/api/routes/admin.py
  - migrations/versions/20260328_0007_hard_budget_guardrails.py
  - src/nebula/services/policy_service.py
  - src/nebula/services/policy_simulation_service.py
  - console/src/lib/admin-api.ts
  - console/src/components/policy/policy-form.tsx
  - console/src/components/ledger/ledger-request-detail.tsx
  - docs/route-decision-vocabulary.md
  - docs/policy-guardrails.md
  - tests/test_governance_api.py
  - tests/test_governance_runtime_hardening.py
  - tests/test_service_flows.py
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
key_decisions:
  - Represented hard cumulative budget policy with explicit `hard_budget_limit_usd` and `hard_budget_enforcement` fields instead of mutating `soft_budget_usd`.
  - Centralized hard-budget enforcement in `PolicyService.evaluate()` and reused that exact path from simulation via `before_timestamp` rather than building a replay-only budget engine.
  - Allowed downgrade only for compatible auto/default-to-local flows and kept explicit premium or premium-only requests as exact denials when downgrade is impossible or disallowed.
  - Preserved the raw persisted `policy_outcome` field in request detail for audit continuity, then layered structured budget evidence beside it for operator inspection.
  - Kept hard-budget documentation and UI copy inside existing routing/decisioning scope rather than expanding into billing or analytics semantics.
patterns_established:
  - Add enforcement-oriented policy fields explicitly and carry them through persistence, admin metadata, and console contracts instead of reinterpreting advisory fields in place.
  - Keep runtime and replay semantics aligned by routing both through the same policy-evaluation path and passing replay-specific context (`before_timestamp`) rather than building a second decision engine.
  - Expose new control-plane outcomes through stable labeled fields and shared vocabulary on existing observability surfaces before adding any new analytics UI.
observability_surfaces:
  - `/v1/admin/policy/options` now classifies hard-budget controls as runtime-enforced while keeping `soft_budget_usd` advisory-only.
  - Usage ledger request detail renders labeled hard-budget evidence beside the persisted `policy_outcome`, making downgrade-versus-deny outcomes inspectable without raw JSON spelunking.
  - Policy simulation responses now reflect the same hard-budget evaluation path used at runtime, including replay-window spend semantics and operator-readable changed-request evidence.
  - Docs (`docs/route-decision-vocabulary.md`, `docs/policy-guardrails.md`) establish the stable operator vocabulary for hard-budget outcomes.
drill_down_paths:
  - .gsd/milestones/M005/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M005/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M005/slices/S03/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-28T03:47:29.859Z
blocker_discovered: false
---

# S03: Hard budget guardrails

**Delivered enforceable hard cumulative budget guardrails with shared runtime/simulation semantics, deterministic downgrade-versus-deny behavior, and operator-visible evidence across policy, ledger, and docs.**

## What Happened

S03 turned Nebula's previously advisory budget posture into an enforceable, explainable hard-guardrail loop without widening the product beyond decisioning control-plane scope. The slice first established explicit cumulative hard-budget policy fields across the shared tenant policy contract, SQLAlchemy model, Alembic migration, governance store hydration, admin policy-options metadata, and console typings, preserving `soft_budget_usd` as advisory-only instead of overloading it with runtime meaning. It then centralized enforcement in `PolicyService.evaluate()`, where tenant cumulative spend is compared against the hard cap and resolved deterministically into either a downgrade-to-local outcome for compatible auto-routed/default-local requests or an exact denial for explicit premium and premium-only requests. `PolicySimulationService` now reuses that same path via `before_timestamp`, so replayed simulations inherit the real runtime semantics instead of a separate budget engine. Finally, the operator loop was closed by teaching the policy editor to distinguish runtime-enforced hard guardrails from advisory soft-budget signals, extending ledger request detail with labeled hard-budget evidence next to the persisted `policy_outcome`, and documenting stable budget vocabulary in `docs/route-decision-vocabulary.md` and `docs/policy-guardrails.md`. The assembled result is a narrow but meaningful control-plane capability: hard spend caps now change routing behavior predictably, those outcomes are inspectable after the fact, and downstream recommendation work can build on persisted downgrade-versus-deny evidence instead of inferred spend pressure.

## Verification

All slice-plan verification checks passed in the assembled worktree: `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x` (7 passed), `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` (11 passed), `./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "budget or simulation or runtime_policy" -x` (11 passed), `./.venv/bin/pytest tests/test_governance_api.py -k "guardrail or policy_denied or simulation" -x` (8 passed), and `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx && test -f docs/policy-guardrails.md` (19 passed plus docs presence). Observability surfaces were explicitly confirmed through policy-options metadata, simulation API responses, and ledger request-detail rendering tests that validate structured hard-budget evidence and advisory/runtime copy separation.

## Requirements Advanced

- R041 — Implemented the explicit policy fields, central enforcement logic, shared simulation semantics, and operator evidence path needed for enforceable hard spend guardrails with graceful downgrade behavior.
- R044 — Kept the work inside existing decisioning, policy, ledger, and documentation surfaces rather than expanding into billing, analytics, SDK, or hosted-authority scope.

## Requirements Validated

- R041 — Focused backend and console verification passed for policy-options metadata, runtime/service hard-budget enforcement, simulation replay semantics, and operator evidence surfaces via `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x`, `./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "budget or simulation or runtime_policy" -x`, `./.venv/bin/pytest tests/test_governance_api.py -k "guardrail or policy_denied or simulation" -x`, and `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

No dedicated alerting or dashboard aggregation exists yet for hard-budget exhaustion trends; operators inspect per-request evidence and simulation previews, with recommendation-grade guidance deferred to S04.

## Follow-ups

S04 should consume the now-stable hard-budget outcomes and vocabulary when generating recommendations so recommendation logic can treat downgrade-versus-deny evidence as first-class operator guidance instead of inferring spend pressure from soft-budget signals.

## Files Created/Modified

- `src/nebula/models/governance.py` — Extended tenant policy contract, persistence model, and admin options metadata with explicit hard cumulative budget fields and preserved soft-budget advisory semantics.
- `src/nebula/db/models.py` — Added hard-budget columns for tenant policy persistence.
- `src/nebula/services/governance_store.py` — Kept policy write/read hydration and usage ledger mapping aligned with the new guardrail fields.
- `src/nebula/api/routes/admin.py` — Exposed hard-budget controls through admin policy options metadata as runtime-enforced fields.
- `migrations/versions/20260328_0007_hard_budget_guardrails.py` — Added Alembic migration for hard-budget guardrail persistence.
- `src/nebula/services/policy_service.py` — Centralized cumulative hard-budget downgrade-versus-deny evaluation shared by runtime and simulation.
- `src/nebula/services/policy_simulation_service.py` — Reused the shared policy evaluation path during chronological ledger replay with before_timestamp semantics.
- `console/src/lib/admin-api.ts` — Mirrored hard-budget contract types and options metadata in the console admin client.
- `console/src/components/policy/policy-form.tsx` — Explained runtime-enforced hard guardrails versus advisory soft-budget controls in the policy editor.
- `console/src/components/ledger/ledger-request-detail.tsx` — Rendered structured hard-budget evidence in ledger request detail alongside persisted policy outcome.
- `docs/route-decision-vocabulary.md` — Documented stable route-decision and policy-guardrail vocabulary for operator-visible budget outcomes.
- `docs/policy-guardrails.md` — Added dedicated operator documentation for hard cumulative budget guardrails.
- `tests/test_governance_api.py` — Added focused backend coverage for hard-budget enforcement, simulation replay, and policy options/admin evidence.
- `tests/test_governance_runtime_hardening.py` — Added focused runtime/service hard-budget tests.
- `tests/test_service_flows.py` — Extended service-flow coverage for shared budget evaluation and simulation semantics.
- `console/src/components/policy/policy-form.test.tsx` — Locked policy form/page and ledger request-detail behavior with focused Vitest coverage.
