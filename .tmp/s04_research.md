# S04: Recommendations and cache controls — Research

## Summary

Active requirements for this slice are **R042** (recommendation-grade operator feedback) and **R043** (semantic cache becomes tunable and inspectable), with **R044** as the scope guard. This is **targeted research**, not deep/new-tech work: the backend already has the needed factual seams (usage ledger, route signals, policy simulation, hard-budget outcomes, benchmark report structures, semantic-cache runtime health), and the console already has the right operator surfaces (Policy preview, Observability ledger detail, dependency health). The main work is to add a **narrow recommendation/cache-control contract** that reuses existing evidence rather than inventing a separate analytics subsystem.

Best implementation direction: keep S04 **observability-first for display**, but **policy-page-adjacent for cache tuning controls**. Backend should compute compact recommendation + cache insight summaries from ledger-backed evidence and existing policy semantics; console should render them in Observability and reuse the policy editor for any actual tenant policy changes. This follows the existing project pattern of exposing new decisioning semantics through stable labeled fields on existing operator surfaces before adding new product areas (same pattern used in S01/S03).

Relevant installed skills already present:
- **react-best-practices** — applies to new React/Next.js operator UI and recommends keeping data-fetching and UI seams explicit.
- **best-practices** — relevant for keeping the new API/UI narrow and explainable.

Promising non-installed skills discovered for directly relevant tech:
- FastAPI: `npx skills add wshobson/agents@fastapi-templates`
- Next.js: `npx skills add wshobson/agents@nextjs-app-router-patterns`
- Qdrant: `npx skills add davila7/claude-code-templates@qdrant-vector-search`
These are optional; current slice looks implementable without them because the codebase patterns are already established.

## Recommendation

Implement S04 as **three seams in order**:

1. **Backend recommendation/cache-summary seam first**
   - Add typed admin response models and a backend service that derives:
     - compact recommendation cards grounded in recent ledger + simulation/budget evidence
     - compact cache insight metrics grounded in recorded `cache_hit`, route mix, and current runtime cache health
   - Keep outputs bounded and operator-readable, not BI-shaped.

2. **Admin API + console read surfaces second**
   - Expose one or two read endpoints under existing admin surfaces.
   - Render recommendation-grade feedback in **Observability** because that page already frames itself as persisted operator evidence plus supporting runtime context.
   - Render cache tuning visibility either in Observability or as a policy-page evidence panel, but keep the actual editing path in the **existing policy form**.

3. **Policy cache controls last**
   - If R043 needs more than the existing boolean `semantic_cache_enabled`, add the smallest explicit policy knobs necessary and thread them through persistence/admin/policy form using the S03 pattern.
   - Avoid expanding into cache management operations, invalidation workflows, dataset inspection, or Qdrant administration.

## Implementation Landscape

### Existing backend seams

- `src/nebula/services/policy_simulation_service.py`
  - Already replays recent tenant ledger rows oldest-first, returns bounded aggregates plus changed-request samples, and includes approximation notes.
  - Downstream-ready for S04 because S02 explicitly established it as a reusable replay-only seam for recommendation work.
  - Natural reuse path: recommendation service can either call this service or mirror its evaluation vocabulary (`changed_routes`, `newly_denied`, cost delta, changed requests).

- `src/nebula/services/policy_service.py`
  - Central source of truth for routing/policy evaluation and hard-budget semantics.
  - Emits stable `policy_outcome` fragments like `soft_budget=exceeded`, `hard_budget=exceeded(...)`, and `budget_action=downgraded_to_local`.
  - S04 should treat these strings as factual evidence, not infer budget pressure from raw spend.

- `src/nebula/services/router_service.py`
  - Produces the stable route-signal vocabulary already persisted in the ledger: `token_count`, `complexity_tier`, `budget_proximity` (currently always `None`), `model_constraint`, `keyword_match`, plus `replay` in replay mode.
  - `budget_proximity` is present but not implemented; do **not** make S04 depend on it unless the slice explicitly decides to finish that signal.

