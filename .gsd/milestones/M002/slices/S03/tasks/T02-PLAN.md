---
estimated_steps: 3
estimated_files: 7
skills_used:
  - react-best-practices
  - test
---

# T02: Lock the integrated story with focused proof and operator UAT

**Slice:** S03 — Integrated production-structuring walkthrough
**Milestone:** M002

## Description

Turn the assembled story into something future agents can verify and humans can rehearse. This task should add a compact integrated UAT artifact for the exact production-structuring walkthrough and tighten any focused Vitest assertions needed so the Tenants, Playground, and Observability surfaces still match that story without drifting into pseudo-entities or collapsing the proof-order boundaries.

## Steps

1. Write `.gsd/milestones/M002/slices/S03/S03-UAT.md` as a human-run acceptance script that follows the same order as the canonical walkthrough: choose tenant/API-key structure, decide whether `X-Nebula-Tenant-ID` is needed, send the public request, capture `X-Request-ID` and `X-Nebula-*`, correlate the usage ledger, then use Playground and Observability as corroboration only.
2. Review the focused console tests in `console/src/app/(console)/tenants/page.test.tsx`, `console/src/components/tenants/tenant-editor-drawer.test.tsx`, `console/src/components/tenants/tenant-table.test.tsx`, `console/src/components/playground/playground-form.test.tsx`, `console/src/components/playground/playground-page.test.tsx`, and `console/src/app/(console)/observability/page.test.tsx`; tighten assertions only where the integrated story needs more explicit coverage.
3. Keep the verification narrow and text-focused: preserve existing runtime-truth copy patterns, pair positive assertions with negative pseudo-entity checks where relevant, and avoid adding broad snapshots or new UI mechanics.

## Must-Haves

- [ ] `.gsd/milestones/M002/slices/S03/S03-UAT.md` gives a human executor a concrete end-to-end script with the exact proof order and the right boundary reminders.
- [ ] The targeted Vitest files explicitly protect the integrated story across tenant structuring, Playground corroboration, and Observability persisted explanation without implying new runtime objects.

## Verification

- `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx 'src/app/(console)/observability/page.test.tsx'`
- `test -s .gsd/milestones/M002/slices/S03/S03-UAT.md`

## Observability Impact

- Signals added/changed: no new runtime signals; this task hardens the documented interpretation of existing `X-Request-ID`, `X-Nebula-*`, usage-ledger, Playground, and Observability evidence.
- How a future agent inspects this: run the focused Vitest command and read `.gsd/milestones/M002/slices/S03/S03-UAT.md` alongside the touched console tests.
- Failure state exposed: wording drift, missing proof-order coverage, or pseudo-entity regressions show up as targeted test failures or an incomplete UAT script.

## Inputs

- `docs/integrated-adoption-proof.md` — canonical story that the UAT and test assertions must mirror.
- `console/src/app/(console)/tenants/page.test.tsx` — tenant-boundary truth-surface guardrail.
- `console/src/components/tenants/tenant-editor-drawer.test.tsx` — tenant metadata and non-pseudo-entity guidance guardrail.
- `console/src/components/tenants/tenant-table.test.tsx` — negative pseudo-entity drift guardrail.
- `console/src/components/playground/playground-form.test.tsx` — operator-only, tenant-selected, immediate-vs-recorded evidence guardrail.
- `console/src/components/playground/playground-page.test.tsx` — Playground corroboration-only framing guardrail.
- `console/src/app/(console)/observability/page.test.tsx` — persisted-evidence-plus-dependency-health framing guardrail.

## Expected Output

- `.gsd/milestones/M002/slices/S03/S03-UAT.md` — integrated acceptance script for the final production-structuring walkthrough.
- `console/src/app/(console)/tenants/page.test.tsx` — updated or confirmed focused tenant-page assertion coverage.
- `console/src/components/tenants/tenant-editor-drawer.test.tsx` — updated or confirmed focused drawer assertion coverage.
- `console/src/components/tenants/tenant-table.test.tsx` — updated or confirmed negative drift coverage.
- `console/src/components/playground/playground-form.test.tsx` — updated or confirmed focused Playground form coverage.
- `console/src/components/playground/playground-page.test.tsx` — updated or confirmed focused Playground page coverage.
- `console/src/app/(console)/observability/page.test.tsx` — updated or confirmed focused Observability coverage.
