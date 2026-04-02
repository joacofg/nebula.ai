---
id: T01
parent: S03
milestone: M006
provides: []
requires: []
affects: []
key_files: ["src/nebula/models/governance.py", "src/nebula/services/policy_simulation_service.py", "console/src/lib/admin-api.ts", "tests/test_service_flows.py", ".gsd/milestones/M006/slices/S03/tasks/T01-SUMMARY.md"]
key_decisions: ["Infer baseline parity from persisted replay hints when explicit route_mode booleans are absent, but keep gated and policy-forced replay paths null-mode instead of fabricating signals."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x` and the focused simulation suite passed with the new changed-request parity assertions."
completed_at: 2026-04-02T03:46:43.647Z
blocker_discovered: false
---

# T01: Extended simulation changed-request samples with route parity fields and null-safe gated semantics aligned to runtime routing signals.

> Extended simulation changed-request samples with route parity fields and null-safe gated semantics aligned to runtime routing signals.

## What Happened
---
id: T01
parent: S03
milestone: M006
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/policy_simulation_service.py
  - console/src/lib/admin-api.ts
  - tests/test_service_flows.py
  - .gsd/milestones/M006/slices/S03/tasks/T01-SUMMARY.md
key_decisions:
  - Infer baseline parity from persisted replay hints when explicit route_mode booleans are absent, but keep gated and policy-forced replay paths null-mode instead of fabricating signals.
duration: ""
verification_result: passed
completed_at: 2026-04-02T03:46:43.647Z
blocker_discovered: false
---

# T01: Extended simulation changed-request samples with route parity fields and null-safe gated semantics aligned to runtime routing signals.

**Extended simulation changed-request samples with route parity fields and null-safe gated semantics aligned to runtime routing signals.**

## What Happened

Extended PolicySimulationChangedRequest with baseline and simulated route mode, calibrated/degraded booleans, and route score fields. Wired PolicySimulationService to derive baseline parity from persisted ledger route_signals with bounded inference for older rows that only persisted replay hints, and to derive simulated parity from PolicyEvaluation.route_decision. Preserved explicit null-mode behavior for calibrated_routing_disabled and policy-forced explicit override paths instead of synthesizing fake route signals. Mirrored the contract in console/src/lib/admin-api.ts and added focused service-level assertions proving calibrated parity, policy-forced null-mode parity, and gated null-mode parity in replay samples.

## Verification

Ran `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x` and the focused simulation suite passed with the new changed-request parity assertions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x` | 0 | ✅ pass | 600ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/models/governance.py`
- `src/nebula/services/policy_simulation_service.py`
- `console/src/lib/admin-api.ts`
- `tests/test_service_flows.py`
- `.gsd/milestones/M006/slices/S03/tasks/T01-SUMMARY.md`


## Deviations
None.

## Known Issues
None.
