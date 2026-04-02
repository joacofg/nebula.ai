# S01 Research — Calibrated routing core

## Summary
- S01 primarily advances active requirement **R039** and sets the foundation for **R045**, **R047**, and **R048**. This slice owns the routing-core contract that later slices will use for ledger-backed evidence, replay parity, and operator inspection.
- The current routing seam is narrow and centralized in `src/nebula/services/router_service.py`. Runtime and replay already share the same basic structure via `choose_target_with_reason()` and `choose_target_for_replay()`, and both emit a `RouteDecision` with `target`, `reason`, `signals`, and `score`.
- The existing implementation is still heuristic-first: token-count thresholds plus keyword hints, with a tiny model-constraint bonus. `budget_proximity` is present in the contract but not implemented. This slice is where the calibrated scoring model should replace that heuristic center while staying additive and explainable.
- The best seam is to keep `RouteDecision` as the stable carrier, enrich `signals` with a calibrated breakdown, and preserve the replayable subset (`token_count`, `keyword_match`, `complexity_tier`) so simulation does not drift.

## Recommendation
- Build S01 as a **backend contract slice**, not a console slice. Keep changes centered on:
  - `src/nebula/services/router_service.py`
  - `src/nebula/services/policy_service.py`
  - `src/nebula/services/chat_service.py`
  - `src/nebula/models/governance.py`
  - tests around routing/runtime headers/ledger replay
  - docs vocabulary update in `docs/route-decision-vocabulary.md`
- Treat the calibrated router as a **small explicit additive scorer**, not a classifier. The current code already follows the project’s anti-sprawl constraint and the milestone context explicitly requires explicit additive scoring. Extend that pattern instead of introducing a separate calibration engine or ML-like abstraction.
- Preserve the old signals as compatibility keys and add new calibrated fields additively. Later slices and current console code tolerate extra JSON in `route_signals`, but replay only consumes a few keys today.
- Keep runtime/replay parity as a first-order design rule in S01. If runtime computes a score that replay cannot reconstruct from persisted signals plus bounded ledger metadata, S03 will inherit drift.

## Implementation Landscape

### 1. Router core is already centralized and is the natural first task
- File: `src/nebula/services/router_service.py`
- Current structure:
  - `RouteDecision` dataclass: `target`, `reason`, `signals`, `score`
  - `ReplayRouteContext`: `token_count`, `keyword_match`, `complexity_tier`
  - `choose_target_with_reason()` for live routing
  - `choose_target_for_replay()` for simulation
- Current live routing logic:
  - explicit model override -> immediate route decision with empty signals
  - policy `local_only` / `premium_only` -> immediate route decision with empty signals
  - otherwise compute `token_count`, derive `complexity_tier`, detect keyword hints, set `model_constraint`, leave `budget_proximity=None`, compute `score=min(token_count/500,1)+0.1 if model_constraint`, then route local only for `low` + no keyword
- Current replay logic mirrors that structure but only consumes `ReplayRouteContext` + optional serialized request fallback.
- Planner implication: this file can carry most of S01 without touching provider orchestration. The risky part is designing a signal vocabulary that is both interpretable and replayable.

### 2. Policy service already wraps routing and is where any control flag would land
- File: `src/nebula/services/policy_service.py`
- `PolicyService.evaluate()` calls router live or replay paths and then layers on:
  - explicit model conflict denial
  - soft-budget annotation
  - premium allowlist guardrail
  - per-request premium guardrail
  - hard-budget downgrade/deny logic
- Important detail: hard-budget downgrade preserves the existing `route_decision.signals` and `score` when replacing the reason with `hard_budget_downgrade`.
- Policy outcomes are composed as semicolon-separated operator-facing fragments and already act as a stable explanation surface across headers, ledger, and simulation.
- Planner implication:
  - If S01 adds a tenant-scoped rollout valve for calibrated routing, this is the right enforcement point together with `TenantPolicy`.
  - If S01 defers the control field, the router can still expose calibrated vs heuristic/degraded state through `signals` and/or `reason` while keeping policy schema unchanged.

### 3. Runtime metadata propagation is already complete enough for calibrated evidence
- Files:
  - `src/nebula/services/chat_service.py`
  - `src/nebula/api/routes/chat.py`
- `ChatService._metadata()` copies `route_decision.signals` into `CompletionMetadata.route_signals` and `route_decision.score` into `route_score`.
- `_record_usage()` persists `route_reason`, `policy_outcome`, and `route_signals` into `UsageLedgerRecord`.
- `src/nebula/api/routes/chat.py` exposes `X-Nebula-Route-Score` and the other route headers from metadata.
- Planner implication: once the router emits calibrated signals and score, runtime headers and ledger persistence mostly come along for free. S01 should prove this with tests rather than redesigning the transport path.

