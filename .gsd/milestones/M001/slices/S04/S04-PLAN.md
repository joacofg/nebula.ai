# S04: Day-1 value proof surface

**Goal:** Make Nebula's day-1 differentiators visibly valuable immediately after adoption by connecting the public migration path, operator Playground evidence, persisted ledger evidence, and Observability health into one explicit proof surface.
**Demo:** A team can follow one canonical day-1 value walkthrough, submit or migrate a public chat-completions request, then see route target, route reason, provider, fallback use, policy outcome, and persisted operator evidence reflected coherently in docs and console surfaces.

## Must-Haves

- S04 delivers one canonical day-1 value proof document that builds on `docs/quickstart.md` and `docs/reference-migration.md` without reopening the S01 public contract boundary.
- The Playground value surface shows the immediate routing and policy fields adopters need to trust what happened, including route reason, tenant attribution, and policy mode alongside the existing request metadata.
- The recorded/persisted operator evidence clearly reinforces the same request outcome through ledger-backed route/provider/fallback/policy data.
- Observability remains the persisted explanation surface for route, fallback, policy, and dependency-health validation during adoption.
- Verification proves the public `X-Nebula-*` header path, `X-Request-ID` → usage-ledger correlation, and console evidence surfaces all align for R005 and R009.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py -q`
- `npm --prefix console run test -- --run playground-metadata && npm --prefix console run test -- --run playground-recorded-outcome`
- `npm --prefix console run test -- --run playground && npm --prefix console run test -- --run observability`
- `npm --prefix console run e2e -- --grep "playground|observability"`
- `rg -n "day-1 value|X-Request-ID|Playground|Observability|route reason|policy" README.md docs/day-1-value.md docs/quickstart.md docs/reference-migration.md`

## Observability / Diagnostics

- Runtime signals: public `X-Nebula-*` headers, `X-Request-ID`, persisted usage-ledger fields, runtime dependency-health states, and console metadata cards for immediate versus recorded evidence.
- Inspection surfaces: `tests/test_reference_migration.py`, `tests/test_admin_playground_api.py`, `tests/test_governance_api.py`, `console/src/components/playground/playground-metadata.tsx`, `console/src/components/playground/playground-recorded-outcome.tsx`, `console/src/app/(console)/observability/page.tsx`, and `docs/day-1-value.md`.
- Failure visibility: route target/reason mismatches, missing fallback/policy fields, missing request correlation, and degraded optional dependency state must remain inspectable through headers, ledger rows, and UI copy.
- Redaction constraints: keep the slice focused on metadata-only operator evidence; do not expose raw prompts, raw responses beyond existing Playground behavior, or secret credential values in docs or UI.

## Integration Closure

- Upstream surfaces consumed: `docs/adoption-api-contract.md`, `docs/quickstart.md`, `docs/reference-migration.md`, `tests/test_reference_migration.py`, `tests/test_admin_playground_api.py`, `tests/test_governance_api.py`, `console/src/lib/admin-api.ts`, and the existing Playground/Observability pages.
- New wiring introduced in this slice: one canonical day-1 value doc, stronger Playground metadata rendering, stronger recorded-outcome rendering, and explicit copy/linking that frames Observability as the persisted explanation surface.
- What remains before the milestone is truly usable end-to-end: S05 must assemble quickstart, migration proof, and this day-1 value proof into one final integrated adoption walkthrough.

## Tasks

- [x] **T01: Publish the canonical day-1 value proof path** `est:45m`
  - Why: S04's main gap is narrative cohesion; without one canonical artifact, the existing migration, Playground, ledger, and Observability proof surfaces remain scattered and do not clearly satisfy R005/R009.
  - Files: `docs/day-1-value.md`, `docs/quickstart.md`, `docs/reference-migration.md`, `README.md`
  - Do: Write one canonical `docs/day-1-value.md` that starts from the S03 public request and `X-Request-ID` correlation pattern, explains immediate versus persisted evidence, and positions Playground and Observability as operator corroboration rather than the adoption target; then add minimal links from the quickstart, migration guide, and README so the repo has one explicit day-1 value path without duplicating contract/setup content.
  - Verify: `rg -n "day-1 value|X-Request-ID|Playground|Observability|route reason|policy" README.md docs/day-1-value.md docs/quickstart.md docs/reference-migration.md`
  - Done when: the repo has one discoverable day-1 value proof doc and all touched entry docs link to it in a way that preserves the S01/S02/S03 boundaries.
- [x] **T02: Expand Playground and Observability proof surfaces for day-1 trust** `est:1h15m`
  - Why: The runtime already exposes the right data, but the console currently hides part of the routing/policy story and undersells the persisted operator proof needed for immediate adoption trust.
  - Files: `console/src/components/playground/playground-metadata.tsx`, `console/src/components/playground/playground-recorded-outcome.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/app/(console)/playground/page.tsx`, `console/src/app/(console)/observability/page.tsx`, `console/src/lib/admin-api.ts`
  - Do: Render the already-available immediate metadata fields needed by S04 (`tenantId`, `routeReason`, `policyMode`) in Playground, strengthen the recorded-outcome card so persisted route/provider/fallback/policy evidence is obvious next to tokens/cost, and tighten Observability/detail-page copy so it clearly reads as the persisted explanation surface for route/fallback/policy plus dependency health; keep the work additive and reuse existing admin-api data instead of inventing new fetch paths or endpoints.
  - Verify: `npm --prefix console run test -- --run playground-metadata && npm --prefix console run test -- --run playground-recorded-outcome`
  - Done when: an operator can inspect one console request and understand the immediate route decision, policy framing, recorded ledger outcome, and where dependency degradation fits into the same story without guessing.
- [x] **T03: Lock the day-1 value story with backend and console proof tests** `est:1h`
  - Why: S04 closes only if the narrative, UI surfaces, and runtime evidence stay aligned under executable checks rather than doc-only assertions.
  - Files: `tests/test_reference_migration.py`, `tests/test_admin_playground_api.py`, `tests/test_governance_api.py`, `console/src/components/playground/playground-metadata.test.tsx`, `console/src/components/playground/playground-recorded-outcome.test.tsx`, `console/e2e/playground.spec.ts`, `console/e2e/observability.spec.ts`
  - Do: Extend the focused backend and console tests so they assert the exact day-1 evidence surfaces S04 depends on: public headers remain the migration truth, Playground shows immediate route/policy fields, recorded outcome shows persisted route/provider/fallback/policy data, and Observability still exposes dependency degradation plus request explanation; keep the assertions aligned to current runtime behavior rather than inventing new contract promises.
  - Verify: `pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py -q && npm --prefix console run test -- --run playground && npm --prefix console run test -- --run observability && npm --prefix console run e2e -- --grep "playground|observability"`
  - Done when: the slice's backend, component, and end-to-end tests prove that public adoption evidence and operator-visible value surfaces tell one consistent story.

## Files Likely Touched

- `docs/day-1-value.md`
- `docs/quickstart.md`
- `docs/reference-migration.md`
- `README.md`
- `console/src/components/playground/playground-metadata.tsx`
- `console/src/components/playground/playground-recorded-outcome.tsx`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/app/(console)/playground/page.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `tests/test_reference_migration.py`
- `tests/test_admin_playground_api.py`
- `tests/test_governance_api.py`
- `console/e2e/playground.spec.ts`
- `console/e2e/observability.spec.ts`
