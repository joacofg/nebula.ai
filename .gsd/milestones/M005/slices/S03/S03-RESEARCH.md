# S03 Research — Hard budget guardrails

## Summary

S03 primarily advances **R041** and must stay aligned with **R044** scope discipline. The codebase already has most of the enforcement seam in place: `TenantPolicy.max_premium_cost_per_request` is a real runtime-enforced control, `PolicyService.evaluate()/resolve()` already computes projected premium cost and can deny requests, chat/admin paths already persist policy-denied outcomes into the usage ledger, simulation already replays candidate policies against ledger traffic, and the policy console already treats per-request premium cost as a runtime-enforced control. What is missing for this slice is the **hard budget guardrail layer beyond per-request cost**: explicit tenant spend-cap semantics, predictable downgrade-vs-deny behavior, persisted/observable outcomes, and operator-facing configuration language that replaces the current “soft budget signal only” posture.

This is **targeted research**, not greenfield. The safest implementation path is to extend the existing policy model + `PolicyService` decision/evaluation flow rather than inventing a second budget engine. The natural slice seam is: backend policy contract/enforcement first, then ledger/simulation surface alignment, then console UX/docs/tests.

## Recommendation

Build S03 by extending the existing runtime policy evaluation contract instead of bolting budget behavior into `ChatService` or the console.

Recommended shape:
- Add new **hard budget policy fields** to `TenantPolicy` and persistence (`src/nebula/models/governance.py`, `src/nebula/db/models.py`, migration, `GovernanceStore`).
- Put all decision semantics in **`PolicyService.evaluate()`** so both runtime and simulation inherit the same downgrade/deny rules.
- Reuse S01’s stable route-signal/route-reason vocabulary and Observability drawer pattern for budget evidence; do not add ad-hoc JSON-only UI.
- Extend simulation to report changed requests under the new hard-budget semantics rather than creating a separate budget preview subsystem.
- Update the policy page to distinguish **runtime-enforced hard guardrails** from the legacy soft advisory field.

This follows the existing project pattern and supports R044: narrow control-plane work, no new broad public API promise, no hosted authority drift.

## Implementation Landscape

### Backend files that already define the seam

- `src/nebula/models/governance.py`
  - `TenantPolicy` currently has:
    - `routing_mode_default`
    - `allowed_premium_models`
    - `semantic_cache_enabled`
    - `fallback_enabled`
    - `max_premium_cost_per_request`
    - `soft_budget_usd`
  - `UsageLedgerRecord` already persists `policy_outcome`, `route_reason`, and `route_signals`.
  - Simulation request/response models already exist and can absorb new outcome text without new route shapes.

- `src/nebula/services/policy_service.py`
  - This is the core enforcement seam.
  - `evaluate()` already:
    - gets a route decision from `RouterService`
    - checks explicit-model conflicts
    - computes `soft_budget_exceeded`
    - computes `projected_premium_cost`
    - denies on premium allowlist conflict
    - denies on `max_premium_cost_per_request`
    - produces a semicolon-delimited `policy_outcome`
  - `resolve()` already turns `PolicyEvaluation.denied` into a real HTTP 403 via `_policy_denied()`.
  - `_policy_denied()` already sets response headers needed for operator correlation.
  - This is where downgrade/deny semantics should live.

- `src/nebula/services/chat_service.py`
  - Already records `policy_denied` ledger rows when `PolicyService.resolve()` raises 403.
  - Already threads `policy_outcome`, `route_reason`, `route_signals`, and `route_score` into metadata/ledger.
  - Good place to consume richer `PolicyResolution`, but not the right place to own budget logic.

- `src/nebula/services/governance_store.py`
  - Already persists policies and usage ledger rows.
  - Already exposes `tenant_spend_total(tenant_id, before_timestamp=None)`.
  - That method is the existing factual basis for spend-aware guardrails and is also replay-safe for simulation windows.

- `src/nebula/services/policy_simulation_service.py`
  - Already replays ledger-backed traffic using `PolicyService.evaluate()`.
  - This is a major accelerator: if S03 keeps all semantics in `PolicyService`, simulation gets the new hard-budget outcomes “for free,” with only output wording/sample expectations needing adjustment.

- `src/nebula/services/router_service.py`
  - Has a documented `budget_proximity` signal and `policy_budget_advisory` reason in docs, but runtime code currently leaves `budget_proximity` as `None` and never emits a budget reason.
  - S01 summary explicitly called this out as a follow-up for S03.
  - Important constraint: keep override routes signal-free per S01 pattern.

- `src/nebula/api/routes/admin.py`
  - `/v1/admin/policy/options` currently classifies fields into `runtime_enforced_fields`, `soft_signal_fields`, and `advisory_fields`.
  - Today `soft_budget_usd` is the only soft field.
  - S03 should likely extend these option groups rather than hardcoding new console assumptions.

