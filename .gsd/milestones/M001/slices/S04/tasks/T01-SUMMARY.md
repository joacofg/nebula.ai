---
id: T01
parent: S04
milestone: M001
provides:
  - Canonical day-1 value proof documentation that links the public request evidence path to operator corroboration surfaces.
key_files:
  - docs/day-1-value.md
  - docs/quickstart.md
  - docs/reference-migration.md
  - README.md
key_decisions:
  - Kept the public `POST /v1/chat/completions` request as the only adoption proof target and framed Playground and Observability strictly as operator corroboration surfaces.
patterns_established:
  - Public headers plus `X-Request-ID` first, then Playground, usage-ledger, and Observability corroboration in linked docs without duplicating contract or setup guidance.
observability_surfaces:
  - docs/day-1-value.md, public `X-Nebula-*` headers, `X-Request-ID`, usage ledger lookup, and Observability dependency-health framing
duration: 35m
verification_result: passed
completed_at: 2026-03-23T19:44:00-03:00
blocker_discovered: false
---

# T01: Publish the canonical day-1 value proof path

**Published a canonical day-1 value proof doc and linked quickstart, migration, and README entrypoints to the same public-request-first evidence path.**

## What Happened

I first fixed the missing `## Observability Impact` section in `.gsd/milestones/M001/slices/S04/tasks/T01-PLAN.md` so the task contract explicitly described the signals and failure visibility this doc work depends on.

I then created `docs/day-1-value.md` as the canonical S04 artifact. The document keeps the existing slice boundaries intact: it starts from a real public `POST /v1/chat/completions` request, treats `X-Nebula-*` headers and `X-Request-ID` as the immediate proof surface, and then explains how Playground, the persisted usage ledger, and Observability corroborate that same outcome for operators.

After that, I added minimal handoff links rather than duplicating existing canon:

- `docs/quickstart.md` now points readers to the new day-1 proof after first-request confirmation.
- `docs/reference-migration.md` now points readers to the new day-1 proof after the public migration proof succeeds.
- `README.md` now includes one concise documentation-map link to the new day-1 value proof.

I reviewed the touched docs for boundary discipline and kept contract/setup semantics in their existing homes (`docs/adoption-api-contract.md`, `docs/quickstart.md`, and `docs/reference-migration.md`) instead of restating them.

## Verification

I verified the task deliverables directly by checking that `docs/day-1-value.md` exists and that the required proof terms appear across `README.md`, `docs/day-1-value.md`, `docs/quickstart.md`, and `docs/reference-migration.md`.

I also ran the slice-level verification commands to record the current status at this intermediate task:

- the targeted console component tests passed
- the broader console slice suite partially failed because there is currently no `observability` Vitest target
- the E2E command failed before tests ran due to a pre-existing TypeScript error in `console/src/components/deployments/remote-action-card.tsx`
- the Python verification command failed in this worktree because `pytest` is not installed in the available environment

Those failures are outside the scope of the documentation changes made in T01, but they are recorded here for downstream tasks.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `test -f docs/day-1-value.md` | 0 | ✅ pass | <1s |
| 2 | `rg -n "day-1 value|X-Request-ID|Playground|Observability|route reason|policy" README.md docs/day-1-value.md docs/quickstart.md docs/reference-migration.md` | 0 | ✅ pass | <1s |
| 3 | `pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py -q` | 127 | ❌ fail | 14.6s |
| 4 | `npm --prefix console run test -- --run playground-metadata && npm --prefix console run test -- --run playground-recorded-outcome` | 0 | ✅ pass | 11.9s |
| 5 | `npm --prefix console run test -- --run playground && npm --prefix console run test -- --run observability` | 1 | ❌ fail | 9.3s |
| 6 | `npm --prefix console run e2e -- --grep "playground|observability"` | 1 | ❌ fail | 7.1s |

## Diagnostics

Future agents can inspect the shipped proof path from `docs/day-1-value.md` and verify the intended runtime signals through the public `X-Nebula-*` headers, `X-Request-ID`, `GET /v1/admin/usage/ledger?request_id=...`, and the console Observability surface.

Current slice-gate failures to inspect later:

- Python environment issue: `pytest: command not found`
- Console suite gap: `vitest --run observability` reported `No test files found`
- Existing E2E blocker: Next.js compile failure in `console/src/components/deployments/remote-action-card.tsx:84` because `deployment.id` is typed as `string | null` where `string` is required

## Deviations

None.

## Known Issues

- The slice-level Python verification command cannot run in the current worktree environment because `pytest` is unavailable.
- The slice-level console verification command expects an `observability` Vitest target that does not currently exist.
- The slice-level Playwright verification command is blocked by an unrelated existing TypeScript error in `console/src/components/deployments/remote-action-card.tsx`.

## Files Created/Modified

- `docs/day-1-value.md` — new canonical day-1 value proof walkthrough connecting public request evidence to operator corroboration surfaces
- `docs/quickstart.md` — added a handoff to the canonical day-1 proof after first-request confirmation
- `docs/reference-migration.md` — added a handoff from migration proof to the operator-visible day-1 walkthrough
- `README.md` — added one documentation-map link to the new day-1 value proof
- `.gsd/milestones/M001/slices/S04/tasks/T01-PLAN.md` — added the missing `## Observability Impact` section required by execution
- `.gsd/milestones/M001/slices/S04/S04-PLAN.md` — marked T01 complete
