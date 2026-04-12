---
id: S05
parent: M008
milestone: M008
provides:
  - A canonical end-to-end governance proof path future reviewers and milestone validators can follow without reopening M008 scope.
  - A locked ordering contract that keeps selected request evidence ahead of supporting runtime health context.
  - Validated requirement evidence for R062, R063, and R064.
requires:
  - slice: S01
    provides: Typed evidence-governance policy fields and request-time governance markers.
  - slice: S02
    provides: Persisted-row governance truth and deletion by `evidence_expires_at` through the usage-ledger seam.
  - slice: S03
    provides: Retention lifecycle execution plus health/dependency observability support.
  - slice: S04
    provides: Shared retained/suppressed/deleted/not-hosted vocabulary and hosted metadata-only trust-boundary surfaces.
affects:
  - Future milestone validation and roadmap reassessment work that depends on one canonical M008 governance proof path.
key_files:
  - docs/m008-integrated-proof.md
  - README.md
  - docs/architecture.md
  - tests/test_health.py
  - console/src/app/(console)/observability/page.test.tsx
  - .gsd/DECISIONS.md
  - .gsd/KNOWLEDGE.md
  - .gsd/PROJECT.md
key_decisions:
  - Kept the M008 close-out proof pointer-only and delegated detailed contracts back to policy/options, ledger, retention lifecycle, and hosted trust-boundary canonicals instead of duplicating them.
  - Preserved request-led evidence as primary by tightening only ordering assertions where integrated-governance sequencing had been implicit.
  - Kept retention lifecycle health explicitly subordinate to governance-store and selected-request evidence to avoid compliance-dashboard or authority drift.
patterns_established:
  - Use pointer-only integrated proof docs to assemble milestone close-out stories while keeping detailed contracts in their original backend/UI seams.
  - For governance-story close-out, add narrow ordering assertions in health and observability tests instead of widening product scope or adding new dashboards.
  - Treat runtime health as supporting context and keep request-level persisted evidence primary while it exists.
observability_surfaces:
  - `/health/ready`
  - `/health/dependencies`
  - `console/src/components/ledger/ledger-request-detail.tsx`
  - `console/src/app/(console)/observability/page.tsx`
  - `console/src/lib/hosted-contract.ts`
  - `console/src/app/trust-boundary/page.tsx`
drill_down_paths:
  - .gsd/milestones/M008/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M008/slices/S05/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-12T17:31:48.790Z
blocker_discovered: false
---

# S05: S05

**Closed M008 with a canonical integrated governance proof that assembles tenant policy, persisted request evidence, deletion by persisted expiration, supporting retention health, and the hosted metadata-only boundary into one executable end-to-end story.**

## What Happened

S05 finished the M008 milestone by turning the already-shipped S01–S04 seams into one bounded, reviewable proof path instead of adding more governance surface area. The slice authored `docs/m008-integrated-proof.md` as a pointer-only integrated walkthrough that follows the established close-out pattern from prior milestones and keeps each seam in its canonical role: policy/options and the policy form establish the tenant-governed evidence boundary first; the usage-ledger row plus request detail remain the primary historical proof while a row still exists; governed deletion is anchored to the row’s persisted `evidence_expires_at` marker rather than current-policy inference; `retention_lifecycle` health and Observability remain supporting runtime context rather than replacement evidence; and hosted trust-boundary surfaces remain metadata-only and explicitly non-authoritative. Discoverability links in `README.md` and `docs/architecture.md` make the proof easy to find without duplicating backend or UI contracts elsewhere. The slice also tightened the executable proof with two narrow regression assertions: backend health ordering now verifies `governance_store` precedes `retention_lifecycle`, and the console observability test now locks selected request evidence ahead of supporting runtime-health context. Together these changes make the assembled governance story mechanically reviewable and catch drift in deletion semantics, request-detail authority, runtime-health role, or hosted-boundary wording without widening Nebula into a compliance dashboard, archive/recovery system, or hosted authority layer.

## Verification

All slice-level verification passed in the assembled worktree. Backend verification: `./.venv/bin/pytest tests/test_governance_api.py tests/test_retention_lifecycle_service.py tests/test_health.py tests/test_hosted_contract.py -k "usage_ledger or retention or lifecycle or health or heartbeat"` → 13 passed, 32 deselected. Console verification: `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx 'src/app/(console)/observability/page.test.tsx' src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx` → 5 files passed, 39 tests passed. Additional task-level verification already recorded by executors confirmed `docs/m008-integrated-proof.md` exists, contains the required headings and vocabulary, has no TODO/TBD placeholders, and is linked from `README.md` and `docs/architecture.md`. Observability/diagnostic surfaces were explicitly confirmed: request detail remains the authoritative selected-row evidence while a row exists, `/health/ready` and `/health/dependencies` continue exposing `retention_lifecycle` as supporting runtime context, and hosted trust-boundary wording stays aligned to the shared metadata-only contract.

## Requirements Advanced

- R062 — assembled the full governance chain from tenant policy to persistence/deletion to operator evidence to hosted metadata-only boundary into one executable proof path.
- R063 — preserved Nebula’s request-led debugging model by making the persisted request row authoritative while it exists and treating health/hosted as supporting context only.
- R064 — proved the milestone stayed bounded and did not expand into payload capture, retention-dashboard sprawl, soft-delete recovery, or hosted authority.

## Requirements Validated

- R062 — validated by `docs/m008-integrated-proof.md`, README/architecture discoverability links, and passing focused backend/console verification for ledger, retention lifecycle, health, and hosted seams.
- R063 — validated by passing request-detail, observability, and hosted trust-boundary tests that keep request-led evidence primary and metadata-only hosted wording intact.
- R064 — validated by the pointer-only integrated proof plus focused regression coverage that rejects governance-story drift into compliance-platform or hosted-authority scope.

## New Requirements Surfaced

- No new requirements surfaced; S05 validated and closed R062, R063, and R064.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

The integrated proof remains intentionally pointer-only and depends on the canonical backend, console, and health seams for detailed behavior. This is a deliberate scope guardrail, not missing implementation.

## Follow-ups

None.

## Files Created/Modified

- `docs/m008-integrated-proof.md` — Added the canonical pointer-only integrated governance proof for M008.
- `README.md` — Added discoverability link to the new M008 integrated proof.
- `docs/architecture.md` — Added discoverability link to the new M008 integrated proof from architecture docs.
- `tests/test_health.py` — Added ordering assertion that `governance_store` precedes `retention_lifecycle` in health/dependency output.
- `console/src/app/(console)/observability/page.test.tsx` — Added observability ordering assertions to keep selected request evidence ahead of supporting runtime context.
- `.gsd/DECISIONS.md` — Appended the S05 integrated-proof close-out decision.
- `.gsd/KNOWLEDGE.md` — Recorded the integrated proof ordering guardrail for future slices.
- `.gsd/PROJECT.md` — Refreshed project state to mark M008 complete and summarize S05 close-out.