### 4. Ledger schema is flexible for signal expansion; tenant control changes would need policy schema + migration
- Files:
  - `src/nebula/models/governance.py`
  - `src/nebula/db/models.py`
  - `src/nebula/services/governance_store.py`
  - `migrations/versions/20260326_0006_route_signals.py`
- `UsageLedgerRecord.route_signals` is already `dict[str, Any] | None`, persisted as JSON in `UsageLedgerModel.route_signals`.
- `GovernanceStore.record_usage()` and `_usage_from_model()` already pass the JSON through unchanged.
- This means S01 can expand the route-signals payload without a DB migration.
- But `TenantPolicy` is strongly typed and persisted field-by-field in both DB model and store. Any new calibrated-routing control would require:
  - `src/nebula/models/governance.py`
  - `src/nebula/db/models.py`
  - `src/nebula/services/governance_store.py`
  - `src/nebula/api/routes/admin.py` policy options
  - console policy types/forms/tests
  - Alembic migration under `migrations/versions/`
- Planner implication: do not casually add a policy field inside a routing task. If the rollout valve is in scope for S01, carve it as a distinct task because it crosses backend persistence, admin API, console policy UI, and migration.

### 5. Replay path is already signal-driven and will tolerate additive route_signals if the replay subset stays stable
- File: `src/nebula/services/policy_simulation_service.py`
- Replay currently reconstructs `ReplayRouteContext` from:
  - `route_signals.token_count`
  - `route_signals.keyword_match`
  - `route_signals.complexity_tier`
- When signals are incomplete, it synthesizes a prompt from stored token counts.
- Changed-request reporting compares:
  - baseline vs simulated route target
  - policy outcome
  - estimated premium cost
- Planner implication:
  - S01 should not break the existing replay subset.
  - If S01 introduces a calibrated mode marker or score breakdown in signals, replay can ignore those initially and still stay functional.
  - If S01 changes route reasons or score semantics, policy simulation tests and docs need alignment immediately.

### 6. Console request detail is additive-friendly and can survive richer signals without immediate UI work
- Files:
  - `console/src/components/ledger/ledger-request-detail.tsx`
  - `console/src/components/ledger/ledger-request-detail.test.tsx`
  - `console/src/lib/admin-api.ts`
- The request-detail panel reads `route_signals` as untyped JSON and only renders a few known keys today:
  - `token_count`
  - `complexity_tier`
  - `keyword_match`
  - `model_constraint`
  - `budget_proximity`
- Extra fields will not break the UI.
- Planner implication: S01 can stop at backend payload shape plus targeted test updates if the current route detail assertions need to reflect new reason codes or signal values. Full operator-surface rendering belongs more naturally to S04.

## Constraints and Risks
- **Interpretability constraint**: milestone context says explicit additive scoring only. Avoid hidden weights spread across services or free-form “confidence” fields without a deterministic definition.
- **Parity risk**: runtime and replay are implemented as two separate methods in `RouterService`. Any scoring change must be made in shared helpers or duplicated carefully; otherwise S03 will have semantic drift.
- **Contract drift risk**: `docs/route-decision-vocabulary.md` still describes the current S01-era signal set and score formula (`min(token_count / 500, 1.0) + 0.1 if model_constraint`). If the router changes, this doc becomes stale immediately.
- **Header/test coupling risk**: several tests assert specific route reasons and exact route score formatting (`X-Nebula-Route-Score`). Any score formula or reason change will break targeted tests across runtime, governance, and migration proof.
- **Policy-field scope risk**: introducing the “small tenant-scoped calibrated-routing control” literally in S01 is feasible but no longer a router-only task. It becomes a cross-stack policy-surface change with migration cost.

## Natural Task Seams

### Seam A — Router calibration contract (highest risk, first)
Owns the scoring model and route-signals schema.
- Files:
  - `src/nebula/services/router_service.py`
  - `docs/route-decision-vocabulary.md`
  - `tests/test_router_signals.py`
- Likely output:
  - shared helper(s) for score component derivation used by both live and replay
  - richer `signals` payload with explicit calibrated-vs-heuristic/degraded markers and additive breakdown
  - updated score semantics and reason vocabulary
- Verify with focused router tests first.

### Seam B — Runtime propagation and ledger persistence proof
Confirms calibrated router output reaches headers + usage ledger unchanged.
- Files:
  - `src/nebula/services/chat_service.py`
  - `src/nebula/api/routes/chat.py`
  - `tests/test_router_signals.py`
  - `tests/test_response_headers.py`
  - possibly focused `tests/test_governance_api.py`
- Likely output:
  - no major code changes beyond propagation compatibility
  - tests asserting header score/reason and persisted `route_signals` shape
- Verify with focused API tests rather than broad suites first.

### Seam C — Policy integration / degraded semantics
If the slice exposes calibrated-vs-heuristic fallback semantics or a control flag, this seam owns it.
- Files:
  - `src/nebula/services/policy_service.py`
  - `src/nebula/models/governance.py`
  - possibly `src/nebula/db/models.py`, `src/nebula/services/governance_store.py`, `src/nebula/api/routes/admin.py`
  - `tests/test_governance_runtime_hardening.py`
  - `tests/test_service_flows.py`
- Likely output:
  - policy-aware routing mode / degraded-mode semantics
  - preserved hard-budget downgrade behavior over calibrated scores
- This seam can stay backend-only if no persisted policy field is added yet.

### Seam D — Optional tenant control surface (only if planner decides S01 must ship it now)
This is separable and should not block the core calibrated router if the policy choice is still unsettled.
- Files:
  - `src/nebula/models/governance.py`
  - `src/nebula/db/models.py`
  - `src/nebula/services/governance_store.py`
  - `src/nebula/api/routes/admin.py`
  - `console/src/lib/admin-api.ts`
  - `console/src/components/policy/policy-form.tsx`
  - related console policy tests
  - new Alembic revision in `migrations/versions/`
- This seam is much broader than the router work. Keep it separate if included.

## What to Build or Prove First
1. **Define the calibrated route-decision contract in `router_service.py` first.** Everything else consumes it.
2. **Keep replay parity by extracting shared score/signal derivation helpers.** Do not implement live and replay calibration independently.
3. **Prove runtime propagation via headers and ledger with focused tests.** This is the shortest path to the roadmap’s “calibrated-versus-heuristic routing mode and explicit additive score breakdown in runtime evidence.”
4. **Only then decide whether to add a persisted tenant control in S01.** The codebase can support it, but it is a broader slice inside the slice.

## Verification Plan
Start narrow; broaden only after the routing contract settles.

### Focused backend checks
- `./.venv/bin/pytest tests/test_router_signals.py -x`
- `./.venv/bin/pytest tests/test_governance_runtime_hardening.py -x`
- `./.venv/bin/pytest tests/test_service_flows.py -k "simulation or runtime_policy" -x`
- `./.venv/bin/pytest tests/test_response_headers.py -x`
- If governance API behavior changes: `./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation or hard_budget or route_reason" -x`

### Type / diagnostics checks
- `lsp diagnostics` on touched Python and TS files after edits

### If policy schema / migration changes
- `./.venv/bin/alembic upgrade head`
- rerun the focused backend tests above
- targeted console tests for policy form/admin client if any TS contract changed

### If console policy surface changes
- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`

## Skill Notes
- Relevant installed skill: **debug-like-expert**. The useful rule for this slice is its core principle: **verify, don’t assume**. That matters here because runtime and replay already diverge structurally into separate methods; parity must be proven by tests, not assumed from matching intent.
- Skill discovery suggestion for direct core tech:
  - FastAPI skill candidates from `npx skills find "FastAPI"`:
    - `npx skills add wshobson/agents@fastapi-templates` (highest install count, broad relevance)
    - `npx skills add mindrally/skills@fastapi-python` (relevant backend framing)
  - No installation done.

## Concrete File Map
- `src/nebula/services/router_service.py` — live + replay route decision core; main S01 pressure point
- `src/nebula/services/policy_service.py` — policy-aware route wrapping, denial/downgrade semantics, candidate place for calibrated-routing control
- `src/nebula/services/chat_service.py` — route metadata -> ledger persistence bridge
- `src/nebula/api/routes/chat.py` — response headers, including `X-Nebula-Route-Score`
- `src/nebula/services/policy_simulation_service.py` — replay input reconstruction from persisted route signals
- `src/nebula/models/governance.py` — `TenantPolicy`, `UsageLedgerRecord`, simulation response shapes
- `src/nebula/db/models.py` — persisted tenant policy + `usage_ledger.route_signals` JSON column
- `src/nebula/services/governance_store.py` — policy persistence and usage ledger serialization/deserialization
- `docs/route-decision-vocabulary.md` — canonical operator-facing routing contract; will need immediate alignment
- `tests/test_router_signals.py` — best first test target for S01
- `tests/test_governance_runtime_hardening.py` — policy/runtime guardrail interactions
- `tests/test_service_flows.py` — simulation parity and policy-resolution integration
- `tests/test_response_headers.py` — outward runtime evidence contract
- `tests/test_governance_api.py` — admin replay / ledger API assertions if route reasons or policy outcomes shift
- `console/src/components/ledger/ledger-request-detail.tsx` — existing bounded operator view of `route_signals`; tolerant of additive fields
- `console/src/components/policy/policy-form.tsx` — only relevant if S01 includes the tenant-scoped control now
