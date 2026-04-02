---
estimated_steps: 6
estimated_files: 5
skills_used: []
---

# T02: Thread calibration evidence through admin policy simulation

Reuse the new summary contract in the replay path so policy simulation describes calibration evidence with the same ledger-backed semantics as runtime-facing admin data.

Steps:
1. Extend `src/nebula/services/policy_simulation_service.py` and `src/nebula/api/routes/admin.py` so simulation responses include or reference the shared calibration summary/evidence state for the replay window instead of inventing separate replay-only logic.
2. Mirror the backend contract in `console/src/lib/admin-api.ts` so the console can consume the same summary shape without ad hoc typing.
3. Add focused backend API coverage in `tests/test_governance_api.py` and service-level coverage in `tests/test_service_flows.py` proving simulation reports the same sufficient/thin/stale semantics, preserves oldest-first replay determinism, and surfaces rollout-disabled calibration evidence distinctly from missing-data degradation.
4. Keep the admin surface narrow: extend existing simulation/admin payloads only as needed, and avoid creating a broad new API family or analytics endpoint unless the shared contract cannot fit the current seams.

## Inputs

- `src/nebula/models/governance.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/policy_simulation_service.py`
- `src/nebula/api/routes/admin.py`
- `console/src/lib/admin-api.ts`
- `tests/test_service_flows.py`
- `tests/test_governance_api.py`

## Expected Output

- `src/nebula/services/policy_simulation_service.py`
- `src/nebula/api/routes/admin.py`
- `console/src/lib/admin-api.ts`
- `tests/test_service_flows.py`
- `tests/test_governance_api.py`

## Verification

./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x

## Observability Impact

Makes replay-window calibration state inspectable through the existing admin simulation surface and keeps approximation notes aligned with the shared evidence contract.
