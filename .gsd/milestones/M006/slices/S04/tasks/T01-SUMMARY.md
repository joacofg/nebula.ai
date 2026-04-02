---
id: T01
parent: S04
milestone: M006
provides: []
requires: []
affects: []
key_files: ["console/src/components/ledger/ledger-request-detail.tsx", "console/src/components/ledger/ledger-request-detail.test.tsx", ".gsd/milestones/M006/slices/S04/tasks/T01-SUMMARY.md"]
key_decisions: ["Reused the existing S03 route vocabulary and policy-preview parity strings in the ledger request-detail surface instead of introducing a new explanation vocabulary.", "Treated duplicate routing-state labels in the summary card and detail row as intentional bounded operator evidence and locked that behavior in focused tests."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the focused verification command from the task plan: npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx. The first run failed because the new UI intentionally repeats routing-state values in both the summary and detail rows; updated the tests to assert that bounded duplication explicitly. Re-ran the suite and it passed with 15/15 tests. Also attempted LSP diagnostics for console/src/components/ledger/ledger-request-detail.tsx, but no TypeScript language server was active in this environment."
completed_at: 2026-04-02T04:04:56.027Z
blocker_discovered: false
---

# T01: Added bounded routing-state inspection to ledger request detail, including calibrated, degraded, rollout-disabled, and unscored persisted rows.

> Added bounded routing-state inspection to ledger request detail, including calibrated, degraded, rollout-disabled, and unscored persisted rows.

## What Happened
---
id: T01
parent: S04
milestone: M006
key_files:
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - .gsd/milestones/M006/slices/S04/tasks/T01-SUMMARY.md
key_decisions:
  - Reused the existing S03 route vocabulary and policy-preview parity strings in the ledger request-detail surface instead of introducing a new explanation vocabulary.
  - Treated duplicate routing-state labels in the summary card and detail row as intentional bounded operator evidence and locked that behavior in focused tests.
duration: ""
verification_result: mixed
completed_at: 2026-04-02T04:04:56.028Z
blocker_discovered: false
---

# T01: Added bounded routing-state inspection to ledger request detail, including calibrated, degraded, rollout-disabled, and unscored persisted rows.

**Added bounded routing-state inspection to ledger request detail, including calibrated, degraded, rollout-disabled, and unscored persisted rows.**

## What Happened

Extended the ledger request-detail component with local helpers that parse persisted route_signals into operator-facing routing inspection fields. The panel now renders bounded request-scoped routing state, route mode, route score, and additive score components when present, while preserving explicit null-mode semantics for rollout-disabled and unscored rows. Added focused Vitest coverage for calibrated additive-score rendering, degraded replay rendering, rollout-disabled null-mode rows, and partial-signal unscored rows. Adjusted assertions to explicitly lock the intentional duplication of routing-state values across the summary card and detail row.

## Verification

Ran the focused verification command from the task plan: npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx. The first run failed because the new UI intentionally repeats routing-state values in both the summary and detail rows; updated the tests to assert that bounded duplication explicitly. Re-ran the suite and it passed with 15/15 tests. Also attempted LSP diagnostics for console/src/components/ledger/ledger-request-detail.tsx, but no TypeScript language server was active in this environment.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` | 1 | ❌ fail | 2600ms |
| 2 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` | 0 | ✅ pass | 3000ms |
| 3 | `lsp diagnostics console/src/components/ledger/ledger-request-detail.tsx` | 1 | ❌ fail | 0ms |


## Deviations

None.

## Known Issues

No active TypeScript language server was available in the worktree, so diagnostics could not be collected through LSP.

## Files Created/Modified

- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `.gsd/milestones/M006/slices/S04/tasks/T01-SUMMARY.md`


## Deviations
None.

## Known Issues
No active TypeScript language server was available in the worktree, so diagnostics could not be collected through LSP.