- `src/nebula/services/governance_store.py`
  - Critical facts already available:
    - `list_usage_records(...)` with tenant/status/route/time filtering
    - `tenant_spend_total(..., before_timestamp=...)`
    - persisted `route_signals`, `policy_outcome`, `cache_hit`, `fallback_used`, `estimated_cost`, `latency_ms`, `terminal_status`
  - This is enough for compact recommendation generation without schema expansion if recommendations are derived on read.

- `src/nebula/services/semantic_cache_service.py`
  - Current cache functionality is intentionally minimal:
    - `lookup(prompt)` → response only
    - `store(prompt, response, model)`
    - payload includes `prompt`, `response`, `model`, `created_at`
    - health surface only says reachable/degraded/enabled
  - Important limitation: there is **no existing inspection API** for cache entries, no per-tenant keying, no threshold override per tenant, and no metrics beyond Prometheus lookup counters.
  - Therefore R043 should likely be satisfied by **control-plane visibility/tuning around observed request outcomes**, not by exposing raw Qdrant contents.

- `src/nebula/observability/metrics.py`
  - Only cache metric is `CACHE_LOOKUPS{result}`. No latency/hit-quality metrics split by tenant.
  - S04 may need additive metrics if backend tests require stronger proof, but operator UI can already rely on ledger `cache_hit` facts rather than Prometheus.

- `src/nebula/benchmarking/run.py`
  - Already computes compact summary/report structures with route distribution, cache hit rate, fallback rate, estimated premium cost, avoided premium cost, comparison groups, and key takeaways.
  - Good model for recommendation phrasing/aggregation: bounded summaries, not free-form analytics.
  - Strong candidate source for extracting helper patterns (not necessarily direct reuse) when defining recommendation response DTOs.

### Existing API/model seams

- `src/nebula/models/governance.py`
  - Holds the shared admin-facing typed models for policies, usage ledger, and simulation.
  - Best place to add new response DTOs for:
    - recommendation summary/cards
    - cache insight/tuning summary
    - optional tenant-scoped recommendation endpoint payloads
  - Also the place where any new **minimal** policy fields for cache tuning would need to be added.

- `src/nebula/api/routes/admin.py`
  - Current admin precedent is strong:
    - `GET /policy/options`
    - `POST /tenants/{tenant_id}/policy/simulate`
    - `GET /usage/ledger`
  - Natural S04 extension is additive read endpoints such as tenant-scoped recommendations and/or cache insights under `/admin/tenants/{tenant_id}/...`.
  - Follow the S02/S03 rule: non-mutating previews/insights should be explicit and bounded.

- `src/nebula/core/container.py`
  - Already wires simulation service separately; adding a dedicated recommendation/cache-insight service is straightforward.

### Existing console seams

- `console/src/app/(console)/observability/page.tsx`
  - Best fit for recommendation-grade feedback.
  - Page already frames itself as **persisted request explanation** plus dependency health context.
  - It already loads tenants, ledger rows, and runtime health. Adding another query for recommendation/cache summaries is a natural extension.
  - If new UI is added here, keep the wording evidence-based: “based on recent ledger-backed traffic”, “supporting runtime context”, “did not change policy”.

- `console/src/components/ledger/ledger-request-detail.tsx`
  - Already turns raw persisted policy and route data into labeled operator evidence sections.
  - Good place for **per-request cache evidence** if S04 needs request-detail-level explanation (e.g. recommendation rationale references cache hit/miss patterns), but not ideal for aggregate “next best action” cards.

- `console/src/app/(console)/policy/page.tsx`
  - Already has separate **simulate** and **save** mutations and clears previews on tenant switch/save.
  - This is a good home for **cache tuning controls** if new policy fields are added.

- `console/src/components/policy/policy-form.tsx`
  - Strong reference for how to present operator guidance without implying persistence.
  - If cache tuning adds more fields, follow the same grouping strategy used for hard budget vs soft budget:
    - runtime-enforced cache controls
    - evidence/explanation panel
  - Do not add autonomous “apply recommendation” behavior without explicit save semantics.

- `console/src/lib/admin-api.ts`
  - Central place for new frontend contracts and fetch helpers.

