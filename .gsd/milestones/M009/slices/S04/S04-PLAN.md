# S04: Request-first operator evidence

**Goal:** Expose outcome-grounded request evidence on the existing request-first Observability surfaces so operators can tell whether the selected request used grounded, thin, stale, or degraded routing without introducing a new dashboard surface.
**Demo:** After this: the selected request in Observability and request detail explains whether routing was grounded, thin, stale, or degraded using the existing request-first evidence surfaces.

## Must-Haves

- The selected request detail explains the request investigation in grounded/thin/stale/degraded vocabulary tied to the existing persisted `route_signals` and supporting `calibration_summary` contract.
- Observability page copy and badges keep the selected ledger row authoritative while clearly positioning tenant calibration, cache, and dependency cards as supporting context.
- Focused console tests prove grounded, thin, stale, degraded, and rollout-disabled operator wording on request detail and page-level request-first hierarchy.
- Stale observability fixtures no longer crash request-detail rendering when the `UsageLedgerRecord` shape includes governed metadata fields.

## Proof Level

- This slice proves: This slice proves: integration
- Real runtime required: no
- Human/UAT required: no

## Integration Closure

- Upstream surfaces consumed: `console/src/lib/admin-api.ts` shared `CalibrationEvidenceSummary` / `UsageLedgerRecord` contracts; `console/src/components/ledger/ledger-request-detail.tsx`; `console/src/app/(console)/observability/page.tsx`; S02/S03 persisted `route_signals` and `calibration_summary` vocabulary.
- New wiring introduced in this slice: copy/state mapping inside existing selected-request request detail and observability composition only; no new API surface.
- What remains before the milestone is truly usable end-to-end: S05 still needs the final live request → persisted evidence → replay parity → operator walkthrough and milestone anti-drift close-out.

## Verification

- Runtime signals: existing selected-request UI state, persisted `route_signals`, and tenant `calibration_summary` remain the inspection seam; this slice only clarifies how those signals are interpreted.
- Inspection surfaces: `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/app/(console)/observability/page.tsx`, and their focused Vitest suites.
- Failure visibility: wording/state drift or stale fixtures will fail focused request-detail and observability tests instead of silently regressing operator explanation.
- Redaction constraints: request detail must continue honoring governed metadata suppression and must not imply hosted/raw row recovery.

## Tasks

- [x] **T01: Align selected-request evidence wording with grounded/thin/stale/degraded states** `est:45m`
  ---
estimated_steps: 5
estimated_files: 4
skills_used:
  - react-best-practices
  - verify-before-complete
---

# T01: Align selected-request evidence wording with grounded/thin/stale/degraded states

**Slice:** S04 — Request-first operator evidence
**Milestone:** M009

## Description

R076 is fulfilled only if the selected request itself explains outcome-informed routing using one operator vocabulary. This task should refine the existing `LedgerRequestDetail` mapping so grounded/thin/stale/degraded meaning is explicit on the selected row, while preserving the request-first rule from D051/MEM051: the persisted row stays authoritative and the tenant summary remains supporting context only.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| `getTenantRecommendations()` / `calibration_summary` data consumed by `LedgerRequestDetail` | Keep request detail renderable from the selected `UsageLedgerRecord` alone and fall back to request-level wording rather than crashing or hiding the row. | Render the selected row without tenant-summary copy and keep supporting-context sections optional. | Treat unknown/missing summary fields conservatively, avoid new UI-only evidence states, and keep wording anchored to persisted request evidence. |

## Load Profile

- **Shared resources**: Browser render tree and React Query cached observability/admin responses.
- **Per-operation cost**: One selected-request detail render plus supporting copy/state mapping; trivial compute over an already-fetched row and summary.
- **10x breakpoint**: Copy/state branching drift becomes harder to reason about before raw rendering cost matters.

## Negative Tests

