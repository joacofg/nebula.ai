---
id: T02
parent: S01
milestone: M009
key_files:
  - src/nebula/services/governance_store.py
  - tests/test_service_flows.py
key_decisions:
  - Made `GovernanceStore.summarize_calibration_evidence()` the authoritative summary seam for degraded/thin/stale/sufficient classification and stopped duplicating that logic in the service-flow fake store.
  - Kept degraded reasons split between `degraded_replay_signals` and `missing_route_signals`, while making summary-state precedence explicit: once sufficiency is met, degraded outranks stale to preserve honest operator/replay diagnosis.
duration: 
verification_result: passed
completed_at: 2026-04-27T14:49:53.618Z
blocker_discovered: false
---

# T02: Centralized ledger-backed outcome-evidence summarization in GovernanceStore with explicit degraded precedence and shared backend test coverage.

**Centralized ledger-backed outcome-evidence summarization in GovernanceStore with explicit degraded precedence and shared backend test coverage.**

## What Happened

Updated `src/nebula/services/governance_store.py` so tenant-scoped calibration summarization still uses the existing bounded ledger read path (`limit`, optional `from_timestamp`/`to_timestamp`) but now computes summary state with explicit degraded semantics. Eligible rows are still separated from excluded override rows and gated calibration-disabled rows, while degraded eligible rows remain counted and reasoned independently from sufficient calibrated rows. The state machine now takes `degraded_request_count` into account: no sufficient rows stays `thin`, below-threshold sufficient rows stays `thin`, degraded eligible evidence wins over freshness once the sufficiency threshold is met, and only fully sufficient non-degraded windows can become `stale` or `sufficient`. Added an inline precedence comment so downstream slices can rely on the stale-vs-degraded rule without rediscovering it.

In `tests/test_service_flows.py`, removed the duplicated hand-built summary implementation from `FakeSimulationGovernanceStore` and delegated its `summarize_calibration_evidence()` path into the real governance-store helper methods and constants. That keeps policy-simulation and store-level tests pinned to the shipped summarizer instead of a drifting fake. Expanded coverage to assert exact gated/degraded reason counts and added a tenant/window scoping test proving out-of-window and other-tenant rows do not contaminate the summary. Existing API-level calibration summary coverage in `tests/test_governance_api.py` continued to pass against the same seam.

## Verification

Ran the task-plan verification target against `tests/test_service_flows.py` using the project virtualenv, then ran a focused governance API regression that exercises the same `calibration_summary` payload seam. Both passed. LSP diagnostics for the edited store and test file were clean, confirming the deterministic ledger summarization changes and the delegated fake-store test harness compile without issues.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_service_flows.py -k "governance_store_calibration_summary or calibration_summary"` | 0 | ✅ pass | 690ms |
| 2 | `./.venv/bin/pytest tests/test_governance_api.py -k "calibration_summary or policy_simulation_returns_summary"` | 0 | ✅ pass | 720ms |

## Deviations

Used `./.venv/bin/pytest` instead of bare `pytest` because the shell environment did not expose pytest on PATH. Also replaced the hand-rolled FakeSimulationGovernanceStore summary derivation with delegation into the real GovernanceStore seam so verification covered the shipped implementation rather than a duplicate test-only copy.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/services/governance_store.py`
- `tests/test_service_flows.py`