### Existing tests that matter

- `tests/test_service_flows.py`
  - Has the best focused backend/service-level precedent for simulation replay and change detection.
  - Natural home for recommendation service tests and cache-insight derivation tests.

- `tests/test_governance_api.py`
  - Already verifies policy options metadata, usage ledger facts, simulation semantics, and guardrail API behavior.
  - Natural home for admin endpoint tests for recommendation/cache-summary APIs.

- `console/src/components/policy/policy-form.test.tsx`
  - Strong precedent for preview-before-save, grouped control surfaces, and explicit copy.

- `console/src/components/policy/policy-page.test.tsx`
  - Good place if policy page gains cache-related controls or evidence panels.

- `console/src/app/(console)/observability/page.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx`
  - Existing observability framing tests are slightly divergent in wording (`Persisted request explanation` vs older `Persisted request evidence` expectations). Planner should expect to touch/realign tests if Observability copy changes.

- `console/src/components/ledger/ledger-request-detail.test.tsx`
  - Shows the established pattern: convert raw policy strings into structured evidence cards and test that structure explicitly.

## Natural seams for planning

### Seam 1 — backend recommendation service

Likely new file:
- `src/nebula/services/recommendation_service.py` (recommended)

Likely touched files:
- `src/nebula/models/governance.py`
- `src/nebula/core/container.py`
- `tests/test_service_flows.py`

Why this is a clean task:
- Pure derivation logic from existing ledger/simulation/policy facts.
- Can be built/tested without UI.
- Unblocks both API and console tasks.

What it should probably compute:
- bounded recommendation list (e.g. up to 3)
- each item with stable fields like:
  - `kind` / `category` (`routing`, `budget`, `cache`)
  - `title`
  - `summary`
  - `evidence` / `why_now`
  - `suggested_policy_changes` (if any)
  - `projected_impact` (compact, maybe route/cost/denial deltas)
- cache insight block such as:
  - recent cache-hit rate from usage ledger
  - avoided premium cost from cache hits
  - cache-disabled policy warning when hits could matter
  - runtime health/degraded reason if cache backend unavailable

### Seam 2 — admin API contract

Likely touched files:
- `src/nebula/api/routes/admin.py`
- `src/nebula/models/governance.py`
- `console/src/lib/admin-api.ts`
- `tests/test_governance_api.py`

Why this is a clean task:
- Mostly typed DTO wiring and explicit endpoint behavior.
- Can be verified independently of UI details.

Probable endpoint shapes:
- `GET /v1/admin/tenants/{tenant_id}/recommendations`
- possibly include cache insight in same response to stay narrow
- or separate `GET /v1/admin/tenants/{tenant_id}/cache-insights`

Recommendation: prefer **one compact endpoint** first to avoid surface sprawl unless tests/readability clearly benefit from separation.

### Seam 3 — Observability recommendation rendering

Likely touched files:
- `console/src/app/(console)/observability/page.tsx`
- possibly new component(s) under `console/src/components/observability/` or reuse existing panel patterns
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`

Why this is a clean task:
- Pure read UI using the new endpoint.
- Independent from policy editing if no new controls are added yet.

What to show:
- grounded next-best actions
- evidence basis tied to recent traffic
- compact projected impact
- cache effectiveness and runtime availability context
- copy that explicitly avoids auto-optimization claims

### Seam 4 — policy cache controls (only if needed)

Potential files:
- `src/nebula/models/governance.py`
- `src/nebula/db/models.py`
- migration file under `migrations/versions/`
- `src/nebula/services/governance_store.py`
- `src/nebula/api/routes/admin.py` (`/policy/options` metadata)
- `console/src/lib/admin-api.ts`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`

This is the riskiest scope seam. Only do it if R043 cannot honestly be satisfied with the existing `semantic_cache_enabled` plus new inspectability/recommendation surfaces. The current slice context says “tunable” semantic cache behavior, but the existing codebase has no per-tenant threshold/TTL/quality knobs. Adding those would require real product decisions and likely persistence changes.

## Risks / constraints / surprises