### Console files that will need adjustment

- `console/src/lib/admin-api.ts`
  - Mirrors the backend `TenantPolicy` shape. Any new budget fields must be added here first for end-to-end TS correctness.

- `console/src/components/policy/policy-form.tsx`
  - Current grouping is explicit and already suitable for extension.
  - It treats `max_premium_cost_per_request` as runtime-enforced and `soft_budget_usd` as “Soft budget signal only. Adds policy outcome metadata when exceeded but does not block routing in Phase 4.”
  - This copy will become incorrect once hard budget semantics are added.

- `console/src/app/(console)/policy/page.tsx`
  - Already wires save vs preview separately and reuses simulation output. Good existing seam.

- `console/src/components/ledger/ledger-request-detail.tsx`
  - Already renders stable labeled route-signal rows instead of raw JSON, following the S01 pattern.
  - If S03 persists new budget-related signals or clearer policy outcomes, this drawer is the right operator surface to extend.

### Existing tests already proving adjacent behavior

Backend/runtime:
- `tests/test_governance_runtime_hardening.py`
  - `test_policy_enforces_premium_allowlist_and_request_guardrail`
  - `test_soft_budget_annotations_do_not_block_routing`
- `tests/test_governance_api.py`
  - `test_spend_guardrail_denial_returns_exact_detail_and_ledger_correlation`
  - simulation endpoint tests already cover changed routes/newly denied requests
- `tests/test_service_flows.py`
  - simulation service replay behavior and runtime resolution toggles

Console:
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `console/e2e/policy.spec.ts`

These establish the verification harness and the language that will need to move from soft/advisory to hard-enforced.

## Natural Seams for Planning

### Seam 1 — Policy contract + persistence
Risk: medium; unblocks everything else.

Likely files:
- `src/nebula/models/governance.py`
- `src/nebula/db/models.py`
- `src/nebula/services/governance_store.py`
- new Alembic migration in `migrations/versions/`
- `console/src/lib/admin-api.ts`

Planner note: do this first because every downstream runtime, simulation, and UI path depends on the policy shape.

### Seam 2 — Runtime hard-budget decisioning
Risk: highest.

Likely files:
- `src/nebula/services/policy_service.py`
- possibly `src/nebula/services/router_service.py` if budget proximity becomes a real signal/reason
- possibly `src/nebula/services/chat_service.py` only for richer ledger metadata threading

Planner note: this is the core proof for R041. Decide the exact semantics first:
- when spend cap is exceeded, do we downgrade to local if possible?
- when downgrade is impossible, do we deny?
- how explicit model requests behave under the hard guardrail?
- whether fallback to premium is blocked once budget is exhausted

The code strongly suggests a **hybrid** model is the best fit for the slice title and roadmap language: graceful downgrade when request can still succeed locally, explicit denial when the caller/policy requires premium. That matches the milestone wording better than deny-only.

### Seam 3 — Simulation + operator evidence
Risk: medium.

