# S02 Research — Policy simulation loop

## Summary

S02 primarily advances **R040** and materially supports **R044**. The core backend pieces needed for simulation already exist in assembled form: S01 established a stable route-decision vocabulary (`docs/route-decision-vocabulary.md`), persisted route signals into the usage ledger (`src/nebula/db/models.py`, `src/nebula/services/governance_store.py`), and exposed policy/routing outcomes through the admin ledger and operator UI. What is missing is a **non-mutating replay path** that can evaluate a candidate tenant policy against **recent ledger-backed traffic** and return grounded projected outcomes before save.

This is **targeted research**, not deep: the tech is familiar and the codebase already has the right seams. The slice should be built around a new simulation service + admin route + console policy-page integration, reusing existing `PolicyService`, `RouterService`, `GovernanceStore`, and ledger DTOs rather than inventing a parallel analytics model.

## Recommendation

Build S02 as a narrow **ledger replay simulation** loop:

1. **Backend first:** add a simulation-only service that loads recent usage-ledger rows, reconstructs minimal chat requests from persisted fields/signals, re-runs `PolicyService.resolve(...)` plus routing decision logic against a **candidate `TenantPolicy`**, and returns aggregate/projected results.
2. **API second:** expose this via a new admin endpoint under the existing admin/policy surface, scoped to a tenant and recent-traffic filter window.
3. **UI third:** integrate simulation into the policy editor as a “preview before save” action that uses the current unsaved form state and renders a compact result summary plus changed-outcome breakdown.
4. **Proof:** verify with focused backend tests for replay semantics and console tests for policy-page preview UX; avoid broad e2e unless needed.

This aligns with the project’s existing patterns and supports the requirement without drifting into a generic analytics product. It also follows the available **react-best-practices** skill guidance implicitly: keep Next.js/React work narrowly stateful and colocated in page/form seams rather than over-distributing mutation logic.

## Implementation Landscape

### Existing backend seams

- `src/nebula/services/policy_service.py`
  - Already computes the decisioning contract that matters for simulation: `PolicyResolution` includes `route_decision`, `policy_mode`, `cache_enabled`, `fallback_enabled`, `policy_outcome`, `soft_budget_exceeded`, and `projected_premium_cost`.
  - Important detail: `resolve()` already computes **projected premium cost** for premium routes via `_estimate_request_cost()`, and already incorporates **tenant cumulative spend** through `tenant_spend_total()` for soft-budget logic.
  - This is the correct seam for simulation. Do **not** duplicate rule evaluation in a second “simulator rules” implementation.

- `src/nebula/services/router_service.py`
  - S01 made the route decision model interpretable and stable. `choose_target_with_reason()` produces `RouteDecision(target, reason, signals, score)`.
  - It currently depends only on prompt/request/routing mode/policy. That makes it replayable for simulation.
  - `budget_proximity` is still a placeholder (`None`) despite existing vocabulary/docs claiming a spend-ratio meaning. S02 should not assume it is populated unless the slice explicitly adds it.

- `src/nebula/services/chat_service.py`
  - `_resolve_policy()` already records denied requests into the ledger on `HTTPException(403)` with `final_route_target="denied"`, route reason, and policy outcome.
  - `_record_usage()` centralizes persisted terminal outcomes for completion requests.
  - For S02, this file is useful as the source of runtime truth about terminal statuses and persisted semantics, but the simulation path should likely live outside `ChatService` to avoid fake provider execution.

- `src/nebula/services/governance_store.py`
  - Already exposes `list_usage_records(...)`, `tenant_spend_total(...)`, `get_policy(...)`, and `upsert_policy(...)`.
  - `list_usage_records()` supports request, tenant, terminal status, route target, and time-window filters and returns `UsageLedgerRecord`s ordered newest-first with a limit.
  - This is almost enough for simulation traffic selection. The natural extension is either:
    - reuse `list_usage_records()` directly from a new simulation service, or
    - add a simulation-specific read helper if replay needs different filtering/shape.
  - Existing store already maps `route_signals` back out in `_usage_from_model()`, which matters because S01 fixed a prior hydration omission.

- `src/nebula/api/routes/admin.py`
  - Existing admin seams already cover policy CRUD and usage ledger reads.
  - Natural place for S02 endpoint(s): near `/tenants/{tenant_id}/policy` and `/usage/ledger`, not as a brand-new unrelated router.

