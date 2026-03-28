# S04: Recommendations and cache controls

**Goal:** Deliver grounded operator recommendations and semantic-cache control surfaces by deriving bounded recommendation/cache summaries from ledger-backed evidence, exposing them through a narrow admin contract, and rendering them in existing Observability and policy surfaces without widening Nebula into analytics or cache-management scope.
**Demo:** After this: Operators can see grounded next-best-action guidance and tune semantic-cache behavior with enough visibility to improve results intentionally.

## Tasks
- [x] **T01: Added typed recommendation and cache-summary backend contracts with deterministic read-only service coverage.** — Why: S04 depends on a narrow, deterministic backend seam that turns existing ledger, simulation, hard-budget, and runtime-cache facts into bounded operator guidance before any API or UI work can stay honest.

Steps:
1. Extend `src/nebula/models/governance.py` with typed recommendation and cache-summary DTOs plus any minimal tenant policy fields required for cache tuning, keeping the response bounded and operator-readable.
2. Implement `src/nebula/services/recommendation_service.py` to derive tenant-scoped recommendations and cache insights from `list_usage_records(...)`, hard-budget/policy outcomes, cache-hit history, avoided premium-cost estimates, and runtime cache health without writing policies, usage rows, or cache data.
3. Wire the new service through `src/nebula/core/container.py` and add focused service tests in `tests/test_service_flows.py` for deterministic recommendation ordering, bounded output, degraded-cache insight behavior, and no-mutation guarantees.

Must-haves:
- Introduce stable DTOs for recommendation cards and cache insight summaries rather than free-form dicts.
- Keep recommendation logic ledger-backed and scope-disciplined under R044; do not depend on raw prompt text, opaque scoring, or Qdrant entry inspection.
- If cache tuning needs more than `semantic_cache_enabled`, add only the smallest explicit policy knobs needed and carry them through the shared model contract here.

Verification:
- `./.venv/bin/pytest tests/test_service_flows.py -k "recommendation or cache" -x`
- Service tests prove bounded recommendation/cache output, degraded-health visibility, and zero policy/usage mutation side effects.

Inputs:
- `src/nebula/models/governance.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/semantic_cache_service.py`
- `src/nebula/services/policy_simulation_service.py`
- `src/nebula/core/container.py`
- `tests/test_service_flows.py`

Expected output:
- `src/nebula/models/governance.py`
- `src/nebula/services/recommendation_service.py`
- `src/nebula/core/container.py`
- `tests/test_service_flows.py`
  - Estimate: 1.5h
  - Files: src/nebula/models/governance.py, src/nebula/services/recommendation_service.py, src/nebula/services/governance_store.py, src/nebula/services/semantic_cache_service.py, src/nebula/core/container.py, tests/test_service_flows.py
  - Verify: ./.venv/bin/pytest tests/test_service_flows.py -k "recommendation or cache" -x
- [ ] **T02: Expose tenant recommendation API and console contracts** — Why: Once the backend derivation seam exists, S04 needs one narrow admin contract and shared frontend typings so Observability and policy surfaces can consume the same tenant-scoped evidence without duplicating heuristics.

Steps:
1. Add tenant-scoped admin endpoint wiring in `src/nebula/api/routes/admin.py` for the compact recommendation/cache summary response, including tenant existence checks and admin-only protection.
2. Extend `console/src/lib/admin-api.ts` with the new response types and fetch helper, reusing the shared typed contract instead of ad-hoc UI parsing.
3. Add focused API tests in `tests/test_governance_api.py` for auth, 404 handling, bounded response structure, tenant scoping, and degraded-cache evidence propagation.

Must-haves:
- Keep the API surface narrow: one compact read path for tenant recommendations/cache insight unless tests prove a second endpoint is necessary.
- Preserve admin-only and tenant-scoped semantics with explicit 404 behavior for missing tenants.
- Ensure the response stays bounded and deterministic enough for UI rendering and future S05 proof work.

Verification:
- `./.venv/bin/pytest tests/test_governance_api.py -k "recommendation or cache" -x`
- API tests prove admin protection, tenant scoping, bounded structure, and degraded-cache evidence behavior.

Inputs:
- `src/nebula/api/routes/admin.py`
- `src/nebula/models/governance.py`
- `src/nebula/core/container.py`
- `console/src/lib/admin-api.ts`
- `tests/test_governance_api.py`
- `tests/test_service_flows.py`

Expected output:
- `src/nebula/api/routes/admin.py`
- `console/src/lib/admin-api.ts`
- `tests/test_governance_api.py`
  - Estimate: 1h
  - Files: src/nebula/api/routes/admin.py, src/nebula/models/governance.py, src/nebula/core/container.py, console/src/lib/admin-api.ts, tests/test_governance_api.py
  - Verify: ./.venv/bin/pytest tests/test_governance_api.py -k "recommendation or cache" -x
- [ ] **T03: Render observability recommendations and cache controls in existing operator surfaces** — Why: S04 is only true when operators can actually see grounded next-best-action guidance and tune cache behavior intentionally through existing product surfaces, not just via backend contracts.

Steps:
1. Update `console/src/app/(console)/observability/page.tsx` to fetch the new tenant recommendation/cache summary alongside ledger/runtime health and render bounded recommendation cards plus cache-effectiveness context with copy grounded in ledger-backed evidence.
2. Extend `console/src/components/policy/policy-form.tsx` (and page wiring if needed) so cache tuning remains in the existing policy editor, with any new cache knobs grouped as runtime-enforced controls and evidence-oriented copy that avoids implying autosave or autonomous optimization.
3. Add/align focused Vitest coverage in `console/src/app/(console)/observability/page.test.tsx`, `console/src/app/(console)/observability/observability-page.test.tsx`, `console/src/components/policy/policy-form.test.tsx`, and `console/src/components/policy/policy-page.test.tsx` for recommendation framing, cache insight visibility, and cache-control save/preview behavior.

Must-haves:
- Observability copy must explicitly say recommendations are based on recent ledger-backed traffic and supporting runtime context, not black-box optimization.
- Policy-page work must keep cache tuning in the existing save/preview flow and avoid creating a separate cache-management area.
- Normalize the existing observability wording drift in tests while preserving the established persisted-evidence framing.

Verification:
- `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`
- UI tests prove recommendation cards, cache insight context, and cache-control save/preview semantics render on the intended surfaces.

Inputs:
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `console/src/lib/admin-api.ts`

Expected output:
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
  - Estimate: 1.5h
  - Files: console/src/app/(console)/observability/page.tsx, console/src/app/(console)/observability/page.test.tsx, console/src/app/(console)/observability/observability-page.test.tsx, console/src/components/policy/policy-form.tsx, console/src/components/policy/policy-form.test.tsx, console/src/components/policy/policy-page.test.tsx, console/src/lib/admin-api.ts
  - Verify: npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx
