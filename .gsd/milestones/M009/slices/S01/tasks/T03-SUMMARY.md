---
id: T03
parent: S01
milestone: M009
key_files:
  - tests/test_governance_api.py
  - tests/test_service_flows.py
key_decisions:
  - Strengthened replay/admin contract coverage entirely in tests, preserving live routing behavior while proving degraded and suppressed ledger metadata stays visible through serialized calibration summaries.
  - Used a synthetic suppressed ledger copy in the admin API test to prove missing route_signals serialize as degraded evidence with replay-safe null parity fields instead of being misclassified or backfilled.
duration: 
verification_result: passed
completed_at: 2026-04-27T15:00:07.716Z
blocker_discovered: false
---

# T03: Locked policy simulation and admin tests to honor degraded and suppressed outcome-evidence summaries without changing routing behavior.

**Locked policy simulation and admin tests to honor degraded and suppressed outcome-evidence summaries without changing routing behavior.**

## What Happened

Updated replay-facing and admin-facing backend tests to lock the shared outcome-evidence contract at consumer boundaries. In `tests/test_governance_api.py`, I expanded policy simulation coverage so the admin payload continues to expose `calibration_summary` for compatibility while proving that persisted explicit-premium rows remain excluded, persisted calibrated rows remain sufficient, and a synthetic persisted row with suppressed `route_signals` is counted as degraded with the `missing_route_signals` reason. I also asserted that replay samples for suppressed rows keep route-mode parity fields null, preventing admin/replay consumers from inventing calibrated metadata not present in the ledger. In `tests/test_service_flows.py`, I extended the simulation-level contract test to cover both degraded replay signals and missing route signals in the same summary window while preserving thin-state precedence when sufficiency is not met. No production routing or store logic changed; this task solely tightened the tests around the already-shipped summary seam.

## Verification

Ran the task-plan verification commands against the project venv and confirmed both consumer seams honor the shared outcome-evidence contract. `tests/test_governance_api.py` now passes with policy simulation assertions that serialized `calibration_summary` payloads expose thin/degraded semantics, excluded/degraded reason counts, replay-safe null parity fields for suppressed route signals, and unchanged persisted policy state. `tests/test_service_flows.py` now passes with simulation-level coverage proving window summaries include both `degraded_replay_signals` and `missing_route_signals` while preserving thin-state precedence before sufficiency is reached.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_governance_api.py -k "calibration_summary or policy_simulation" -q` | 0 | ✅ pass | 1290ms |
| 2 | `./.venv/bin/pytest tests/test_service_flows.py -k "policy_simulation_exposes_window_calibration_summary" -q` | 0 | ✅ pass | 620ms |
| 3 | `./.venv/bin/pytest tests/test_governance_api.py -k "calibration_summary or policy_simulation" && ./.venv/bin/pytest tests/test_service_flows.py -k "policy_simulation_exposes_window_calibration_summary"` | 0 | ✅ pass | 1850ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `tests/test_governance_api.py`
- `tests/test_service_flows.py`
