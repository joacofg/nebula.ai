---
id: S01
parent: M005
milestone: M005
provides:
  - A stable route-decision vocabulary (`token_complexity`, explicit signal keys, route-score semantics) that downstream slices can reuse for simulation and recommendation work.
  - Persisted ledger evidence for route signals and score-adjacent reasoning, available through the existing admin ledger path.
  - An operator-visible Route Decision drawer section in Observability for inspecting why Nebula chose a route.
requires:
  []
affects:
  - S02
  - S03
  - S04
  - S05
key_files:
  - src/nebula/services/router_service.py
  - src/nebula/services/policy_service.py
  - src/nebula/services/chat_service.py
  - src/nebula/services/governance_store.py
  - src/nebula/db/models.py
  - src/nebula/models/governance.py
  - src/nebula/api/routes/chat.py
  - migrations/versions/20260326_0006_route_signals.py
  - console/src/lib/admin-api.ts
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - docs/route-decision-vocabulary.md
  - tests/test_router_signals.py
  - .gsd/KNOWLEDGE.md
  - .gsd/PROJECT.md
key_decisions:
  - Kept override routes signal-free with default score 0.0 and limited structured signals to heuristic routing decisions.
  - Exposed route score as an additive informational Nebula header without changing existing header names or semantics.
  - Rendered route signals in Observability through explicit labeled rows instead of raw JSON so operator inspection remains stable as the vocabulary evolves.
  - Kept R039 active because S01 materially strengthens routing interpretability and evidence surfaces but does not yet prove broader outcome-aware adaptive scoring.
patterns_established:
  - When adding new usage-ledger fields, update the DB model, record path, response schema, and hydration path together; otherwise admin reads can silently drop persisted data.
  - Operator-facing decision evidence should use stable labeled fields and documented vocabulary rather than raw JSON blobs so downstream slices can build on a durable contract.
  - Override route paths should remain signal-free to avoid implying heuristic scoring where no heuristic decision was made.
observability_surfaces:
  - `X-Nebula-Route-Score` response header on public chat completions.
  - Persisted `route_signals` field on usage-ledger admin records.
  - Observability request-detail drawer Route Decision section showing labeled signal values.
  - `docs/route-decision-vocabulary.md` as the stable operator/reference vocabulary for route reasons and signals.
drill_down_paths:
  - .gsd/milestones/M005/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M005/slices/S01/tasks/T02-SUMMARY.md
  - .gsd/milestones/M005/slices/S01/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-28T02:56:34.813Z
blocker_discovered: false
---

# S01: Adaptive routing model

**Delivered an interpretable adaptive-routing foundation with explicit route signals, additive route-score/header exposure, persisted ledger evidence, and operator-visible route-decision vocabulary.**

## What Happened

S01 replaced Nebula's older opaque prompt-length routing posture with an interpretable route-decision model that produces explicit signal metadata and a normalized score at routing time, then carried that evidence all the way through the public response and operator-observability path. On the backend, the router now estimates token count, derives a complexity tier, records keyword and policy-constraint signals, and exposes a normalized score while preserving signal-free override paths for explicit model and routing-mode decisions. The chat path threads those route decisions into completion metadata, emits `X-Nebula-Route-Score` alongside the existing `X-Nebula-*` headers, and persists route signals into the usage ledger via the new `route_signals` JSON column and admin schema wiring. On the console side, the usage-ledger request drawer gained a dedicated Route Decision section that maps stable signal keys to readable operator labels instead of exposing raw JSON, and the slice added `docs/route-decision-vocabulary.md` as the canonical operator/reference vocabulary for signals, score semantics, and reason codes. During slice close-out I verified the assembled worktree rather than relying only on task summaries and found one real integration defect: the write path and migration persisted `route_signals`, but the admin ledger hydration path omitted the field. Fixing `GovernanceStore._usage_from_model()` closed that gap, after which the focused route-signal persistence test passed and the slice delivered the full backend-to-UI observability chain promised by the plan.

