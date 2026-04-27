---
estimated_steps: 51
estimated_files: 4
skills_used: []
---

# T02: Prove request-first observability hierarchy with repaired page-level fixtures

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

## Inputs

- ``console/src/app/(console)/observability/page.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``
- ``console/src/components/ledger/ledger-request-detail.tsx``

## Expected Output

- ``console/src/app/(console)/observability/page.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``

## Verification

npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx' && npm --prefix console run test -- --run 'src/app/(console)/observability/observability-page.test.tsx'

## Observability Impact

Page-level request-first regressions are localized by the observability Vitest suites and current selected-request UI state; no new runtime observability surface is added.
