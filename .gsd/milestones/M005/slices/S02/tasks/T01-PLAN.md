---
estimated_steps: 1
estimated_files: 7
skills_used: []
---

# T01: Build the ledger replay simulation contract and backend service

Add simulation request/response models to `src/nebula/models/governance.py`, including window metadata, aggregate outcome counts, and a bounded changed-request sample that echoes baseline vs simulated route/policy outcomes. Create `src/nebula/services/policy_simulation_service.py` as a replay-only service that loads recent `UsageLedgerRecord`s for one tenant, derives replay inputs from persisted route signals/ledger metadata, reuses existing policy and routing semantics where possible, and documents the signal-driven approximation where prompt text is unavailable. Extend the router/policy seams only as needed to support signal-based replay and projected premium-cost evaluation without provider execution, then wire the new service through `src/nebula/core/container.py`. Add focused service tests in `tests/test_service_flows.py` covering route-target changes, newly denied outcomes, tenant/window scoping, empty windows, and the guarantee that simulation does not persist policy or usage changes.

## Inputs

- ``src/nebula/models/governance.py``
- ``src/nebula/services/router_service.py``
- ``src/nebula/services/policy_service.py``
- ``src/nebula/services/governance_store.py``
- ``src/nebula/core/container.py``
- ``tests/test_service_flows.py``

## Expected Output

- ``src/nebula/models/governance.py``
- ``src/nebula/services/policy_simulation_service.py``
- ``src/nebula/services/router_service.py``
- ``src/nebula/services/policy_service.py``
- ``src/nebula/services/governance_store.py``
- ``src/nebula/core/container.py``
- ``tests/test_service_flows.py``

## Verification

./.venv/bin/pytest tests/test_service_flows.py -k simulation -x

## Observability Impact

- Signals added/changed: typed simulation summary fields for evaluated rows, changed routes, newly denied requests, and cost delta.
- How a future agent inspects this: run `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x` and inspect the simulation response models.
- Failure state exposed: replay mismatches, tenant/time-window scoping bugs, and accidental mutation of ledger/policy state become explicit test failures.
