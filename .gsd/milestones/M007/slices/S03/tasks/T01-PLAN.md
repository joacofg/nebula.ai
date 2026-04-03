---
estimated_steps: 17
estimated_files: 5
skills_used: []
---

# T01: Restructure Observability into a request-led investigation flow

Rework `console/src/app/(console)/observability/page.tsx` so the selected request is the page’s obvious lead object and the rest of the page reads as follow-up context for that investigation. Keep the existing data sources, preserve `LedgerRequestDetail` as the authoritative persisted evidence seam, and tighten the page-level structure so the next action is legible through layout and section sequencing rather than copy alone.

Steps:
1. Recompose the top-level Observability page layout in `console/src/app/(console)/observability/page.tsx` around one investigation-first flow that leads with selected-request inspection, keeps request detail authoritative, and regroups supporting cards as follow-up context for the same request.
2. Update `console/src/app/(console)/observability/page.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` to assert DOM order, scoped supporting-card hierarchy, explicit policy-preview follow-up cues, and negative guards against dashboard/routing-studio/analytics drift.
3. Keep `console/src/components/ledger/ledger-request-detail.tsx` stable unless the new flow exposes a small wording mismatch; if touched, preserve its authoritative persisted-record contract and keep focused coverage aligned.

Must-haves:
- The selected request remains the lead investigation object and `LedgerRequestDetail` still reads as the authoritative persisted evidence row.
- Recommendations, calibration, cache, and dependency sections are explicitly subordinate follow-up context for the selected request.
- The page structure makes the next operator action legible and keeps policy preview as the follow-up comparison surface.
- Focused page tests lock hierarchy and anti-drift boundaries with scoped assertions rather than copy-only snapshots.

Verification:
- `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`
- `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx`

Observability Impact:
- Signals added/changed: the selected-request-first UI hierarchy and its policy-preview follow-up cues become the primary inspection signal on the page.
- How a future agent inspects this: read `console/src/app/(console)/observability/page.tsx` and rerun the focused Observability Vitest files.
- Failure state exposed: hierarchy drift, duplicate-label scoping mistakes, or dashboard-language regressions fail in focused page tests instead of surfacing only as subjective UI review.

## Inputs

- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/components/health/runtime-health-cards.tsx`
- `console/src/components/health/runtime-health-cards.test.tsx`

## Expected Output

- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`

## Verification

npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx

## Observability Impact

UI hierarchy and failure-localizing tests for the selected-request investigation flow.
