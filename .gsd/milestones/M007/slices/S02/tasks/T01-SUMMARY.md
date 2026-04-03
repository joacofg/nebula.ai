---
id: T01
parent: S02
milestone: M007
provides: []
requires: []
affects: []
key_files: ["src/nebula/api/routes/admin.py", "src/nebula/models/governance.py", "src/nebula/services/policy_simulation_service.py", "tests/test_governance_api.py", "tests/test_service_flows.py", ".gsd/milestones/M007/slices/S02/tasks/T01-SUMMARY.md"]
key_decisions: ["Kept policy simulation comparison-first by tightening bounds and tests around the existing route/status/policy/cost evidence instead of widening the response into dashboard-style aggregates.", "Resolved contract drift at the backend admin boundary rather than changing console types that were already aligned with the intended policy-preview contract."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the task-plan verification commands successfully: `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x` and `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x`. Also ran LSP diagnostics on the touched backend and test files; no new diagnostics were introduced. One pre-existing Ruff/LSP warning remains in `tests/test_governance_api.py` for a duplicate embeddings test definition unrelated to this task."
completed_at: 2026-04-03T02:10:02.512Z
blocker_discovered: false
---

# T01: Aligned admin policy options with cache tuning controls and tightened bounded simulation contract coverage.

> Aligned admin policy options with cache tuning controls and tightened bounded simulation contract coverage.

## What Happened
---
id: T01
parent: S02
milestone: M007
key_files:
  - src/nebula/api/routes/admin.py
  - src/nebula/models/governance.py
  - src/nebula/services/policy_simulation_service.py
  - tests/test_governance_api.py
  - tests/test_service_flows.py
  - .gsd/milestones/M007/slices/S02/tasks/T01-SUMMARY.md
key_decisions:
  - Kept policy simulation comparison-first by tightening bounds and tests around the existing route/status/policy/cost evidence instead of widening the response into dashboard-style aggregates.
  - Resolved contract drift at the backend admin boundary rather than changing console types that were already aligned with the intended policy-preview contract.
duration: ""
verification_result: passed
completed_at: 2026-04-03T02:10:02.514Z
blocker_discovered: false
---

# T01: Aligned admin policy options with cache tuning controls and tightened bounded simulation contract coverage.

**Aligned admin policy options with cache tuning controls and tightened bounded simulation contract coverage.**

## What Happened

Updated the admin policy-options contract so runtime-enforced fields now include the live semantic-cache tuning controls already edited in the console. Tightened shared governance models for policy simulation by bounding approximation notes and changed-request samples and constraining cost fields to non-negative values, while preserving the existing comparison-first route/status/policy/cost shape. Strengthened focused pytest coverage at the admin boundary and model layer, including policy-options classification checks and bounded simulation-request validation, and corrected stale simulation assertions to current inclusive replay-window and policy-outcome behavior.

## Verification

Ran the task-plan verification commands successfully: `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x` and `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x`. Also ran LSP diagnostics on the touched backend and test files; no new diagnostics were introduced. One pre-existing Ruff/LSP warning remains in `tests/test_governance_api.py` for a duplicate embeddings test definition unrelated to this task.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x` | 0 | ✅ pass | 5400ms |
| 2 | `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x` | 0 | ✅ pass | 12600ms |
| 3 | `lsp diagnostics src/nebula/api/routes/admin.py src/nebula/models/governance.py src/nebula/services/policy_simulation_service.py tests/test_service_flows.py` | 0 | ✅ pass | 100ms |
| 4 | `lsp diagnostics tests/test_governance_api.py` | 0 | ✅ pass | 100ms |


## Deviations

Did not modify `console/src/lib/admin-api.ts` because its shared types already matched the intended stricter contract; the actual drift was in the backend response and focused backend tests. Updated stale governance pytest expectations uncovered during execution so they match current inclusive replay-window semantics and richer policy-outcome strings.

## Known Issues

Pre-existing duplicate test definition warning remains in `tests/test_governance_api.py` (`test_embeddings_requests_can_be_correlated_through_usage_ledger`, Ruff/LSP F811). It is outside this task's scope.

## Files Created/Modified

- `src/nebula/api/routes/admin.py`
- `src/nebula/models/governance.py`
- `src/nebula/services/policy_simulation_service.py`
- `tests/test_governance_api.py`
- `tests/test_service_flows.py`
- `.gsd/milestones/M007/slices/S02/tasks/T01-SUMMARY.md`


## Deviations
Did not modify `console/src/lib/admin-api.ts` because its shared types already matched the intended stricter contract; the actual drift was in the backend response and focused backend tests. Updated stale governance pytest expectations uncovered during execution so they match current inclusive replay-window semantics and richer policy-outcome strings.

## Known Issues
Pre-existing duplicate test definition warning remains in `tests/test_governance_api.py` (`test_embeddings_requests_can_be_correlated_through_usage_ledger`, Ruff/LSP F811). It is outside this task's scope.
