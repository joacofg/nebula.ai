# S04: Operator inspection surfaces

**Goal:** Expose calibrated-versus-heuristic routing state and contributing evidence through the existing request-detail and Observability console surfaces without adding new admin APIs or analytics-style views.
**Demo:** After this: After this: operators can inspect calibrated-vs-heuristic routing state and contributing evidence in existing request-detail and Observability surfaces.

## Tasks
- [x] **T01: Added bounded routing-state inspection to ledger request detail, including calibrated, degraded, rollout-disabled, and unscored persisted rows.** — Add bounded request-detail rendering for the selected persisted ledger row so operators can inspect calibrated, degraded, rollout-disabled, and unscored routing states directly from `route_signals` without inventing a new API or analytics surface.

Steps:
1. Extend `console/src/components/ledger/ledger-request-detail.tsx` with small local helpers that parse persisted `route_signals` into operator-facing routing-state fields: route mode, calibrated/degraded markers, total route score, and additive score components while preserving intentional null-mode semantics for rollout-disabled or policy-forced rows.
2. Reuse the established S03 vocabulary from `console/src/components/policy/policy-form.tsx` and `docs/route-decision-vocabulary.md` so calibrated, degraded, rollout-disabled, and unscored rows read consistently across preview and request detail.
3. Keep the selected ledger row authoritative: render routing evidence as part of request inspection, preserve existing budget/calibration summary context, and avoid turning the panel into a generic tenant analytics summary.
4. Extend `console/src/components/ledger/ledger-request-detail.test.tsx` with focused cases for calibrated rows with additive score components, degraded rows, rollout-disabled/null-mode rows, and rows whose route signals are absent or partial.

Must-haves:
- The panel shows a compact routing-state explanation derived from persisted `route_signals`, including route mode and score when present.
- Rollout-disabled and other intentional null-mode rows stay explicit rather than looking like missing data.
- Existing request-detail framing and no-payload-leak guarantees remain intact.
- Focused Vitest assertions cover the new routing inspection states and bounded rendering behavior.
  - Estimate: 45m
  - Files: console/src/components/ledger/ledger-request-detail.tsx, console/src/components/ledger/ledger-request-detail.test.tsx, console/src/components/policy/policy-form.tsx
  - Verify: npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx
- [ ] **T02: Compose Observability around request-first routing inspection** — Tighten the Observability page so it clearly presents one selected request as the primary proof surface, with calibration summary, grounded recommendations, cache/runtime state, and dependency health as supporting context for the same routing investigation.

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
  - Estimate: 45m
  - Files: console/src/app/(console)/observability/page.tsx, console/src/app/(console)/observability/observability-page.test.tsx, console/src/app/(console)/observability/page.test.tsx, console/src/components/ledger/ledger-request-detail.tsx
  - Verify: npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/app/'(console)'/observability/page.test.tsx
