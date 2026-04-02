---
id: T02
parent: S02
milestone: M006
provides: []
requires: []
affects: []
key_files: ["src/nebula/models/governance.py", "src/nebula/services/policy_simulation_service.py", "console/src/lib/admin-api.ts", "tests/test_service_flows.py", "tests/test_governance_api.py", ".gsd/milestones/M006/slices/S02/tasks/T02-SUMMARY.md"]
key_decisions: ["Reused GovernanceStore.summarize_calibration_evidence() directly in policy simulation so replay and runtime admin surfaces share one calibration vocabulary."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` successfully after aligning the fake simulation store helper with the real summary contract. Re-ran `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` after tightening endpoint assertions and it passed. LSP diagnostics were clean for the touched Python files."
completed_at: 2026-04-02T03:27:47.568Z
blocker_discovered: false
---

# T02: Added shared calibration evidence summaries to admin policy simulation responses and aligned backend/console typing around the replay-window contract.

> Added shared calibration evidence summaries to admin policy simulation responses and aligned backend/console typing around the replay-window contract.

## What Happened
---
id: T02
parent: S02
milestone: M006
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/policy_simulation_service.py
  - console/src/lib/admin-api.ts
  - tests/test_service_flows.py
  - tests/test_governance_api.py
  - .gsd/milestones/M006/slices/S02/tasks/T02-SUMMARY.md
key_decisions:
  - Reused GovernanceStore.summarize_calibration_evidence() directly in policy simulation so replay and runtime admin surfaces share one calibration vocabulary.
duration: ""
verification_result: passed
completed_at: 2026-04-02T03:27:47.569Z
blocker_discovered: false
---

# T02: Added shared calibration evidence summaries to admin policy simulation responses and aligned backend/console typing around the replay-window contract.

**Added shared calibration evidence summaries to admin policy simulation responses and aligned backend/console typing around the replay-window contract.**

## What Happened

Extended the policy simulation response model to include the shared CalibrationEvidenceSummary contract, then updated PolicySimulationService to derive that summary directly from GovernanceStore for the same tenant/window replay request instead of inventing replay-only classification logic. Mirrored the contract in console admin API types so downstream UI code can consume one bounded summary shape. Added focused service and admin API tests proving replay responses preserve oldest-first deterministic sampling, report thin window state correctly, and distinguish rollout-disabled calibration evidence from degraded or missing replay signals.

## Verification

Ran `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` successfully after aligning the fake simulation store helper with the real summary contract. Re-ran `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` after tightening endpoint assertions and it passed. LSP diagnostics were clean for the touched Python files.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` | 0 | ✅ pass | 7900ms |
| 2 | `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` | 0 | ✅ pass | 3200ms |
| 3 | `lsp diagnostics src/nebula/models/governance.py` | 0 | ✅ pass | 0ms |
| 4 | `lsp diagnostics src/nebula/services/policy_simulation_service.py` | 0 | ✅ pass | 0ms |
| 5 | `lsp diagnostics tests/test_service_flows.py` | 0 | ✅ pass | 0ms |


## Deviations

None.

## Known Issues

`tests/test_governance_api.py` still has a pre-existing duplicate test definition warning unrelated to this task’s changes.

## Files Created/Modified

- `src/nebula/models/governance.py`
- `src/nebula/services/policy_simulation_service.py`
- `console/src/lib/admin-api.ts`
- `tests/test_service_flows.py`
- `tests/test_governance_api.py`
- `.gsd/milestones/M006/slices/S02/tasks/T02-SUMMARY.md`


## Deviations
None.

## Known Issues
`tests/test_governance_api.py` still has a pre-existing duplicate test definition warning unrelated to this task’s changes.
