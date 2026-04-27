---
id: T01
parent: S03
milestone: M009
key_files:
  - src/nebula/services/policy_service.py
  - src/nebula/services/policy_simulation_service.py
  - tests/test_service_flows.py
key_decisions:
  - Allowed replay callers to inject a CalibrationEvidenceSummary override into PolicyService.evaluate() instead of coupling evidence lookup to the absence of replay_context.
  - Computed the tenant-window calibration summary once per simulation request and reused that same object for every replay row and the final response payload to avoid evidence-classification drift.
duration: 
verification_result: passed
completed_at: 2026-04-27T21:06:04.498Z
blocker_discovered: false
---

# T01: Reused one tenant-window outcome evidence summary across policy simulation replay and verified parity/degraded diagnostics

**Reused one tenant-window outcome evidence summary across policy simulation replay and verified parity/degraded diagnostics**

## What Happened

Updated the replay evaluation seam so PolicyService.evaluate() accepts an explicit evidence summary override, letting replay callers reuse tenant-window outcome evidence instead of implicitly dropping evidence whenever replay_context is present. In PolicySimulationService.simulate(), I now compute the tenant-window calibration_summary once before the replay loop, pass that exact object into every replayed evaluation, and return the same object in the response payload. I added focused service-flow coverage proving replay now emits shared outcome_evidence=sufficient/degraded vocabulary in simulated_policy_outcome, that a low-complexity replay can flip for the same evidence-driven reason as runtime under a sufficient summary, and that missing replay signals still surface degraded route mode honestly under the shared summary. During verification I corrected the new fixtures to match the actual replay scoring path, which reconstructs prompts from persisted signals before the router computes replay scores.

## Verification

Ran the slice task verification command `./.venv/bin/pytest tests/test_service_flows.py -k "policy_simulation and (outcome or replay or degraded or parity or hard_budget)"` after updating the replay seam and test fixtures. The focused suite passed with 5 tests covering hard-budget replay windows, shared outcome-evidence propagation, evidence-driven parity changes, degraded replay honesty, and window-scoped calibration summary diagnostics.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_service_flows.py -k "policy_simulation and (outcome or replay or degraded or parity or hard_budget)"` | 0 | ✅ pass | 780ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/services/policy_service.py`
- `src/nebula/services/policy_simulation_service.py`
- `tests/test_service_flows.py`
