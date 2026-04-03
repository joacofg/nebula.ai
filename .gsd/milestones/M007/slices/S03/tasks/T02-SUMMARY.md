---
id: T02
parent: S03
milestone: M007
provides: []
requires: []
affects: []
key_files: ["console/src/components/ledger/ledger-table.tsx", "console/src/components/ledger/ledger-table.test.tsx", ".gsd/KNOWLEDGE.md"]
key_decisions: ["Kept the stronger request-selection affordance inside `LedgerTable` by adding explicit selector semantics and bounded copy instead of widening the page or turning the table into a second detail surface."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the focused console Vitest suite for the ledger table and both Observability page test files. All targeted tests passed, confirming the stronger row-selection cues while preserving the selected-request-first page hierarchy."
completed_at: 2026-04-03T02:35:53.880Z
blocker_discovered: false
---

# T02: Made the selected ledger row read as the current investigation target without expanding the table beyond a bounded request selector.

> Made the selected ledger row read as the current investigation target without expanding the table beyond a bounded request selector.

## What Happened
---
id: T02
parent: S03
milestone: M007
key_files:
  - console/src/components/ledger/ledger-table.tsx
  - console/src/components/ledger/ledger-table.test.tsx
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Kept the stronger request-selection affordance inside `LedgerTable` by adding explicit selector semantics and bounded copy instead of widening the page or turning the table into a second detail surface.
duration: ""
verification_result: passed
completed_at: 2026-04-03T02:35:53.881Z
blocker_discovered: false
---

# T02: Made the selected ledger row read as the current investigation target without expanding the table beyond a bounded request selector.

**Made the selected ledger row read as the current investigation target without expanding the table beyond a bounded request selector.**

## What Happened

Updated `console/src/components/ledger/ledger-table.tsx` so request selection is explicit instead of relying on background tint alone. The selected row now exposes `aria-selected`, the request cell is a real button with `aria-pressed`, and the active entry gets a compact `Current investigation` badge plus short supporting copy that points back to the primary detail view. Unselected rows keep a lighter `Select request` cue so the table still reads as a bounded selector rather than a second analysis surface. Extended `console/src/components/ledger/ledger-table.test.tsx` to lock the new selected and unselected affordances, selector semantics, and anti-drift boundaries. The existing Observability page tests already passed against the stronger table seam, so no page-level code changes were needed. Recorded the seam choice in `.gsd/KNOWLEDGE.md` for future Observability refinement work.

## Verification

Ran the focused console Vitest suite for the ledger table and both Observability page test files. All targeted tests passed, confirming the stronger row-selection cues while preserving the selected-request-first page hierarchy.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx` | 0 | ✅ pass | 11700ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/components/ledger/ledger-table.tsx`
- `console/src/components/ledger/ledger-table.test.tsx`
- `.gsd/KNOWLEDGE.md`


## Deviations
None.

## Known Issues
None.