## Verification

Re-ran all slice-level verification from the assembled worktree and required all planned checks to pass. Backend verification passed with `./.venv/bin/pytest tests/test_router_signals.py::test_route_decision_carries_signals tests/test_router_signals.py::test_token_count_signal_from_prompt tests/test_router_signals.py::test_budget_proximity_signal tests/test_router_signals.py::test_model_constraint_signal tests/test_router_signals.py::test_score_by_complexity_tier tests/test_router_signals.py::test_route_signals_persisted_in_ledger tests/test_router_signals.py::test_route_score_header -x` (7 passed) and `./.venv/bin/pytest tests/test_chat_completions.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_governance_runtime_hardening.py tests/test_response_headers.py tests/test_reference_migration.py tests/test_benchmarking.py tests/test_service_flows.py -x` (49 passed). Observability/UI verification passed with `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` (5 passed) and `npm --prefix console run build && test -f docs/route-decision-vocabulary.md` (build succeeded and doc exists). The close-out rerun also proved that the ledger route_signals persistence gap from task execution was fixed in the assembled worktree.

## Requirements Advanced

- R039 — Added explicit routing signals, normalized scoring, score/header exposure, ledger persistence, and operator-visible route-decision surfaces that materially strengthen Nebula's routing evidence beyond prompt-length heuristics.
- R044 — Kept the v4 work narrowly focused on decisioning quality, observability, and operator control without expanding Nebula into broader API parity, SDK work, or hosted authority.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

Task-plan verification commands referenced legacy test module names (`tests/test_admin.py`, `tests/test_governance.py`) that do not exist in this worktree, so slice verification used the real split modules present locally. During close-out, I also fixed one assembled-worktree defect that task execution left behind: admin ledger reads persisted `route_signals` to the database correctly but dropped them on read because `GovernanceStore._usage_from_model()` did not map the new field.

## Known Limitations

The routing model is still primarily heuristic: `budget_proximity` is present as a stable signal name but remains null until downstream spend context is threaded in, and the score is not yet calibrated from observed outcomes. R039 therefore advances materially but is not yet fully validated by this slice alone.

## Follow-ups

S02 should reuse the persisted route_signals plus stable `token_complexity` vocabulary for simulation replay instead of inventing a second decision schema. S03 can build true budget-aware signals on top of the existing `budget_proximity` placeholder once spend context is threaded into routing resolution. S05 should revisit whether the current score formula is sufficiently outcome-aware to validate R039 fully.

## Files Created/Modified

- `src/nebula/services/router_service.py` — Extended route decisions with explicit signals, token-based scoring, and policy-aware heuristic routing inputs.
- `src/nebula/services/policy_service.py` — Threaded tenant policy through routing resolution so signal generation can consider policy constraints.
- `src/nebula/services/chat_service.py` — Added route score and route signals to completion metadata and usage recording flow.
- `src/nebula/services/governance_store.py` — Added route_signals persistence and fixed ledger hydration so admin reads now return the stored signal map.
- `src/nebula/db/models.py` — Added route_signals JSON column to the usage ledger ORM model.
- `src/nebula/models/governance.py` — Extended governance API schema with route_signals for admin ledger responses.
- `src/nebula/api/routes/chat.py` — Exposed X-Nebula-Route-Score on chat responses.
- `migrations/versions/20260326_0006_route_signals.py` — Added Alembic migration for the usage_ledger.route_signals column.
- `console/src/lib/admin-api.ts` — Extended the console admin API contract with route_signals.
- `console/src/components/ledger/ledger-request-detail.tsx` — Added an operator-facing Route Decision section to the ledger detail drawer with stable plain-language labels.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Locked positive and negative drawer rendering paths with focused Vitest coverage.
- `docs/route-decision-vocabulary.md` — Documented the stable route-signal and reason-code vocabulary for operators and downstream simulation work.
- `tests/test_router_signals.py` — Added and updated backend tests covering route signals, route score headers, and ledger persistence.
