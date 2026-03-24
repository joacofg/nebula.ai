---
id: T02
parent: S05
milestone: M003
provides:
  - Pointer-only discoverability links for the embeddings integrated walkthrough plus validated R024 evidence grounded in passing focused embeddings proof checks
key_files:
  - README.md
  - docs/architecture.md
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M003/slices/S05/tasks/T02-SUMMARY.md
key_decisions:
  - Kept README.md and docs/architecture.md strictly pointer-only by linking the integrated walkthrough instead of restating embeddings request, auth, or failure semantics
patterns_established:
  - Requirement close-out for narrow adoption slices should cite discoverability surfaces, the integrated walkthrough, and rerun focused proof commands together rather than treating docs-only edits as sufficient
observability_surfaces:
  - README.md
  - docs/architecture.md
  - docs/embeddings-integrated-adoption-proof.md
  - .gsd/REQUIREMENTS.md
  - tests/test_embeddings_reference_migration.py
  - tests/test_embeddings_api.py
  - tests/test_governance_api.py
duration: 18m
verification_result: passed
completed_at: 2026-03-23T23:35:00-03:00
blocker_discovered: false
---

# T02: Wire discoverability and close out R024 evidence

**Added pointer-only discoverability links for the embeddings integrated walkthrough and validated R024 with passing focused proof evidence.**

## What Happened

I first read the slice/task plan, the prior T01 summary, `README.md`, `docs/architecture.md`, `docs/embeddings-integrated-adoption-proof.md`, and `.gsd/REQUIREMENTS.md` to make sure the discoverability edits would stay narrow and consistent with the assembled proof order.

I then updated `README.md` in two places: the documentation map now includes `docs/embeddings-integrated-adoption-proof.md` as the joined walkthrough, and the `POST /v1/embeddings` endpoint entry now points readers to the integrated proof path in addition to the canonical contract. I updated `docs/architecture.md` the same way, adding one pointer from the embeddings request-flow paragraph and one pointer from the Observability/product-proof section. In each case, I kept the edits pointer-only so those files still delegate detailed request/response, auth, and exclusion semantics to `docs/embeddings-adoption-contract.md`.

After the doc wiring was in place, I reran the focused embeddings proof suite and the repo/doc discoverability checks. Unlike the earlier T01 environment mismatch, pytest now resolved `rootdir` to this worktree and all focused embeddings tests passed. Because the executable checks and grep checks passed without surfacing wording drift, I did not need to modify `docs/embeddings-integrated-adoption-proof.md` further.

Finally, I updated `R024` from `active` to `validated` with concrete evidence that cites the discoverability links, the integrated walkthrough, and the passing focused embeddings verification commands. I then marked T02 complete in the slice plan.

## Verification

I verified both must-haves directly:

- confirmed the focused embeddings proof suite passes in this worktree:
  - `tests/test_embeddings_reference_migration.py`
  - `tests/test_embeddings_api.py`
  - `tests/test_governance_api.py -k embeddings`
- confirmed repo/docs discoverability now mentions the integrated walkthrough alongside the contract, migration guide, public `POST /v1/embeddings` path, `X-Request-ID`, `/v1/admin/usage/ledger`, and Observability surfaces
- confirmed `.gsd/REQUIREMENTS.md` now records `R024` as `validated` and includes validation text tied to `docs/embeddings-integrated-adoption-proof.md` and the focused pytest reruns

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py` | 0 | ✅ pass | ~1.1s |
| 2 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py` | 0 | ✅ pass | ~1.1s |
| 3 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` | 0 | ✅ pass | ~0.9s |
| 4 | `rg -n "embeddings-integrated-adoption-proof|embeddings-adoption-contract|embeddings-reference-migration|POST /v1/embeddings|X-Request-ID|/v1/admin/usage/ledger|Observability" README.md docs/architecture.md docs/*.md && rg -n "R024|validated|embeddings-integrated-adoption-proof" .gsd/REQUIREMENTS.md` | 0 | ✅ pass | ~0.02s |

## Diagnostics

Future agents can inspect this task through:

- `README.md` for repo-level discoverability of the embeddings integrated walkthrough
- `docs/architecture.md` for the pointer-only architecture-level link back to the joined proof path
- `docs/embeddings-integrated-adoption-proof.md` for the canonical public-request -> headers -> ledger -> Observability proof order
- `.gsd/REQUIREMENTS.md` for the validated `R024` entry and its cited evidence
- `tests/test_embeddings_reference_migration.py`, `tests/test_embeddings_api.py`, and `tests/test_governance_api.py -k embeddings` for the executable proof suite named in the requirement validation

## Deviations

- None.

## Known Issues

- None discovered during this task. The earlier pytest rootdir/path mismatch recorded in T01 did not reproduce here; the focused embeddings suite passed from this worktree.

## Files Created/Modified

- `README.md` — added pointer-only discoverability references to `docs/embeddings-integrated-adoption-proof.md` from the documentation map and embeddings endpoint entry
- `docs/architecture.md` — added pointer-only references to the embeddings integrated walkthrough from the request-flow and Observability/product-proof sections
- `.gsd/REQUIREMENTS.md` — updated `R024` from active to validated with concrete proof references
- `.gsd/milestones/M003/slices/S05/tasks/T02-SUMMARY.md` — recorded execution narrative, verification evidence, and close-out state for T02
