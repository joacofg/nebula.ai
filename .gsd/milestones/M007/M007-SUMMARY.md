---
id: M007
title: "Operator Decision Clarity — Context"
status: complete
completed_at: 2026-04-03T03:02:28.825Z
key_decisions:
  - D040: Observability is request investigation first, request detail remains the authoritative persisted evidence record, and policy preview is a save/don’t-save decision-review surface.
  - D041: Lock the operator-surface evidence hierarchy with selected-request-first Observability, authoritative request detail, and preview-before-save policy tests rather than copy-only checks.
  - D042: Keep policy options and preview bounded to runtime-enforced cache controls plus comparison-first replay evidence, and keep Observability supporting cards explicitly subordinate to the selected request.
  - D043: Close M007 with a pointer-only integrated proof and focused cross-surface Vitest verification rather than widening the product into a new dashboard or workflow surface.
key_files:
  - docs/m007-integrated-proof.md
  - README.md
  - docs/architecture.md
  - console/src/app/(console)/observability/page.tsx
  - console/src/components/ledger/ledger-table.tsx
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/policy/policy-form.tsx
  - console/src/app/(console)/policy/page.tsx
  - src/nebula/api/routes/admin.py
  - src/nebula/services/policy_simulation_service.py
lessons_learned:
  - For page-identity work, DOM-order and scoped negative assertions are stronger guardrails than copy-only checks.
  - When the intended operator contract already exists in console types, fix drift at the backend admin seam first instead of widening frontend payloads.
  - Request-selection clarity should be strengthened inside bounded selector seams like LedgerTable rather than by adding new explainer surfaces.
  - Policy preview remains cleaner when baseline-versus-draft summaries are derived from the existing simulation result at render time and stale preview state is reset at the page entrypoint.
---

# M007: Operator Decision Clarity — Context

**M007 turned Observability, request detail, and policy preview into one coherent operator decision system with explicit page roles, bounded supporting context, and a verified integrated proof path.**

## What Happened

M007 clarified Nebula’s operator surfaces without widening product scope. S01 established the page-role contract: Observability is request-investigation-first, request detail is the authoritative persisted evidence seam, and policy preview is a replay-before-save decision surface. S02 tightened the supporting admin and console seams so cache controls and simulation evidence stayed bounded to runtime-aligned comparison data rather than drifting into dashboard aggregates. S03 then recomposed Observability around one selected request as the lead investigation object, with recommendations, calibration, cache posture, and dependency health explicitly framed as subordinate follow-up context; request selection was strengthened inside LedgerTable through bounded selector semantics instead of new explainer surfaces. S04 reworked policy preview into a compare-before-save flow that leads with baseline-versus-draft consequences, keeps replay evidence secondary, and clears stale preview state on tenant switch and save success. S05 assembled the final operator proof as a pointer-only walkthrough in docs/m007-integrated-proof.md, added discoverability links in README.md and docs/architecture.md, and reran the focused six-file console Vitest bundle unchanged. In the assembled worktree, the milestone now reads as one coherent decision system: a selected persisted request leads the investigation, request detail remains authoritative, supporting context stays visibly secondary, policy preview presents a clear save/don’t-save decision, and the review path is explicit without turning Nebula into a dashboard, routing studio, or parallel workflow product.

## Success Criteria Results

- **Observability and policy surfaces read as one coherent decision system rather than a loose collection of proof cards:** Met. S01 defined the explicit role contract, S03 reworked Observability around a selected-request-first investigation flow, S04 reworked policy preview into a compare-before-save decision flow, and S05 assembled those seams in `docs/m007-integrated-proof.md` with discoverability links from `README.md` and `docs/architecture.md`.
- **Observability clearly leads with one selected request investigation and keeps supporting context secondary:** Met. S01 and S03 summary evidence shows selected-request-first composition, bounded `LedgerTable` affordances (`aria-selected`, pressed state, `Current investigation`), and subordinate recommendations/calibration/cache/dependency framing. Reverified in the assembled worktree by `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-table.test.tsx`, included in the final six-file bundle (39/39 tests).
- **Request detail remains the authoritative persisted evidence record for the selected request:** Met. S01 tightened `console/src/components/ledger/ledger-request-detail.tsx` copy and tests to keep the persisted ledger row authoritative, S03 intentionally left that seam authoritative while page composition changed around it, and the assembled six-file bundle revalidated `src/components/ledger/ledger-request-detail.test.tsx` (15 assertions inside the final 39/39 pass).
- **Policy preview supports a clear baseline-versus-draft save / don’t-save decision instead of blending editor and analytics roles:** Met. S02 bounded simulation/options contracts, S04 reworked `console/src/components/policy/policy-form.tsx` and `console/src/app/(console)/policy/page.tsx` into a compare-before-save flow with bounded replay evidence and stale-preview reset behavior, and the assembled worktree revalidated `src/components/policy/policy-form.test.tsx` plus `src/components/policy/policy-page.test.tsx` in the final six-file bundle (39/39 tests).
- **The milestone stays within existing operator-surface scope and avoids dashboard / analytics-product / redesign sprawl:** Met. S01-S05 summaries consistently record scoped negative assertions against dashboard, routing-studio, analytics-product, redesign-sprawl, and parallel-workflow drift. The integrated proof is pointer-only rather than a new product surface, and the final six-file Vitest bundle passed unchanged with those anti-drift guards intact.
- **One integrated proof path makes the assembled operator story reviewable without re-reading slice history:** Met. S05 added `docs/m007-integrated-proof.md` and discoverability links from `README.md` and `docs/architecture.md`; file existence was rechecked in the assembled worktree and the focused cross-surface six-file console bundle passed unchanged (6 files, 39/39 tests).

