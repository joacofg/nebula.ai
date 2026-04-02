---
id: S03
parent: M006
milestone: M006
provides:
  - A stable runtime/simulation parity contract for calibrated, degraded, and rollout-disabled routing semantics that downstream operator-inspection work can reuse without re-deriving meaning from raw route signals.
requires:
  - slice: S01
    provides: Shared calibrated routing vocabulary, response-header semantics, and the tenant-scoped `calibrated_routing_enabled` rollout valve.
  - slice: S02
    provides: Tenant-scoped calibration evidence classification and the bounded sufficient/thin/stale/degraded/gated vocabulary reused by simulation and downstream operator surfaces.
affects:
  - S04
  - S05
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/policy_simulation_service.py
  - console/src/lib/admin-api.ts
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-page.test.tsx
  - tests/test_service_flows.py
  - tests/test_governance_api.py
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Infer baseline replay parity from persisted ledger route signals when available, with bounded fallback inference for older rows that only retained replay hints, but keep calibrated-routing-disabled and policy-forced paths null-mode instead of synthesizing fake route semantics.
  - Prove degraded and gated replay parity at the admin boundary from real runtime requests plus correlated usage-ledger evidence rather than relying only on synthetic replay fixtures.
  - Keep routing parity rendering inside the existing policy preview changed-request cards and reuse rollout-disabled vocabulary instead of widening the preview into a separate routing-inspection surface.
patterns_established:
  - Use the usage ledger as the parity seam between live runtime and simulation: correlate `X-Request-ID` and persisted route fields first, then assert replay changed-request fields against that shared evidence.
  - Treat `route_mode=null` as a first-class, intentional state for rollout-disabled or policy-forced routing rather than as missing data; only token-complexity decisions should emit calibrated/degraded scoring semantics.
  - Count simulation changes on route, policy outcome, or projected premium cost deltas so unchanged targets can still surface meaningful parity differences.
observability_surfaces:
  - Admin policy simulation changed-request samples now expose baseline/simulated route mode, calibrated/degraded flags, route reason, and route score parity fields.
  - Policy preview changed-request cards render a compact routing parity line, including explicit rollout-disabled rendering when calibrated routing is gated.
  - Usage-ledger correlation remains the authoritative diagnostic seam for runtime-to-replay parity proof.
drill_down_paths:
  - .gsd/milestones/M006/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M006/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M006/slices/S03/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-02T03:57:24.611Z
blocker_discovered: false
---

# S03: Runtime / simulation parity

**Policy simulation replay now exposes the same calibrated, degraded, and rollout-disabled routing semantics as live runtime for the same tenant traffic class, and the policy preview surfaces that parity compactly without widening scope.**

## What Happened

S03 closed the runtime-versus-replay gap introduced by M006/S01 and S02. The backend simulation contract now carries baseline and simulated route mode, calibrated/degraded flags, and route score fields on changed-request samples, using persisted ledger route signals when available and bounded inference for older replayable rows that only retained token/keyword hints. The replay path preserves explicit null route mode for calibrated-routing-disabled and policy-forced rows instead of fabricating synthetic routing signals, so gated and forced cases stay visibly distinct from degraded evidence.

The slice then locked parity at the admin boundary with focused runtime-to-replay tests that start from real chat-completions requests, correlate the request through usage-ledger rows, and assert that simulation changed-request samples match the shipped runtime headers and persisted route evidence. That coverage now includes a calibrated request that replays as calibrated, a degraded replay case where missing persisted route signals intentionally leaves runtime and ledger without route mode while replay still classifies the row as degraded evidence, and a calibrated-routing-disabled gate where replay and live runtime both expose the same `calibrated_routing_disabled` reason with null route mode.

On the console side, the existing policy preview changed-request cards now render one compact routing parity line that compares baseline versus simulated routing semantics using the established vocabulary. Calibrated and degraded markers plus route score appear when meaningful, and null route mode tied to `calibrated_routing_disabled` renders as an intentional rollout-disabled state rather than missing data. The preview stayed bounded: no new dashboard, analytics surface, or separate routing inspector was added. The slice therefore delivers runtime/simulation parity through the existing admin simulation contract and bounded policy preview surface that S04 can now build on for richer operator inspection.

## Verification

Slice-plan verification passed exactly as written: `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x` passed (6 selected tests), `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` passed, and `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx` passed (4 tests). I also inspected the assembled backend and console code paths to confirm that null route mode remains intentional for rollout-disabled and policy-forced cases and that the preview rendering stays compact and local to the changed-request cards.

## Requirements Advanced

- R039 — S03 proved that replay now reports the same calibrated-versus-degraded-versus-gated routing semantics as live runtime for the same tenant traffic class, using correlated runtime headers and usage-ledger evidence rather than heuristic-only assertions. This materially strengthens the outcome-aware routing story, but full operator inspection closure and integrated milestone proof are still pending.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

Replay parity is still constrained by what the usage ledger persists. Older or thinner rows without full `route_signals` can only recover bounded inferred baseline semantics from replay hints, so degraded parity remains an evidence-aware approximation rather than perfect historical reconstruction. Operator inspection also remains intentionally compact in the policy preview; richer request-detail and Observability inspection is deferred to S04.

## Follow-ups

S04 should reuse the new parity fields directly in request-detail and Observability surfaces instead of re-deriving route-mode semantics in the UI. Milestone close-out should also include an integrated proof that the runtime request, headers, ledger row, replay response, and operator surfaces all tell the same calibration story for the same request class.

## Files Created/Modified

- `src/nebula/models/governance.py` — Extended `PolicySimulationChangedRequest` with baseline/simulated route parity fields for mode, calibrated/degraded flags, and route score.
- `src/nebula/services/policy_simulation_service.py` — Derived baseline parity from persisted ledger route signals or bounded replay inference, derived simulated parity from `PolicyEvaluation.route_decision`, and preserved explicit null-mode semantics for gated/policy-forced cases.
- `console/src/lib/admin-api.ts` — Mirrored the backend simulation changed-request parity contract and nullability in the console admin API types.
- `console/src/components/policy/policy-form.tsx` — Rendered a compact routing parity line in changed-request cards, including explicit rollout-disabled text when route mode is intentionally null because calibrated routing is disabled.
- `console/src/components/policy/policy-page.test.tsx` — Locked compact parity rendering for calibrated-to-degraded and degraded-to-rollout-disabled preview cases.
- `tests/test_service_flows.py` — Added focused service-level assertions for changed-request parity fields, bounded inference, null-mode gated semantics, and changed-row sampling behavior.
- `tests/test_governance_api.py` — Added runtime-to-replay parity coverage that correlates live request headers and usage-ledger rows to simulation changed-request entries for calibrated, degraded, and gated scenarios.
- `.gsd/KNOWLEDGE.md` — Recorded the replay-parity proof pattern so future slices reuse runtime-plus-ledger correlation instead of weaker synthetic-only parity evidence.
