---
id: S05
parent: M006
milestone: M006
provides:
  - A code-backed, pointer-only calibrated-routing close-out path that downstream milestone validation can use to assess final M006 integrity and requirement status.
requires:
  - slice: S01-S04
    provides: Shared calibrated runtime contract, tenant-scoped calibration evidence, replay parity semantics, and selected-request-first operator inspection surfaces from S01-S04.
affects:
  - M006 milestone validation and close-out
key_files:
  - docs/m006-integrated-proof.md
  - README.md
  - docs/architecture.md
  - tests/test_governance_api.py
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/PROJECT.md
key_decisions:
  - D038: Keep the M006 close-out proof pointer-only and discoverability-first instead of duplicating calibrated-routing, replay, or operator-surface contracts.
  - D039: Validate R049 from the assembled M006 close-out proof while leaving R039 active until milestone validation decides whether the stronger outcome-aware-routing claim is fully proved.
patterns_established:
  - Keep integrated proof docs pointer-only and composition-first; join shipped seams in strict order instead of duplicating contract or UI detail.
  - For close-out work, strengthen the strongest existing executable seams rather than adding a new integration harness.
  - Keep the selected persisted request authoritative in Observability; supporting calibration, recommendation, cache, and dependency context remains subordinate and scoped.
observability_surfaces:
  - Public `X-Nebula-*` and `X-Request-ID` response headers for immediate calibrated-routing evidence.
  - `GET /v1/admin/usage/ledger?request_id=...` as the persisted request-evidence seam.
  - `POST /v1/admin/tenants/{tenant_id}/policy/simulate` changed-request output for replay parity and rollout-disabled/degraded semantics.
  - Selected-request-first Observability and ledger request-detail surfaces in the console.
  - Focused executable seams in tests/test_response_headers.py and tests/test_governance_api.py.
drill_down_paths:
  - .gsd/milestones/M006/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M006/slices/S05/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-02T13:26:08.437Z
blocker_discovered: false
---

# S05: Integrated proof and close-out

**Pointer-only M006 close-out proof plus focused backend and console verification now tie calibrated public headers, request-id ledger evidence, replay parity, and selected-request-first operator inspection into one bounded review path.**

## What Happened

S05 closed the calibrated-routing milestone story without widening product scope. T01 added docs/m006-integrated-proof.md as a pointer-only walkthrough that preserves the strict proof order `docs/route-decision-vocabulary.md` → one public `POST /v1/chat/completions` response → calibrated `X-Nebula-*` and `X-Request-ID` evidence → `GET /v1/admin/usage/ledger?request_id=...` correlation → `POST /v1/admin/tenants/{tenant_id}/policy/simulate` replay parity → selected-request-first Observability inspection. README.md and docs/architecture.md were updated only with discoverability links, keeping detailed contracts in their canonical sources. T02 then tightened the strongest existing executable seams instead of creating a new harness: backend coverage now asserts one calibrated public request through headers, the correlated usage-ledger row, replay changed-request parity, and the bounded rollout-disabled case; console coverage keeps the selected request primary while calibration, recommendation, cache, and policy-preview context stay subordinate and bounded. The result is one reviewable, code-backed M006 proof path that demonstrates calibrated live routing, durable request-id evidence, replay parity, explicit degraded or rollout-disabled semantics, and operator inspection without drifting into analytics, tuning, hosted-authority, or new public-API scope.

## Verification

All slice-plan verification passed in the assembled worktree. Mechanical proof integrity checks passed with `./.venv/bin/python` for file existence, non-empty content, required proof seams, and absence of `TODO`/`TBD`, plus `rg` checks across README.md, docs/architecture.md, and docs/m006-integrated-proof.md. Backend verification passed with `./.venv/bin/pytest tests/test_response_headers.py -x` and `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x`. Console verification passed with `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-page.test.tsx`. I also checked LSP diagnostics on `tests/test_governance_api.py` and found one pre-existing unrelated Ruff warning for a duplicate test name outside the S05 seam; no new slice-specific diagnostics surfaced.

## Requirements Advanced

- R039 — S05 assembled the final close-out evidence for the stronger outcome-aware-routing claim by joining route vocabulary, public calibrated headers, request-id ledger correlation, replay parity, and selected-request-first operator inspection into one executable review path. It materially strengthens the proof for milestone validation, but the requirement remains active pending that explicit decision.

## Requirements Validated

- R049 — Validated by the assembled pointer-only close-out proof in docs/m006-integrated-proof.md, discoverability links in README.md and docs/architecture.md, and passing focused verification: `./.venv/bin/python` file/content checks for docs/m006-integrated-proof.md plus README.md/docs/architecture.md, `rg` proof-token checks, `./.venv/bin/pytest tests/test_response_headers.py -x`, `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x`, and `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-page.test.tsx`. The assembled story stays bounded: no new admin routes, no new public API family, no analytics-product drift, and no hosted-authority expansion.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

The task-plan mechanical verification snippet referenced `python`; in the active worktree the reliable interpreter path was `./.venv/bin/python`, so the same check was executed there instead. No product-scope deviation occurred.

## Known Limitations

R039 remains active rather than validated: the slice proves the assembled close-out path and scope discipline, but the stronger outcome-aware-routing claim still needs explicit milestone-level validation. An unrelated Ruff warning for a duplicate test name remains in tests/test_governance_api.py outside the S05 seam.

## Follow-ups

Milestone validation should decide explicitly whether the assembled M006 evidence is strong enough to validate R039, rerun final milestone-level verification against the assembled worktree, and treat the remaining duplicate-test-name Ruff warning in tests/test_governance_api.py as unrelated cleanup rather than calibrated-routing evidence.

## Files Created/Modified

- `docs/m006-integrated-proof.md` — Added the pointer-only calibrated-routing close-out walkthrough that joins route vocabulary, public headers, request-id-to-ledger correlation, replay parity, bounded degraded or rollout-disabled semantics, and selected-request-first Observability without duplicating canonical contracts.
- `README.md` — Added top-level discoverability pointer to the M006 integrated proof.
- `docs/architecture.md` — Added architecture-guide discoverability pointer to the M006 integrated proof.
- `tests/test_governance_api.py` — Tightened backend close-out proof assertions around calibrated public headers, request-id ledger correlation, replay parity, and rollout-disabled semantics.
- `console/src/app/(console)/observability/page.test.tsx` — Kept Observability assertions selected-request-first and supporting context bounded in the close-out proof.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Tightened Observability request-detail coverage around bounded calibrated-routing context.
- `console/src/components/policy/policy-page.test.tsx` — Kept policy preview wording bounded to compact replay evidence rather than a broader analytics/tuning surface.
- `.gsd/KNOWLEDGE.md` — Recorded the M006 integrated-proof composition rule for future slices and close-out work.
- `.gsd/PROJECT.md` — Refreshed current-state project framing to reflect that M006 is assembled in the worktree and that R049 is validated while R039 remains active pending milestone validation.
