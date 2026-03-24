---
id: T02
parent: S03
milestone: M002
provides:
  - An integrated operator UAT script plus focused console assertions that lock the production-structuring proof order and corroboration-only boundaries.
key_files:
  - .gsd/milestones/M002/slices/S03/S03-UAT.md
  - console/src/components/playground/playground-form.test.tsx
  - console/src/components/playground/playground-page.test.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - .gsd/milestones/M002/slices/S03/S03-PLAN.md
key_decisions:
  - Kept T02 narrow by adding a human-run UAT artifact and only tightening text assertions where Playground and Observability needed stronger negative drift coverage.
patterns_established:
  - When the integrated proof is already encoded in UI copy, protect it with positive runtime-truth assertions paired with negative pseudo-entity and boundary-confusion checks instead of adding new UI mechanics.
observability_surfaces:
  - .gsd/milestones/M002/slices/S03/S03-UAT.md, docs/integrated-adoption-proof.md, focused Vitest assertions for Playground and Observability wording, X-Request-ID, X-Nebula-* headers, usage ledger, dependency-health context
duration: 16m
verification_result: passed
completed_at: 2026-03-23T21:15:00-03:00
blocker_discovered: false
---

# T02: Lock the integrated story with focused proof and operator UAT

**Added the integrated S03 UAT script and tightened focused console tests so tenant structuring, Playground corroboration, and Observability persisted-evidence boundaries stay explicit.**

## What Happened

I started by verifying the canonical integrated walkthrough from T01 and rereading the focused console tests and their backing page/component copy so any changes would stay runtime-truthful and text-aligned.

I then created `.gsd/milestones/M002/slices/S03/S03-UAT.md` as a compact human-run acceptance script that mirrors the canonical proof order exactly: production structuring first, the conditional `X-Nebula-Tenant-ID` decision, the real public request, immediate header capture, usage-ledger correlation, then Tenants, Playground, and Observability as corroboration surfaces only. The UAT also carries the slice redaction rule by referring only to header names, request identifiers, and non-secret metadata.

On the test side, the existing tenant-focused assertions already covered the runtime-boundary story well, so I left the tenant page, tenant editor drawer, and tenant table tests unchanged. I only tightened the places where the integrated story benefits from extra negative guardrails: Playground form now guards against public-boundary wording drift, Playground page now rejects pseudo-entity drift and keeps the corroboration framing explicit, and Observability now rejects replacement-style wording and workspace drift while preserving the persisted-evidence-plus-dependency-health explanation.

Finally, I marked T02 complete in the slice plan once the focused suite and slice-level checks passed.

## Verification

I ran the focused Vitest command from the task and slice plans, covering the tenant, Playground, and Observability surfaces named in the contract. All six files and all sixteen tests passed.

I then ran the slice-level artifact and grep checks to verify that both `docs/integrated-adoption-proof.md` and the new `.gsd/milestones/M002/slices/S03/S03-UAT.md` are present and that the required tenant, `X-Nebula-Tenant-ID`, usage-ledger, Playground, and Observability anchors appear in the joined proof surfaces.

For observability impact, I verified the task preserved the documented diagnostic anchors rather than introducing new signals: `X-Request-ID`, `X-Nebula-*` headers, usage-ledger records, Playground request metadata, and Observability dependency-health context remain the inspection points called out by both the docs and the focused tests.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx 'src/app/(console)/observability/page.test.tsx'` | 0 | ✅ pass | 1.798s |
| 2 | `test -s .gsd/milestones/M002/slices/S03/S03-UAT.md` | 0 | ✅ pass | 0.001s |
| 3 | `test -s docs/integrated-adoption-proof.md && test -s .gsd/milestones/M002/slices/S03/S03-UAT.md` | 0 | ✅ pass | 0.001s |
| 4 | `rg -n "X-Nebula-Tenant-ID|Playground|Observability|usage ledger|tenant" docs/integrated-adoption-proof.md .gsd/milestones/M002/slices/S03/S03-UAT.md` | 0 | ✅ pass | 0.001s |

## Diagnostics

To inspect this task later, read `.gsd/milestones/M002/slices/S03/S03-UAT.md` alongside `docs/integrated-adoption-proof.md` and confirm the story order is still production structuring → conditional tenant header → public request → headers / `X-Request-ID` → usage ledger → Playground corroboration → Observability corroboration.

For code-level drift detection, rerun the focused Vitest command and inspect these guardrails:

- `console/src/components/playground/playground-form.test.tsx` for immediate-vs-recorded evidence wording
- `console/src/components/playground/playground-page.test.tsx` for operator-only corroboration framing and pseudo-entity rejection
- `console/src/app/(console)/observability/page.test.tsx` for persisted-evidence-plus-dependency-health framing and replacement-boundary rejection

The slice's diagnostic anchors remain `X-Request-ID`, the `X-Nebula-*` headers, usage-ledger records, Playground metadata, and Observability dependency-health context.

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `.gsd/milestones/M002/slices/S03/S03-UAT.md` — added the integrated human-run acceptance script for the final production-structuring walkthrough.
- `console/src/components/playground/playground-form.test.tsx` — added a negative assertion to keep the form from drifting into public-boundary framing.
- `console/src/components/playground/playground-page.test.tsx` — tightened corroboration-only and pseudo-entity drift coverage.
- `console/src/app/(console)/observability/page.test.tsx` — tightened replacement-boundary and pseudo-entity drift coverage for the persisted evidence surface.
- `.gsd/milestones/M002/slices/S03/S03-PLAN.md` — marked T02 done.
