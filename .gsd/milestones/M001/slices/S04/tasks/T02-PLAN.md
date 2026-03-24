---
estimated_steps: 5
estimated_files: 6
skills_used:
  - react-best-practices
---

# T02: Expand Playground and Observability proof surfaces for day-1 trust

**Slice:** S04 — Day-1 value proof surface
**Milestone:** M001

## Description

Tighten the existing console surfaces so they visibly prove Nebula's differentiated value on the first operator inspection. The runtime/client types already expose most of the needed information, so this task should stay additive: reveal the missing immediate routing/policy fields in Playground, make the recorded-outcome card reinforce persisted route/provider/fallback/policy evidence, and tune Observability/detail copy so it clearly reads as the persisted explanation surface. Do not add new endpoints or duplicate fetch paths.

## Steps

1. Update the Playground metadata component and page wiring to render `tenantId`, `routeReason`, and `policyMode` from the existing `PlaygroundCompletionResult` fields.
2. Expand the recorded-outcome component so the persisted ledger card highlights route target, provider, fallback/cache status, route reason, and policy outcome alongside token/cost data.
3. Review `console/src/components/ledger/ledger-request-detail.tsx` and `console/src/app/(console)/observability/page.tsx` and tighten copy/layout only as needed so Observability clearly explains persisted route/fallback/policy outcomes plus dependency-health state.
4. Keep all work on the existing `console/src/lib/admin-api.ts` types and queries; do not create new admin API endpoints or duplicate data fetches that React Query already covers.
5. Update affected component/page tests only if the new UI fields or copy require corresponding assertions.

## Must-Haves

- [ ] Playground immediate-response UI shows the route reason, tenant attribution, and policy mode already returned by `createPlaygroundCompletion()`.
- [ ] Recorded/persisted operator evidence makes route/provider/fallback/policy fields obvious without removing the existing token/cost outcome proof, and Observability copy still frames dependency degradation as visible but non-blocking when appropriate.

## Verification

- `npm --prefix console run test -- --run playground-metadata`
- `npm --prefix console run test -- --run playground-recorded-outcome`

## Observability Impact

- Signals added/changed: richer immediate metadata rendering and clearer persisted ledger/detail rendering for route reason, tenant, policy mode, fallback, and provider evidence.
- How a future agent inspects this: use the Playground page, Recorded outcome card, and Observability request detail UI backed by existing admin API queries.
- Failure state exposed: missing/empty route or policy fields, disagreement between immediate and persisted evidence, and degraded dependency state remain visible in the UI.

## Inputs

- `console/src/lib/admin-api.ts` — existing Playground and usage-ledger client types with fields already available for rendering.
- `console/src/app/(console)/playground/page.tsx` — current Playground page wiring for immediate and recorded request evidence.
- `console/src/components/playground/playground-metadata.tsx` — immediate metadata card that currently omits some S04-critical fields.
- `console/src/components/playground/playground-recorded-outcome.tsx` — persisted ledger card that currently underplays route/policy evidence.
- `console/src/components/ledger/ledger-request-detail.tsx` — current persisted request-detail surface in Observability.
- `console/src/app/(console)/observability/page.tsx` — page-level framing for the persisted ledger and dependency-health story.
- `.gsd/milestones/M001/slices/S04/tasks/T01-PLAN.md` — canonical day-1 story this UI work should reinforce.

## Expected Output

- `console/src/components/playground/playground-metadata.tsx` — expanded immediate metadata surface for day-1 trust.
- `console/src/components/playground/playground-recorded-outcome.tsx` — stronger persisted outcome surface with route/policy proof.
- `console/src/components/ledger/ledger-request-detail.tsx` — adjusted persisted request detail framing if needed.
- `console/src/app/(console)/playground/page.tsx` — updated prop wiring for added metadata fields.
- `console/src/app/(console)/observability/page.tsx` — clearer persisted explanation framing if needed.
- `console/src/components/playground/playground-metadata.test.tsx` — component assertions aligned to the richer immediate metadata surface.
- `console/src/components/playground/playground-recorded-outcome.test.tsx` — component assertions aligned to the richer persisted evidence surface.
