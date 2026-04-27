# S04 — Research

**Date:** 2026-04-27

## Summary

S04 is a targeted console slice for active requirement **R076**. The backend seams it depends on are already in place from S02/S03: live requests persist additive `route_signals.outcome_evidence` plus calibrated/degraded score state, and replay now reuses the same evidence vocabulary. The remaining work is to make the existing request-first operator surfaces explain whether the selected request was grounded, thin, stale, or degraded without introducing a tenant-summary-first dashboard. This aligns directly with decision D051 / MEM051: keep the selected request row authoritative and make any tenant context explicitly subordinate.

The main implementation seam is already concentrated in `console/src/components/ledger/ledger-request-detail.tsx` and `console/src/app/(console)/observability/page.tsx`. `LedgerRequestDetail` already renders request-level routing inspection, calibration evidence, and budget evidence. It knows how to phrase `sufficient`, `thin`, and `stale` states, and it already renders degraded request routing when `route_signals.route_mode === "degraded"`. The biggest gap is that the operator vocabulary is split: request detail still speaks in terms of `calibrated/degraded/unscored/rollout disabled`, while the slice requirement asks for explicit grounded/thin/stale/degraded explanation tied to the selected request. The planner should treat this as mostly wording/contract alignment plus focused tests, not a new data-flow feature.

A second important finding: there is already a legacy observability test file whose fixtures are stale against the current `UsageLedgerRecord` shape. `console/src/app/(console)/observability/page.test.tsx` passes, but `console/src/app/(console)/observability/observability-page.test.tsx` currently fails because its mocked ledger row omits `metadata_fields_suppressed`, causing `LedgerRequestDetail` to throw in `formatSuppressedFields()`. That means S04 will likely need a small amount of test-fixture repair or defensive rendering before adding new assertions, otherwise the proof layer for this slice remains noisy.

## Recommendation

Implement S04 as an additive UI contract refinement on the **existing selected-request surfaces**, following the request-first rule from the loaded guidance and prior decisions. Do **not** add a new summary widget, trend panel, or dashboard-level routing-quality visualization. Instead:

1. Extend `LedgerRequestDetail` so the selected request explicitly explains the outcome-grounded evidence state for that request investigation using the existing persisted request row plus optional tenant calibration summary.
2. Keep `ObservabilityPage` framing unchanged at the page-architecture level: selected request first, tenant/replay/cache/dependency context second.
3. Use focused Vitest coverage in the existing request-detail and observability tests to prove grounded/thin/stale/degraded wording and hierarchy.

This follows the installed skills guidance most directly from **react-best-practices** (refine existing components and typed props rather than creating new surface area) and **verify-before-complete** (use fresh focused test evidence before any completion claim). It also follows the S02/S03 forward intelligence: reuse the persisted `route_signals` + `calibration_summary` seam, do not invent replay-only or UI-only evidence structures.

## Implementation Landscape

### Key Files

- `console/src/components/ledger/ledger-request-detail.tsx` — Primary request-detail seam. Already renders authoritative selected-row evidence, `Calibration evidence`, `Routing inspection`, `Budget policy evidence`, and raw route-signal rows. Important helpers:
  - `buildCalibrationExplanation(summary)` — currently maps `sufficient`/`stale`/rollout-disabled/`thin` to badge + summary + detail.
  - `buildRoutingInspection(routeSignals, routeReason)` — currently maps request row state into `calibrated`, `degraded`, `rollout disabled`, or `unscored` summaries.
  - `formatSuppressedFields(fields)` — currently assumes `metadata_fields_suppressed` exists; stale fixtures can crash here.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Best proof seam for S04. Already covers calibrated, degraded, thin, stale, rollout-disabled, null-state, and governance-boundary messaging. This is the natural place to add explicit assertions for grounded/thin/stale/degraded operator wording if the component text changes.
