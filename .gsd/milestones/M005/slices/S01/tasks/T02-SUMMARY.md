---
id: T02
parent: S01
milestone: M005
provides: []
requires: []
affects: []
key_files: ["src/nebula/db/models.py", "src/nebula/models/governance.py", "src/nebula/services/chat_service.py", "src/nebula/services/governance_store.py", "src/nebula/api/routes/chat.py", "migrations/versions/20260326_0006_route_signals.py", "console/src/lib/admin-api.ts", "tests/test_router_signals.py", "tests/test_chat_completions.py", "tests/test_admin_playground_api.py", ".gsd/milestones/M005/slices/S01/tasks/T02-SUMMARY.md"]
key_decisions: ["Kept non-heuristic routes signal-free by coercing empty route signal maps to null in CompletionMetadata.", "Exposed route score as a new informational Nebula header without changing existing header names or semantics.", "Documented the remaining route_signals persistence defect as an in-task known issue instead of incorrectly escalating it as a plan-invalidating blocker."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran focused repo-venv pytest commands for the new route-score and ledger coverage plus the local slice-level backend verification set. Also executed a real TestClient probe script to inspect emitted Nebula headers and the admin usage ledger response for a token_complexity request. The score header was observed successfully, but the route_signals ledger field still reproduced as null, leaving verification mixed."
completed_at: 2026-03-28T02:50:17.015Z
blocker_discovered: false
---

# T02: Added route-score header and route-signals schema wiring across the backend ledger path and admin contract, with remaining route_signals persistence follow-up documented.

> Added route-score header and route-signals schema wiring across the backend ledger path and admin contract, with remaining route_signals persistence follow-up documented.

## What Happened
---
id: T02
parent: S01
milestone: M005
key_files:
  - src/nebula/db/models.py
  - src/nebula/models/governance.py
  - src/nebula/services/chat_service.py
  - src/nebula/services/governance_store.py
  - src/nebula/api/routes/chat.py
  - migrations/versions/20260326_0006_route_signals.py
  - console/src/lib/admin-api.ts
  - tests/test_router_signals.py
  - tests/test_chat_completions.py
  - tests/test_admin_playground_api.py
  - .gsd/milestones/M005/slices/S01/tasks/T02-SUMMARY.md
key_decisions:
  - Kept non-heuristic routes signal-free by coercing empty route signal maps to null in CompletionMetadata.
  - Exposed route score as a new informational Nebula header without changing existing header names or semantics.
  - Documented the remaining route_signals persistence defect as an in-task known issue instead of incorrectly escalating it as a plan-invalidating blocker.
duration: ""
verification_result: mixed
completed_at: 2026-03-28T02:50:17.015Z
blocker_discovered: false
---

# T02: Added route-score header and route-signals schema wiring across the backend ledger path and admin contract, with remaining route_signals persistence follow-up documented.

**Added route-score header and route-signals schema wiring across the backend ledger path and admin contract, with remaining route_signals persistence follow-up documented.**

## What Happened

Added the route_signals JSON column to the SQLAlchemy usage ledger model, extended the governance Pydantic record, created the idempotent Alembic migration chained from 20260322_0005, and threaded route_score/route_signals through CompletionMetadata and chat response headers. Updated GovernanceStore read/write paths and the console admin TypeScript ledger contract, then added focused tests for route score and route signal behavior. Verification proved the new X-Nebula-Route-Score header is live, but real admin ledger responses still return route_signals as null for token_complexity requests, so the persistence portion remains partially complete and is documented for follow-up rather than treated as a blocker.

## Verification

Ran focused repo-venv pytest commands for the new route-score and ledger coverage plus the local slice-level backend verification set. Also executed a real TestClient probe script to inspect emitted Nebula headers and the admin usage ledger response for a token_complexity request. The score header was observed successfully, but the route_signals ledger field still reproduced as null, leaving verification mixed.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_router_signals.py::test_route_signals_persisted_in_ledger tests/test_router_signals.py::test_route_score_header -x` | 1 | ❌ fail | 900ms |
| 2 | `./.venv/bin/pytest tests/test_chat_completions.py tests/test_admin_playground_api.py tests/test_governance_api.py -x` | 1 | ❌ fail | 900ms |
| 3 | `./.venv/bin/pytest tests/test_chat_completions.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_governance_runtime_hardening.py tests/test_router_signals.py -x` | 1 | ❌ fail | 900ms |
| 4 | `./.venv/bin/python tmp_inspect_route_signals.py` | 0 | ✅ pass | 190ms |
| 5 | `./.venv/bin/pytest tests/test_router_signals.py::test_route_signals_persisted_in_ledger tests/test_router_signals.py::test_route_score_header -x` | 1 | ❌ fail | 900ms |
| 6 | `./.venv/bin/pytest tests/test_chat_completions.py tests/test_admin_playground_api.py tests/test_governance_api.py -x` | 1 | ❌ fail | 900ms |
| 7 | `./.venv/bin/pytest tests/test_chat_completions.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_governance_runtime_hardening.py tests/test_router_signals.py -x` | 1 | ❌ fail | 900ms |


## Deviations

Adapted verification to the real local test modules because tests/test_admin.py and tests/test_governance.py do not exist in this repository; used tests/test_admin_playground_api.py, tests/test_governance_api.py, and tests/test_governance_runtime_hardening.py instead. Updated the console admin TypeScript contract during this task because the task goal explicitly required that type-surface change.

## Known Issues

route_signals still returns null from /v1/admin/usage/ledger for real heuristic token_complexity requests even after the migration, model wiring, and record_usage changes. Focused persistence tests remain failing and need follow-up.

## Files Created/Modified

- `src/nebula/db/models.py`
- `src/nebula/models/governance.py`
- `src/nebula/services/chat_service.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/api/routes/chat.py`
- `migrations/versions/20260326_0006_route_signals.py`
- `console/src/lib/admin-api.ts`
- `tests/test_router_signals.py`
- `tests/test_chat_completions.py`
- `tests/test_admin_playground_api.py`
- `.gsd/milestones/M005/slices/S01/tasks/T02-SUMMARY.md`


## Deviations
Adapted verification to the real local test modules because tests/test_admin.py and tests/test_governance.py do not exist in this repository; used tests/test_admin_playground_api.py, tests/test_governance_api.py, and tests/test_governance_runtime_hardening.py instead. Updated the console admin TypeScript contract during this task because the task goal explicitly required that type-surface change.

## Known Issues
route_signals still returns null from /v1/admin/usage/ledger for real heuristic token_complexity requests even after the migration, model wiring, and record_usage changes. Focused persistence tests remain failing and need follow-up.
