---
estimated_steps: 6
estimated_files: 3
skills_used: []
---

# T03: Prove replay-facing and admin summary consumers honor the new contract

Close the slice by proving that the richer evidence contract survives through existing backend consumers without changing live route choice yet. This gives S02/S03 a stable integration seam and catches accidental drift between typed models, summary derivation, and simulation/admin responses.

Steps:
1. Update replay/admin-facing tests to assert the summary contract shape and semantics exposed through policy simulation and governance APIs still serialize correctly and remain bounded to persisted ledger metadata.
2. Verify that request rows with suppressed or degraded `route_signals` surface honest degraded summary reasons instead of being silently counted as thin/sufficient evidence.
3. Keep assertions focused on contract stability and replay-safe payloads; do not introduce live routing behavior changes in this slice.
4. If needed, add narrowly scoped fixtures/helpers to keep the new evidence-state assertions readable for downstream slices.

## Inputs

- ``src/nebula/services/policy_simulation_service.py``
- ``tests/test_governance_api.py``
- ``tests/test_service_flows.py``
- ``src/nebula/services/governance_store.py``
- ``src/nebula/models/governance.py``

## Expected Output

- ``tests/test_governance_api.py``
- ``tests/test_service_flows.py``

## Verification

pytest tests/test_governance_api.py -k "calibration_summary or policy_simulation" && pytest tests/test_service_flows.py -k "policy_simulation_exposes_window_calibration_summary"

## Observability Impact

Locks the existing admin/policy-simulation inspection surfaces to the new summary semantics so later failures can be diagnosed from serialized payloads, not just internal store behavior.
