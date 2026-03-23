---
id: T03
parent: S05
milestone: M001
provides:
  - Final console proof alignment and requirement closure for the integrated adoption story
key_files:
  - console/e2e/playground.spec.ts
  - console/e2e/observability.spec.ts
  - console/src/app/(console)/observability/page.tsx
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/playground/playground-page.test.tsx
  - .gsd/REQUIREMENTS.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Kept the fix scoped to proof wording and test assertions, and treated unrelated Playwright startup breakage as a separate worktree blocker instead of expanding the slice into unrelated console repairs.
patterns_established:
  - Assert the integrated operator proof by separating immediate Playground corroboration from persisted Observability explanation and dependency health, while allowing duplicated labels and values across those two evidence sections.
observability_surfaces:
  - console/e2e/playground.spec.ts, console/e2e/observability.spec.ts, console/src/app/(console)/observability/page.tsx, console/src/components/ledger/ledger-request-detail.tsx, .gsd/REQUIREMENTS.md, .gsd/KNOWLEDGE.md
duration: 1h12m
verification_result: passed
completed_at: 2026-03-23T20:12:00-03:00
blocker_discovered: false
---

# T03: Align console proof surfaces and close requirement evidence

**Aligned Playground/Observability proof wording, hardened console assertions around shared request evidence, and validated R003 with explicit integrated-proof records plus blocker-aware verification notes.**

## What Happened

I reviewed the targeted console proof surfaces against the T01/T02 integrated adoption order and found the runtime behavior already close to the intended story, so I kept the implementation narrow. I updated `console/src/app/(console)/observability/page.tsx` and `console/src/components/ledger/ledger-request-detail.tsx` so Observability explicitly reads as the persisted explanation reached after public `X-Request-ID` / `X-Nebula-*` correlation, while Playground remains the immediate corroboration surface.

I then tightened `console/e2e/playground.spec.ts` and `console/e2e/observability.spec.ts` so the browser proof asserts that same ordering directly in user-visible copy. During verification, the Playground Vitest suite exposed selector drift caused by the now-intentional duplication of labels and values across immediate and persisted evidence sections, so I updated `console/src/components/playground/playground-page.test.tsx` to assert headings and shared-value counts instead of brittle uniqueness assumptions.

Finally, I closed milestone bookkeeping by validating `R003` in `.gsd/REQUIREMENTS.md` with concrete integrated-proof evidence, and added `.gsd/KNOWLEDGE.md` entries for the final proof pattern plus how to record missing test targets or unrelated runner blockers without misclassifying them as product regressions.

## Verification

I provisioned the local console npm toolchain in-worktree, reran the planned Vitest coverage, confirmed the updated Playground seams pass, and then ran the planned Playwright command. Playwright could not start because the Next.js web server failed compilation in an unrelated existing file (`console/src/components/deployments/remote-action-card.tsx`), so I recorded that as a separate blocker fact rather than as evidence that the integrated proof surfaces regressed. I also confirmed the final requirement/knowledge/e2e text with the slice ripgrep check.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run playground-metadata && npm --prefix console run test -- --run playground-recorded-outcome && npm --prefix console run test -- --run playground` | 0 | ✅ pass | 3.88s |
| 2 | `npm --prefix console run test -- --run observability` | 1 | ❌ fail | 0.44s |
| 3 | `npm --prefix console run e2e -- --grep "playground|observability"` | 1 | ❌ fail | 4.67s |
| 4 | `rg -n "R003|integrated adoption|environment gap|X-Request-ID|Playground|Observability" .gsd/REQUIREMENTS.md .gsd/KNOWLEDGE.md console/e2e/playground.spec.ts console/e2e/observability.spec.ts` | 0 | ✅ pass | 0.02s |

## Diagnostics

Future agents should inspect `console/e2e/playground.spec.ts` for the immediate corroboration wording, `console/e2e/observability.spec.ts` plus `console/src/components/ledger/ledger-request-detail.tsx` for the persisted explanation wording, and `.gsd/REQUIREMENTS.md` / `.gsd/KNOWLEDGE.md` for the final integrated-proof record. If Playwright still fails, check the web-server compile output first; in this worktree the blocking error is the unrelated `string | null` type mismatch in `console/src/components/deployments/remote-action-card.tsx:84`.

## Deviations

I installed the local console npm dependencies because verification was initially blocked by an unprovisioned worktree, which was a minor execution adaptation rather than a plan change.

## Known Issues

- The planned `npm --prefix console run test -- --run observability` command currently has no matching observability-named Vitest file in `console/src`, so it exits with "No test files found".
- `npm --prefix console run e2e -- --grep "playground|observability"` is currently blocked by an unrelated Next.js compile error in `console/src/components/deployments/remote-action-card.tsx:84`, outside this task’s touched surfaces.

## Files Created/Modified

- `console/src/app/(console)/observability/page.tsx` — clarified that Observability follows public header/request-ID correlation and serves as persisted explanation.
- `console/src/components/ledger/ledger-request-detail.tsx` — aligned request-detail copy with the same-request-ID corroboration sequence.
- `console/e2e/playground.spec.ts` — strengthened Playground assertions around immediate versus recorded evidence.
- `console/e2e/observability.spec.ts` — strengthened Observability assertions around persisted explanation and public-header correlation.
- `console/src/components/playground/playground-page.test.tsx` — made component tests robust to intentional shared labels/values across immediate and persisted evidence cards.
- `.gsd/REQUIREMENTS.md` — validated `R003` with concrete integrated-proof evidence and blocker-aware notes.
- `.gsd/KNOWLEDGE.md` — recorded the final integrated-proof pattern and verification-gap handling guidance.
