---
estimated_steps: 10
estimated_files: 6
skills_used: []
---

# T02: Centralize hard-budget downgrade and denial semantics in PolicyService

Implement the real hard-budget behavior in `PolicyService.evaluate()` so runtime requests and simulation replays share one decision path for cumulative spend caps, downgrade-to-local when allowed, deny when premium is required, and persist explainable outcomes that preserve S01's override-route-signal discipline.

Steps:
1. Add focused runtime/service tests that cover cumulative spend exhaustion, local downgrade eligibility, explicit premium denial, and replay-window spend calculations using `before_timestamp`.
2. Update `PolicyService.evaluate()` (and only the minimum adjacent runtime plumbing it truly needs) to compute spend-cap state from `tenant_spend_total`, choose downgrade vs deny deterministically, and emit stable `policy_outcome` / budget evidence.
3. Confirm simulation replay inherits the exact same semantics through `PolicySimulationService` without introducing a second budget engine.

Must-haves:
- [ ] Runtime and simulation both rely on `PolicyService.evaluate()` for hard-budget decisions.
- [ ] When cumulative spend cap is exhausted, auto-routed traffic downgrades to local when compatible instead of failing ambiguously.
- [ ] Explicit premium or premium-only cases deny with exact operator-readable detail when downgrade is impossible or disallowed.
- [ ] Soft-budget advisory behavior remains non-blocking and distinct from the new hard guardrails.

## Inputs

- ``src/nebula/services/policy_service.py``
- ``src/nebula/services/policy_simulation_service.py``
- ``src/nebula/services/router_service.py``
- ``src/nebula/services/governance_store.py``
- ``tests/test_governance_runtime_hardening.py``
- ``tests/test_service_flows.py``
- ``tests/test_governance_api.py``

## Expected Output

- ``src/nebula/services/policy_service.py``
- ``src/nebula/services/policy_simulation_service.py``
- ``src/nebula/services/router_service.py``
- ``tests/test_governance_runtime_hardening.py``
- ``tests/test_service_flows.py``
- ``tests/test_governance_api.py``

## Verification

./.venv/bin/pytest tests/test_governance_runtime_hardening.py tests/test_service_flows.py -k "budget or simulation or runtime_policy" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "guardrail or policy_denied or simulation" -x

## Observability Impact

- Signals added/changed: `policy_outcome`, denial detail, terminal status, and any budget evidence attached to route signals for persisted ledger rows and simulation output.
- How a future agent inspects this: replay the focused pytest suites and inspect `/v1/admin/usage/ledger?request_id=...` or simulation responses for downgrade-vs-deny explanation.
- Failure state exposed: exact denial detail and recorded route/policy fields should make incorrect downgrade/deny behavior diagnosable without raw prompt access.
