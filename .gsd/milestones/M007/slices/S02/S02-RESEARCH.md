# S02 Research — Tighten supporting evidence and preview contracts

## Summary

S02 supports R050-R055, with the slice pressure concentrated on R052-R054: tighten the supporting data/UI seams so Observability and policy preview make the next operator action clearer without reopening S01’s page-identity decision or widening into dashboard/analytics scope. This is targeted work in an established Next.js 15 / React 19 / TanStack Query console. The existing structure already matches D040/D041 and the M007 knowledge rule: keep selected request evidence primary, use DOM-order and scoped negative assertions to guard boundaries, and avoid inventing new authority surfaces.

The important implementation question is not “what should these pages be?” anymore. S01 answered that. The question for S02 is whether the current bounded contracts expose enough decision-oriented evidence for later S03/S04 restructuring. Current evidence suggests two likely seams: (1) policy simulation response/preview presentation is still aggregate-plus-sample, but not yet explicitly comparison-first at the decision level; (2) Observability supporting context is still tenant-summary-shaped, which is compatible with S01 but may need tighter linkage to the selected request/follow-up action.

## Recommendation

Plan S02 as two bounded units:

1. **Contract-tightening pass first** across backend/shared admin types if execution confirms existing response fields are insufficient for clearer operator follow-up or if the runtime/admin contract mismatch around policy options is real.
2. **Console consumption pass second** in Observability and policy preview, reusing S01’s page-role contract and test pattern rather than re-arguing hierarchy in copy.

Keep request detail authoritative and unchanged in role. Only extend it if a new supporting seam needs a clearer handoff from request evidence to follow-up action. Avoid introducing a new page, dashboard summary, trend surface, or free-form analytics explanation.

## Implementation Landscape

### Console files already carrying the slice

- `console/src/app/(console)/observability/page.tsx`
  - Page is already explicitly request-first.
  - Pulls three independent data sources: ledger rows, tenant recommendations bundle, runtime health.
  - Supporting context section currently mixes recommendation cards, calibration summary, cache posture, and dependency health.
  - Natural seam for S02: tighten how supporting context points back to the selected request and implied next action, without changing the top-level section order S01 locked.

- `console/src/components/ledger/ledger-request-detail.tsx`
  - Authoritative persisted evidence seam for one selected row.
  - Already includes structured supporting interpretation for calibration, budget, and routing inspection.
  - Natural seam for S02: preserve as authoritative row-level evidence; only add bounded follow-up cues if needed. Do not convert into a tenant-summary surface.

- `console/src/components/ledger/ledger-table.tsx`
  - Current selection surface for the lead request object.
  - Table columns are timestamp/request/tenant/route/provider/status/latency/cost.
  - If S02 needs stronger investigation cues, this is the likely place for minimal row affordance changes rather than new summary cards.

- `console/src/components/ledger/ledger-filters.tsx`
  - Current filter surface used by Observability.
  - If supporting evidence needs tighter scoping to a request window/tenant window, this is the existing seam.

- `console/src/app/(console)/policy/page.tsx`
  - Owns tenant selection and the simulation/save mutations.
  - Simulation currently requests `limit: 50`, `changed_sample_limit: 5` and stores one `latestSimulation` blob.
  - Natural seam for S02: if clearer preview contracts require additional fields or separate baseline/simulated summaries, the page-level query/mutation plumbing already exists.

- `console/src/components/policy/policy-form.tsx`
  - Main preview-before-save implementation.
  - Current preview shows 4 aggregate metrics, one replay-window note, bounded changed-request sample, and approximation notes.
  - Existing helper functions already encode route parity and changed-request summaries cleanly.
  - Natural seam for S02: enrich comparison framing here rather than inventing another policy-preview component.

- `console/src/lib/admin-api.ts`
  - Shared frontend contract seam for `RecommendationBundle`, `PolicySimulationResponse`, `PolicySimulationChangedRequest`, `CalibrationEvidenceSummary`, and `PolicyOptionsResponse`.
  - Any backend shape change should land here first, then flow into page/components/tests.

### Backend files most relevant if contracts need tightening

- `src/nebula/models/governance.py`
  - Canonical backend schema for `PolicySimulationResponse`, `PolicySimulationChangedRequest`, `RecommendationBundle`, `RecommendationCard`, `CacheControlSummary`.
  - Strong boundedness already exists: changed requests are sampled, recommendation evidence is max 4 items, recommendations max 3, cache insights max 2.
  - This is the first place to extend if S02 needs more explicit decision-oriented fields while preserving bounded scope.

- `src/nebula/services/policy_simulation_service.py`
  - Simulation is intentionally metadata-only and deterministic.
  - Returns summary counts, bounded changed-request sample, approximation notes, and `calibration_summary` for the replay window.
  - Change detection already treats route/status/policy/cost deltas as meaningful, per M005 knowledge.
  - Natural seam for S02 if preview needs stronger baseline-vs-simulated comparison primitives.

