---
estimated_steps: 5
estimated_files: 6
skills_used:
  - agent-browser
  - react-best-practices
---

# T03: Align console proof surfaces and close requirement evidence

**Slice:** S05 — Final integrated adoption proof
**Milestone:** M001

## Description

Finish the final assembly by making the console/UAT proof read the same way as the docs and backend tests, then update milestone bookkeeping so `R003` has explicit integrated validation evidence. This task should prefer existing UI/test seams over new product surface area.

## Steps

1. Review `console/e2e/playground.spec.ts`, `console/e2e/observability.spec.ts`, `console/src/app/(console)/observability/page.tsx`, and `console/src/components/ledger/ledger-request-detail.tsx` against the integrated-proof ordering and wording from T01/T02.
2. Tighten e2e assertions and any minimal supporting copy needed so Playground reads as immediate corroboration while Observability reads as persisted explanation plus dependency health for the same request story.
3. Run the planned console component and Playwright checks; if `vitest` or `playwright` are missing in the worktree, capture that as an environment-gap fact in milestone bookkeeping instead of implying product failure.
4. Update `.gsd/REQUIREMENTS.md` so `R003` has concrete integrated validation language grounded in the final proof artifact and executable seams.
5. Update `.gsd/KNOWLEDGE.md` with the final integrated-proof pattern and environment-gap handling guidance for future slices/agents.

## Must-Haves

- [ ] The console proof keeps Playground as corroboration and Observability as persisted explanation plus dependency health.
- [ ] The final milestone bookkeeping gives `R003` concrete integrated validation evidence.
- [ ] Environment blockers are recorded as missing local runners, not as product regressions.

## Verification

- `npm --prefix console run test -- --run playground-metadata && npm --prefix console run test -- --run playground-recorded-outcome && npm --prefix console run test -- --run playground && npm --prefix console run test -- --run observability`
- `npm --prefix console run e2e -- --grep "playground|observability"`
- `rg -n "R003|integrated adoption|environment gap|X-Request-ID|Playground|Observability" .gsd/REQUIREMENTS.md .gsd/KNOWLEDGE.md console/e2e/playground.spec.ts console/e2e/observability.spec.ts`

## Observability Impact

- Signals added/changed: clearer UI/e2e proof language tying immediate Playground metadata to persisted Observability/ledger evidence; explicit requirement/knowledge records for environment gaps
- How a future agent inspects this: run the named console tests/e2e specs and read `.gsd/REQUIREMENTS.md` plus `.gsd/KNOWLEDGE.md` for the final integrated validation pattern
- Failure state exposed: UI wording/assertion drift, lost corroboration ordering, or missing local `vitest` / `playwright` tooling becomes visible and attributable

## Inputs

- `console/e2e/playground.spec.ts` — current Playground end-to-end corroboration assertions
- `console/e2e/observability.spec.ts` — current Observability explanation/dependency-health assertions
- `console/src/app/(console)/observability/page.tsx` — persisted explanation framing in the console
- `console/src/components/ledger/ledger-request-detail.tsx` — request-detail explanation language
- `.gsd/REQUIREMENTS.md` — current requirement validation state, including active `R003`
- `.gsd/KNOWLEDGE.md` — current cross-slice lessons and environment-gap guidance

## Expected Output

- `console/e2e/playground.spec.ts` — integrated-proof-aligned Playground assertions
- `console/e2e/observability.spec.ts` — integrated-proof-aligned Observability assertions
- `console/src/app/(console)/observability/page.tsx` — minimal copy/supporting alignment if needed
- `console/src/components/ledger/ledger-request-detail.tsx` — minimal copy/supporting alignment if needed
- `.gsd/REQUIREMENTS.md` — `R003` updated with concrete integrated validation evidence
- `.gsd/KNOWLEDGE.md` — final integrated-proof and environment-gap lessons captured
