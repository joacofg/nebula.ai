---
id: T01
parent: S01
milestone: M005
provides: []
requires: []
affects: []
key_files: ["src/nebula/services/router_service.py", "src/nebula/services/policy_service.py", "tests/test_router_signals.py", "tests/test_response_headers.py", "tests/test_governance_runtime_hardening.py", "tests/test_reference_migration.py", "tests/test_benchmarking.py", "tests/test_admin_playground_api.py", "tests/test_governance_api.py", ".gsd/milestones/M005/slices/S01/tasks/T01-SUMMARY.md"]
key_decisions: ["Kept override routes signal-free with default score 0.0 and limited structured signals to heuristic token-complexity decisions.", "Preserved existing policy-denial data semantics where response headers expose attempted route metadata while ledger rows record terminal denied outcomes."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Verified the new route-signal behavior with `./.venv/bin/pytest tests/test_router_signals.py ... -x`, which passed after implementation and covered RouteDecision defaults, token counts, complexity tiers, model-constraint signals, and score behavior. Verified compatibility across existing backend paths with `./.venv/bin/pytest tests/test_router_signals.py tests/test_chat_completions.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_governance_runtime_hardening.py tests/test_response_headers.py tests/test_reference_migration.py tests/test_benchmarking.py tests/test_service_flows.py -x`, which passed with 54 tests green. Initial attempts using bare `pytest` failed because pytest was not on PATH, and the task-plan verification command failed because `tests/test_admin.py` / `tests/test_governance.py` do not exist locally; both issues were documented and corrected by using the repo venv and the actual test module names."
completed_at: 2026-03-28T02:44:13.894Z
blocker_discovered: false
---

# T01: Added scored route-signal metadata to heuristic routing decisions and threaded tenant policy through router resolution.

> Added scored route-signal metadata to heuristic routing decisions and threaded tenant policy through router resolution.

## What Happened
---
id: T01
parent: S01
milestone: M005
key_files:
  - src/nebula/services/router_service.py
  - src/nebula/services/policy_service.py
  - tests/test_router_signals.py
  - tests/test_response_headers.py
  - tests/test_governance_runtime_hardening.py
  - tests/test_reference_migration.py
  - tests/test_benchmarking.py
  - tests/test_admin_playground_api.py
  - tests/test_governance_api.py
  - .gsd/milestones/M005/slices/S01/tasks/T01-SUMMARY.md
key_decisions:
  - Kept override routes signal-free with default score 0.0 and limited structured signals to heuristic token-complexity decisions.
  - Preserved existing policy-denial data semantics where response headers expose attempted route metadata while ledger rows record terminal denied outcomes.
duration: ""
verification_result: mixed
completed_at: 2026-03-28T02:44:13.895Z
blocker_discovered: false
---

# T01: Added scored route-signal metadata to heuristic routing decisions and threaded tenant policy through router resolution.

**Added scored route-signal metadata to heuristic routing decisions and threaded tenant policy through router resolution.**

## What Happened

Extended the router’s heuristic decision model to emit structured route signals and a normalized score while preserving backward compatibility for all existing RouteDecision construction sites. Replaced the old char-count/simple-prompt reason split with token-estimate-based complexity routing under the single `token_complexity` reason code, added a helper token estimator, and threaded the tenant policy object through PolicyService.resolve so model-constraint and future budget signals can be computed at routing time. Added focused router-signal unit tests and then updated stale backend tests that still encoded retired route reasons, outdated premium-model aliases, or older denial-record assumptions so verification matched the current runtime contract.

## Verification

Verified the new route-signal behavior with `./.venv/bin/pytest tests/test_router_signals.py ... -x`, which passed after implementation and covered RouteDecision defaults, token counts, complexity tiers, model-constraint signals, and score behavior. Verified compatibility across existing backend paths with `./.venv/bin/pytest tests/test_router_signals.py tests/test_chat_completions.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_governance_runtime_hardening.py tests/test_response_headers.py tests/test_reference_migration.py tests/test_benchmarking.py tests/test_service_flows.py -x`, which passed with 54 tests green. Initial attempts using bare `pytest` failed because pytest was not on PATH, and the task-plan verification command failed because `tests/test_admin.py` / `tests/test_governance.py` do not exist locally; both issues were documented and corrected by using the repo venv and the actual test module names.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `pytest tests/test_router_signals.py::test_route_decision_carries_signals tests/test_router_signals.py::test_token_count_signal_from_prompt tests/test_router_signals.py::test_budget_proximity_signal tests/test_router_signals.py::test_model_constraint_signal tests/test_router_signals.py::test_score_by_complexity_tier tests/test_chat_completions.py tests/test_admin.py tests/test_governance.py tests/test_response_headers.py tests/test_governance_runtime_hardening.py tests/test_reference_migration.py tests/test_benchmarking.py tests/test_service_flows.py -x` | 127 | ❌ fail | 100ms |
| 2 | `./.venv/bin/pytest tests/test_router_signals.py::test_route_decision_carries_signals tests/test_router_signals.py::test_token_count_signal_from_prompt tests/test_router_signals.py::test_budget_proximity_signal tests/test_router_signals.py::test_model_constraint_signal tests/test_router_signals.py::test_score_by_complexity_tier tests/test_chat_completions.py tests/test_response_headers.py tests/test_governance_runtime_hardening.py tests/test_reference_migration.py tests/test_benchmarking.py tests/test_service_flows.py -x` | 0 | ✅ pass | 1100ms |
| 3 | `./.venv/bin/pytest tests/test_chat_completions.py tests/test_admin.py tests/test_governance.py -x` | 4 | ❌ fail | 100ms |
| 4 | `./.venv/bin/pytest tests/test_router_signals.py tests/test_chat_completions.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_governance_runtime_hardening.py tests/test_response_headers.py tests/test_reference_migration.py tests/test_benchmarking.py tests/test_service_flows.py -x` | 0 | ✅ pass | 1970ms |


## Deviations

The task plan’s verification command referenced `tests/test_admin.py` and `tests/test_governance.py`, but those files do not exist in this workspace. I adapted verification to the actual split modules present locally: `tests/test_admin_playground_api.py`, `tests/test_governance_api.py`, and `tests/test_governance_runtime_hardening.py`. I also normalized several stale tests that still asserted retired route reasons or older premium-model alias assumptions.

## Known Issues

`budget_proximity` is intentionally present but remains `None` until downstream work threads spend context into the route signals. Slice-level persistence, header, UI, and vocabulary work remain for later tasks.

## Files Created/Modified

- `src/nebula/services/router_service.py`
- `src/nebula/services/policy_service.py`
- `tests/test_router_signals.py`
- `tests/test_response_headers.py`
- `tests/test_governance_runtime_hardening.py`
- `tests/test_reference_migration.py`
- `tests/test_benchmarking.py`
- `tests/test_admin_playground_api.py`
- `tests/test_governance_api.py`
- `.gsd/milestones/M005/slices/S01/tasks/T01-SUMMARY.md`


## Deviations
The task plan’s verification command referenced `tests/test_admin.py` and `tests/test_governance.py`, but those files do not exist in this workspace. I adapted verification to the actual split modules present locally: `tests/test_admin_playground_api.py`, `tests/test_governance_api.py`, and `tests/test_governance_runtime_hardening.py`. I also normalized several stale tests that still asserted retired route reasons or older premium-model alias assumptions.

## Known Issues
`budget_proximity` is intentionally present but remains `None` until downstream work threads spend context into the route signals. Slice-level persistence, header, UI, and vocabulary work remain for later tasks.
