---
id: T01
parent: S05
milestone: M001
provides:
  - Canonical integrated adoption walkthrough that preserves the public request → headers → ledger → Playground → Observability proof order
key_files:
  - docs/integrated-adoption-proof.md
  - README.md
  - docs/quickstart.md
  - docs/reference-migration.md
  - docs/day-1-value.md
  - .gsd/milestones/M001/slices/S05/tasks/T01-PLAN.md
key_decisions:
  - Kept adoption-api-contract and production-model as linked canonicals instead of duplicating contract or runtime-model content in the integrated walkthrough
patterns_established:
  - Treat Playground as admin-only corroboration and Observability as persisted explanation after the public route and usage-ledger correlation are already established
observability_surfaces:
  - docs/integrated-adoption-proof.md
  - rg vocabulary/content integrity checks across README.md and docs/*.md
  - local runner absence surfaced by python3 -m pytest, vitest, and playwright command failures
duration: 57m
verification_result: passed
completed_at: 2026-03-23T18:58:37-03:00
blocker_discovered: false
---

# T01: Compose the canonical integrated adoption walkthrough

**Added the integrated adoption proof doc and linked Nebula's entry docs to one stable public-to-operator verification path.**

## What Happened

I first fixed the pre-flight task-plan gap by adding an `## Observability Impact` section to `.gsd/milestones/M001/slices/S05/tasks/T01-PLAN.md`, because this task changes how future agents inspect the final joined adoption story.

I then added `docs/integrated-adoption-proof.md` as the new canonical integrated walkthrough. The new document preserves the required proof order exactly: real public `POST /v1/chat/completions` request, public `X-Nebula-*` plus `X-Request-ID`, usage-ledger correlation, Playground corroboration, and Observability corroboration. It explicitly keeps `docs/adoption-api-contract.md` as the only public contract reference and `docs/production-model.md` as the runtime-truth boundary reference instead of re-explaining those topics.

To make the path discoverable without broad rewriting, I added minimal cross-links in `README.md`, `docs/quickstart.md`, `docs/reference-migration.md`, and `docs/day-1-value.md`. Those links now route readers toward the integrated walkthrough while keeping the existing canonicals in their original roles. I also cleaned an unrelated duplicated tail in `README.md`'s Selected endpoints section that surfaced during verification.

Throughout the touched docs, Playground remains framed as admin-only corroboration rather than the adoption target, and Observability remains the persisted explanation plus dependency-health surface rather than a replacement for the public request contract.

## Verification

I verified the task-level documentation deliverable by confirming `docs/integrated-adoption-proof.md` exists and by running the required ripgrep vocabulary checks across the touched docs.

I also ran the full slice verification commands as required by the slice plan. The documentation-level integrity check passed. The executable backend and console checks did not run in this worktree because the local environment is missing `pytest`, `vitest`, and `playwright`, so those failures were recorded as environment gaps rather than treated as product regressions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `test -f docs/integrated-adoption-proof.md` | 0 | ✅ pass | <1s |
| 2 | `rg -n "integrated adoption|X-Request-ID|Playground|Observability|adoption-api-contract|production-model" README.md docs/integrated-adoption-proof.md docs/quickstart.md docs/reference-migration.md docs/day-1-value.md` | 0 | ✅ pass | <1s |
| 3 | `python3 -m pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_chat_completions.py tests/test_response_headers.py -q` | 1 | ❌ fail | <1s |
| 4 | `npm --prefix console run test -- --run playground-metadata && npm --prefix console run test -- --run playground-recorded-outcome && npm --prefix console run test -- --run playground && npm --prefix console run test -- --run observability` | 127 | ❌ fail | <1s |
| 5 | `npm --prefix console run e2e -- --grep "playground|observability"` | 127 | ❌ fail | <1s |
| 6 | `rg -n "integrated adoption|quickstart|reference migration|day-1 value|adoption-api-contract|production-model|X-Request-ID|Playground|Observability" README.md docs/*.md .gsd/REQUIREMENTS.md .gsd/KNOWLEDGE.md` | 0 | ✅ pass | <1s |

## Diagnostics

Future agents should start with `docs/integrated-adoption-proof.md` to inspect the final joined story, then follow its links back to `docs/quickstart.md`, `docs/reference-migration.md`, `docs/day-1-value.md`, `docs/adoption-api-contract.md`, and `docs/production-model.md` to verify that contract, runtime-model, and operator-surface boundaries still align.

For repository-level integrity, rerun the two ripgrep commands above. For executable slice verification in a provisioned environment, rerun the listed pytest, Vitest, and Playwright commands once `pytest`, `vitest`, and `playwright` are installed in the active worktree.

## Deviations

- I fixed an unrelated duplicated trailing block in `README.md`'s Selected endpoints list after it surfaced during local verification. This was not in the written task plan but was a low-risk integrity cleanup in a touched file.

## Known Issues

- Local executable verification is currently blocked in this worktree because `python3 -m pytest` failed with `No module named pytest`.
- Console unit verification is currently blocked because `vitest` is not installed in the active environment.
- Console e2e verification is currently blocked because `playwright` is not installed in the active environment.

## Files Created/Modified

- `docs/integrated-adoption-proof.md` — new canonical integrated adoption walkthrough preserving the public-to-operator proof order
- `README.md` — added integrated-proof discoverability link and removed duplicated Selected endpoints tail
- `docs/quickstart.md` — added minimal cross-link to the integrated adoption proof
- `docs/reference-migration.md` — added minimal cross-link to the integrated adoption proof after the public migration proof
- `docs/day-1-value.md` — linked the day-1 proof back to the new final joined walkthrough
- `.gsd/milestones/M001/slices/S05/tasks/T01-PLAN.md` — added the missing Observability Impact section required by the pre-flight instruction
