# S03 Research — Rework Observability around a primary investigation flow

## Summary

S03 is targeted console work, not a new backend-contract slice. The existing M007/S01-S02 seams already establish the product boundary: Observability is request-investigation-first, `LedgerRequestDetail` remains the authoritative persisted evidence record, and policy preview remains the explicit comparison/save surface operators may go to next. The main implementation surface is `console/src/app/(console)/observability/page.tsx`, with optional supporting work in `console/src/components/ledger/ledger-table.tsx` if the investigation flow needs stronger selection affordances.

The risk is not missing data. The risk is page structure: Observability currently reads as three stacked sections — selected request, supporting context, dependency health — but the selected-request area is still mostly a table/detail layout rather than a clearer investigation flow with an obvious “inspect this request, then use these follow-up cards” progression. S03 should sharpen that sequence without widening into dashboard summaries, analytics framing, or a replacement for request detail.

Relevant requirement focus for this slice:
- **R050** — Observability has a single primary role as request investigation.
- **R053** — Supporting context stays subordinate to the primary evidence on each page.
- **R054** — Operators can tell what action follows from each decision surface without reading surrounding prose first.
- **R055** — Clarify page identity without widening into dashboard/routing-studio scope.

Relevant skill guidance:
- From the installed `frontend-design` skill: commit to a clear conceptual direction and let structure lead. For S03 that means a distinct investigation flow, not visual decoration.
- From GSD knowledge and hard rules: use DOM-order and scoped negative assertions instead of copy-only checks; preserve request detail as authoritative; keep follow-up cards explicitly subordinate; verify in tests, not prose.

## Recommendation

Build S03 as a **page-orchestration-first** slice:
1. Rework `observability/page.tsx` so the top-level page reads as one investigation flow around the selected request.
2. Only then adjust `ledger-table.tsx` if the page needs clearer request selection cues or row summaries to make the chosen request feel like the lead object.
3. Keep `ledger-request-detail.tsx` largely stable unless the new page structure exposes a small wording gap. It already encodes the authoritative-request-detail contract well.
4. Extend the two Observability page tests first, then add targeted component tests only if page changes force new behavior.

Do **not** start with backend/admin changes. S02 already aligned the supporting contracts, and nothing in the current code suggests a missing API seam for S03.

## Implementation Landscape

### Primary file: `console/src/app/(console)/observability/page.tsx`

This file owns almost all of the S03 behavior:
- fetches tenants, usage ledger, runtime health, and recommendations via React Query
- owns `selectedRequestId` state and auto-selects the first ledger row
- computes `selectedEntry`
- lays out the page in three major sections:
  1. selected request
  2. supporting context
  3. dependency health

Current structure is already within the right product boundary, but the investigation flow is still fairly flat:
- the selected-request section is a two-column `LedgerTable` + `LedgerRequestDetail` grid
- supporting context appears as a second full page section with recommendations, calibration, cache, then dependency health below
- action cues exist in text (`policy preview comparison`, `next comparison or follow-up action`) but the page structure still relies on prose more than sequencing

This is the natural place to:
- reorder or regroup supporting cards around the selected request
- add an explicit “investigation first / follow-up next” structure
- tighten section headers and visual hierarchy without changing source data
- keep dependency health visibly secondary

### Stable authority seam: `console/src/components/ledger/ledger-request-detail.tsx`

This component is already strong and should be preserved as the authority seam.
It:
- renders the selected persisted usage-ledger row
- states directly that it is the authoritative evidence row
- converts calibration, budget, and routing details into structured supporting interpretation
- avoids analytics/dashboard framing

It already encodes most of **R051/R053** behavior. S03 should treat it as stable unless the page redesign truly requires a small local wording change.

### Likely secondary seam: `console/src/components/ledger/ledger-table.tsx`

This is intentionally simple:
- clickable rows
- selected-row highlight (`bg-sky-50`)
- plain columns for timestamp/request/tenant/route/provider/status/latency/cost

If S03 needs stronger “primary investigation object” behavior, this is the likely supporting file.
Possible bounded changes here:
- stronger selected-row affordance
- row wording/visual treatment that makes request selection more legible
- improved discoverability of the selected request without changing the data contract

Keep this bounded. Do not turn the table into a new explorer product.

### Supporting-only components

These appear stable and probably only need to be consumed differently from `page.tsx`:
- `console/src/components/ledger/ledger-filters.tsx`
- `console/src/components/health/runtime-health-cards.tsx`

`LedgerFilters` is a simple controlled form. It is not the place to solve page identity.
`RuntimeHealthCards` is intentionally generic and should stay subordinate; likely no change beyond placement or surrounding copy in `page.tsx`.

### Policy follow-up vocabulary source