- **Malformed inputs**: `route_signals=null`, absent route-mode fields, and missing/empty supporting summary values still render a usable selected-request explanation.
- **Error paths**: No tenant summary available should omit supporting calibration evidence without crashing the request detail.
- **Boundary conditions**: sufficient/grounded, thin, stale, degraded, rollout-disabled, and unscored request states all remain distinguishable without inventing an analytics surface.

## Steps

1. Update `console/src/components/ledger/ledger-request-detail.tsx` state mapping and copy so the request investigation explicitly bridges persisted request routing (`route_signals`) and supporting tenant evidence (`calibration_summary`) using grounded/thin/stale/degraded vocabulary.
2. Preserve D051 request-first hierarchy by keeping selected-row language authoritative and clearly subordinate any tenant summary text; do not add a new panel, chart, or summary-first surface.
3. Harden governed-field rendering where needed so stale or incomplete fixtures do not throw when `metadata_fields_suppressed` is omitted or empty.
4. Extend `console/src/components/ledger/ledger-request-detail.test.tsx` with explicit assertions for grounded/thin/stale/degraded/rollout-disabled wording and request-first hierarchy.
5. Run the focused request-detail test command and fix any expectation drift before handing off.

## Must-Haves

- [ ] The selected request detail uses explicit grounded/thin/stale/degraded operator wording derived from existing persisted evidence seams rather than a new UI-only taxonomy.
- [ ] Request detail still renders safely when route signals or suppressed metadata fields are missing, and the selected row remains authoritative over supporting context.

## Verification

- `npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'`
- The test suite asserts grounded/thin/stale/degraded copy, rollout-disabled handling, and safe rendering with incomplete request fixtures.

## Observability Impact

- Signals added/changed: selected-request explanation copy and state labels derived from persisted `route_signals` plus optional `calibration_summary`.
- How a future agent inspects this: open `console/src/components/ledger/ledger-request-detail.tsx` and run the focused Vitest file.
- Failure state exposed: operator-vocabulary drift or fixture-shape crashes show up as failing request-detail tests.

## Inputs

- `console/src/components/ledger/ledger-request-detail.tsx` — existing request-detail evidence mapping and governed-field rendering.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — focused request-detail contract coverage to extend.
- `console/src/lib/admin-api.ts` — shared `CalibrationEvidenceSummary` and `UsageLedgerRecord` type contract.
- `.gsd/DECISIONS.md` — D051 request-first operator-surface constraint.

## Expected Output

- `console/src/components/ledger/ledger-request-detail.tsx` — updated request-first grounded/thin/stale/degraded explanation mapping.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — focused assertions proving the selected-request operator vocabulary and safe rendering.
  - Files: `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/lib/admin-api.ts`, `.gsd/DECISIONS.md`
  - Verify: npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'

- [x] **T02: Prove request-first observability hierarchy with repaired page-level fixtures** `est:45m`
  ---
estimated_steps: 5
estimated_files: 4
skills_used:
  - react-best-practices
  - verify-before-complete
---

# T02: Prove request-first observability hierarchy with repaired page-level fixtures

**Slice:** S04 — Request-first operator evidence
**Milestone:** M009

## Description

Once the selected-request wording is aligned, the page-level proof must show that Observability still leads with the chosen ledger row and only then offers supporting calibration/cache/dependency context. This task should update the existing page copy/badges only where necessary, repair stale fixtures in the broader observability suite, and lock the hierarchy into focused tests so R076 is verifiable from the existing request-first surfaces.

## Failure Modes

| Dependency | On error | On timeout | On malformed response |
|------------|----------|-----------|----------------------|
| `listUsageLedger()` selected-row fixtures | Keep the page test focused on existing request-first composition and repair fixtures to match current `UsageLedgerRecord` shape instead of weakening the component contract. | Use deterministic mocked queries only; no network timing should be required beyond React Query settling. | Add missing governed metadata fields and route evidence fields so the page exercises the real request-detail contract instead of a stale surrogate. |
| `getTenantRecommendations()` calibration summary fixtures | Keep supporting cards subordinate and state-specific; if a fixture is incomplete, make the mock explicit rather than broadening production null-handling unnecessarily. | Wait on the focused heading/card assertions rather than brittle timing assumptions. | Keep fixture states aligned with the shared `CalibrationEvidenceSummary` union, including degraded-compatible semantics from S03. |

