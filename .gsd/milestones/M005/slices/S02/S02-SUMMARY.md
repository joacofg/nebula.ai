---
id: S02
parent: M005
milestone: M005
provides:
  - A typed backend policy-simulation contract that downstream slices can reuse for replay, recommendation, or guardrail explanation work.
  - A non-mutating admin replay endpoint for tenant policy previews grounded in recent usage-ledger traffic.
  - A console preview-before-save interaction pattern that shows aggregate deltas and changed-request samples without implying persistence.
requires:
  - slice: S01
    provides: Interpretable route signals persisted through the usage ledger and exposed in admin surfaces, which the simulation service reuses as replay inputs.
affects:
  - S03
  - S04
  - S05
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/policy_simulation_service.py
  - src/nebula/services/policy_service.py
  - src/nebula/services/router_service.py
  - src/nebula/services/governance_store.py
  - src/nebula/core/container.py
  - src/nebula/api/routes/admin.py
  - tests/test_service_flows.py
  - tests/test_governance_api.py
  - console/src/lib/admin-api.ts
  - console/src/app/(console)/policy/page.tsx
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/KNOWLEDGE.md
  - .gsd/PROJECT.md
key_decisions:
  - Reused production router and policy semantics through a replay-only evaluation seam instead of maintaining separate simulation logic.
  - Made policy simulation explicitly signal-driven because the usage ledger stores request metadata and route signals, not raw prompt text.
  - Kept simulation and persistence separate in the console so preview results never imply that policy state was saved.
patterns_established:
  - Use persisted route-signal metadata plus narrow reconstructed requests to build replay-only operator previews without storing raw prompts.
  - Treat simulation as a first-class read path that reuses production evaluation seams while guaranteeing no provider execution or persistence side effects.
  - Keep preview and save as separate console mutations with explicit UI language so operator trust is preserved.
observability_surfaces:
  - Policy simulation response aggregates (`evaluated_rows`, `changed_routes`, `newly_denied`, baseline/simulated/cost-delta totals)
  - Bounded changed-request sample showing baseline vs simulated route target, terminal status, policy outcome, route reason, and projected premium cost
  - Console preview-before-save panel with explicit replay notes and non-save feedback
drill_down_paths:
  - .gsd/milestones/M005/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M005/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M005/slices/S02/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-28T03:20:03.140Z
blocker_discovered: false
---

# S02: Policy simulation loop

**Delivered a non-mutating policy simulation loop that replays recent tenant ledger traffic through current routing/policy semantics and surfaces preview-before-save impact in the admin API and console.**

## What Happened

Slice S02 turned Nebula's new route-signal evidence from S01 into a real operator preview loop. On the backend, the slice introduced typed policy simulation models and a dedicated `PolicySimulationService` that loads recent tenant-scoped usage-ledger rows, replays them oldest-first through existing routing and policy evaluation semantics, and returns a bounded summary of what would change under a candidate policy. The replay is intentionally non-mutating: it does not execute providers, write policy, or append usage rows. Because the ledger does not retain raw prompt text, the service reconstructs replay requests from persisted model/token metadata and route signals, and it documents that approximation directly in the response. The admin API then exposed this capability through `POST /v1/admin/tenants/{tenant_id}/policy/simulate`, keeping tenant existence checks and inverted-window validation explicit while preserving the tenant's saved policy untouched. On the console side, the policy page now owns a separate simulation mutation alongside save, and the form renders an explicit preview-before-save panel with evaluated-row counts, changed-route counts, newly denied counts, premium-cost deltas, changed-request samples, replay notes, and clear non-save messaging. Together, these changes deliver the slice goal: operators can now see how a candidate routing or policy change would affect recent real traffic before committing it, using the same runtime semantics Nebula already enforces.

## Verification

All slice-plan verification checks passed in the assembled worktree:

