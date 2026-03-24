---
id: T01
parent: S02
milestone: M001
provides:
  - Canonical quickstart and production-model documentation aligned to the current self-hosted auth, tenant, and operator runtime boundaries.
key_files:
  - docs/quickstart.md
  - docs/production-model.md
  - README.md
  - docs/self-hosting.md
  - docs/architecture.md
  - .gsd/milestones/M001/slices/S02/tasks/T01-PLAN.md
  - .gsd/milestones/M001/slices/S02/S02-PLAN.md
key_decisions:
  - Kept docs/adoption-api-contract.md as the sole public API contract and made the new docs reference it instead of duplicating request/response semantics.
patterns_established:
  - Route self-hosted adopters through one deployment runbook, one quickstart, and one operating-model doc, with credential split and tenant-header rules anchored to runtime code.
observability_surfaces:
  - docs/quickstart.md
  - docs/production-model.md
  - README.md
  - docs/self-hosting.md
  - docs/architecture.md
  - GET /v1/admin/usage/ledger
  - X-Nebula-* response headers
  - X-Request-ID on Playground
  - console Observability and Playground pages
duration: 31m
verification_result: passed_with_environmental_gap
completed_at: 2026-03-23T19:20:00-03:00
blocker_discovered: false
---

# T01: Author the production model and happy-path quickstart docs

**Authored canonical self-hosted quickstart and production-model docs, then linked repo entry docs to that adoption path and operating model.**

## What Happened

I first read the task plan, slice plan, runtime auth/admin/config code, and the relevant console components to anchor the documentation in real behavior. I also fixed the task-plan pre-flight issue by adding an `## Observability Impact` section to `.gsd/milestones/M001/slices/S02/tasks/T01-PLAN.md`.

I then created `docs/production-model.md` to describe the current runtime truth: tenant, policy, and API key are authoritative entities; operator access is the admin-key-backed console plus `/v1/admin/*`; bootstrap access exists but tenant-scoped keys are the preferred long-term model; and `app` / `workload` remain documentation guidance rather than first-class runtime objects in M001.

Next I created `docs/quickstart.md` as the canonical supported self-hosted adoption flow. It walks through configuring `deploy/selfhosted.env`, starting `docker-compose.selfhosted.yml`, signing into the console with the admin key, deciding between bootstrap versus tenant-scoped client keys, sending a first public `POST /v1/chat/completions` request with `X-Nebula-API-Key`, and confirming success through `X-Nebula-*` headers, Playground, the usage ledger, and Observability.

Finally, I updated `README.md`, `docs/self-hosting.md`, and `docs/architecture.md` so the repository points readers to the new canonical docs instead of leaving the adoption path or operating model fragmented across entrypoints.

## Verification

I ran the task-level and slice-level documentation integrity checks. They passed: both docs exist, both have at least five `##` sections, the required credential/header/operator terminology is present, the repo entry docs now reference the new canonical docs, and there are no `TODO` or `TBD` placeholders in the touched documentation.

I also ran the console test suite successfully with `npm --prefix console run test -- --run`.

The backend pytest verification could not run in this worktree environment because `pytest` is not installed and there is no local `.venv` in the working directory. I confirmed that this is an environment/tooling gap (`/bin/bash: pytest: command not found`, `.venv-pytest-missing`) rather than a code-level test failure.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `test -f docs/quickstart.md && test -f docs/production-model.md && grep -c "^## " docs/quickstart.md | awk '{exit !($1 >= 5)}' && grep -c "^## " docs/production-model.md | awk '{exit !($1 >= 5)}'` | 0 | ✅ pass | ~0.1s |
| 2 | `rg -n "X-Nebula-API-Key|X-Nebula-Admin-Key|X-Nebula-Tenant-ID|Playground|Observability|usage ledger|startup|platform|enterprise|app|workload" docs/quickstart.md docs/production-model.md` | 0 | ✅ pass | ~0.1s |
| 3 | `rg -n "docs/quickstart.md|docs/production-model.md|adoption-api-contract|self-hosting|Playground|Observability|usage ledger" README.md docs/self-hosting.md docs/architecture.md docs/quickstart.md docs/production-model.md` | 0 | ✅ pass | ~0.1s |
| 4 | `! rg -n "TODO|TBD" README.md docs/quickstart.md docs/production-model.md docs/self-hosting.md docs/architecture.md` | 0 | ✅ pass | ~0.1s |
| 5 | `pytest tests/test_chat_completions.py tests/test_governance_api.py tests/test_admin_playground_api.py -q` | 127 | ❌ fail | 3.9s |
| 6 | `npm --prefix console run test -- --run` | 0 | ✅ pass | 3.9s |
| 7 | `python3 --version && which python3 && which pytest || true && test -x .venv/bin/pytest && echo .venv-pytest-present || echo .venv-pytest-missing` | 0 | ✅ pass | ~0.1s |

## Diagnostics

To inspect this task later, start with `docs/quickstart.md` for the happy path and `docs/production-model.md` for the authoritative operating model. The runtime evidence surfaces those docs point to are unchanged: public `X-Nebula-*` response headers, Playground `X-Request-ID`, `GET /v1/admin/usage/ledger`, and the console Playground / Observability views. If doc drift is suspected, re-run the `rg` integrity checks and the backend/console suites once a Python test environment with `pytest` is available.

## Deviations

None.

## Known Issues

- The planned backend pytest verification was blocked by the current worktree environment lacking `pytest` and a local `.venv`. No code-level backend regression was observed, but that verification remains to be rerun in a provisioned Python environment.

## Files Created/Modified

- `docs/production-model.md` — added the canonical operating-model reference for tenant, policy, API key, operator, and app/workload guidance.
- `docs/quickstart.md` — added the canonical self-hosted quickstart from environment setup to first public request and operator-visible verification.
- `README.md` — linked the new canonical docs from the documentation map, quick-start section, and admin/bootstrap guidance.
- `docs/self-hosting.md` — linked deployment steps to the new quickstart and production-model references.
- `docs/architecture.md` — linked console/runtime architecture sections to the new canonical docs and adoption contract.
- `.gsd/milestones/M001/slices/S02/tasks/T01-PLAN.md` — added the missing `## Observability Impact` section required by the task pre-flight.
- `.gsd/milestones/M001/slices/S02/S02-PLAN.md` — marked T01 complete.
