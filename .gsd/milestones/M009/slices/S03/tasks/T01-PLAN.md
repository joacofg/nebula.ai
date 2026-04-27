---
estimated_steps: 6
estimated_files: 3
skills_used: []
---

# T01: Wire tenant-window outcome evidence into replay evaluation

Add the replay propagation seam that keeps runtime and simulation on one routing contract.

Steps:
1. Extend `PolicyService.evaluate()` so replay callers can supply an explicit calibration/outcome evidence summary override instead of forcing replay to skip evidence lookup whenever `replay_context` is present.
2. In `PolicySimulationService.simulate()`, compute the tenant-window `calibration_summary` once for the requested replay window before the row loop, pass that same summary into every replayed `PolicyService.evaluate()` call, and return the exact same summary object in the response payload.
3. Preserve current bounded replay behavior: still use `before_timestamp` for spend-window guardrails, keep synthetic prompt reconstruction only as a fallback for missing persisted signals, and do not add a replay-only scoring branch or duplicate evidence classification outside `GovernanceStore.summarize_calibration_evidence()`.
4. Update or add focused backend service tests that prove replay now carries `outcome_evidence=...` vocabulary in `simulated_policy_outcome`, that a low-complexity replay can change for the same evidence-driven reason as live runtime, and that missing replay signals still produce degraded route mode honestly under the shared evidence summary.

## Inputs

- ``src/nebula/services/policy_service.py``
- ``src/nebula/services/policy_simulation_service.py``
- ``src/nebula/services/governance_store.py``
- ``src/nebula/services/router_service.py``
- ``src/nebula/models/governance.py``
- ``tests/test_service_flows.py``

## Expected Output

- ``src/nebula/services/policy_service.py``
- ``src/nebula/services/policy_simulation_service.py``
- ``tests/test_service_flows.py``

## Verification

./.venv/bin/pytest tests/test_service_flows.py -k "policy_simulation and (outcome or replay or degraded or parity or hard_budget)"

## Observability Impact

Keeps replay failure diagnosis request-first: future agents can inspect `simulated_policy_outcome`, `simulated_route_mode`, and returned `calibration_summary` together to see whether parity drift came from missing persisted signals, budget-window timing, or shared evidence-state classification.