- `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x` → 4 passed, 12 deselected
- `./.venv/bin/pytest tests/test_governance_api.py -k simulation -x` → 5 passed, 9 deselected
- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` → 2 files passed, 10 tests passed

Observability/diagnostic surfaces for this slice were also confirmed through code inspection and passing UI/API tests: simulation responses include aggregate replay counts, bounded changed-request detail, and approximation notes, and the console renders those surfaces with explicit non-save feedback.

## Requirements Advanced

- R040 — Implemented the core replay-only simulation loop across backend, admin API, and console preview surfaces so operators can evaluate candidate policy/routing changes against recent real traffic before saving.

## Requirements Validated

- R040 — Validated by passing focused backend service, admin API, and console preview verification: `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x`, `./.venv/bin/pytest tests/test_governance_api.py -k simulation -x`, and `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

Simulation remains an approximation because raw prompt text is intentionally unavailable in usage-ledger rows; replay reconstructs narrow requests from persisted metadata and route signals. The current console flow replays a fixed recent window (`limit: 50`, `changed_sample_limit: 5`) and does not yet expose operator-configurable replay filters. Admin API coverage surfaced a FastAPI deprecation warning for `HTTP_422_UNPROCESSABLE_ENTITY`, but runtime behavior remains correct.

## Follow-ups

S03 should reuse the replay and policy-evaluation seams to explain hard budget guardrail outcomes with the same baseline-vs-simulated vocabulary. S04 should build recommendation logic on top of the persisted simulation/route evidence instead of inventing a separate explanation surface. Consider a future cleanup to replace FastAPI's deprecated `HTTP_422_UNPROCESSABLE_ENTITY` constant usage in the admin route with the newer constant once the codebase standard is updated.

## Files Created/Modified

- `src/nebula/models/governance.py` — Added typed policy simulation request/response models, replay-window metadata, and changed-request summary DTOs shared across backend and admin surfaces.
- `src/nebula/services/policy_simulation_service.py` — Implemented the replay-only policy simulation service that rebuilds simulation inputs from persisted ledger metadata and route signals, reuses runtime policy evaluation semantics, and returns aggregate route/denial/cost deltas without persistence side effects.
- `src/nebula/services/policy_service.py` — Extended runtime policy evaluation seams to support non-mutating projected replay evaluation and projected premium-cost reporting during simulation.
- `src/nebula/services/router_service.py` — Preserved and reused route-signal-driven routing semantics for signal-based simulation replay paths.
- `src/nebula/services/governance_store.py` — Provided the usage-ledger read path needed for tenant/window-scoped replay and ensured simulation consumed persisted route-signal metadata.
- `src/nebula/core/container.py` — Wired the simulation service through the application service container for admin API access.
- `src/nebula/api/routes/admin.py` — Added the non-mutating admin policy simulation endpoint with tenant checks and window validation.
- `tests/test_service_flows.py` — Added focused backend service tests covering changed routes, newly denied outcomes, window scoping, empty windows, keyword-signal replay, and non-mutation guarantees.
- `tests/test_governance_api.py` — Added focused admin API tests proving tenant scoping, aggregate replay output, new-denial detection, empty/unchanged handling, missing-tenant behavior, inverted-window rejection, and saved-policy immutability after simulation.
- `console/src/lib/admin-api.ts` — Added typed console admin API contracts and client helper for policy simulation responses.
- `console/src/app/(console)/policy/page.tsx` — Separated simulation from persistence in the policy page, managing simulation state independently from save state and clearing previews after explicit save or tenant switch.
- `console/src/components/policy/policy-form.tsx` — Added preview-before-save policy editor UX, including replay aggregates, changed-request summaries, approximation notes, explicit non-save messaging, and empty/error states.
- `console/src/components/policy/policy-form.test.tsx` — Added focused component tests for preview-before-save behavior, explicit save separation, aggregate rendering, changed-request summaries, empty/error handling, and runtime-enforced policy control grouping.
- `console/src/components/policy/policy-page.test.tsx` — Added page-level tests proving draft values are sent to simulation, preview remains non-saving, errors stay legible, and zero-result previews are explicit.
- `.gsd/KNOWLEDGE.md` — Recorded slice-level replay-ordering and change-detection lessons for future milestone work.
- `.gsd/PROJECT.md` — Updated current-project state to reflect that M005/S02 is now complete and available for downstream guardrail/recommendation work.
