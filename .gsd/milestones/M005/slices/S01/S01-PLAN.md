# S01: Adaptive routing model

**Goal:** Nebula has an interpretable routing decision model that uses explicit signals and records clearer route reasons than the current heuristic.
**Demo:** After this: Nebula has an interpretable routing decision model that uses explicit signals and records clearer route reasons than the current heuristic.

## Tasks
- [x] **T01: Added scored route-signal metadata to heuristic routing decisions and threaded tenant policy through router resolution.** — 
  - Files: src/nebula/services/router_service.py, src/nebula/services/policy_service.py
  - Verify: `pytest tests/test_router_signals.py::test_route_decision_carries_signals tests/test_router_signals.py::test_token_count_signal_from_prompt tests/test_router_signals.py::test_budget_proximity_signal tests/test_router_signals.py::test_model_constraint_signal tests/test_router_signals.py::test_score_by_complexity_tier -x`
- [x] **T02: Added route-score header and route-signals schema wiring across the backend ledger path and admin contract, with remaining route_signals persistence follow-up documented.** — 
  - Files: src/nebula/db/models.py, src/nebula/models/governance.py, src/nebula/services/governance_store.py, src/nebula/services/chat_service.py, src/nebula/api/routes/chat.py, migrations/versions/20260326_0006_route_signals.py
  - Verify: `pytest tests/test_router_signals.py::test_route_signals_persisted_in_ledger tests/test_router_signals.py::test_route_score_header -x`
- [x] **T03: Added route-signal visibility to the observability drawer and documented the stable route-decision vocabulary.** — 
  - Files: console/src/lib/admin-api.ts, console/src/components/ledger/ledger-request-detail.tsx, console/src/components/ledger/ledger-request-detail.test.tsx, docs/route-decision-vocabulary.md
  - Verify: `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx && test -f docs/route-decision-vocabulary.md`
