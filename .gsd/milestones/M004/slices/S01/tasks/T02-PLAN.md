---
estimated_steps: 4
estimated_files: 4
skills_used:
  - react-best-practices
  - best-practices
---

# T02: Render the canonical trust-boundary guardrails on hosted public surfaces

**Slice:** S01 — Hosted reinforcement boundary
**Milestone:** M004

## Description

Use the shared hosted-contract exports from T01 to render the canonical reinforcement guardrails on the public trust-boundary surfaces. This task should make the non-authoritative hosted narrative visible and testable in the UI without inventing local copy that can drift away from the shared contract.

## Steps

1. Update `console/src/components/hosted/trust-boundary-card.tsx` to render the new shared reinforcement guardrails and operator-reading guidance from `console/src/lib/hosted-contract.ts`.
2. Update `console/src/app/trust-boundary/page.tsx` to reuse the same shared language so the public trust-boundary page presents one canonical metadata-only, non-authoritative narrative.
3. Extend `console/src/components/hosted/trust-boundary-card.test.tsx` and `console/src/app/trust-boundary/page.test.tsx` to assert the newly rendered guardrail sections and phrasing.
4. Keep the rendered language explicitly descriptive: hosted can improve onboarding and fleet visibility, but local runtime enforcement remains authoritative even when hosted data is stale or offline.

## Must-Haves

- [ ] Both public surfaces consume shared hosted-contract content instead of restating trust-boundary copy independently.
- [ ] The rendered wording explicitly clarifies that hosted freshness and posture are visibility-only signals, not runtime authority.
- [ ] The new UI sections remain concise and reusable for downstream proof work rather than becoming a redesign of the page/card.

## Verification

- `npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx`
- `rg -n "fleet posture|confidence|local runtime authority|request-serving path" console/src/app/trust-boundary console/src/components/hosted`

## Observability Impact

- Signals added/changed: additional rendered guardrail copy on public trust-boundary UI backed by shared contract exports
- How a future agent inspects this: run the two focused Vitest files and inspect `console/src/components/hosted/trust-boundary-card.tsx` plus `console/src/app/trust-boundary/page.tsx`
- Failure state exposed: missing or conflicting trust-boundary sections become visible as focused render-test failures

## Inputs

- `console/src/lib/hosted-contract.ts` — shared reinforcement vocabulary and trust-boundary copy from T01
- `console/src/components/hosted/trust-boundary-card.tsx` — reusable hosted trust-boundary card
- `console/src/components/hosted/trust-boundary-card.test.tsx` — focused card assertions
- `console/src/app/trust-boundary/page.tsx` — public trust-boundary entrypoint
- `console/src/app/trust-boundary/page.test.tsx` — focused page assertions

## Expected Output

- `console/src/components/hosted/trust-boundary-card.tsx` — card rendering the shared reinforcement guardrails
- `console/src/components/hosted/trust-boundary-card.test.tsx` — render tests for the new card content
- `console/src/app/trust-boundary/page.tsx` — public page aligned to the shared reinforcement wording
- `console/src/app/trust-boundary/page.test.tsx` — render tests for the page-level guardrail narrative
