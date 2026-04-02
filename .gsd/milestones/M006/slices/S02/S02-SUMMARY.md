---
id: S02
parent: M006
milestone: M006
provides:
  - A shared CalibrationEvidenceSummary contract for tenant-scoped sufficient/thin/stale/gated/degraded evidence derived from existing usage-ledger metadata.
  - Deterministic governance-store aggregation rules that exclude override/policy-forced rows from sufficiency while preserving gated and degraded counts/reasons.
  - Policy simulation responses that reuse the same calibration evidence vocabulary as runtime/admin data.
  - Existing Observability and ledger request-detail surfaces that explain calibration posture without replacing the persisted request-proof story.
requires:
  - slice: S01
    provides: Shared calibrated routing score/mode vocabulary, additive score metadata, and the tenant-scoped calibrated_routing_enabled rollout valve that this slice’s evidence summary builds on.
affects:
  - S03
  - S04
  - S05
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/governance_store.py
  - src/nebula/services/policy_simulation_service.py
  - src/nebula/services/recommendation_service.py
  - console/src/lib/admin-api.ts
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - tests/test_service_flows.py
  - tests/test_governance_api.py
  - .gsd/KNOWLEDGE.md
  - .gsd/PROJECT.md
key_decisions:
  - Derived tenant-scoped calibration evidence strictly from existing usage-ledger metadata instead of widening persistence or adding replay-only summary tables.
  - Excluded explicit overrides and policy-forced routing from calibration sufficiency math while still reporting calibrated_routing_disabled rows as operator-controlled gating.
  - Based calibration staleness on the newest eligible evidence row so fresh degraded rows do not incorrectly flip the tenant summary to stale.
  - Reused GovernanceStore.summarize_calibration_evidence() directly in policy simulation so runtime/admin and replay share one calibration vocabulary.
  - Extended RecommendationBundle with calibration_summary so Observability could reuse the same bounded contract as replay without creating a new admin surface.
  - Hardened Observability tests by scoping duplicate-label assertions to the intended calibration card rather than assuming page-wide uniqueness.
patterns_established:
  - Use one typed tenant-scoped summary contract for new operator/replay evidence instead of inventing separate simulation- or UI-only classifications.
  - Keep calibration evidence bounded to existing usage-ledger metadata and explicit reason/count fields; do not widen persistence or drift into analytics-style aggregates.
  - Treat explicit overrides and policy-forced routing as excluded from sufficiency while showing rollout-disabled traffic separately as operator-controlled gating.
  - When a bounded summary appears in multiple UI panels, keep the product copy shared but scope focused tests to the intended container with within(...).
observability_surfaces:
  - Tenant-scoped CalibrationEvidenceSummary derived from existing usage-ledger metadata in governance/admin services.
  - Policy simulation responses now include the shared calibration_summary for replay-window inspection.
  - Ledger request detail renders compact calibration-evidence context beside the selected persisted ledger row.
  - Observability renders tenant-scoped replay-readiness context beside bounded recommendations and cache/runtime context.
  - Focused backend and console tests lock sufficient/thin/stale/rollout-disabled messaging and duplicate-label assertion discipline.
drill_down_paths:
  - .gsd/milestones/M006/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M006/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M006/slices/S02/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-02T03:39:43.378Z
blocker_discovered: false
---

# S02: Ledger-backed calibration evidence

**Delivered one bounded tenant-scoped calibration evidence contract derived from existing ledger metadata and reused it across replay and operator inspection surfaces.**

## What Happened

