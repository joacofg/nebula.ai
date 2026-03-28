---
id: T03
parent: S03
milestone: M005
provides: []
requires: []
affects: []
key_files: ["console/src/components/policy/policy-form.tsx", "console/src/components/policy/policy-form.test.tsx", "console/src/components/policy/policy-page.test.tsx", "console/e2e/policy.spec.ts", "console/src/components/ledger/ledger-request-detail.tsx", "console/src/components/ledger/ledger-request-detail.test.tsx", "docs/route-decision-vocabulary.md", "docs/policy-guardrails.md", ".gsd/milestones/M005/slices/S03/tasks/T03-SUMMARY.md"]
key_decisions: ["Preserved the raw persisted `policy_outcome` field in request detail for audit continuity, then layered structured budget evidence beside it for operator inspection.", "Kept hard-budget documentation and UI copy inside existing routing/decisioning scope rather than expanding into billing or analytics semantics."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx && test -f docs/policy-guardrails.md` and confirmed all 19 focused Vitest assertions passed and the new docs file exists. The updated tests verify runtime-enforced copy, advisory-only soft-budget wording, and structured hard-budget evidence rendering in the request-detail surface."
completed_at: 2026-03-28T03:45:30.708Z
blocker_discovered: false
---

# T03: Exposed hard-budget guardrail explanations across the policy editor, ledger request detail, and operator docs while keeping soft budget advisory-only.

> Exposed hard-budget guardrail explanations across the policy editor, ledger request detail, and operator docs while keeping soft budget advisory-only.

## What Happened
---
id: T03
parent: S03
milestone: M005
key_files:
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - console/e2e/policy.spec.ts
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - docs/route-decision-vocabulary.md
  - docs/policy-guardrails.md
  - .gsd/milestones/M005/slices/S03/tasks/T03-SUMMARY.md
key_decisions:
  - Preserved the raw persisted `policy_outcome` field in request detail for audit continuity, then layered structured budget evidence beside it for operator inspection.
  - Kept hard-budget documentation and UI copy inside existing routing/decisioning scope rather than expanding into billing or analytics semantics.
duration: ""
verification_result: passed
completed_at: 2026-03-28T03:45:30.709Z
blocker_discovered: false
---

# T03: Exposed hard-budget guardrail explanations across the policy editor, ledger request detail, and operator docs while keeping soft budget advisory-only.

**Exposed hard-budget guardrail explanations across the policy editor, ledger request detail, and operator docs while keeping soft budget advisory-only.**

## What Happened

Updated the policy editor so runtime-enforced controls explicitly explain hard cumulative budget behavior and keep soft budget messaging advisory-only. Extended the ledger request-detail surface with labeled budget evidence derived from persisted policy outcomes so downgrade-versus-deny outcomes are inspectable without raw string parsing. Refreshed the route-decision vocabulary doc and added a dedicated policy guardrails doc to keep operator-facing budget language stable and within decisioning scope.

## Verification

Ran `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx && test -f docs/policy-guardrails.md` and confirmed all 19 focused Vitest assertions passed and the new docs file exists. The updated tests verify runtime-enforced copy, advisory-only soft-budget wording, and structured hard-budget evidence rendering in the request-detail surface.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx && test -f docs/policy-guardrails.md` | 0 | ✅ pass | 934ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `console/e2e/policy.spec.ts`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `docs/route-decision-vocabulary.md`
- `docs/policy-guardrails.md`
- `.gsd/milestones/M005/slices/S03/tasks/T03-SUMMARY.md`


## Deviations
None.

## Known Issues
None.