- `console/src/app/(console)/observability/page.tsx` — Request-first page composition. Passes `selectedEntry` and `recommendationsQuery.data?.calibration_summary` into `LedgerRequestDetail`. Also renders follow-up cards for tenant-scoped replay readiness, cache posture, and dependency health. Natural seam if copy must reinforce that tenant context is supporting only.
- `console/src/app/(console)/observability/page.test.tsx` — Current passing request-first hierarchy proof. Good place for one integrated assertion that the selected request explanation appears before follow-up context and does not drift into analytics wording.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Older/stale test file with broader scenarios for sufficient/thin/stale/gated calibration states. Currently failing because mocked ledger rows omit fields now read by `LedgerRequestDetail`. If retained, it must be repaired; otherwise it will obscure slice verification.
- `console/src/lib/admin-api.ts` — Type contract. `CalibrationEvidenceSummary.state` already includes `"degraded"`; no new backend type should be necessary unless the console wants a more explicit request-level evidence-state helper type.
- `console/src/components/policy/policy-form.tsx` / `console/src/components/policy/policy-form.test.tsx` — Reference pattern for rendering parity-oriented routing state and degraded wording without creating a new UI contract.
- `console/src/components/ledger/ledger-table.tsx` — Selected-request promotion UI. Probably unchanged, but it remains part of the request-first composition proof.

### Build Order

1. **Lock the selected-request vocabulary in `LedgerRequestDetail` first.** This is the authoritative operator surface for R076 and unblocks everything else. Decide whether “grounded” is derived from `calibrationSummary.state === "sufficient"`, from calibrated request-row signals, or from a combination of both. Keep the explanation scoped to the selected request investigation.
2. **Repair/normalize test coverage immediately after the component change.** Update `ledger-request-detail.test.tsx` first because it is the most focused contract suite. Also address the stale fixtures in `observability-page.test.tsx` / `observability/observability-page.test.tsx` or harden `formatSuppressedFields()` so observability tests stop crashing on omitted fixture fields.
3. **Adjust `ObservabilityPage` copy only if needed.** The page already has the right hierarchy. Only change it if the selected-request vs supporting-context framing needs stronger explicit wording for grounded/thin/stale/degraded state.
4. **Run focused console verification.** The page-level tests should prove hierarchy; request-detail tests should prove the actual state wording. No backend code should be touched unless the scout’s findings prove the UI lacks a needed persisted field, which does not appear to be the case.

### Verification Approach

- Focused request-detail contract:
  - `npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'`
- Focused observability hierarchy proof:
  - `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'`
- Broader observability regression (after fixing stale fixtures or component defensiveness):
  - `npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'`
- Optional cross-surface replay-context regression to ensure no vocabulary drift from S03:
  - `npm --prefix console run test -- --run 'src/components/policy/policy-form.test.tsx'`

Current verification state from research:
- `ledger-request-detail.test.tsx` and `observability/page.test.tsx` already pass together.
- `observability/observability-page.test.tsx` currently fails because mocked rows are missing `metadata_fields_suppressed`; this is a pre-existing console test drift the planner should budget for.
- A broad backend governance pytest command is currently noisy/failing for unrelated reasons (stub field drift and older assertion expectations in `tests/test_governance_api.py`), so S04 proof should stay console-focused unless the planner intentionally includes backend cleanup.

## Constraints

- Request-first remains mandatory: selected ledger row must stay authoritative; tenant summary is supporting only (D051, MEM051).
- Reuse the shared evidence contract from S02/S03; do not invent a UI-only evidence taxonomy separate from `route_signals` and `calibration_summary`.
- Keep the surface additive and inspection-oriented; no dashboard, routing studio, or analytics-product drift.
- Hosted remains informational only; request evidence must remain local-row-based.

## Common Pitfalls

- **Splitting request vs tenant vocabulary** — If request detail says `calibrated` while supporting cards say `sufficient/thin/stale/degraded` without a clear bridge, operators may have to infer the relationship themselves. Prefer one explicit explanatory sentence in request detail that ties the selected request to the tenant evidence state.
- **Letting stale tests mask real UI regressions** — `observability/observability-page.test.tsx` already crashes on incomplete fixtures. Fix or harden this before relying on it as slice proof.
- **Over-expanding the page** — The observability page already has multiple supporting cards. Any new UI should replace/clarify wording inside current cards rather than adding new routing-quality surfaces.

## Open Risks

- The exact product wording for “grounded” may need a deliberate choice: the code currently has `sufficient` and `calibrated`, but not a first-class `grounded` label. The planner should make that vocabulary decision explicit so executor work does not churn on copy.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| React / Next.js console work | installed: `react-best-practices` | available |
| UI quality / hierarchy review | installed: `web-design-guidelines` | available |
| Next.js | `vercel-labs/vercel-plugin@nextjs` (`npx skills add vercel-labs/vercel-plugin@nextjs`) | available, not installed |
