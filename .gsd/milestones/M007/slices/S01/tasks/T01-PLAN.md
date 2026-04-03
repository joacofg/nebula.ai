---
estimated_steps: 3
estimated_files: 3
skills_used:
  - react-best-practices
  - frontend-design
---

# T01: Make Observability structurally selected-request-first

**Slice:** S01 — Define page roles and evidence boundaries
**Milestone:** M007

## Description

Rework the Observability page so the selected request investigation section leads the main page hierarchy after filters, with supporting context clearly sequenced after the authoritative request investigation. The goal is to make structure carry the page role, not just the prose.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| `getUsageLedger` data rendered by `console/src/app/(console)/observability/page.tsx` | Preserve the existing ledger error state and keep tests focused on section hierarchy rather than changing fetch behavior. | Keep the existing loading path; do not add new waits or alternate flows in this slice. | Preserve current null/empty-state handling instead of inventing fallback sections that could distort hierarchy. |
| `getTenantRecommendations` / runtime health data used as supporting context | Keep recommendation and health panels subordinate; do not let error or loading states become the lead page object. | Retain current loading cards as supporting context only. | Preserve bounded “supporting context” framing even when recommendation payload fields are sparse. |

## Load Profile

- **Shared resources**: Client-side query rendering for usage-ledger, recommendation, and runtime-health panels.
- **Per-operation cost**: One page render over existing query results; this task is structural and test-focused, not query-expanding.
- **10x breakpoint**: Page readability and DOM complexity drift before performance does; the main risk is supporting cards visually reclaiming priority as more context is added.

## Negative Tests

- **Malformed inputs**: Empty ledger state and sparse supporting-context payloads should still preserve request-first wording and ordering.
- **Error paths**: Recommendation or dependency-health failures must remain visibly secondary to the request investigation contract.
- **Boundary conditions**: The selected-request section must remain the first major evidence section after filters regardless of whether recommendation cards are empty or populated.

## Steps

1. Update `console/src/app/(console)/observability/page.tsx` so the selected-request section renders before supporting context while preserving existing bounded wording and data seams.
2. Extend `console/src/app/(console)/observability/page.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` to assert section order, subordinate supporting-context framing, and rejection of dashboard-style drift.
3. Run the focused Observability Vitest files and leave the page with no new dashboard shell, analytics framing, or alternate workflow entrypoint.

## Must-Haves

- [ ] The selected-request section is the first major evidence section after `LedgerFilters`.
- [ ] Supporting context copy still states it is subordinate to the selected request investigation.
- [ ] Focused tests fail if supporting context moves ahead of the request section or if the page starts reading like a dashboard.

## Verification

- `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx`
- `rg -n "Selected request evidence first|Grounded follow-up guidance for the selected request|Inspect one persisted ledger row before reading tenant context" console/src/app/'(console)'/observability/page.tsx`

## Observability Impact

- Signals added/changed: Structural hierarchy is now encoded in explicit test assertions around section order and supporting-context wording.
- How a future agent inspects this: Run the two Observability Vitest files and inspect the rendered section order in `console/src/app/(console)/observability/page.tsx`.
- Failure state exposed: Regressions surface as failing assertions when supporting context regains primary placement or wording.

## Inputs

- `console/src/app/(console)/observability/page.tsx` — Current page structure and wording that contradict the intended hierarchy.
- `console/src/app/(console)/observability/page.test.tsx` — Focused page test coverage for wording that needs stronger structural assertions.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Integrated Observability test coverage that should encode the same hierarchy contract.

## Expected Output

- `console/src/app/(console)/observability/page.tsx` — Reordered request-first Observability structure with bounded supporting-context placement.
- `console/src/app/(console)/observability/page.test.tsx` — Strengthened structural assertions for request-first hierarchy.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Integrated hierarchy guardrails aligned to the new page order.
