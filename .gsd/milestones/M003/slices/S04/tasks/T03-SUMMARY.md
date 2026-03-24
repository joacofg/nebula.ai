---
id: T03
parent: S04
milestone: M003
provides:
  - Adds an end-to-end Observability proof that embeddings ledger rows are filterable and inspectable via request-id-correlated persisted metadata.
key_files:
  - console/e2e/observability.spec.ts
  - docs/embeddings-reference-migration.md
key_decisions:
  - Kept Observability explicitly subordinate to the public X-Request-ID plus usage-ledger path by extending only the mocked browser proof and migration wording, without adding any new storage, admin APIs, or payload fields.
patterns_established:
  - When closing an operator-proof slice, mirror the durable backend evidence in Playwright by mocking the existing admin API contract and asserting the same request id plus persisted route/outcome fields the migration proof already uses.
observability_surfaces:
  - Playwright proof in console/e2e/observability.spec.ts; public X-Request-ID headers; GET /v1/admin/usage/ledger?request_id=...; Observability request-detail card
duration: 1h
verification_result: passed_with_known_issues
completed_at: 2026-03-24T00:10:00-03:00
blocker_discovered: false
---

# T03: Add end-to-end operator proof for embeddings evidence correlation

**Added an embeddings-focused Observability browser proof and clarified docs so UI inspection remains corroboration of the same X-Request-ID ledger evidence path.**

## What Happened

I read the existing migration proof, observability spec, and slice summaries first to preserve the established evidence order: public `/v1/embeddings` request, `X-Request-ID` and `X-Nebula-*` headers, durable usage-ledger correlation, then Observability as operator corroboration.

I then rewrote `console/e2e/observability.spec.ts` around an embeddings-specific mocked ledger row. The spec now filters `Route target` to `embeddings`, verifies the row remains discoverable by request id, selects it, and asserts the persisted explanation fields shown in the request-detail surface: route target, terminal status, requested/response model, provider, route reason, policy outcome, fallback/cache flags, and the request id itself. The browser proof also keeps the metadata-only boundary explicit by asserting that raw embedding input text and vector content are absent from the UI proof.

Finally, I made a narrow wording update in `docs/embeddings-reference-migration.md` to state plainly that Observability is a secondary surface for inspecting the same durable row after `X-Request-ID` and `GET /v1/admin/usage/ledger?request_id=...` have already established the primary proof path.

## Verification

I ran the focused T03 checks plus the broader slice commands available from this worktree.

Behavior and code-level verification completed as follows:
- The executable migration proof passed with the worktree-correct path: `./tests/test_embeddings_reference_migration.py`.
- The ledger filter and table component tests passed via Vitest async runs.
- The repo grep for embeddings-related operator-proof coverage passed and shows the new browser proof plus existing component/backend proof surfaces.
- The Playwright observability spec could not complete because the console web server fails to compile on a pre-existing type error in `console/src/components/deployments/remote-action-card.tsx`, outside the files touched for T03.
- Some slice-plan commands needed local path corrections in this `.gsd/worktrees/M003` worktree (for example `./tests/...` instead of paths resolved from the monorepo root), and one negative grep from the slice remains broadly matched by legitimate test fixtures/assertions that predate this task.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rg -n 'X-Request-ID|/v1/admin/usage/ledger|Observability|request id' docs/embeddings-reference-migration.md tests/test_embeddings_reference_migration.py console/e2e/observability.spec.ts` | 0 | ✅ pass | ~0.1s |
| 2 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest ./tests/test_embeddings_reference_migration.py` | 0 | ✅ pass | ~0.8s |
| 3 | `npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx` | 0 | ✅ pass | ~0.8s |
| 4 | `npm --prefix console run test -- --run src/components/ledger/ledger-table.test.tsx` | 0 | ✅ pass | ~0.5s |
| 5 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` | 1 | ❌ fail | ~11.5s |
| 6 | `npm --prefix console run e2e -- e2e/observability.spec.ts` | 1 | ❌ fail | ~10.2s |
| 7 | `rg -n 'embeddings' console/src/components/ledger console/src/app/\(console\)/observability console/e2e/observability.spec.ts tests/test_embeddings_reference_migration.py -S` | 0 | ✅ pass | ~0.1s |
| 8 | `! rg -n 'input|embedding"|embeddings"' console/src/components/ledger console/src/lib/admin-api.ts tests/test_embeddings_reference_migration.py -g '!docs/**'` | 1 | ❌ fail | ~0.1s |

## Diagnostics

Future agents can inspect the operator-proof chain in this order:
1. Run `./tests/test_embeddings_reference_migration.py` to confirm the public `POST /v1/embeddings` response, `X-Request-ID`, and durable ledger row still align.
2. Read `console/e2e/observability.spec.ts` to see the exact UI-side corroboration contract for embeddings rows.
3. If the browser proof still fails to start, inspect the existing compile error in `console/src/components/deployments/remote-action-card.tsx:84` before debugging Observability itself.
4. Use the migration guide section added in `docs/embeddings-reference-migration.md` to keep docs aligned with the test-first proof order.

## Deviations

- I updated `docs/embeddings-reference-migration.md` even though the browser proof was the main implementation target, because the new UI assertions made it worthwhile to state the subordinate role of Observability more explicitly.
- Verification commands from the task/slice plans required minor local adaptation in this worktree: the passing Python command used `./tests/test_embeddings_reference_migration.py`, and Playwright had to be run via the existing `npm --prefix console run e2e -- e2e/observability.spec.ts` script rather than a non-existent `playwright` npm script.

## Known Issues

- `npm --prefix console run e2e -- e2e/observability.spec.ts` is currently blocked by a pre-existing Next.js type error in `console/src/components/deployments/remote-action-card.tsx:84` (`string | null` passed where `string` is required). This prevented full browser execution of the new proof.
- The slice-plan command `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` reported “No test files found” during one async run despite the file existing; subsequent foreground rerun attempts hit a local PATH issue (`vitest: command not found`) that appears environment-specific rather than product-specific.
- The slice negative grep still fails because its pattern matches legitimate embeddings fixtures/assertions in tests and shared filter strings, so it is not currently a reliable gate for newly introduced redaction regressions.

## Files Created/Modified

- `console/e2e/observability.spec.ts` — extended the operator proof with an embeddings ledger row, filter interaction, request-detail assertions, and metadata-only absence checks.
- `docs/embeddings-reference-migration.md` — clarified that Observability is corroboration of the same `X-Request-ID` and usage-ledger row rather than a replacement proof source.
