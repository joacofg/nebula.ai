# S01: Define page roles and evidence boundaries

**Goal:** Define and lock the operator-surface role contract so Observability is structurally request-investigation-first, request detail stays the authoritative persisted evidence record, and later slices inherit clear evidence-boundary rules without dashboard drift.
**Demo:** After this: After this: Nebula has one explicit operator-surface model that says what Observability, request detail, and policy preview are for, what evidence leads, and what context stays secondary.

## Tasks
- [x] **T01: Reordered Observability so selected-request investigation leads the page and added hierarchy guardrails in focused tests.** — Rework the Observability page so the selected request investigation section leads the main page hierarchy after filters, with supporting context clearly sequenced after the authoritative request investigation. Strengthen the focused page tests so they assert section order and subordinate framing rather than only headline presence.

Steps:
1. Update `console/src/app/(console)/observability/page.tsx` so the selected-request section renders before supporting context, while preserving existing bounded wording and runtime data seams.
2. Extend `console/src/app/(console)/observability/page.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` to assert the structural hierarchy: selected request leads, supporting context follows, and dependency health remains supporting context.
3. Keep the page within the current Observability surface — no new dashboard shell, analytics framing, or alternate workflow entrypoints.

Must-haves:
- The selected-request section is the first major evidence section after filters.
- Supporting context copy still states it is subordinate to the selected request.
- Tests fail if future changes move supporting context ahead of the request investigation or introduce dashboard-style framing.
  - Estimate: 45m
  - Files: console/src/app/(console)/observability/page.tsx, console/src/app/(console)/observability/page.test.tsx, console/src/app/(console)/observability/observability-page.test.tsx
  - Verify: npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx
- [x] **T02: Locked request-detail authority copy and hardened policy preview guardrails with focused boundary tests.** — Preserve `LedgerRequestDetail` as the authoritative persisted evidence surface and add guardrails that later M007 slices must preserve: interpretation stays secondary, policy preview stays preview-before-save, and no new analytics/dashboard drift appears in these bounded surfaces.

Steps:
1. Review `console/src/components/ledger/ledger-request-detail.tsx` and tighten wording or section ordering only if needed to make persisted evidence clearly lead supporting interpretation.
2. Extend `console/src/components/ledger/ledger-request-detail.test.tsx` with assertions that the persisted record remains primary and supplementary interpretation does not replace it.
3. Add or tighten policy role-boundary assertions in `console/src/components/policy/policy-form.test.tsx` and `console/src/components/policy/policy-page.test.tsx` so S04 inherits an explicit preview-before-save decision-review contract without analytics drift.

Must-haves:
- Request detail still leads with persisted request fields and keeps calibration/budget/routing explanations supplementary.
- Policy preview remains explicitly non-saving until the operator chooses save.
- Tests reject dashboard, routing-studio, or analytics-product framing on these bounded surfaces.
  - Estimate: 45m
  - Files: console/src/components/ledger/ledger-request-detail.tsx, console/src/components/ledger/ledger-request-detail.test.tsx, console/src/components/policy/policy-form.test.tsx, console/src/components/policy/policy-page.test.tsx
  - Verify: npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx
