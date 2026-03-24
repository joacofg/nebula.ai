# S04: Day-1 value proof surface — Research

**Date:** 2026-03-23

## Summary

S04 owns the still-active day-1 value requirements: **R005** (make routing, policy, observability, and provider abstraction visibly valuable immediately after integration) and **R009** (make route, fallback, and policy outcome visible during adoption and validation). The codebase already has most of the raw proof surfaces needed: public `X-Nebula-*` headers on the adoption route, `X-Request-ID` → `GET /v1/admin/usage/ledger` correlation from S03, the admin Playground's immediate-response metadata card, and the console Observability page's ledger + dependency-health views. The gap is not missing core runtime primitives; it is that the current docs and console surfaces still present these as adjacent pieces rather than one explicit “day-1 value” story.

Primary recommendation: treat S04 as a **targeted composition slice** across docs, console wording/presentation, and focused verification. Do not broaden the API contract or invent new backend abstractions. Build a single canonical day-1 value doc/proof path that starts from the S03 migration baseline, then tighten the existing console surfaces so they show the exact values adopters need to trust: route target, route reason, provider, fallback, policy outcome, recorded ledger outcome, and dependency health. If runtime gaps appear, they should be small additive changes to existing response/client types rather than new endpoints.

## Recommendation

Use the existing public-request + operator-correlation pattern as the backbone of S04:
1. **Anchor the story in `docs/reference-migration.md` and `docs/quickstart.md`**, but add one new canonical value-proof doc rather than restating contract/setup details.
2. **Upgrade the console proof surfaces instead of creating new ones**: Playground already shows immediate metadata and recorded outcome; Observability already shows ledger and dependency health. S04 should make them read as an adoption-value sequence, not unrelated admin pages.
3. **Prefer additive fields already available in backend responses**. The current Playground UI drops `routeReason`, `tenantId`, and `policyMode` even though `createPlaygroundCompletion()` already captures them. Exposing those fields is the lowest-risk way to make routing/policy behavior more legible.
4. **Verify via existing test seams first**: backend proof stays in `tests/test_reference_migration.py`, `tests/test_governance_api.py`, and `tests/test_admin_playground_api.py`; console proof stays in the playground/observability component tests plus Playwright e2e specs.

Relevant skill guidance:
- Installed skill **`react-best-practices`** is relevant only as a guardrail for console work: keep S04 additive, avoid new client-side waterfalls, reuse existing React Query queries, and avoid introducing duplicate fetch paths when existing queries already cover the data.

## Implementation Landscape

### Key Files

- `docs/reference-migration.md` — canonical S03 migration proof; already explains the public request, `X-Nebula-*` headers, and `X-Request-ID` → usage-ledger correlation. S04 should build on this instead of replacing it.
- `docs/quickstart.md` — canonical first-request happy path; already points adopters to headers, Playground, usage ledger, and Observability. Likely needs tighter linking to the new S04 value-proof artifact.
- `README.md` — repo entrypoint; already claims routing/fallback/operator visibility value and points to Playground/Observability. Needs any new S04 doc linked here, but should still avoid duplicating contract details.
- `docs/demo-script.md` — contains the clearest existing prose about Nebula’s value proof (“reduce estimated premium spend without hiding routing decisions, fallback behavior, or degraded optional dependencies”). This is strong prior art for S04 wording even though it is framed as a live walkthrough.
- `console/src/app/(console)/playground/page.tsx` — existing operator-side value surface. It already fetches tenants, submits a request, records client-side latency, then loads the correlated ledger row by `requestId`.
- `console/src/components/playground/playground-metadata.tsx` — currently shows `requestId`, `routeTarget`, `provider`, `cacheHit`, `fallbackUsed`, `latencyMs`, `policyOutcome`. This is the natural place to expose additional S04-critical fields already present in client data (`routeReason`, `tenantId`, `policyMode`).
- `console/src/components/playground/playground-recorded-outcome.tsx` — currently shows only terminal status, token counts, and estimated cost. This underplays day-1 value; likely place to add recorded route/provider/policy fields if S04 wants side-by-side “immediate vs persisted” proof.
- `console/src/app/(console)/observability/page.tsx` — current persisted-value surface. It combines ledger filtering with dependency health and already matches the README/demo claim that optional dependency degradation remains visible.
- `console/src/components/ledger/ledger-request-detail.tsx` — shows provider, route reason, policy outcome, fallback, cache hit, token counts for a selected ledger row. Good proof surface already; may only need wording or a couple of extra fields, not a redesign.
- `console/src/components/ledger/ledger-filters.tsx` — filters by tenant, route target, terminal status, and time range. This is enough for S04’s “operator can explain what happened” story; probably no new filters required unless planner wants direct `request_id` search in UI.
- `console/src/lib/admin-api.ts` — crucial seam. `PlaygroundCompletionResult` already contains `tenantId`, `routeReason`, and `policyMode`, but the page/components do not render them. `UsageLedgerRecord` already contains the persisted fields needed for S04.
- `src/nebula/api/routes/admin.py` — confirms `/v1/admin/usage/ledger` supports `request_id`, `tenant_id`, `terminal_status`, `route_target`, and time-window filtering. Also confirms Playground is admin-only and non-streaming.
- `src/nebula/services/chat_service.py` — backend source of truth for header semantics. `_error_headers()` and completion metadata include `X-Nebula-Tenant-ID`, route target/reason, provider, cache-hit, fallback-used, policy mode, and policy outcome. No new backend concept is needed to surface day-1 routing/policy evidence.
- `tests/test_reference_migration.py` — canonical public-path proof. Reuse for any S04 additions that need to assert day-1 value remains visible from the public caller side.
- `tests/test_governance_api.py` — already covers ledger outcomes across local, premium denial, cache hit, fallback, guardrails, and cache-disabled policy signals. Strong backend verification seam for R009.
- `tests/test_admin_playground_api.py` — proves Playground returns `X-Request-ID`, `X-Nebula-*` headers, and can be correlated through the usage ledger.
- `console/src/components/playground/playground-page.test.tsx` — not read in full here, but grep shows it already asserts the page fetches a correlated ledger entry and keeps immediate response visible while waiting. Likely the best unit-level seam for UI proof updates.
- `console/e2e/playground.spec.ts` — current end-to-end proof that Playground shows immediate metadata and recorded ledger outcome for the same request.
- `console/e2e/observability.spec.ts` — current end-to-end proof that Observability filters ledger rows and shows degraded optional dependency health.

