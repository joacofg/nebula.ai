---
id: S05
parent: M005
milestone: M005
provides:
  - A canonical v4 integrated walkthrough that downstream milestone validators and roadmap reassessment can use as the single assembled decisioning proof path.
  - Top-level README and architecture discoverability for the v4 proof so future readers can locate the assembled story quickly without searching task history.
  - Requirement-level evidence that the v4 milestone improved operator decision quality and control while remaining within the narrow decisioning-control-plane scope required by R044.
requires:
  - slice: S02
    provides: Stable route vocabulary, policy simulation replay, hard guardrails, bounded recommendations, and cache-control surfaces delivered by S02-S04 that the integrated proof composes without redefining.
  - slice: S03
    provides: Runtime-enforced hard-budget outcomes and explainable downgrade-versus-deny evidence consumed by the integrated proof path.
  - slice: S04
    provides: Recommendation and semantic-cache tuning/inspection seams plus Observability corroboration used as the final v4 operator evidence story.
affects:
  - M005 downstream reassessment
key_files:
  - docs/v4-integrated-proof.md
  - README.md
  - docs/architecture.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Used the existing integrated-proof document pattern and kept docs/v4-integrated-proof.md strictly pointer-only, delegating canonical detail to the existing docs and code-backed seams instead of duplicating contracts.
  - Kept discoverability wiring in README.md and docs/architecture.md and relied on focused runtime/UI verification plus explicit file/link checks instead of adding brittle prose-snapshot documentation tests.
  - Validated R044 and recorded a requirement decision because the assembled v4 proof demonstrates improved operator decision quality and control without widening Nebula into new public APIs, hosted authority, SDK sprawl, or unrelated platform work.
patterns_established:
  - Integrated-proof docs for Nebula should stay composition-first and pointer-only: assemble the proof order, but delegate detailed contracts to the existing canonical docs and code-backed seams.
  - For documentation-assembly slices, prefer explicit file/link integrity checks plus focused behavior/UI tests over long markdown snapshots so discoverability is enforced without locking prose unnecessarily.
  - When closing a decisioning milestone, preserve the hierarchy route vocabulary -> policy replay -> guardrails -> recommendations/cache posture -> Observability corroboration -> benchmark evidence so later wording changes do not accidentally widen scope or invert the operator proof story.
observability_surfaces:
  - Policy simulation replay preview in the existing policy editor save flow
  - Usage-ledger inspection and request detail via the admin governance API
  - Observability recommendation and cache-summary context on the console Observability page
  - Dependency-health context used as supporting runtime evidence rather than a replacement for ledger proof
drill_down_paths:
  - .gsd/milestones/M005/slices/S05/tasks/T01-SUMMARY.md
  - .gsd/milestones/M005/slices/S05/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-28T04:24:16.051Z
blocker_discovered: false
---

# S05: Integrated v4 proof

**Assembled the shipped v4 decisioning seams into one pointer-only integrated proof path, added top-level discoverability links, and reverified the end-to-end operator story across backend, admin API, console, and docs.**

## What Happened

S05 closed the v4 decisioning milestone by assembling the already-shipped S02-S04 seams into one narrow integrated proof path and then revalidating that the assembled worktree still supports the full operator story end to end. The new docs/v4-integrated-proof.md walkthrough follows the established integrated-proof pattern but stays intentionally pointer-only: it starts from the route-decision vocabulary, moves through preview-before-save policy simulation, reasserts the hard-budget-versus-soft-budget boundary, then joins bounded recommendations, semantic-cache posture, Observability corroboration, and benchmark/evaluation artifacts without restating contracts that already live in canonical docs or code-backed surfaces. README.md and docs/architecture.md now point to that walkthrough so the assembled story is discoverable from the main documentation entrypoints. Slice-level close-out then reran the focused backend, admin API, and console tests that prove the runtime decisioning seams still behave as documented. Those passing checks show the integrated v4 story remains coherent across simulation replay, runtime-enforced hard guardrails, recommendation and cache summaries, policy-editor preview/save discipline, Observability request-detail evidence, and ledger-backed operator wording. The result is a final proof artifact that demonstrates Nebula's v4 control-plane wedge stayed disciplined: stronger operator decisioning and better evidence, but no new public API family, no autonomous optimizer, no hosted-plane authority expansion, and no unrelated app-platform scope drift.

## Verification

All slice-plan verification checks passed in the assembled worktree: `./.venv/bin/pytest tests/test_service_flows.py -k "simulation or recommendation or cache or runtime_policy or budget" -x` passed with 11 selected tests, `./.venv/bin/pytest tests/test_governance_api.py -k "simulation or recommendation or guardrail or policy_options or policy_denied" -x` passed with 13 selected tests, and `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx` passed with 5 files / 22 tests. Discoverability checks also passed: `test -f docs/v4-integrated-proof.md` succeeded and `rg -n "v4-integrated-proof\.md" README.md docs/architecture.md` confirmed both top-level docs link to the new walkthrough. Observability/diagnostic surfaces were included in the targeted console verification and remain corroboration-only supporting context for ledger-backed request evidence.

## Requirements Advanced

- R044 — S05 assembled the final pointer-only proof path and top-level discoverability around the already-shipped v4 decisioning seams, making the narrow control-plane story reviewable end to end.

## Requirements Validated

- R044 — Validated by the new docs/v4-integrated-proof.md walkthrough, discoverability links in README.md and docs/architecture.md, and passing focused verification: ./.venv/bin/pytest tests/test_service_flows.py -k "simulation or recommendation or cache or runtime_policy or budget" -x, ./.venv/bin/pytest tests/test_governance_api.py -k "simulation or recommendation or guardrail or policy_options or policy_denied" -x, npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx, plus file/link checks for docs/v4-integrated-proof.md.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

Use this integrated proof as the dependency summary for milestone close-out and any roadmap reassessment, and preserve its strict proof order if later slices touch route vocabulary, policy replay, Observability framing, or benchmark evidence.

## Files Created/Modified

- `docs/v4-integrated-proof.md` — Added the canonical pointer-only v4 integrated proof walkthrough that assembles route vocabulary, simulation replay, hard guardrails, recommendations, cache controls, Observability corroboration, and benchmark evidence in one strict review order without duplicating detailed contracts.
- `README.md` — Added a top-level pointer to the v4 integrated proof alongside the existing proof and contract references so reviewers can discover the assembled decisioning walkthrough from the main project entrypoint.
- `docs/architecture.md` — Added an architecture-guide pointer to the v4 integrated proof so the assembled decisioning review path is discoverable from the endpoint and surface inventory without restating the v4 contract inline.
- `.gsd/KNOWLEDGE.md` — Recorded the final proof-composition rule so future slices keep the v4 walkthrough pointer-only and verify discoverability with focused checks instead of prose snapshots.
