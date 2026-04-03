---
id: S02
parent: M007
milestone: M007
provides:
  - A bounded backend contract for cache-control policy options and policy simulation comparison evidence that later policy-preview work can trust.
  - Request-first supporting-card wording and scoped console-test patterns that later Observability work can reuse without re-opening page identity.
  - A stronger anti-drift test seam for M007 page-role work across admin contracts, policy preview, and Observability.
requires:
  - slice: S01
    provides: The operator-surface role contract that made Observability request-first, kept ledger request detail authoritative, and defined policy preview as replay-before-save rather than a blended analytics/editor surface.
affects:
  - S03
  - S04
  - S05
key_files:
  - src/nebula/api/routes/admin.py
  - src/nebula/models/governance.py
  - src/nebula/services/policy_simulation_service.py
  - tests/test_governance_api.py
  - tests/test_service_flows.py
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-form.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - .gsd/PROJECT.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Kept policy options and policy preview bounded to runtime-enforced cache controls plus comparison-first replay evidence, rather than widening them into dashboard-style aggregates or analytics payloads.
  - Kept Observability request-first by making recommendation, calibration, cache, and dependency sections explicit supporting context for the selected ledger row, not parallel authorities.
  - Resolved contract drift at the backend admin boundary first because the console’s shared types already matched the intended bounded preview contract.
patterns_established:
  - Fix operator-surface contract drift at the narrowest authoritative seam first: backend admin contracts for runtime truth, then local console copy/tests for page-role framing.
  - For page-identity work, use DOM-order and scoped `within(...)` assertions to lock hierarchy and tolerate duplicate labels across bounded supporting cards.
  - Treat policy simulation as bounded comparison evidence—route/status/policy/cost deltas plus capped changed-request samples—not as an analytics surface.
observability_surfaces:
  - Focused backend/admin verification via `tests/test_governance_api.py -k "policy_options or simulation"` and `tests/test_service_flows.py -k "simulation"` for bounded policy-options and replay contracts.
  - Focused console diagnostics through `src/app/(console)/observability/page.test.tsx`, `src/app/(console)/observability/observability-page.test.tsx`, and `src/components/ledger/ledger-request-detail.test.tsx`, which lock request-first hierarchy and scoped supporting-context wording.
  - Focused console diagnostics through `src/components/policy/policy-form.test.tsx` and `src/components/policy/policy-page.test.tsx`, which lock baseline-vs-draft preview framing and negative checks against dashboard/routing-studio/analytics drift.
drill_down_paths:
  - .gsd/milestones/M007/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M007/slices/S02/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-03T02:21:31.245Z
blocker_discovered: false
---

# S02: Tighten supporting evidence and preview contracts

**Aligned bounded admin policy/simulation contracts with live cache controls and tightened policy-preview and Observability supporting seams so later M007 flows can stay comparison-first and request-first without dashboard drift.**

## What Happened

S02 tightened the contracts underneath the page-role decisions established in S01 instead of introducing new surfaces. On the backend, the slice aligned `/v1/admin/policy/options` with the real runtime-enforced semantic-cache tuning controls already edited in the console, then tightened policy simulation models and focused backend tests so preview evidence stays bounded to baseline-versus-simulated route, status, policy-outcome, and cost deltas plus capped changed-request samples. That work corrected contract drift at the admin boundary rather than widening shared console types, and it refreshed stale simulation expectations to current inclusive replay-window and policy-outcome behavior. On the console, the slice consumed those seams by rewriting policy-preview framing around baseline-versus-draft decision evidence over recent persisted requests with explicit save separation, while Observability supporting cards for recommendations, calibration, cache, and dependencies were made visibly subordinate to the selected request investigation and the authoritative LedgerRequestDetail record. Focused Vitest coverage now locks DOM order, scoped duplicate-label handling, comparison-first wording, and negative guards against dashboard, routing-studio, or analytics-product drift. Together, these changes give S03 and S04 a cleaner foundation: the request remains the lead investigation object, preview remains a bounded replay-before-save comparison seam, and supporting context is explicit follow-up evidence rather than a competing page identity.

## Verification

