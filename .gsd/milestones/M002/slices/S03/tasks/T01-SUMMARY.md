---
id: T01
parent: S03
milestone: M002
provides:
  - A production-structuring-first integrated adoption walkthrough that preserves the public-proof-to-corroboration order.
key_files:
  - docs/integrated-adoption-proof.md
  - .gsd/milestones/M002/slices/S03/tasks/T01-PLAN.md
  - .gsd/milestones/M002/slices/S03/S03-PLAN.md
key_decisions:
  - Kept integrated-adoption guidance composition-first by linking back to production-model, quickstart, and reference-migration instead of duplicating their contract details.
patterns_established:
  - Start integrated operator walkthroughs from enforced tenant/API-key boundaries, then move through public request, headers, persisted ledger evidence, and admin-only corroboration surfaces in that order.
observability_surfaces:
  - docs/integrated-adoption-proof.md, X-Request-ID, X-Nebula-* headers, usage ledger, Playground request metadata, Observability dependency-health context
duration: 25m
verification_result: passed
completed_at: 2026-03-23T21:13:00-03:00
blocker_discovered: false
---

# T01: Tighten the canonical integrated walkthrough

**Reframed the integrated adoption proof around tenant/API-key production structuring while preserving the public request, header, ledger, Playground, and Observability proof order.**

## What Happened

I first fixed the task plan's missing `## Observability Impact` section so the runtime-truth signals and failure modes were explicit for future agents. Then I compared `docs/integrated-adoption-proof.md` against `docs/production-model.md`, `docs/quickstart.md`, and `docs/reference-migration.md` and found that the integrated walkthrough already preserved the public-proof order, but it still started too implicitly from quickstart rather than from production structuring.

I updated `docs/integrated-adoption-proof.md` to make the runtime boundary explicit before any request is sent: tenants are the enforced governance boundary, API keys carry caller scope, operator sessions are separate from client credentials, and app/workload remain guidance-only labels rather than first-class runtime or admin objects. I also added an explicit pre-request step for when `X-Nebula-Tenant-ID` is actually required so the document now states clearly that the header is conditional for intentionally multi-tenant keys rather than universal boilerplate.

The rest of the document stayed composition-first. It still points readers back to the canonical docs for setup, contract, and migration details, and it preserves the required proof sequence of public request → public headers / `X-Request-ID` → usage ledger → Playground corroboration → Observability corroboration.

## Verification

I ran the task-level verification commands from the plan and confirmed the updated walkthrough is non-empty and contains the required production-structuring, tenant-header, usage-ledger, Playground, and Observability language.

I also ran the slice-level focused Vitest suite for the console corroboration surfaces. That suite passed cleanly, which confirms the existing Tenants, Playground, and Observability UI wording still supports this integrated story.

Finally, I ran the remaining slice-level file-presence and grep checks. Those are only partially passing at T01 because `.gsd/milestones/M002/slices/S03/S03-UAT.md` has not been created yet; that artifact belongs to T02 per the slice plan.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `test -s docs/integrated-adoption-proof.md` | 0 | ✅ pass | 0.001s |
| 2 | `rg -n "production-model\|X-Nebula-Tenant-ID\|usage ledger\|Playground\|Observability\|tenant" docs/integrated-adoption-proof.md` | 0 | ✅ pass | 0.020s |
| 3 | `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx 'src/app/(console)/observability/page.test.tsx'` | 0 | ✅ pass | 1.955s |
| 4 | `test -s docs/integrated-adoption-proof.md && test -s .gsd/milestones/M002/slices/S03/S03-UAT.md` | 1 | ❌ fail | 0.003s |
| 5 | `rg -n "X-Nebula-Tenant-ID\|Playground\|Observability\|usage ledger\|tenant" docs/integrated-adoption-proof.md .gsd/milestones/M002/slices/S03/S03-UAT.md` | 2 | ❌ fail | 0.006s |

## Diagnostics

To inspect this task later, read `docs/integrated-adoption-proof.md` and verify the first proof step is production structuring grounded in `docs/production-model.md`, followed by the public request and then the corroboration surfaces. The runtime-truth anchors named by this task remain `X-Request-ID`, the `X-Nebula-*` response headers, usage-ledger records, Playground request metadata, and Observability dependency-health context.

The expected incomplete signal after T01 is the absence of `.gsd/milestones/M002/slices/S03/S03-UAT.md`; that file is intentionally deferred to T02 and is the reason the two slice-level file/UAT checks still fail.

## Deviations

None.

## Known Issues

- `.gsd/milestones/M002/slices/S03/S03-UAT.md` does not exist yet, so the slice-level artifact-presence and combined grep checks remain incomplete until T02.
- An initial attempt to aggregate timing with `python` failed because `python` is not installed in this environment; I reran the verification with plain shell timing instead.

## Files Created/Modified

- `docs/integrated-adoption-proof.md` — reordered and strengthened the integrated walkthrough so it starts from production structuring and makes the conditional tenant-header rule explicit.
- `.gsd/milestones/M002/slices/S03/tasks/T01-PLAN.md` — added the missing `## Observability Impact` section required by the execution contract.