S02 completed the missing tenant-scoped evidence layer for M006’s calibrated routing story. The backend now derives a bounded CalibrationEvidenceSummary directly from existing usage-ledger metadata for a tenant and classifies evidence as sufficient, thin, stale, rollout-disabled/gated, and degraded without adding new persistence or analytics-style aggregates. That shared contract was then reused in the policy simulation path so replay uses the same classification vocabulary and deterministic tenant-window semantics as the runtime/admin layer. Finally, the console surfaces adopted the same summary in two bounded places: request detail shows compact calibration context next to the selected ledger row, and Observability renders tenant-scoped replay-readiness context beside recommendations and cache/runtime context while explicitly preserving the persisted request-evidence story as primary. Slice close-out also hardened focused Observability tests after the shared labels appeared intentionally in more than one bounded panel.

## Verification

Passed all slice-plan verification commands in the assembled worktree: `./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x`, `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x`, and `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx`. The console verification initially failed only because the close-out test still assumed labels like `Eligible calibrated rows` and `Rollout-disabled rows` were unique across the whole page after the same bounded summary was rendered in more than one panel; scoping those assertions to the intended card fixed the false negative without changing shipped behavior.

## Requirements Advanced

- R039 — S02 adds the tenant-scoped ledger-backed calibration summary, shared replay vocabulary, and bounded operator rendering that M006 needs before final parity proof and integrated close-out can validate outcome-aware routing.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

T03 had to extend RecommendationBundle and RecommendationService with calibration_summary so Observability could reuse the shared bounded calibration contract without adding a new admin surface. During slice close-out, the focused Observability Vitest assertions also needed scoping with within(...) because the same calibration labels now appear intentionally in both the tenant summary card and the request-detail panel. No shipped product behavior changed during close-out beyond that test hardening.

## Known Limitations

R039 remains active. The slice establishes the bounded ledger-backed calibration evidence vocabulary and reuses it across replay and operator surfaces, but it does not yet prove full runtime/simulation parity across all scenarios or provide the final integrated milestone walkthrough. `tests/test_governance_api.py` still carries a pre-existing duplicate test definition warning unrelated to this slice.

## Follow-ups

S03 should prove runtime and replay parity against the same tenant traffic classes now that both paths share CalibrationEvidenceSummary vocabulary. S04 should keep operator rendering bounded by reusing these existing summary fields instead of introducing route-inspection or analytics-specific APIs. S05 will need one integrated proof path showing public/request evidence, calibration summary state, replay parity, and degraded/gated explanations together.

## Files Created/Modified

- `src/nebula/models/governance.py` — Added bounded calibration evidence summary models and shared governance typing for tenant-scoped ledger-backed evidence.
- `src/nebula/services/governance_store.py` — Implemented tenant-scoped calibration summary derivation from usage-ledger metadata with sufficient/thin/stale/gated/degraded classification.
- `src/nebula/services/policy_simulation_service.py` — Reused the shared calibration evidence summary in policy simulation responses for replay-window parity.
- `src/nebula/services/recommendation_service.py` — Extended recommendation responses to carry calibration_summary so Observability could reuse the same bounded evidence contract.
- `console/src/lib/admin-api.ts` — Mirrored the shared calibration evidence contract in console admin API types.
- `console/src/components/ledger/ledger-request-detail.tsx` — Rendered request-adjacent calibration evidence messaging while keeping the persisted ledger row as the primary proof surface.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Added focused request-detail coverage for sufficient, thin, stale, rollout-disabled, and absent-summary calibration messaging.
- `console/src/app/(console)/observability/page.tsx` — Rendered tenant-scoped calibration evidence beside recommendations and cache/runtime context without turning Observability into an analytics destination.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Added focused Observability coverage for calibration-state messaging and hardened duplicate-label assertions by scoping to the intended card.
- `tests/test_service_flows.py` — Added focused backend tests for calibration summary classification and simulation reuse of the shared contract.
- `tests/test_governance_api.py` — Added focused admin API coverage proving simulation surfaces the shared calibrated evidence semantics.
- `.gsd/KNOWLEDGE.md` — Recorded an S02 testing lesson about scoping duplicate-label Observability assertions.
- `.gsd/PROJECT.md` — Refreshed current project state to reflect M006/S02 completion.
