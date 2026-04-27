---
estimated_steps: 1
estimated_files: 5
skills_used: []
---

# T01: Extend router and policy seams for live outcome-grounded scoring

Add the shared runtime contract that lets live routing consume the S01 calibration summary without re-classifying evidence. Keep the change additive: extend the router breakdown/signals vocabulary with bounded outcome-grounded factors and teach `PolicyService.evaluate()` to fetch tenant-scoped evidence immediately before live route choice, while preserving explicit overrides, calibrated-routing disablement, hard-budget guardrails, and serializable parity-friendly signals. Record installed skills in frontmatter as `verify-before-complete` and `test` because executors must prove the new contract with real backend assertions before claiming the task is done.

## Inputs

- ``src/nebula/services/router_service.py``
- ``src/nebula/services/policy_service.py``
- ``src/nebula/models/governance.py``
- ``src/nebula/services/governance_store.py``
- ``tests/test_router_signals.py``
- ``tests/test_service_flows.py``

## Expected Output

- ``src/nebula/services/router_service.py``
- ``src/nebula/services/policy_service.py``
- ``src/nebula/models/governance.py``
- ``tests/test_router_signals.py``
- ``tests/test_service_flows.py``

## Verification

./.venv/bin/pytest tests/test_router_signals.py -k "outcome or evidence or route" && ./.venv/bin/pytest tests/test_service_flows.py -k "outcome_grounded or policy_service_live_evidence or hard_budget"

## Observability Impact

Expands persisted/request-visible route diagnostics with outcome-evidence state and additive score-factor details so later failures can be localized to summary lookup, scoring, or policy gating rather than just final target changes.
