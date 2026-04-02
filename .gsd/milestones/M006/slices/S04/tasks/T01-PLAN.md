---
estimated_steps: 11
estimated_files: 3
skills_used: []
---

# T01: Render calibrated routing inspection in ledger request detail

Add bounded request-detail rendering for the selected persisted ledger row so operators can inspect calibrated, degraded, rollout-disabled, and unscored routing states directly from `route_signals` without inventing a new API or analytics surface.

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

## Inputs

- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/lib/admin-api.ts`

## Expected Output

- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`

## Verification

npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx

## Observability Impact

This task strengthens the primary operator inspection surface for a single request. Failures remain inspectable in the selected request panel itself, and the focused test file becomes the contract that locks calibrated/degraded/null-mode rendering.
