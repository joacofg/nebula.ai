---
id: T02
parent: S02
milestone: M001
provides:
  - Canonical entry docs that route adopters through one quickstart, one production model, and one public API contract boundary, with verification tied to existing evidence surfaces.
key_files:
  - README.md
  - docs/self-hosting.md
  - docs/quickstart.md
  - docs/production-model.md
  - .gsd/milestones/M001/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S02/S02-PLAN.md
key_decisions:
  - Kept docs/adoption-api-contract.md as the sole public compatibility contract while tightening entry-doc links to the canonical quickstart and production model.
patterns_established:
  - Entry docs should route readers to one deployment runbook, one happy-path quickstart, one operating-model reference, and one public API contract instead of restating overlapping guidance.
observability_surfaces:
  - README.md
  - docs/self-hosting.md
  - docs/architecture.md
  - docs/quickstart.md
  - docs/production-model.md
  - X-Nebula-* response headers
  - X-Request-ID on Playground
  - GET /v1/admin/usage/ledger
  - console Playground and Observability views
duration: 24m
verification_result: passed_with_environmental_gaps
completed_at: 2026-03-23T19:31:00-03:00
blocker_discovered: false
---

# T02: Wire entry docs to the new canonical adoption story and lock verification to existing evidence

**Tightened the repo entry docs around the canonical quickstart, production model, and public contract, then re-ran the slice doc checks and captured the local test-environment gaps.**

## What Happened

I started by reading the slice/task plans, the prior task summary, and the current entry-point docs to verify whether the T01 changes already covered part of this task. The main implementation work turned out to be refinement rather than broad rewriting: the core routing already existed, but the entry docs still benefited from more explicit canonical links.

I updated `README.md` so the documentation map now names `docs/adoption-api-contract.md` alongside the new canonical quickstart and production-model docs, making the public contract boundary explicit at the repo entrypoint. I updated `docs/self-hosting.md` related-doc links to include the quickstart, production model, and adoption contract so the deployment runbook no longer strands readers after startup. I also added architecture backlinks in `docs/quickstart.md` and `docs/production-model.md` so a reader can move between deployment, runtime model, operator confirmation surfaces, and the public contract without dead ends.

During verification, I observed an environment split rather than a content problem: the documentation integrity commands passed when rerun directly in this worktree, but backend pytest is unavailable because `pytest` is not installed here, and the console test command fails locally because `console/node_modules/.bin/vitest` is absent in this worktree even though an earlier console run succeeded from the parent repo environment.

## Verification

I reran the slice-level doc shape check, the planned ripgrep integrity check, and the placeholder scan directly in this worktree. All three passed, confirming that the canonical docs exist, have the expected section depth, contain the intended cross-links, and do not include `TODO` or `TBD` placeholders.

I also reran the backend and console verification commands exactly as planned. Both failed for environment/tooling reasons rather than product-behavior regressions: `pytest` is missing from the worktree environment, and the console worktree does not have a local `vitest` binary installed. I recorded those gaps explicitly so a future agent can rerun the same commands in a provisioned environment without re-investigating the docs.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `test -f docs/quickstart.md && test -f docs/production-model.md && grep -c "^## " docs/quickstart.md | awk '{exit !($1 >= 5)}' && grep -c "^## " docs/production-model.md | awk '{exit !($1 >= 5)}'` | 0 | ✅ pass | ~0.1s |
| 2 | `rg -n "docs/quickstart.md|docs/production-model.md|adoption-api-contract|self-hosting|Playground|Observability|usage ledger" README.md docs/self-hosting.md docs/architecture.md docs/quickstart.md docs/production-model.md` | 0 | ✅ pass | ~0.1s |
| 3 | `! rg -n "TODO|TBD" README.md docs/quickstart.md docs/production-model.md docs/self-hosting.md docs/architecture.md` | 0 | ✅ pass | ~0.1s |
| 4 | `pytest tests/test_chat_completions.py tests/test_governance_api.py tests/test_admin_playground_api.py -q` | 127 | ❌ fail | ~0.1s |
| 5 | `npm --prefix console run test -- --run` | 127 | ❌ fail | ~0.5s |
| 6 | `python3 --version && which python3 && which pytest || true && test -x .venv/bin/pytest && echo .venv-pytest-present || echo .venv-pytest-missing && test -x console/node_modules/.bin/vitest && echo console-vitest-present || echo console-vitest-missing` | 0 | ✅ pass | ~0.1s |

## Diagnostics

To inspect this task later, start with `README.md`, `docs/self-hosting.md`, `docs/quickstart.md`, and `docs/production-model.md`. The docs now point consistently at the same runtime evidence surfaces: public `X-Nebula-*` response headers, Playground `X-Request-ID`, `GET /v1/admin/usage/ledger`, and the console Playground / Observability pages.

If verification needs to be completed later, rerun the documented pytest and console commands in a worktree that has Python test tooling installed and the console dependencies present locally.

## Deviations

None.

## Known Issues

- The current worktree environment does not provide `pytest`, so the planned backend evidence suite could not be executed here.
- The current worktree environment does not contain `console/node_modules/.bin/vitest`, so the planned console suite could not be executed here even though a prior run succeeded from the parent repository environment.

## Files Created/Modified

- `README.md` — added the canonical adoption-contract entry in the documentation map and preserved the quickstart/production-model routing at the repo entrypoint.
- `docs/self-hosting.md` — expanded related-doc links so deployment readers can continue directly to the quickstart, production model, and public contract.
- `docs/quickstart.md` — added an architecture backlink in related docs to complete the adoption-path cross-linking.
- `docs/production-model.md` — added an architecture backlink in related docs to complete the operating-model cross-linking.
- `.gsd/milestones/M001/slices/S02/S02-PLAN.md` — marked T02 complete.
- `.gsd/milestones/M001/slices/S02/tasks/T02-SUMMARY.md` — recorded implementation details, verification outcomes, and environment gaps for clean resumption.