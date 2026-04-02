---
id: T02
parent: S03
milestone: M006
provides: []
requires: []
affects: []
key_files: ["tests/test_governance_api.py", "tests/test_service_flows.py", ".gsd/milestones/M006/slices/S03/tasks/T02-SUMMARY.md"]
key_decisions: ["Prove degraded replay behavior at the admin boundary from a real runtime request plus ledger correlation instead of inventing degraded parity from a synthetic unchanged ledger stub."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the task-plan verification command. `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x` passed, `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` passed, and the combined rerun passed as well."
completed_at: 2026-04-02T03:52:26.657Z
blocker_discovered: false
---

# T02: Added runtime-to-replay parity tests that lock calibrated, degraded, and gated simulation semantics against live headers and usage-ledger evidence.

> Added runtime-to-replay parity tests that lock calibrated, degraded, and gated simulation semantics against live headers and usage-ledger evidence.

## What Happened
---
id: T02
parent: S03
milestone: M006
key_files:
  - tests/test_governance_api.py
  - tests/test_service_flows.py
  - .gsd/milestones/M006/slices/S03/tasks/T02-SUMMARY.md
key_decisions:
  - Prove degraded replay behavior at the admin boundary from a real runtime request plus ledger correlation instead of inventing degraded parity from a synthetic unchanged ledger stub.
duration: ""
verification_result: passed
completed_at: 2026-04-02T03:52:26.658Z
blocker_discovered: false
---

# T02: Added runtime-to-replay parity tests that lock calibrated, degraded, and gated simulation semantics against live headers and usage-ledger evidence.

**Added runtime-to-replay parity tests that lock calibrated, degraded, and gated simulation semantics against live headers and usage-ledger evidence.**

## What Happened

Extended tests/test_governance_api.py so simulation changed-request samples are now proven against real chat-completions headers and request-scoped usage-ledger rows. The calibrated path now asserts route target, route reason, route mode, calibrated/degraded booleans, and route score parity from runtime through persistence into replay. The gated path now proves the same correlation while preserving explicit null route-mode semantics when calibrated routing is disabled. I also kept tests/test_service_flows.py aligned to the actual changed-request contract after confirming that a synthetic unchanged ledger stub should not be sampled as a changed degraded row.

## Verification

Ran the task-plan verification command. `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x` passed, `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` passed, and the combined rerun passed as well.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x` | 0 | ✅ pass | 600ms |
| 2 | `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` | 0 | ✅ pass | 630ms |
| 3 | `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` | 0 | ✅ pass | 4500ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `tests/test_governance_api.py`
- `tests/test_service_flows.py`
- `.gsd/milestones/M006/slices/S03/tasks/T02-SUMMARY.md`


## Deviations
None.

## Known Issues
None.
