---
id: T01
parent: S02
milestone: M005
provides: []
requires: []
affects: []
key_files: ["src/nebula/models/governance.py", "src/nebula/services/policy_simulation_service.py", "src/nebula/services/policy_service.py", "src/nebula/services/router_service.py", "src/nebula/services/governance_store.py", "src/nebula/core/container.py", "tests/test_service_flows.py", ".gsd/milestones/M005/slices/S02/tasks/T01-SUMMARY.md"]
key_decisions: ["Reused production policy/router semantics through a non-mutating evaluation seam instead of duplicating simulation logic.", "Made replay explicitly signal-driven because ledger rows do not retain raw prompt text, and documented that approximation in the simulation response."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x` three times. The first failure was a changed-request ordering assertion mismatch caused by intentional oldest-first replay after newest-first store fetches; updated the test to match the real chronological sampling contract. The second failure showed that unchanged routing can still appear in the changed sample when projected premium cost changes; updated the assertion to verify cost-delta visibility instead. The final run passed all four simulation-focused tests, confirming typed summary fields, scoping, denial handling, and non-mutation behavior."
completed_at: 2026-03-28T03:06:19.416Z
blocker_discovered: false
---

# T01: Added typed policy simulation models and a replay-only service that re-evaluates recent tenant ledger traffic without mutating policy or usage state.

> Added typed policy simulation models and a replay-only service that re-evaluates recent tenant ledger traffic without mutating policy or usage state.

## What Happened
---
id: T01
parent: S02
milestone: M005
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/policy_simulation_service.py
  - src/nebula/services/policy_service.py
  - src/nebula/services/router_service.py
  - src/nebula/services/governance_store.py
  - src/nebula/core/container.py
  - tests/test_service_flows.py
  - .gsd/milestones/M005/slices/S02/tasks/T01-SUMMARY.md
key_decisions:
  - Reused production policy/router semantics through a non-mutating evaluation seam instead of duplicating simulation logic.
  - Made replay explicitly signal-driven because ledger rows do not retain raw prompt text, and documented that approximation in the simulation response.
duration: ""
verification_result: mixed
completed_at: 2026-03-28T03:06:19.417Z
blocker_discovered: false
---

# T01: Added typed policy simulation models and a replay-only service that re-evaluates recent tenant ledger traffic without mutating policy or usage state.

**Added typed policy simulation models and a replay-only service that re-evaluates recent tenant ledger traffic without mutating policy or usage state.**

## What Happened

Added policy simulation DTOs to the governance models, created a replay-only policy simulation service, and wired it into the service container. The service loads recent tenant-scoped ledger rows, reconstructs approximate replay requests from stored route signals and request metadata, and reuses router/policy logic through new non-mutating evaluation seams. Extended RouterService with replay-aware signal-based routing and PolicyService with an exception-free evaluation path that returns denial and projected premium-cost outcomes for simulation while preserving existing runtime resolve behavior. Added focused service tests covering route changes, newly denied premium requests, tenant/window scoping, empty windows, signal-driven replay behavior, and the guarantee that simulation does not persist policy or usage changes.

## Verification

Ran `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x` three times. The first failure was a changed-request ordering assertion mismatch caused by intentional oldest-first replay after newest-first store fetches; updated the test to match the real chronological sampling contract. The second failure showed that unchanged routing can still appear in the changed sample when projected premium cost changes; updated the assertion to verify cost-delta visibility instead. The final run passed all four simulation-focused tests, confirming typed summary fields, scoping, denial handling, and non-mutation behavior.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x` | 1 | ❌ fail | 1000ms |
| 2 | `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x` | 1 | ❌ fail | 1000ms |
| 3 | `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x` | 0 | ✅ pass | 1000ms |


## Deviations

None.

## Known Issues

Simulation is intentionally approximate because raw prompt text is not stored in the ledger; replay reconstructs request complexity from persisted route signals and token metadata.

## Files Created/Modified

- `src/nebula/models/governance.py`
- `src/nebula/services/policy_simulation_service.py`
- `src/nebula/services/policy_service.py`
- `src/nebula/services/router_service.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/core/container.py`
- `tests/test_service_flows.py`
- `.gsd/milestones/M005/slices/S02/tasks/T01-SUMMARY.md`


## Deviations
None.

## Known Issues
Simulation is intentionally approximate because raw prompt text is not stored in the ledger; replay reconstructs request complexity from persisted route signals and token metadata.
