---
estimated_steps: 48
estimated_files: 4
skills_used: []
---

# T01: Align selected-request evidence wording with grounded/thin/stale/degraded states

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

## Inputs

- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/lib/admin-api.ts``
- ``.gsd/DECISIONS.md``

## Expected Output

- ``console/src/components/ledger/ledger-request-detail.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``

## Verification

npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'

## Observability Impact

Selected-request explanation drift is localized by the request-detail component and its focused Vitest suite; no new runtime telemetry is introduced.