## Definition of Done Results

- **All roadmap slices are complete:** Met. `M007-ROADMAP.md` shows S01-S05 all marked ✅.
- **All slice summaries exist:** Met. `find .gsd/milestones/M007/slices -maxdepth 2 -name 'S*-SUMMARY.md'` returned S01-SUMMARY.md through S05-SUMMARY.md.
- **Task drill-down artifacts exist across slices:** Met. The milestone directory contains 10 task summaries across S01-S05 (`find ... -path '*/tasks/*-SUMMARY.md' | wc -l` → 10).
- **Cross-slice integration points work in the assembled worktree:** Met. The focused assembled console verification passed unchanged: `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/ledger/ledger-table.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` → 6/6 files, 39/39 tests.
- **Non-.gsd code/doc changes exist for the milestone:** Met with caveat. `git diff --stat HEAD $(git merge-base HEAD main) -- ':!.gsd/'` was empty because this branch appears already merged relative to `main`, so the diff check alone was inconclusive rather than evidencing no shipped work. Current assembled non-`.gsd` milestone files remain present and verified (`docs/m007-integrated-proof.md`, `README.md`, `docs/architecture.md`, `console/src/app/(console)/observability/page.tsx`, `console/src/components/ledger/ledger-table.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/policy/policy-form.tsx`, `console/src/app/(console)/policy/page.tsx`), and the integrated six-file bundle passed against that assembled snapshot, satisfying the close-out base-check guardrail recorded in project knowledge.

## Requirement Outcomes

- **R050 — Active → validated.** Evidence: S03 established selected-request-first Observability composition and bounded selection semantics; S05 assembled and reverified the shipped proof path. Final assembled verification passed in `src/app/'(console)'/observability/page.test.tsx`, `src/app/'(console)'/observability/observability-page.test.tsx`, and `src/components/ledger/ledger-table.test.tsx` as part of the six-file 39/39 Vitest bundle, and `docs/m007-integrated-proof.md` now captures the review order.
- **R051 — Active → validated.** Evidence: S01 tightened request-detail authority framing, S03 preserved it while reworking page composition, and the assembled worktree revalidated `src/components/ledger/ledger-request-detail.test.tsx` in the six-file 39/39 Vitest bundle; the integrated proof explicitly keeps request detail as the authoritative persisted evidence seam.
- **R052 — Active → validated.** Evidence: S02 bounded simulation/options seams, S04 reworked policy preview into the compare-before-save decision flow, and the assembled worktree revalidated `src/components/policy/policy-form.test.tsx` plus `src/components/policy/policy-page.test.tsx` in the six-file 39/39 Vitest bundle. `docs/m007-integrated-proof.md` preserves the decision-first review order.
- **R053 — Active → validated.** Evidence: S02 made recommendation, calibration, cache, and dependency cards explicitly subordinate to the selected request; S03 preserved that hierarchy in page composition; and the final six-file Vitest bundle revalidated scoped supporting-context assertions across Observability, request detail, and policy preview.
- **R054 — Active → validated.** Evidence: S03 made the selected request the obvious investigation object and pointed toward policy preview as the next step; S04 made policy preview read as baseline-versus-draft decision review with explicit next-step cues; S05 assembled that operator flow in `docs/m007-integrated-proof.md` and revalidated it in the six-file focused bundle.
- **R055 — Active → validated.** Evidence: The milestone stayed pointer-only and bounded: no new dashboard, routing studio, analytics product, redesign-sprawl effort, or parallel operator workflow was introduced. This was locked by negative assertions across S01-S05 and confirmed in final close-out by `docs/m007-integrated-proof.md`, discoverability links in `README.md` / `docs/architecture.md`, and the unchanged six-file 39/39 console Vitest pass.

No active requirement was invalidated or re-scoped during close-out. Deferred requirements R056 and R057 remain deferred because M007 intentionally clarified existing page roles rather than adding richer workflow or broader posture/trend surfaces.

## Deviations

The mandatory diff-against-main check was inconclusive because this milestone branch appears already merged relative to `main`, so `git diff --stat HEAD $(git merge-base HEAD main) -- ':!.gsd/'` returned empty. Per the existing close-out base-check guidance, I treated that as a base-selection caveat rather than proof of no shipped code and relied on the assembled non-`.gsd` file set plus passing focused verification to confirm milestone delivery.

## Follow-ups

None required for milestone close-out. If future work revisits operator workflows, treat richer handoff/playbook features (R056) and broader posture/trend views (R057) as new scope rather than extensions of M007’s page-identity work.
