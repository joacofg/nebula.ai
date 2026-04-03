---
estimated_steps: 5
estimated_files: 6
skills_used: []
---

# T01: Align policy-options and simulation contracts with console preview needs

Update the admin policy contract so runtime-enforced fields truthfully include the semantic-cache tuning controls already edited in the console, then tighten backend/shared types and focused tests around bounded simulation comparison output. Use the existing admin route/model seams; do not widen the contract into analytics payloads or unbounded samples.

Steps:
1. Confirm and align `PolicyOptionsResponse` / `/v1/admin/policy/options` so runtime-enforced fields include the semantic-cache similarity-threshold and max-entry-age controls when they are live policy inputs.
2. Keep `PolicySimulationResponse` bounded and comparison-first by strengthening any shared type/test expectations needed for baseline-vs-simulated route/status/policy/cost evidence without adding dashboard-style aggregates.
3. Add or tighten focused pytest coverage around policy options and simulation so contract drift is caught at the admin boundary before console work lands.

## Inputs

- ``src/nebula/api/routes/admin.py``
- ``src/nebula/models/governance.py``
- ``src/nebula/services/policy_simulation_service.py``
- ``tests/test_governance_api.py``
- ``tests/test_service_flows.py``
- ``console/src/lib/admin-api.ts``

## Expected Output

- ``src/nebula/api/routes/admin.py``
- ``src/nebula/models/governance.py``
- ``src/nebula/services/policy_simulation_service.py``
- ``tests/test_governance_api.py``
- ``tests/test_service_flows.py``
- ``console/src/lib/admin-api.ts``

## Verification

./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x && ./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x

## Observability Impact

Locks the admin API contract with executable failure signals in pytest so later console regressions can be localized to backend contract drift instead of ambiguous UI behavior.