1. **No per-tenant cache tuning seam exists today**
   - `TenantPolicy` only has `semantic_cache_enabled: bool`.
   - `SemanticCacheService` only uses global settings (`semantic_cache_threshold`, collection name).
   - If planner assumes tenant-level threshold tuning is already wired, execution will stall.

2. **Qdrant cache is not tenant-scoped in stored payloads**
   - `store()` payload includes prompt/response/model/created_at only.
   - There is no tenant_id in stored cache payloads from current code.
   - That makes direct tenant-specific cache inspection/control tricky without additional design work.
   - Strong argument for S04 to stay at the ledger-observed behavior layer rather than raw cache-entry introspection.

3. **Ledger is the durable truth for operator evidence**
   - This is consistent across S01/S02/S03 and existing Observability framing.
   - Recommendation/cache summaries should be derived from ledger facts + runtime health, not from transient provider/cache internals.

4. **Observability tests already have wording drift**
   - There are two observability page tests with slightly different expected copy. Any UI change here should normalize tests early.

5. **`budget_proximity` signal is a stub**
   - Router emits the key but always leaves it `None`.
   - Do not build recommendation logic that depends on a meaningful value unless you intentionally finish that feature as part of S04.

6. **Scope creep pressure is high here**
   - It would be easy to turn “recommendations and cache controls” into dashboards, scoring engines, or cache-management UIs.
   - R044 and D022/D026 strongly argue for bounded recommendations + explicit controls only.

## What to prove first

1. **Recommendation service can produce useful, bounded output from existing evidence alone**
   - This retires the biggest uncertainty in R042/R043 without schema churn.

2. **Operator-visible cache insight can be grounded in ledger + runtime health**
   - If yes, planner can likely avoid a migration-heavy cache-control expansion.

3. **Whether additional cache policy fields are truly necessary**
   - If not necessary, keep S04 much narrower.
   - If necessary, isolate that as a later task after read-only insight surfaces are working.

## Suggested verification plan

Backend/service:
- `./.venv/bin/pytest tests/test_service_flows.py -k "recommendation or cache" -x`
- likely new focused tests proving:
  - recommendations are grounded in ledger/simulation/budget outcomes
  - recommendation list is bounded and deterministic
  - cache insights reflect `cache_hit`, route mix, avoided premium cost, and degraded runtime cache health
  - no mutation/persistence side effects from recommendation reads

Admin API:
- `./.venv/bin/pytest tests/test_governance_api.py -k "recommendation or cache" -x`
- likely new focused tests proving:
  - endpoint is admin-only and tenant-scoped
  - missing tenant returns 404
  - response structure contains compact recommendation/cache sections
  - outputs stay explicit and bounded

Console:
- `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`
- if only Observability changes, policy tests may be unnecessary; if cache controls are added to policy page, include both policy test files.

Optional integrated check if a new Observability section is added:
- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/page.test.tsx`

## Concrete file recommendations for the planner

Start by reading/touching these files first:
- `src/nebula/models/governance.py`
- `src/nebula/services/policy_simulation_service.py`
- `src/nebula/services/policy_service.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/semantic_cache_service.py`
- `src/nebula/api/routes/admin.py`
- `src/nebula/core/container.py`
- `console/src/lib/admin-api.ts`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/components/policy/policy-form.tsx`
- `tests/test_service_flows.py`
- `tests/test_governance_api.py`

Recommended initial decomposition:
1. backend derivation service + DTOs
2. admin endpoint wiring + API tests
3. observability UI rendering + UI tests
4. optional cache policy controls only if requirement proof still needs them

## Skill-informed implementation notes

- From the installed **react-best-practices** skill: keep React/Next data boundaries explicit and avoid conflating read-only recommendation fetches with save/update mutations. This matches the existing separation in `console/src/app/(console)/policy/page.tsx` between simulate and save.
- From the installed **best-practices** skill: prefer narrow, composable API surfaces and stable typed contracts over ad-hoc UI-only heuristics. That aligns with the existing `governance.py` + `admin-api.ts` pattern already used by S02/S03.
