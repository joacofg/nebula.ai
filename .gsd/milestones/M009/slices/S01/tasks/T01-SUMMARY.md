---
id: T01
parent: S01
milestone: M009
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/router_service.py
  - tests/test_service_flows.py
  - tests/test_governance_api.py
key_decisions:
  - Preserved the existing `calibration_summary` field name for compatibility while redefining its `state` as the shared outcome-evidence contract.
  - Made degraded an explicit summary-state outcome with higher precedence than sufficient/stale when degraded eligible evidence exists in-window.
duration: 
verification_result: mixed
completed_at: 2026-04-27T14:45:37.991Z
blocker_discovered: false
---

# T01: Defined the shared outcome-evidence contract by extending calibration summaries with degraded state precedence and locking the seam with backend tests.

**Defined the shared outcome-evidence contract by extending calibration summaries with degraded state precedence and locking the seam with backend tests.**

## What Happened

Updated `src/nebula/models/governance.py` to make the existing `calibration_summary` seam explicitly carry the richer outcome-evidence vocabulary while preserving payload compatibility for downstream admin and replay consumers. Added inline compatibility notes so later slices keep using `calibration_summary` naming but treat its `state` as the shared outcome-evidence contract. Updated `src/nebula/services/router_service.py` comments to clarify that request-level `route_mode` remains the per-request parity seam while degraded can also surface as a summary-level outcome. In `tests/test_service_flows.py`, expanded the fake summary derivation to express the new precedence rule and added a focused contract test proving that degraded wins over sufficient/stale when degraded eligible rows coexist with enough calibrated evidence in the same window. Added an inline compatibility note in `tests/test_governance_api.py` so API readers know the field name remains stable while semantics grow richer.

## Verification

Ran the task-plan verification target with the project venv after discovering `pytest` was not on PATH, then ran a broader regression sweep over the touched backend seams. The focused contract command passed and proved the new degraded summary-state precedence; the broader suite covering governance API, router signals, and service flows also passed.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `pytest tests/test_service_flows.py -k "calibration_summary or outcome"` | 127 | ❌ fail | 0ms |
| 2 | `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or outcome"` | 0 | ✅ pass | 840ms |
| 3 | `./.venv/bin/pytest tests/test_governance_api.py tests/test_router_signals.py tests/test_service_flows.py` | 0 | ✅ pass | 16380ms |

## Deviations

Used `./.venv/bin/pytest` instead of bare `pytest` because the shell environment did not expose pytest on PATH. No contract or scope deviation beyond that execution-path adjustment.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/models/governance.py`
- `src/nebula/services/router_service.py`
- `tests/test_service_flows.py`
- `tests/test_governance_api.py`
