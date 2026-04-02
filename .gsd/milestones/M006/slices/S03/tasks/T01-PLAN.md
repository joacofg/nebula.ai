---
estimated_steps: 6
estimated_files: 4
skills_used: []
---

# T01: Extend the simulation changed-request contract with routing parity fields

Add the smallest backend contract needed for S03: extend `PolicySimulationChangedRequest` and the simulation service so replay changed-request samples carry the same calibrated/degraded/gated semantics that runtime already persists in `route_signals` and headers. Keep the vocabulary aligned to S01/S02 and preserve explicit null mode when calibrated routing is gated.

Steps:
1. Update the typed governance models in `src/nebula/models/governance.py` to add baseline/simulated parity fields for route mode, calibrated/degraded booleans, and route score on `PolicySimulationChangedRequest`, keeping gated rows explicit as null mode rather than synthesizing fake route signals.
2. Wire `src/nebula/services/policy_simulation_service.py` to derive baseline parity values from persisted ledger `route_signals` and simulated parity values from `PolicyEvaluation.route_decision`, including unchanged route targets that still count as changed because policy outcome or projected cost changed.
3. Mirror the contract in `console/src/lib/admin-api.ts` so the console uses the same field names and nullability as the backend response.
4. Add or update focused service-level assertions in `tests/test_service_flows.py` for the changed-request payload shape so later tasks can rely on the parity fields instead of re-deriving them in the UI.

## Inputs

- `src/nebula/models/governance.py`
- `src/nebula/services/policy_simulation_service.py`
- `console/src/lib/admin-api.ts`
- `tests/test_service_flows.py`
- `tests/test_router_signals.py`

## Expected Output

- `src/nebula/models/governance.py`
- `src/nebula/services/policy_simulation_service.py`
- `console/src/lib/admin-api.ts`
- `tests/test_service_flows.py`

## Verification

./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x

## Observability Impact

Changes the simulation payload that operators and future agents inspect during replay debugging; the task should keep parity fields bounded, explicit, and null-safe for gated paths.
