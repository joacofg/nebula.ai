---
estimated_steps: 11
estimated_files: 4
skills_used: []
---

# T02: Compose Observability around request-first routing inspection

Tighten the Observability page so it clearly presents one selected request as the primary proof surface, with calibration summary, grounded recommendations, cache/runtime state, and dependency health as supporting context for the same routing investigation.

Steps:
1. Update `console/src/app/(console)/observability/page.tsx` copy and layout only where needed so the page explicitly ties selected request inspection to supporting calibration and runtime context, without introducing a new inspector concept or analytics framing.
2. Wire any request-detail changes from T01 into the page composition and keep tenant calibration summary bounded to readiness/supporting context rather than a replacement for persisted request evidence.
3. Extend `console/src/app/(console)/observability/observability-page.test.tsx` and `console/src/app/(console)/observability/page.test.tsx` to assert request-primary framing, bounded supporting-context wording, and duplicate-label-safe scoped assertions when the same calibration labels appear in multiple cards.
4. Re-run the focused request-detail and Observability Vitest suites together to prove the integrated inspection surface still matches the routed-request story shipped by S01–S03.

Must-haves:
- Observability explicitly reads as selected request evidence first, supporting context second.
- Calibration summary and runtime cards do not claim authority over the selected persisted ledger row.
- Scoped tests tolerate intentional duplicate labels across cards and lock the non-analytics framing.
- The integrated focused Vitest suite passes with the new request-detail rendering in place.

## Inputs

- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`

## Expected Output

- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/app/(console)/observability/page.test.tsx`

## Verification

npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/app/'(console)'/observability/page.test.tsx

## Observability Impact

This task preserves diagnosability at the page-composition level: the selected request panel, calibration summary card, recommendation cards, and runtime-health section keep distinct roles, and the focused Observability tests verify that role separation remains visible.
