# Slice Summary — M004 / S02: Fleet posture UX

## Outcome
S02 delivered a real hosted fleet-posture reading layer on the deployments console without expanding hosted authority. The deployments page now gives operators an at-a-glance summary of linked/current deployments, pending enrollment, stale/offline visibility, and bounded-action-blocked deployments before they open the detail drawer. The inventory table also became a scan surface instead of an inventory-only list: each row now exposes helper-derived posture meaning and bounded-action availability so operators can distinguish pending, linked, stale, offline, revoked, unlinked, and unsupported cases during scan time.

This slice stayed inside the metadata-only trust boundary established in S01. It did not add new backend status enums, new hosted authority, or new serving-time claims. Instead, it synthesized existing `DeploymentRecord` facts into clearer operator-facing posture cues and reused the shared hosted-contract wording to keep the hosted plane descriptive and non-authoritative.

## What shipped
- Added `console/src/components/deployments/fleet-posture.ts` as the shared pure derivation seam for:
  - fleet-level posture counts
  - per-deployment posture interpretation
  - bounded-action availability / blocked / unavailable semantics
- Added `console/src/components/deployments/fleet-posture-summary.tsx` and wired it into `console/src/app/(console)/deployments/page.tsx` above the deployments table.
- Updated `console/src/components/deployments/deployment-table.tsx` to add a compact posture column that combines:
  - existing enrollment-state badge reuse
  - freshness badge reuse for active deployments
  - helper-derived posture labels/details
  - bounded-action scan text (`Rotation available`, `Rotation blocked`, `Rotation unavailable`)
- Updated `console/src/components/deployments/remote-action-card.tsx` to consume the shared bounded-action helper instead of maintaining its own local blocked-state branching.
- Added and expanded focused Vitest coverage for the derivation seam, page summary, table scan-time state rendering, remote-action alignment, and hosted-contract wording.

## Slice-level verification
Passed all slice-plan checks:

1. `npm --prefix console run test -- --run src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx src/lib/hosted-contract.test.ts`
   - Result: 5 files passed, 26 tests passed.
2. `rg -n "metadata-backed and descriptive only|fleet posture|local runtime|pending enrollment|stale|offline|unlinked|revoked|bounded" console/src`
   - Result: required trust-boundary and posture vocabulary present in the expected hosted-console seams.

## Observability / diagnostic confirmation
The slice plan called out derivation and wording seams as inspection surfaces. Those are now in place and separable:
- `console/src/components/deployments/fleet-posture.ts` isolates posture classification and bounded-action derivation.
- `console/src/components/deployments/fleet-posture-summary.tsx` isolates top-of-page summary composition.
- `console/src/components/deployments/deployment-table.tsx` isolates scan-time row rendering.
- `console/src/components/deployments/remote-action-card.tsx` now reuses the same bounded-action semantics rather than duplicating them.

That means later regressions can be localized quickly:
- helper tests fail → derivation drift
- summary/table tests fail with helper tests green → rendering/composition drift
- hosted-contract tests fail → trust-boundary wording drift

## Requirement impact
Validated in this slice:
- **R032** — hosted at-a-glance fleet posture view
- **R033** — legible pending/linked/stale/offline/revoked/unlinked/bounded-action states
- **R035** — clear bounded hosted action availability/blocked/irrelevant semantics with explicit reasons
- **R036** — multi-deployment understanding from one deployments entry surface

Still active after this slice:
- **R034** remains active because S02 preserved and exercised the trust-boundary guardrails, but S03 still needs to prove the integrated milestone story.
- **R037** and **R038** remain for S03/S04 integrated confidence proof and refinement work.

## Patterns established
1. **Derive posture in pure helpers first, then render it in UI.**
   The new `fleet-posture.ts` seam is the canonical source for fleet counts, row interpretation, and bounded-action availability. Summary cards, the scan table, and the remote-action detail surface should keep consuming that seam rather than adding local condition trees.

2. **Reuse hosted-contract wording instead of inventing page-local trust language.**
   The deployments page summary uses `console/src/lib/hosted-contract.ts` for descriptive claims, operator reading guidance, and bounded-action framing. Future hosted UX work should keep doing that.

3. **Keep scan surfaces compact and descriptive, not dashboard-heavy.**
   The table upgrade intentionally added one posture column instead of multiple telemetry columns. That keeps the hosted console readable for evaluators while still surfacing the important interpretation cues.

4. **Separate derivation tests from rendering tests.**
   The helper seam, summary, table, and remote-action card each have focused coverage, which makes later debugging cheaper and less ambiguous.

## Key decisions captured
- Added a new shared derivation seam for posture and bounded-action semantics so all hosted fleet surfaces stay aligned and fail closed.
- Kept the inventory table compact by composing status/freshness badges with one posture column rather than expanding into a noisy operations dashboard.
- Preserved the existing drawer workflow; the new summary/table help operators decide what to inspect next rather than replacing detail surfaces.

## Gotchas / lessons for next slices
- Do not fork blocked-action reasoning again. `getBoundedActionAvailability()` is now the canonical helper and should remain the only place that decides available vs blocked vs unavailable.
- Duplicate canonical wording can be correct when both the page and an embedded card intentionally reuse hosted-contract copy. Tests should verify reuse/presence, not uniqueness.
- Some scan-time labels can appear both as badges and as posture headings. Test assertions should tolerate semantically correct duplicate text instead of forcing awkward copy divergence.

## What S03 should know
S03 can now build the integrated confidence walkthrough on top of a real hosted fleet entry surface rather than isolated deployment details. The hosted console has the necessary seams to demonstrate:
- page-level fleet summary
- row-level interpretation for mixed deployment states
- bounded-action availability framed as bounded operational assistance
- explicit local-runtime caveats sourced from the shared hosted contract

The next slice should focus on proving that these surfaces create a clearer multi-deployment confidence story in context, not on adding new hosted mechanics or richer hosted authority.
