---
estimated_steps: 6
estimated_files: 7
skills_used: []
---

# T02: Run assembled close-out verification and tighten cross-surface guards only if needed

Use the integrated proof order to re-run the focused console verification bundle and only touch tests if the assembled story reveals a real missing guard across Observability, request detail, ledger selection, and policy preview/page seams.

Steps:
1. Run the focused Vitest bundle covering `page.test.tsx`, `observability-page.test.tsx`, `ledger-request-detail.test.tsx`, `ledger-table.test.tsx`, `policy-form.test.tsx`, and `policy-page.test.tsx` to prove the assembled operator story in the shipped worktree.
2. Compare any failure or uncovered gap against the new integrated proof doc and prior slice summaries before editing: only add or tighten assertions when the gap is real integrated-proof drift, not because the slice needs extra churn.
3. If changes are required, keep them scoped to the relevant test file and assert the specific cross-surface boundary at risk: request-first ordering, request-detail authority, policy-preview next-step guidance, bounded selector semantics, or anti-drift language.
4. Re-run the same focused Vitest bundle until it passes cleanly and leaves a narrow, code-backed close-out proof for M007.

## Inputs

- ``docs/m007-integrated-proof.md``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/components/ledger/ledger-table.test.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``

## Expected Output

- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``
- ``console/src/components/ledger/ledger-table.test.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``

## Verification

npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/ledger/ledger-table.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx

## Observability Impact

Signals added/changed: focused Vitest assertions remain the durable failure-localization surface for hierarchy drift, authority drift, bounded selector regressions, and anti-drift wording changes.
How a future agent inspects this: re-run the same six-file Vitest bundle and inspect the failing test closest to the violated page role.
Failure state exposed: test failures should pinpoint whether the break is in Observability order, request-detail authority, policy-preview/save separation, or scope-language drift.
