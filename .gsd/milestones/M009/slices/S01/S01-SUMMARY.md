---
id: S01
parent: M009
milestone: M009
provides:
  - A deterministic tenant-scoped outcome-evidence summary contract with explicit `sufficient`/`thin`/`stale`/`degraded` states.
  - The authoritative GovernanceStore summarization seam for bounded recent ledger evidence.
  - Replay-safe degraded reason vocabulary (`missing_route_signals`, `degraded_replay_signals`) that downstream slices can persist and render consistently.
requires:
  []
affects:
  - S02
  - S03
  - S04
  - S05
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/router_service.py
  - src/nebula/services/governance_store.py
  - tests/test_service_flows.py
  - tests/test_governance_api.py
key_decisions:
  - Kept `calibration_summary` as the compatibility field name while redefining its `state` as the shared outcome-evidence contract.
  - Made `GovernanceStore.summarize_calibration_evidence()` the single authoritative summary seam for M009 instead of allowing fake/test duplication.
  - Established state precedence where thin wins before sufficiency, and degraded outranks stale/sufficient once enough recent evidence exists but trustworthiness is compromised.
patterns_established:
  - Extend existing typed evidence seams additively instead of opening new API families when deepening backend semantics.
  - Delegate test doubles and replay-facing fixtures to shipped summarization logic when parity matters more than isolated fake behavior.
  - Model degraded trustworthiness explicitly as a summary-state outcome, not just as a per-row reason, so downstream consumers can make honest bounded decisions.
observability_surfaces:
  - Backend request/ledger-first evidence seam remains authoritative through `calibration_summary` counters, reasons, and replay-safe null parity fields.
  - Targeted backend tests now prove degraded/suppressed evidence remains inspectable through existing policy simulation and governance/admin summary payloads.
drill_down_paths:
  - .gsd/milestones/M009/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M009/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M009/slices/S01/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-27T15:01:47.685Z
blocker_discovered: false
---

# S01: S01

**Locked the shared tenant-scoped outcome-evidence contract behind `calibration_summary`, with deterministic GovernanceStore summarization and backend proof for sufficient/thin/stale/degraded states.**

## What Happened

S01 closed the contract seam that all remaining M009 work depends on without changing live route choice yet. The slice preserved the existing `calibration_summary` field name for compatibility, but redefined its `state` as the shared outcome-evidence vocabulary (`sufficient`, `thin`, `stale`, `degraded`) so runtime routing, policy simulation replay, and admin/request evidence consumers can all speak one serializable language. On the derivation side, `GovernanceStore.summarize_calibration_evidence()` is now the authoritative ledger-backed summarizer for bounded tenant-scoped outcome evidence. It retains deterministic bounded-window reads and explicit counters/reasons while making degraded a first-class summary-state outcome. The key precedence rule established here is that thin still wins before sufficiency is reached, but once evidence volume is sufficient, degraded outranks stale/sufficient when eligible recent rows are not trustworthy enough for grounded use. This keeps failure handling honest for both operators and replay consumers instead of letting freshness alone mask degraded evidence quality.

The slice also removed a major drift risk from downstream work by making tests and replay-facing fakes delegate to the real GovernanceStore summarization seam rather than hand-rolling duplicate summary logic. Policy simulation and governance/admin tests now prove that suppressed or degraded ledger rows remain visible as degraded evidence with explicit reasons such as `missing_route_signals` and `degraded_replay_signals`, while persisted explicit-premium rows remain excluded and replay-safe parity fields stay null when the ledger lacks route-mode truth. Together, these changes establish the stable backend contract that S02-S04 can consume for live routing, replay parity, and operator explanation without widening the public surface or inventing a new analytics layer.

## Verification

Ran the slice-plan verification commands against the project virtualenv and confirmed the assembled backend contract passes end to end. `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or outcome or governance_store_calibration_summary or policy_simulation_exposes_window_calibration_summary"` passed (6 passed), proving summary-state transitions, deterministic tenant/window scoping, degraded precedence, and simulation-level exposure of degraded reasons. `./.venv/bin/pytest tests/test_governance_api.py -k "calibration_summary or policy_simulation"` passed (7 passed), proving policy simulation and governance/admin payloads serialize the richer contract correctly, preserve compatibility via `calibration_summary`, and surface suppressed route-signal rows honestly as degraded evidence. LSP diagnostics for `src/nebula/services/governance_store.py`, `tests/test_service_flows.py`, and `tests/test_governance_api.py` reported no diagnostics. Observability-specific runtime surfaces were not yet part of this slice; the relevant diagnostic seam here is the persisted-summary/request-first backend evidence path, which is now explicitly test-covered.

## Requirements Advanced

- R073 — Provides the deterministic tenant-scoped evidence contract that live outcome-grounded routing will consume in S02.
- R074 — Provides the shared serializable vocabulary and authoritative summarization seam that replay parity will consume in S03.
- R075 — Defines the typed factor/evidence vocabulary that request-level persistence can build on in S02.
- R076 — Provides the grounded/thin/stale/degraded evidence states that request-first operator surfaces will explain in S04.
- R078 — Keeps the milestone on a bounded, explainable, request-first path by deepening existing seams instead of adding analytics or new public APIs.

## Requirements Validated

- R077 — Deterministic GovernanceStore summarization and targeted backend tests prove explicit fail-safe classification for missing, thin, stale, degraded, and sufficient evidence, including suppressed route-signal cases.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

None at slice scope. Individual task verification used `./.venv/bin/pytest` instead of bare `pytest` because pytest was not exposed on PATH in this shell environment.

## Known Limitations

This slice does not yet change live route-choice behavior, persist new request-level route factors, or render the richer evidence states in the console. It closes the shared backend contract and proof seam only; those integrations remain for S02-S04.

## Follow-ups

S02 should consume the shared summary seam in live routing and persist the actual outcome-grounded route factors on request rows. S03 should reuse the same seam to enforce replay parity and honest degraded approximation. S04 should surface the grounded/thin/stale/degraded story on the existing request-first operator surfaces without widening into analytics.

## Files Created/Modified

- `src/nebula/models/governance.py` — Extended the typed governance summary contract so `calibration_summary` carries the richer outcome-evidence state vocabulary while preserving compatibility.
- `src/nebula/services/router_service.py` — Clarified comments around the per-request route-mode seam versus summary-level degraded evidence semantics.
- `src/nebula/services/governance_store.py` — Centralized deterministic tenant-scoped ledger summarization with explicit degraded/thin/stale/sufficient state precedence.
- `tests/test_service_flows.py` — Added and tightened contract/store/replay-facing tests for summary-state precedence, tenant/window scoping, and degraded reason exposure.
- `tests/test_governance_api.py` — Expanded admin/policy simulation tests to prove serialized summaries preserve compatibility and expose suppressed/degraded evidence honestly.
