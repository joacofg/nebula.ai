---
id: T02
parent: S02
milestone: M005
provides: []
requires: []
affects: []
key_files: ["src/nebula/api/routes/admin.py", "tests/test_governance_api.py", ".gsd/milestones/M005/slices/S02/tasks/T02-SUMMARY.md"]
key_decisions: ["Reused the existing PolicySimulationRequest bounds and replay service instead of adding route-local filtering logic beyond explicit tenant and time-window validation.", "Kept simulation request samples faithful to T01 semantics, where changed entries can reflect policy-outcome deltas even when the route target stays the same."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran ./.venv/bin/pytest tests/test_governance_api.py -k simulation -x. The first two runs failed because the initial assertions assumed the changed-request sample only contained route flips; after reading the T01 replay contract and observed API output, I updated the test expectations to accept policy-outcome deltas for unchanged premium routes. The final run passed all five simulation-focused API tests, verifying explicit 404/422 failures, tenant-scoped summary output, newly denied detection, unchanged and empty windows, and non-mutation of persisted policy."
completed_at: 2026-03-28T03:10:07.910Z
blocker_discovered: false
---

# T02: Added an admin policy simulation endpoint that replays tenant ledger traffic against a candidate policy without mutating saved policy state.

> Added an admin policy simulation endpoint that replays tenant ledger traffic against a candidate policy without mutating saved policy state.

## What Happened
---
id: T02
parent: S02
milestone: M005
key_files:
  - src/nebula/api/routes/admin.py
  - tests/test_governance_api.py
  - .gsd/milestones/M005/slices/S02/tasks/T02-SUMMARY.md
key_decisions:
  - Reused the existing PolicySimulationRequest bounds and replay service instead of adding route-local filtering logic beyond explicit tenant and time-window validation.
  - Kept simulation request samples faithful to T01 semantics, where changed entries can reflect policy-outcome deltas even when the route target stays the same.
duration: ""
verification_result: mixed
completed_at: 2026-03-28T03:10:07.911Z
blocker_discovered: false
---

# T02: Added an admin policy simulation endpoint that replays tenant ledger traffic against a candidate policy without mutating saved policy state.

**Added an admin policy simulation endpoint that replays tenant ledger traffic against a candidate policy without mutating saved policy state.**

## What Happened

Added POST /v1/admin/tenants/{tenant_id}/policy/simulate beside the existing tenant policy CRUD routes. The endpoint reuses the T01 simulation DTOs, performs explicit 404 tenant checks and inverted-window validation, and delegates to the replay-only PolicySimulationService with a reconstructed tenant context so candidate policies are evaluated without persistence. Added focused governance API tests covering missing-tenant and invalid-window failures, tenant-scoped aggregate replay output, newly denied detection under tighter premium guardrails, unchanged and empty simulation windows, and the guarantee that the saved tenant policy is unchanged after simulation calls.

## Verification

Ran ./.venv/bin/pytest tests/test_governance_api.py -k simulation -x. The first two runs failed because the initial assertions assumed the changed-request sample only contained route flips; after reading the T01 replay contract and observed API output, I updated the test expectations to accept policy-outcome deltas for unchanged premium routes. The final run passed all five simulation-focused API tests, verifying explicit 404/422 failures, tenant-scoped summary output, newly denied detection, unchanged and empty windows, and non-mutation of persisted policy.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_governance_api.py -k simulation -x` | 1 | ❌ fail | 810ms |
| 2 | `./.venv/bin/pytest tests/test_governance_api.py -k simulation -x` | 1 | ❌ fail | 760ms |
| 3 | `./.venv/bin/pytest tests/test_governance_api.py -k simulation -x` | 0 | ✅ pass | 880ms |


## Deviations

None.

## Known Issues

The route uses status.HTTP_422_UNPROCESSABLE_ENTITY for the custom inverted-window response, which triggers a FastAPI deprecation warning in the test run; behavior is correct, but the status constant can be updated later to the newer alias.

## Files Created/Modified

- `src/nebula/api/routes/admin.py`
- `tests/test_governance_api.py`
- `.gsd/milestones/M005/slices/S02/tasks/T02-SUMMARY.md`


## Deviations
None.

## Known Issues
The route uses status.HTTP_422_UNPROCESSABLE_ENTITY for the custom inverted-window response, which triggers a FastAPI deprecation warning in the test run; behavior is correct, but the status constant can be updated later to the newer alias.