- `src/nebula/models/governance.py`
  - Contains current admin DTOs: `TenantPolicy`, `UsageLedgerRecord`, `PolicyOptionsResponse`, etc.
  - S02 should add explicit simulation request/response models here rather than passing untyped dicts through the admin API.

### Existing frontend seams

- `console/src/app/(console)/policy/page.tsx`
  - Loads tenants, tenant policy, policy options, and saves via `updateTenantPolicy(...)` mutation.
  - This page is the correct container for a simulation query/mutation because it already owns selected tenant + policy lifecycle.

- `console/src/components/policy/policy-form.tsx`
  - Current form state already tracks the exact editable fields needed to build a candidate `TenantPolicy` payload.
  - The clean seam is to add a **simulate action** using the same `toPolicyPayload(...)` output as save, while keeping save explicit.
  - This preserves R044 scope discipline: preview-before-save inside the existing policy editor, not a separate analytics dashboard.

- `console/src/lib/admin-api.ts`
  - Shared admin client already centralizes policy and ledger endpoints.
  - S02 should add typed simulation request/response types and a client function here.

- `console/src/app/(console)/observability/page.tsx`
  - Useful reference for existing operator evidence framing and ledger filters, but probably not the primary entry point for S02. The roadmap/context says policy editor and observability are involved, but the clean first implementation is policy page first.

### Existing proof/test seams

- `tests/test_service_flows.py`
  - Good unit-level seam for simulation service behavior because the file already uses fakes/stubs for `PolicyService`, `ChatService`, and store-level behavior.

- `tests/test_governance_api.py`
  - Good API-level seam for a new simulation endpoint because it already covers admin policy APIs, ledger correlation, denied behavior, and policy enforcement.

- `console/src/components/policy/policy-form.test.tsx`
  - Best place for preview-button/form-state interaction tests.

- `console/src/app/(console)/policy/page.tsx` / surrounding tests
  - Best place for page-level query/mutation wiring tests if a separate page test is needed.

## Natural seams for task decomposition

### Seam 1 — Simulation contract and backend replay engine

Likely files:
- `src/nebula/models/governance.py`
- new `src/nebula/services/policy_simulation_service.py` (recommended)
- `src/nebula/services/governance_store.py` (maybe helper additions only)
- `src/nebula/core/container.py` (to wire the new service)

This is the riskiest seam and should be built first because it determines what the UI can honestly display.

### Seam 2 — Admin route exposure

Likely files:
- `src/nebula/api/routes/admin.py`
- `src/nebula/models/governance.py`
- tests in `tests/test_governance_api.py`

Expose the replay result with explicit request/response models and tenant scoping.

### Seam 3 — Policy editor preview UX

Likely files:
- `console/src/lib/admin-api.ts`
- `console/src/app/(console)/policy/page.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- maybe `console/src/components/policy/*` for a dedicated preview panel component if the UI becomes dense

Keep this as a narrow enhancement to the save flow: draft policy → simulate → inspect summary → save if desired.

## What to build or prove first

1. **Replay semantics over recent ledger traffic**
   - Prove that S02 can select real recent tenant traffic from the ledger and produce stable summary output without hitting providers.
2. **Candidate-policy evaluation fidelity**
   - Prove simulation uses the same policy/routing logic as runtime (`PolicyService.resolve`, `RouterService`) rather than a copy.
3. **Explainable delta output**
   - Prove the result can answer operator questions like:
     - how many requests would route local vs premium vs denied?
     - how many would newly deny?
     - how many would change route target?
     - what policy outcomes/reasons dominate?
4. **Preview-before-save UX**
   - Prove operators can simulate the currently edited policy without persisting it.

## Likely design constraints and surprises

- **There is no raw prompt in the usage ledger.**
  - `UsageLedgerRecord` persists request metadata, route/policy evidence, token counts, costs, statuses, and signals — but not request messages/content.
  - Therefore a faithful replay of `RouterService.choose_target_with_reason(prompt, request, ...)` cannot reconstruct the original prompt exactly from ledger alone.
  - This is the major S02 constraint.

- **S01 intentionally made route signals stable enough for replay.**
  - `docs/route-decision-vocabulary.md` explicitly says S02 simulation depends on these names for ledger replay.
  - That means simulation can and should use persisted signals as evidence/input where prompt text is unavailable.

- **Current router API is prompt-driven, but replay data is signal-driven.**
  - This mismatch is the main architectural decision for S02.
  - Cleanest path: add a replay-oriented method to router logic (or the new simulation service) that derives a simulated route from persisted signal values + requested model + candidate policy, rather than inventing fake prompts.
  - Avoid broad refactors unless necessary; a narrow, explicit replay path is acceptable if it reuses the same vocabulary and threshold semantics.

- **PolicyService already computes spend-aware projected denial for premium requests.**
  - This can feed useful simulation output immediately, especially around `max_premium_cost_per_request` and `soft_budget_usd` effects.

- **Scope discipline matters.**
  - R044 means the result should be recommendation-grade enough to preview a policy change, but not a full warehouse/reporting product. Return compact aggregates and a bounded sample of changed requests, not arbitrary BI dimensions.

## Suggested simulation shape

A practical S02 response should include:

- simulation window metadata
  - tenant id
  - number of ledger rows evaluated
  - from/to timestamps used
- candidate policy echo
- aggregate baseline vs simulated counts
  - by route target (`local`, `premium`, `cache`, `denied` where applicable)
  - by terminal/policy effect category
- change summary
  - `changed_request_count`
  - `newly_denied_count`
  - `route_target_changed_count`
  - `estimated_premium_cost_delta` (aggregate)
- top reasons / top policy outcomes
- bounded changed-request sample
  - request id
  - original final route target
  - simulated route target
  - original route reason
  - simulated route reason
  - original policy outcome
  - simulated policy outcome

That is enough to support trust and operator action without becoming an analytics product.

## Suggested replay strategy

Given ledger-only traffic, the likely replay inputs per row are:

- `requested_model`
- `route_signals`
- `route_reason`
- `prompt_tokens` / `total_tokens`
- `estimated_cost`
- `terminal_status`
- candidate `TenantPolicy`

Recommended approach:

- Create a simulation service that treats runtime behavior in two layers:
  1. **routing replay layer** using S01 signal vocabulary (`token_count` / `complexity_tier` / `keyword_match` / `model_constraint`) to reproduce the heuristic routing path under a candidate policy
  2. **policy evaluation layer** reusing `PolicyService` cost/guardrail logic where possible

Because raw prompts are absent, the planner should avoid “re-run exact completion request” designs.

## Verification plan

### Backend

Focused tests should cover:

- candidate policy simulation against recent ledger rows returns bounded aggregates
- simulation can identify route-target changes when routing mode or allowlist changes
- simulation can identify new denials from `max_premium_cost_per_request`
- simulation remains tenant-scoped and recent-traffic-scoped
- simulation does not mutate policy or usage ledger

Most likely commands:
- `./.venv/bin/pytest tests/test_governance_api.py -k simulation -x`
- `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x`

### Console

Focused tests should cover:

- policy form can request a simulation with unsaved draft values
- preview results render summary/delta state without saving
- save action remains explicit and separate from simulation

Most likely command:
- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx`

If page wiring gets substantial, also run:
- `npm --prefix console run test -- --run src/app/'(console)'/policy/page.tsx`

### Slice-level assembled check

- `./.venv/bin/pytest tests/test_governance_api.py tests/test_service_flows.py -k 'simulation or policy' -x`
- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`

## Skill discovery

Installed/relevant skills already available:
- **react-best-practices** — relevant for Next.js/React policy-page state and mutation wiring.
- **test** — useful when generating or tightening focused tests for the new backend/UI seams.

Promising external skills not installed:
- FastAPI: `npx skills add wshobson/agents@fastapi-templates`
- Next.js: `npx skills add wshobson/agents@nextjs-app-router-patterns`
- PostgreSQL/data modeling: `npx skills add wshobson/agents@postgresql-table-design`

These are relevant but not required; the existing codebase patterns are already sufficient for S02.

## Planner notes

- Keep S02 **policy-page-first** on the UI, not observability-first.
- Do not require prompt persistence; work with ledger-backed evidence already present.
- Prefer a dedicated simulation service over bloating `ChatService`.
- Add typed simulation DTOs in `src/nebula/models/governance.py` and `console/src/lib/admin-api.ts` to keep the contract stable.
- Preserve explicit save semantics: simulation previews a candidate policy, but nothing persists until the existing save mutation runs.
- If replay fidelity becomes contentious, bias toward explicit documented approximation grounded in S01 signals rather than hidden heuristics. That better satisfies both R040 and R044.