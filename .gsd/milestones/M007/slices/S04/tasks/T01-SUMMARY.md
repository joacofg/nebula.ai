---
id: T01
parent: S04
milestone: M007
provides: []
requires: []
affects: []
key_files: ["console/src/components/policy/policy-form.tsx", "console/src/components/policy/policy-form.test.tsx", ".gsd/milestones/M007/slices/S04/tasks/T01-SUMMARY.md"]
key_decisions: ["Derived preview decision summaries at render time from simulationResult instead of adding client state or changing the payload contract.", "Kept changed-request evidence and replay notes explicitly subordinate to a decision-first preview summary."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the focused Vitest suite with npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx and it passed. Attempted post-edit LSP diagnostics for the TS files, but no TypeScript language server was active in this environment, so focused Vitest coverage remained the verification surface."
completed_at: 2026-04-03T02:44:23.497Z
blocker_discovered: false
---

# T01: Restructured the policy preview into a decision-first baseline-versus-draft review with explicit next-step guidance and bounded evidence.

> Restructured the policy preview into a decision-first baseline-versus-draft review with explicit next-step guidance and bounded evidence.

## What Happened
---
id: T01
parent: S04
milestone: M007
key_files:
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - .gsd/milestones/M007/slices/S04/tasks/T01-SUMMARY.md
key_decisions:
  - Derived preview decision summaries at render time from simulationResult instead of adding client state or changing the payload contract.
  - Kept changed-request evidence and replay notes explicitly subordinate to a decision-first preview summary.
duration: ""
verification_result: mixed
completed_at: 2026-04-03T02:44:23.498Z
blocker_discovered: false
---

# T01: Restructured the policy preview into a decision-first baseline-versus-draft review with explicit next-step guidance and bounded evidence.

**Restructured the policy preview into a decision-first baseline-versus-draft review with explicit next-step guidance and bounded evidence.**

## What Happened

Refactored the preview section in console/src/components/policy/policy-form.tsx so it derives a decision summary directly from simulationResult at render time. The preview now leads with baseline-versus-draft consequence and explicit next-step guidance, while keeping the changed-request sample and replay notes subordinate. Loading, failure, empty-window, unchanged, and changed-outcome states all preserve explicit save separation. Expanded console/src/components/policy/policy-form.test.tsx to prove the new hierarchy, save/don’t-save semantics, malformed/null routing parity rendering, rollout-disabled parity handling, and anti-drift wording boundaries.

## Verification

Ran the focused Vitest suite with npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx and it passed. Attempted post-edit LSP diagnostics for the TS files, but no TypeScript language server was active in this environment, so focused Vitest coverage remained the verification surface.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx` | 0 | ✅ pass | 1270ms |
| 2 | `lsp diagnostics console/src/components/policy/policy-form.tsx` | 1 | ❌ fail | 0ms |
| 3 | `lsp diagnostics console/src/components/policy/policy-form.test.tsx` | 1 | ❌ fail | 0ms |


## Deviations

None.

## Known Issues

No active TypeScript language server was available for diagnostics in this environment.

## Files Created/Modified

- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `.gsd/milestones/M007/slices/S04/tasks/T01-SUMMARY.md`


## Deviations
None.

## Known Issues
No active TypeScript language server was available for diagnostics in this environment.