## Load Profile

- **Shared resources**: React Query caches, selected-row page composition, and test fixture data reused across multiple observability suites.
- **Per-operation cost**: One mocked page render plus focused assertions over selected-request and supporting-context sections.
- **10x breakpoint**: Fixture drift across parallel observability tests becomes the main maintenance risk before render performance matters.

## Negative Tests

- **Malformed inputs**: Legacy page fixtures missing governed metadata fields should be repaired so they no longer crash request detail.
- **Error paths**: No recommendation cards or thin/stale/gated summaries should still preserve the request-first page framing.
- **Boundary conditions**: grounded/sufficient, thin, stale, and rollout-disabled supporting summaries remain subordinate to the same selected request investigation.

## Steps

1. Update `console/src/app/(console)/observability/page.tsx` only where needed so badges/copy align with the request-detail grounded/thin/stale/degraded vocabulary while preserving the current page architecture.
2. Repair `console/src/app/(console)/observability/page.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` fixtures to include the current `UsageLedgerRecord` fields, especially governed metadata suppression fields consumed by request detail.
3. Add or tighten page-level assertions proving the selected ledger row appears before supporting calibration/cache/dependency cards and that supporting cards never overrule the selected request evidence.
4. Keep the broader observability coverage anchored to existing request-first surfaces; do not add dashboard-style analytics assertions.
5. Run both focused page-level test files and fix copy/fixture drift until they pass together.

## Must-Haves

- [ ] Observability page tests prove the selected ledger row remains first and authoritative while calibration/cache/dependency cards stay supporting context for the same request.
- [ ] The broader observability suite uses up-to-date request fixtures and no longer crashes on missing `metadata_fields_suppressed` or other current ledger fields.

## Verification

- `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx'`
- `npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'`
- Both page-level suites pass while asserting request-first hierarchy and grounded/thin/stale/degraded supporting-context behavior.

## Observability Impact

- Signals added/changed: page-level wording/badges that explain supporting calibration state relative to the selected request.
- How a future agent inspects this: run the two observability Vitest files and compare their fixtures/assertions with `LedgerRequestDetail` behavior.
- Failure state exposed: selected-request hierarchy drift or stale fixture regressions show up as page-level test failures instead of silent UI erosion.

## Inputs

- `console/src/app/(console)/observability/page.tsx` — request-first page composition and supporting-context copy.
- `console/src/app/(console)/observability/page.test.tsx` — focused page hierarchy contract.
- `console/src/app/(console)/observability/observability-page.test.tsx` — broader observability regression suite with stale fixtures to repair.
- `console/src/components/ledger/ledger-request-detail.tsx` — selected-request component contract established by T01.

## Expected Output

- `console/src/app/(console)/observability/page.tsx` — aligned request-first page wording/badge handling if needed.
- `console/src/app/(console)/observability/page.test.tsx` — focused hierarchy assertions kept current.
- `console/src/app/(console)/observability/observability-page.test.tsx` — repaired fixtures and broader request-first regression coverage.
  - Files: `console/src/app/(console)/observability/page.tsx`, `console/src/app/(console)/observability/page.test.tsx`, `console/src/app/(console)/observability/observability-page.test.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`
  - Verify: npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx' && npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'

## Files Likely Touched

- console/src/components/ledger/ledger-request-detail.tsx
- console/src/components/ledger/ledger-request-detail.test.tsx
- console/src/lib/admin-api.ts
- .gsd/DECISIONS.md
- console/src/app/(console)/observability/page.tsx
- console/src/app/(console)/observability/page.test.tsx
- console/src/app/(console)/observability/observability-page.test.tsx