Likely files:
- `src/nebula/services/policy_simulation_service.py`
- `tests/test_service_flows.py`
- `tests/test_governance_api.py`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`

Planner note: because simulation already reuses `PolicyService.evaluate()`, most work is likely expectation/copy/output refinement, not a new engine.

### Seam 4 — Observability/docs closeout
Risk: low-medium.

Likely files:
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `docs/route-decision-vocabulary.md`
- likely a new focused doc for budget semantics under `docs/`

Planner note: keep operator-facing evidence stable and labeled. S01 established this as a pattern and D023/D024 reinforce it.

## Key Findings and Constraints

### 1) Hard per-request guardrails already exist; the missing piece is cumulative spend behavior
The repo already enforces `max_premium_cost_per_request` in `PolicyService.evaluate()` and has full runtime/API correlation tests for it. S03 therefore should not “rebuild guardrails”; it should add the missing **hard cumulative budget** semantics and graceful downgrade behavior around them.

### 2) `soft_budget_usd` is explicitly advisory today
Multiple tests and console copy hardcode the phrase that soft budget “does not block routing in Phase 4.” S03 will need to preserve this field as advisory or deliberately supersede it with new hard-budget fields. Reusing `soft_budget_usd` for hard enforcement would create semantic drift and test churn. Prefer new explicit fields over mutating the meaning of the soft field.

### 3) `tenant_spend_total()` is already the right enforcement primitive
`GovernanceStore.tenant_spend_total()` sums completed/fallback/cache-hit estimated costs and already supports `before_timestamp`, which is especially useful for simulation windows. This means no new spend aggregation service is needed.

### 4) Simulation architecture is already aligned with S03
`PolicySimulationService` delegates candidate-policy evaluation to `PolicyService.evaluate()`. That is a strong existing pattern: any hard-budget rule added in `PolicyService` automatically flows into preview-before-save UX. This is the most important integration shortcut in the slice.

### 5) Route vocabulary already reserves budget evidence space
`docs/route-decision-vocabulary.md` includes `budget_proximity` and `policy_budget_advisory`, but runtime routing does not actually compute them yet. S03 can either:
- finally make `budget_proximity` real as part of route decision evidence, or
- keep budget outcomes in `policy_outcome` only and defer route-signal enrichment.

Given R041’s emphasis on “explainable recorded outcomes,” I recommend at least populating budget evidence in operator-visible surfaces, but not overcomplicating the router if enforcement can stay in `PolicyService`.

### 6) Keep override paths signal-free
S01’s summary and decision D023 explicitly say override routes should remain signal-free. If a request is explicitly premium and then denied for budget reasons, preserve the explicit route reason and put the budget explanation in `policy_outcome` and/or denial detail rather than synthesizing heuristic route signals.

### 7) The console is already structured around field classes
`/v1/admin/policy/options` exposes backend-driven field classes. That’s the cleanest way to add hard-budget controls without embedding phase-specific logic into the React form.

## Skill Guidance Applied

Relevant installed skills:
- **`react-best-practices`** — applicable to `console/` work. Use it when implementing/refactoring policy UI so state flows stay explicit and client components stay narrowly responsible.
- **`test`** — applicable when adding or updating focused pytest/vitest coverage for the new guardrail semantics.

Suggested external skills discovered (not installed):
- FastAPI: `npx skills add wshobson/agents@fastapi-templates` (highest installs, directly relevant to admin/runtime route patterns)
- Next.js: `npx skills add wshobson/agents@nextjs-app-router-patterns` (highest installs, directly relevant to console page/component wiring)
- SQLAlchemy/Alembic: `npx skills add bobmatnyc/claude-mpm-skills@sqlalchemy-orm` (most installed relevant ORM skill found)

No extra library-doc lookup was needed because FastAPI, Pydantic, SQLAlchemy, React Query, and Next.js patterns are already established in this codebase.

## Planner-Facing Build Order

1. **Decide the policy contract** for hard cumulative budget enforcement and downgrade behavior.
   - This is the only ambiguous part of the slice.
   - Recommend explicit fields rather than overloading `soft_budget_usd`.

2. **Implement/verify `PolicyService` semantics**.
   - Add tests first or in lockstep.
   - Ensure `evaluate()` is the single source of truth so runtime and simulation match.

3. **Thread any new fields through persistence/admin option metadata**.
   - Backend model → DB model/migration → store hydration → admin API types.

4. **Update simulation outputs and console policy form**.
   - Reuse existing preview-before-save flow; don’t invent a new UX.

5. **Extend observability/docs** only after runtime semantics are stable.
   - Budget outcomes must read clearly in ledger detail and docs.

## Verification Plan

### Backend focused checks
Use focused tests first because they already encode the slice seam:
- `./.venv/bin/pytest tests/test_governance_runtime_hardening.py -x`
- `./.venv/bin/pytest tests/test_service_flows.py -k "simulation or runtime_policy" -x`
- `./.venv/bin/pytest tests/test_governance_api.py -k "policy_simulation or guardrail or policy_denied" -x`

### Broader backend regression
- `./.venv/bin/pytest tests/test_chat_completions.py tests/test_governance_api.py tests/test_service_flows.py tests/test_governance_runtime_hardening.py tests/test_response_headers.py -x`

### Console checks
- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`
- If UI copy/behavior changes materially, also run: `npm --prefix console run test -- --run src/lib/admin-api.test.ts`
- Optional higher-confidence flow: `make console-e2e` or focused Playwright on `console/e2e/policy.spec.ts`

### Proof expectations for slice completion
To claim S03 complete, verification should prove:
- a tenant policy can hard-stop premium spend beyond a configured cumulative threshold,
- the system downgrades to local when allowed and legible,
- the system denies when downgrade is impossible or incompatible with explicit premium requirements,
- simulation reproduces those outcomes against ledger-backed traffic,
- ledger/admin/console surfaces explain what happened without raw JSON spelunking.

## Watchouts

- Do **not** scatter spend checks across `ChatService` fallback branches; that will fork runtime vs simulation semantics.
- Do **not** silently repurpose `soft_budget_usd` into a hard guardrail; existing tests/docs/UI define it as advisory.
- If you add new policy fields, remember the S01 persistence lesson: update DB model, write path, read hydration, API schema, and TS contract together.
- If router budget signals are introduced, keep explicit override paths signal-free.
- Preserve R044 discipline: no analytics-product drift, no broad public API expansion, no hosted-plane authority changes.
