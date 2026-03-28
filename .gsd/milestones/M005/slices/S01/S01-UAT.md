# S01: Adaptive routing model — UAT

**Milestone:** M005
**Written:** 2026-03-28T02:56:34.813Z

# S01 UAT — Adaptive routing model

## Preconditions
- Repo dependencies are installed (`make setup` and `npm --prefix console install` already completed in the active worktree).
- Python tests run via `./.venv/bin/pytest`.
- Console tests/build run from the existing `console/` workspace.
- No external premium credentials are required for these checks because the focused backend tests use the mock premium provider.

## Test Case 1 — Heuristic routing emits explicit signal metadata and persists it to the ledger
1. Run:
   `./.venv/bin/pytest tests/test_router_signals.py::test_route_signals_persisted_in_ledger tests/test_router_signals.py::test_route_score_header -x`
2. Expected outcome:
   - Both tests pass.
   - The response for a medium-complexity `nebula-auto` request includes `X-Nebula-Route-Target: premium`, `X-Nebula-Route-Reason: token_complexity`, and `X-Nebula-Route-Score: 1.0000`.
   - The matching `/v1/admin/usage/ledger?request_id=...` record returns a non-null `route_signals` object with `token_count`, `complexity_tier`, `keyword_match`, `model_constraint`, and `budget_proximity` keys.

## Test Case 2 — Signal generation stays interpretable across complexity tiers and policy cues
1. Run:
   `./.venv/bin/pytest tests/test_router_signals.py::test_route_decision_carries_signals tests/test_router_signals.py::test_token_count_signal_from_prompt tests/test_router_signals.py::test_budget_proximity_signal tests/test_router_signals.py::test_model_constraint_signal tests/test_router_signals.py::test_score_by_complexity_tier -x`
2. Expected outcome:
   - All tests pass.
   - Default `RouteDecision` objects remain backward-compatible with empty signals and score `0.0`.
   - Low/medium/high prompts produce ordered scores and expected complexity tiers.
   - `model_constraint` flips to `true` when policy allowlists are present.
   - `budget_proximity` exists in the signal map but remains `null` until downstream spend context is added.

## Test Case 3 — Existing backend request, header, and governance flows still work after routing-model changes
1. Run:
   `./.venv/bin/pytest tests/test_chat_completions.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_governance_runtime_hardening.py tests/test_response_headers.py tests/test_reference_migration.py tests/test_benchmarking.py tests/test_service_flows.py -x`
2. Expected outcome:
   - The full focused slice-level backend set passes.
   - Existing `X-Nebula-*` headers remain intact while adding the new route-score header.
   - Reference migration and governance flows continue to correlate public requests to admin ledger evidence successfully.

## Test Case 4 — Observability drawer shows labeled route decision evidence only when signals are present
1. Run:
   `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`
2. Expected outcome:
   - All five Vitest tests pass.
   - The request-detail drawer renders a `Route Decision` section for entries with `route_signals` and shows labeled rows such as `Token count`, `Complexity tier`, `Keyword match`, and `Model constraint`.
   - Entries without `route_signals` do not render the `Route Decision` section.

## Test Case 5 — Console remains production-buildable after the new route-decision UI wiring
1. Run:
   `npm --prefix console run build && test -f docs/route-decision-vocabulary.md`
2. Expected outcome:
   - The Next.js console build succeeds without type or compile errors.
   - `docs/route-decision-vocabulary.md` exists in the assembled worktree.

## Edge Cases
- Explicit model overrides (`explicit_local_model`, `explicit_premium_model`) and routing-mode overrides (`policy_local_only`, `policy_premium_only`) should remain signal-free and score `0.0`; this avoids suggesting that a heuristic score drove an override path.
- A medium-complexity heuristic request may still show `model_constraint: true` under the default tenant policy because the policy carries an allowed premium-model list; UAT should treat that as expected runtime-aligned behavior, not a regression.
- `budget_proximity` appearing as `null` is expected in S01; it is a stable schema placeholder for downstream budget-aware routing work, not evidence of broken persistence.