Use these existing policy seams as the canonical “next action” language rather than inventing new wording:
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-page.test.tsx`

They already frame policy work as:
- “Preview before save”
- compare draft against recent persisted baseline
- save remains explicit
- no dashboard / routing studio / analytics-product drift

If Observability needs a clearer implied next step, point to this existing policy-preview concept. Do not create a new action family.

## File Map

- `console/src/app/(console)/observability/page.tsx`
  - Main S03 execution surface. Owns query orchestration, selected-request state, and all page-level hierarchy.
- `console/src/app/(console)/observability/page.test.tsx`
  - Focused page-role test with mocked admin API + runtime fetch. Good place for sharper request-first and next-step assertions.
- `console/src/app/(console)/observability/observability-page.test.tsx`
  - Integrated page test. Already asserts heading order, scoped supporting context, duplicate-label-safe assertions, and request-detail authority.
- `console/src/components/ledger/ledger-request-detail.tsx`
  - Stable authority seam for the selected persisted request.
- `console/src/components/ledger/ledger-request-detail.test.tsx`
  - Strong focused coverage for authority, calibrated/degraded/rollout-disabled states, and budget evidence. Preserve these semantics.
- `console/src/components/ledger/ledger-table.tsx`
  - Candidate secondary seam if stronger selection affordances are needed.
- `console/src/components/ledger/ledger-table.test.tsx`
  - Minimal coverage today; expand only if row-selection behavior changes.
- `console/src/components/ledger/ledger-filters.tsx`
  - Controlled filter form; unlikely to be the main slice target.
- `console/src/components/health/runtime-health-cards.tsx`
  - Generic dependency-health renderer; likely stable.
- `console/src/components/policy/policy-form.tsx`
  - Canonical save/don’t-save follow-up language for Observability to point toward.
- `console/src/components/policy/policy-page.test.tsx`
  - Canonical negative-boundary assertions against dashboard/routing-studio/analytics drift.

## Natural Task Split

### Task 1 — Rework Observability page structure around the selected-request investigation
**Files:**
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`

**Goal:**
Make the page read as one primary investigation flow where the selected request is visibly the lead object and the surrounding cards clearly follow from it.

**Why first:**
This is the main slice value and likely retires most ambiguity without touching component seams.

### Task 2 — Tighten request-selection affordances only if the page restructure needs it
**Files:**
- `console/src/components/ledger/ledger-table.tsx`
- `console/src/components/ledger/ledger-table.test.tsx`
- optionally `console/src/app/(console)/observability/page.tsx` / tests for integration fallout

**Goal:**
If needed, make selecting and recognizing the primary request easier without inventing a new explorer surface.

**Why second:**
Only do this after the page structure is clear. The current table may already be sufficient once the surrounding layout is improved.

### Task 3 — Small authority-copy adjustments only if exposed by the new flow
**Files:**
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`

**Goal:**
Patch any wording gaps revealed by the new page hierarchy while preserving the authoritative-persisted-record contract.

**Why third:**
Likely unnecessary, but it is the right bounded seam if integration tests reveal a mismatch.

## Constraints and Guardrails

- Keep Observability request-investigation-first. This is the durable M007 rule.
- Do not widen into posture summary, dashboard, analytics, or routing-studio framing.
- Treat `LedgerRequestDetail` as the authoritative evidence seam, not one card among peers.
- Supporting cards must read as follow-up context for the selected request.
- Use existing policy-preview language for the implied next action.
- Prefer DOM-order assertions and scoped `within(...)` checks over copy-only tests.
- Expect duplicate labels across request detail and supporting cards; scope assertions to the intended section rather than enforcing uniqueness.

## Verification

Primary slice verification command:

```bash
npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/ledger/ledger-table.test.tsx src/components/health/runtime-health-cards.test.tsx
```

Optional if `LedgerFilters` changes are touched:

```bash
npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx
```

What to prove:
- top-level Observability order still puts selected-request investigation before supporting context and dependency health
- request detail remains the authoritative persisted record
- supporting recommendation/calibration/cache/dependency sections stay subordinate to the selected request
- the page makes the next follow-up action legible and still points toward policy preview rather than inventing a new workflow
- negative assertions still reject dashboard / routing studio / analytics-product drift

## Existing Verification Gap / Gotcha

There is a pre-existing focused test issue in `console/src/components/ledger/ledger-filters.test.tsx`:
- current failure: `Invalid Chai property: toBeSelected`
- `console/src/test/setup.ts` does import `@testing-library/jest-dom/vitest`, so this looks like a matcher-usage/setup mismatch isolated to that file, not a global test-environment absence

This does **not** block S03 unless the slice touches `ledger-filters.test.tsx` or broadens the verification set to include it. If the planner includes that file, budget a tiny cleanup.

## Skill Discovery

Installed relevant skill:
- `frontend-design` — useful only in the narrow sense of committing to a clear structural direction; do not turn this slice into visual-polish work.

Promising external skill candidate if the team wants one later:
- `wshobson/agents@nextjs-app-router-patterns`
  - install: `npx skills add wshobson/agents@nextjs-app-router-patterns`
  - why relevant: strongest Next.js/App Router-specific result from `npx skills find "Next.js"`
  - not required for this slice because the repo’s existing tests and patterns are already the better guide
