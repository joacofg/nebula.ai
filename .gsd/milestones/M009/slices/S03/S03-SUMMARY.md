---
id: S03
parent: M009
milestone: M009
provides:
  - Replay parity for outcome-grounded routing using the same tenant-window evidence summary and additive scoring semantics as runtime.
  - Honest degraded replay semantics when persisted historical route signals are incomplete.
  - An additive console/admin evidence contract that accepts degraded replay state without a new replay-only UI surface.
requires:
  - slice: S01
    provides: The authoritative tenant-scoped outcome evidence summary contract and `sufficient`/`thin`/`stale`/`degraded` state vocabulary.
  - slice: S02
    provides: Persisted live route factors, additive runtime scoring semantics, and request evidence fields used to prove unchanged-policy replay parity.
affects:
  - S04
  - S05
key_files:
  - src/nebula/services/policy_service.py
  - src/nebula/services/policy_simulation_service.py
  - tests/test_service_flows.py
  - tests/test_governance_api.py
  - console/src/lib/admin-api.ts
  - console/src/components/policy/policy-form.test.tsx
  - .gsd/PROJECT.md
key_decisions:
  - Allow replay callers to inject a calibration evidence summary override into `PolicyService.evaluate()` so replay and runtime traverse the same scoring contract.
  - Compute the tenant-window `calibration_summary` once per simulation request and reuse that same object across replayed rows and the response payload to prevent evidence-classification drift.
  - Keep the console/admin contract additive by extending `calibration_summary.state` with `degraded` instead of adding a replay-only evidence field.
patterns_established:
  - Shared runtime/replay semantics should flow through one evaluation path with explicit dependency injection rather than a replay-specific scoring branch.
  - Tenant-window evidence classification should be computed once per bounded replay window and reused everywhere that simulation request needs it.
  - Request-first operator surfaces can absorb richer evidence states by widening existing typed vocabularies instead of introducing new preview-only structures.
observability_surfaces:
  - `POST /v1/admin/tenants/{tenant_id}/policy/simulate` response fields `simulated_policy_outcome`, `simulated_route_mode`, `simulated_route_score`, and `calibration_summary` remain the authoritative replay diagnostics.
  - Focused backend verification in `tests/test_service_flows.py` and `tests/test_governance_api.py` localizes parity drift and degraded-path regressions without requiring provider calls or ledger mutation.
  - Console regression coverage in `console/src/components/policy/policy-form.test.tsx` localizes typing/rendering drift when degraded replay evidence reaches the request-first preview.
drill_down_paths:
  - .gsd/milestones/M009/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M009/slices/S03/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-27T21:12:03.030Z
blocker_discovered: false
---

# S03: S03

**Policy simulation replay now reuses the same tenant-window outcome evidence summary and additive routing semantics as runtime, proving unchanged-policy parity where evidence exists and surfacing degraded replay honestly when persisted signals are incomplete.**

## What Happened

S03 closed the replay-credibility gap between live runtime and admin simulation for outcome-grounded routing. On the backend, `PolicyService.evaluate()` was extended so replay callers can inject a precomputed calibration evidence summary instead of replay implicitly skipping evidence lookup whenever `replay_context` is present. `PolicySimulationService.simulate()` now computes one tenant-window `calibration_summary` for the requested replay window, reuses that exact summary object for every replayed request, and returns the same bounded summary in the API response so there is no replay-only evidence classification path. Service-flow tests proved that replay now carries the same `outcome_evidence=...` vocabulary as runtime, that a low-complexity replay can flip for the same evidence-driven reason as live routing when the summary is sufficient, and that missing persisted route signals still produce honest degraded route mode under the shared summary. On the public/admin boundary, governance API coverage was tightened into a two-pass simulation proof: unchanged-policy replay now asserts route target/reason/mode/score parity against runtime for calibrated rows, while a changed-policy pass preserves drift assertions without conflating them with parity semantics. The same API coverage also proves simulation remains non-mutating and side-effect free. On the console seam, the existing `CalibrationEvidenceSummary.state` union was extended additively to include `degraded`, and a focused policy-form regression test proved degraded replay evidence can pass through the existing request-first preview without introducing a replay-only UI contract or crashing the surface.

## Verification

Re-ran all slice-level verification commands and they passed. `./.venv/bin/pytest tests/test_service_flows.py -k "policy_simulation and (outcome or replay or degraded or parity or hard_budget)"` passed with 5 focused service-flow tests covering hard-budget replay windows, shared outcome-evidence propagation, evidence-driven parity changes, degraded replay honesty, and window-scoped calibration summary diagnostics. `./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation and (outcome_grounded or degraded or parity or hard_budget)"` passed and proved unchanged-policy replay parity, degraded-path honesty, preserved changed-policy drift behavior, non-mutation of saved policy, and no provider side effects. `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx` passed and confirmed degraded calibration evidence remains compatible with the existing request-first preview contract.

## Requirements Advanced

- R074 — Policy simulation replay now injects the same tenant-window calibration evidence summary into shared policy evaluation, proving unchanged-policy route score/mode parity with runtime and preserving honest degraded replay behavior.
- R078 — Replay credibility was improved without adding provider side effects, replay-only evidence vocabulary, or dashboard-heavy operator surfaces; the slice stayed metadata-only and request-first.

## Requirements Validated

- R074 — Validated by focused service-flow, admin API, and console tests proving runtime/replay outcome-grounded parity, one-summary reuse per simulation window, and degraded replay honesty under incomplete persisted signals.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

The planned admin replay proof was implemented by restructuring the existing broad simulation test into a two-pass unchanged-policy versus changed-policy flow instead of adding a completely separate test file. This kept the contract proof localized while making parity and drift failures easier to interpret.

## Known Limitations

S03 does not yet expose grounded/thin/stale/degraded explanations on the existing Observability and request-detail UI; that request-first operator narrative is still pending in S04. The slice also does not produce the final cross-surface live-request → persisted evidence → replay → operator walkthrough, which remains the purpose of S05.

## Follow-ups

S04 should read the persisted runtime and replay evidence vocabulary already stabilized here and surface it on selected-request operator paths without inventing replay-only terminology. S05 should assemble one integrated proof that pairs a happy-path request and a degraded-path request across runtime persistence, replay parity, and operator inspection.

## Files Created/Modified

- `src/nebula/services/policy_service.py` — Added an explicit calibration evidence summary override so replay callers can reuse live scoring semantics instead of bypassing evidence lookup.
- `src/nebula/services/policy_simulation_service.py` — Computed one tenant-window calibration summary per simulation request, reused it across replayed rows, and returned the same bounded summary in the response payload.
- `tests/test_service_flows.py` — Added focused replay parity and degraded-path service coverage for shared outcome-evidence propagation and evidence-driven route changes.
- `tests/test_governance_api.py` — Restructured simulation API coverage into unchanged-policy parity and changed-policy drift passes while asserting non-mutation and no provider side effects.
- `console/src/lib/admin-api.ts` — Extended the `CalibrationEvidenceSummary.state` union to include `degraded` so replay evidence typing stays aligned with backend semantics.
- `console/src/components/policy/policy-form.test.tsx` — Added regression coverage showing degraded replay evidence remains compatible with the existing request-first policy preview.
- `.gsd/PROJECT.md` — Refreshed project state to reflect that M009 S03 is complete and replay parity is now part of the current system contract.
