---
estimated_steps: 6
estimated_files: 3
skills_used: []
---

# T02: Prove runtime and replay parity across calibrated, degraded, and gated paths

Lock the S03 requirement at the backend boundary with focused parity tests. Use real runtime requests plus replay over the same tenant traffic class so parity is proven from shipped behavior, not assumed from shared architecture.

Steps:
1. Extend `tests/test_governance_api.py` to assert that simulation changed-request entries expose the same route reason, route mode, calibrated/degraded flags, and route score semantics as the live request that produced the ledger row.
2. Cover three concrete scenarios: a calibrated live request that stays calibrated in replay, a degraded replay case where missing or partial persisted signals produce `route_mode="degraded"`, and a calibrated-routing-disabled gate where runtime and replay both expose `calibrated_routing_disabled` with null route mode.
3. Reuse the existing oldest-first replay ordering and current admin endpoint; do not add a new endpoint or widen persistence.
4. Keep assertions aligned to the current contract by pairing runtime headers and ledger rows with simulation response fields rather than asserting on copy alone.

## Inputs

- `tests/test_governance_api.py`
- `tests/test_service_flows.py`
- `src/nebula/services/policy_simulation_service.py`
- `src/nebula/services/policy_service.py`
- `src/nebula/services/router_service.py`

## Expected Output

- `tests/test_governance_api.py`
- `tests/test_service_flows.py`

## Verification

./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x

## Observability Impact

Strengthens the backend proof that replay diagnostics remain trustworthy by verifying parity fields against live headers and persisted ledger evidence, including failure-safe gated behavior.