Re-ran every slice-plan verification command in the assembled worktree and all passed: `./.venv/bin/pytest tests/test_governance_api.py -k "policy_options or simulation" -x` (9 passed), `./.venv/bin/pytest tests/test_service_flows.py -k "simulation" -x` (7 passed), and `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` (32 passed). This confirms the bounded admin contract, policy-preview comparison wording, request-first Observability framing, and scoped duplicate-label test seams still hold in the assembled slice. One upstream FastAPI deprecation warning about `HTTP_422_UNPROCESSABLE_ENTITY` appeared in governance tests, but no slice regressions were detected.

## Requirements Advanced

- R052 — S02 strengthened the policy-preview save/don’t-save workflow by aligning backend simulation/options contracts to bounded comparison evidence and by tightening preview copy/test coverage around baseline-versus-draft decision framing.
- R053 — S02 made supporting recommendation, calibration, cache, and dependency context explicitly subordinate to the selected request investigation and locked that hierarchy with scoped Vitest assertions.
- R054 — S02 clarified next-action cues on both operator surfaces: policy preview now reads as replay evidence for a save decision, and Observability supporting cards now read as follow-up context for the selected request investigation.
- R055 — S02 preserved M007 scope discipline by tightening existing backend/UI seams and adding negative test coverage against dashboard, routing-studio, and analytics-product drift rather than introducing new surfaces or aggregates.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

T01 did not modify `console/src/lib/admin-api.ts` because the shared frontend types already matched the intended bounded contract; the real drift was at the backend admin response and focused backend-test boundary. T01 also updated stale simulation assertions to match current inclusive replay-window semantics and richer policy-outcome strings. Otherwise the slice stayed within plan.

## Known Limitations

This slice tightens support seams but does not yet complete the larger page-flow rewrites. Observability is not yet fully reworked around a single selected-request investigation journey across the whole page, and policy preview is not yet the full comparison-and-decision flow planned for S04. A pre-existing duplicate test definition warning remains in `tests/test_governance_api.py` (`F811` for an embeddings test) outside this slice’s scope.

## Follow-ups

S03 should build directly on the new request-first supporting-card wording and scoped duplicate-label test pattern when restructuring Observability around one primary investigation flow. S04 should reuse the aligned backend simulation/options contract and the explicit baseline-versus-draft wording when turning policy preview into a save-or-don’t-save comparison flow, without adding analytics-style aggregates or a parallel preview surface.

## Files Created/Modified

- `src/nebula/api/routes/admin.py` — Aligned admin policy-options output with runtime-enforced cache tuning controls.
- `src/nebula/models/governance.py` — Tightened bounded policy-simulation response models and validation semantics.
- `src/nebula/services/policy_simulation_service.py` — Kept simulation output comparison-first within bounded route/status/policy/cost evidence seams.
- `tests/test_governance_api.py` — Added and updated focused admin-boundary coverage for policy options and simulation contracts.
- `tests/test_service_flows.py` — Tightened service-layer simulation coverage around bounded replay semantics.
- `console/src/components/policy/policy-form.tsx` — Reframed policy preview copy around baseline-versus-draft decision evidence and explicit save separation.
- `console/src/components/policy/policy-form.test.tsx` — Locked comparison-first preview wording and negative anti-drift assertions.
- `console/src/components/policy/policy-page.test.tsx` — Locked policy-page preview semantics and bounded comparison framing.
- `console/src/app/(console)/observability/page.tsx` — Tightened supporting-context wording so Observability cards point back to selected-request investigation.
- `console/src/app/(console)/observability/page.test.tsx` — Verified request-first Observability framing in the page wrapper.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Added scoped assertions for subordinate supporting-card wording and hierarchy.
- `console/src/components/ledger/ledger-request-detail.tsx` — Preserved request-detail authority while supporting the refined request-first page framing.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Verified authoritative persisted-evidence wording remains intact under the refined framing.
- `.gsd/PROJECT.md` — Updated current project state to reflect M007 S02 completion and the tightened operator-support seams.
- `.gsd/KNOWLEDGE.md` — Recorded durable guidance about backend-first seam fixes, bounded simulation contracts, and scoped request-first console assertions.