### Build Order

1. **Define the canonical S04 artifact first** — likely a new doc such as `docs/day-1-value.md` (name to be chosen by planner) that explicitly ties together the S03 migration request, public headers, Playground immediate metadata, usage-ledger evidence, and Observability dependency health. This unblocks all downstream wording and prevents console copy from drifting.
2. **Then tighten Playground proof fields** — easiest/highest-value UI change is to render fields already returned by `createPlaygroundCompletion()` but currently hidden (`routeReason`, `tenantId`, `policyMode`). This directly strengthens R005/R009 without backend work.
3. **Then decide whether Recorded Outcome needs additive persisted fields** — if the new doc wants immediate-vs-persisted comparison, `PlaygroundRecordedOutcome` is the natural place to show final route/provider/policy data in addition to tokens/cost.
4. **Finally align Observability wording/tests** — likely copy-level changes or modest detail-card additions so the page reads as the persisted explanation surface for adoption, not just an admin ledger browser.

### Verification Approach

Preferred verification stack:

- Backend/public proof:
  - `pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py -q`
  - Focus on assertions around `X-Nebula-*`, `X-Request-ID`, and ledger rows for route/fallback/policy scenarios.
- Console unit/integration proof:
  - `npm --prefix console run test -- --run playground`
  - `npm --prefix console run test -- --run observability`
  - If the test runner does not support names cleanly, run full `npm --prefix console run test -- --run`.
- Console e2e proof:
  - `npm --prefix console run e2e -- --grep "playground|observability"` if supported, otherwise `make console-e2e`.
- Artifact/doc integrity:
  - `rg -n "day-1|routing|fallback|policy outcome|provider|Observability|Playground|usage ledger|X-Request-ID|X-Nebula" README.md docs/*.md`
  - ensure no `TODO|TBD` in the touched docs.

Observable success for S04:
- one public adoption request can be traced through immediate response headers and persisted operator evidence without guessing
- the console Playground clearly explains immediate route/policy evidence before ledger persistence completes
- the console Observability surface clearly explains persisted route/policy/fallback outcome and degraded optional dependency state
- docs point adopters through this sequence explicitly, without reopening S01/S02 contract/setup scope

## Constraints

- S04 must stay inside the **S01 compatibility boundary**. Do not broaden the public API promise just to make the value proof feel richer.
- S03 established that the **public request + `X-Request-ID` → usage-ledger correlation pattern is canonical**. Reuse it; do not invent a different proof path.
- Playground is explicitly **admin-only and non-streaming** (`src/nebula/api/routes/admin.py`, `tests/test_admin_playground_api.py`). It can support operator proof, but it must not be presented as the migration target.
- In the console, React Query is already the data-fetching pattern. Per `react-best-practices`, avoid duplicating fetch paths or creating new waterfalls when existing queries (`listTenants`, `getUsageLedgerEntry`, `listUsageLedger`) already provide the data.

## Common Pitfalls

- **Reopening contract scope** — S04 is about visible value on top of the existing adoption surface, not about adding new public compatibility claims. Keep contract language linked back to `docs/adoption-api-contract.md`.
- **Treating Playground as the adoption path** — the public proof remains `POST /v1/chat/completions`; Playground is operator-side corroboration only.
- **Underselling existing data** — `admin-api.ts` already captures more Playground fields than the UI renders. Check client types before proposing backend changes.
- **Explaining value only in docs, not product surfaces** — R005/R009 require product-visible proof. A doc-only slice would likely feel incomplete.

## Open Risks

- The current console already proves the mechanics, so the main risk is **insufficient narrative cohesion**: planners/executors could ship superficial copy changes and still leave the value proof scattered across pages.
- Verification may still hit the known worktree environment gap where local `pytest` or console dependencies are missing; prior slices recorded that this is an environment issue, not necessarily a product issue.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| React / Next.js console | installed `react-best-practices` | available |
| FastAPI | `wshobson/agents@fastapi-templates` | available via `npx skills add wshobson/agents@fastapi-templates` |
| Next.js App Router | `wshobson/agents@nextjs-app-router-patterns` | available via `npx skills add wshobson/agents@nextjs-app-router-patterns` |
| React Query | `mindrally/skills@react-query` | available via `npx skills add mindrally/skills@react-query` |