- `src/nebula/services/recommendation_service.py`
  - Recommendations remain tenant-scoped, deterministic, and read-only.
  - Current output is intentionally generic operator guidance plus evidence tuples.
  - Natural seam for S02 only if supporting context needs a more explicit “why this matters now / what to do next” contract and current `title/summary/recommended_action/evidence` is insufficient.

- `src/nebula/api/routes/admin.py`
  - Admin API wiring for `/tenants/{tenant_id}/recommendations`, `/tenants/{tenant_id}/policy/simulate`, and `/policy/options`.
  - **Watch item:** `get_policy_options()` currently returns runtime-enforced fields that include `routing_mode_default`, `calibrated_routing_enabled`, `allowed_premium_models`, `semantic_cache_enabled`, `fallback_enabled`, `max_premium_cost_per_request`, `hard_budget_limit_usd`, `hard_budget_enforcement`, but not `semantic_cache_similarity_threshold` or `semantic_cache_max_entry_age_hours`. Console fixtures/tests currently treat both cache tuning fields as runtime-enforced. Execution should verify whether this is an intentional contract or a real mismatch.

## What to Build or Prove First

1. **Resolve the policy-options contract truth first.**
   - If cache tuning fields are supposed to be runtime-enforced, align `src/nebula/api/routes/admin.py` with the frontend fixtures/types/tests before any preview/UI tightening. Otherwise later policy work will rest on a drifting contract.

2. **Decide whether simulation needs backend shape changes or only better rendering.**
   - Current shape already provides: replay window, aggregate counts, calibration summary, and bounded changed-request sample with parity fields.
   - If that is enough, keep backend unchanged and rework `policy-form.tsx` presentation only.
   - If not, add only minimal bounded fields that strengthen save/don’t-save clarity.

3. **Tighten supporting context in Observability without changing top-level hierarchy.**
   - `page.tsx` section order is already the contract from S01.
   - S02 should make supporting cards more obviously subordinate/actionable, not move them ahead of the selected request.

4. **Keep request detail stable unless a handoff gap appears.**
   - `ledger-request-detail.tsx` is already a strong authoritative seam and later slices depend on that stability.

## Verification

Primary focused console verification:

- `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`

Add backend verification if any contract shape changes land:

- `./.venv/bin/pytest tests/test_governance_api.py -k "simulation or recommendations or policy_options" -x`
- `./.venv/bin/pytest tests/test_service_flows.py -k "simulation or recommendation or cache" -x`

Targeted proof to add/strengthen in tests:

- Observability supporting-context assertions should keep selected-request evidence first and use scoped assertions (`within(...)`) when duplicated calibration labels appear, per M006 knowledge.
- Policy preview assertions should prove comparison-first/save-explicit behavior, not just presence of changed rows.
- Negative assertions should continue blocking `dashboard`, `routing studio`, and `analytics product` drift.
- If backend contracts change, assert boundedness remains intact (sample limits, max recommendation counts, deterministic ordering).

## Constraints and Patterns to Reuse

- From `react-best-practices` skill: keep this as local React/Next.js refinement, not a new abstraction layer. Existing components already own the right seams; extend them instead of introducing new indirection.
- From project knowledge / S01 summary:
  - Prefer DOM-order assertions plus scoped negative checks over copy-only tests.
  - Keep the selected persisted ledger row as the lead evidence object.
  - Keep policy preview read-only until save is explicitly chosen.
  - Render rollout-disabled/unscored parity states as first-class output, not missing data.
- From M005 knowledge:
  - Simulation changes are not route-target-only; policy outcome and projected cost deltas also matter.
  - Recommendation surfaces must stay bounded and typed.
- From M006 knowledge:
  - Observability assertions should scope duplicate labels to the intended card/section.
  - Request-first inspection framing is authoritative; supporting cards explain but do not replace the row.

## Risks / Watch Items

- Copy-only cleanup would miss the real slice goal. Any change should tighten actionable seams or contract clarity, not just wording.
- Overcorrecting Observability into tenant-posture summary would regress R050/R051 and S01.
- Overexpanding policy simulation into analytics or routing-studio behavior would regress R055/R044 scope discipline.
- If the `policy/options` runtime-enforced field mismatch is real, it can create subtle UI/contract drift and should be settled before later M007 policy work.

## Skill Discovery Notes

Installed/relevant skills already present:

- `react-best-practices` — relevant for React/Next.js refactors in `console/`; use its guidance to keep changes local and avoid unnecessary abstraction.
- `frontend-design` / `make-interfaces-feel-better` exist but are not primary for this slice; M007 is product-clarity, not visual-polish work.

Promising external skills discovered but not installed:

- Next.js: `npx skills add wshobson/agents@nextjs-app-router-patterns`
- TanStack Query: `npx skills add deckardger/tanstack-agent-skills@tanstack-query-best-practices`

These are optional. The current codebase already has enough local precedent for this slice.
