---
estimated_steps: 4
estimated_files: 5
skills_used:
  - test
  - agent-browser
---

# T03: Add end-to-end operator proof for embeddings evidence correlation

**Slice:** S04 — Durable evidence correlation
**Milestone:** M003

## Description

Close the slice at integration proof level by showing the same embeddings evidence path across the public proof and the operator UI. This task should extend the existing Observability browser proof with an embeddings ledger row that can be filtered and inspected, then make any minimal wording/test alignment updates needed so the migration proof and human guide still present Observability as corroboration of the request-id ledger truth rather than as a replacement for it.

## Steps

1. Read `console/e2e/observability.spec.ts`, `tests/test_embeddings_reference_migration.py`, and `docs/embeddings-reference-migration.md` to preserve the established proof order: public request first, request-id/headers second, durable ledger correlation third, Observability as operator corroboration.
2. Extend `console/e2e/observability.spec.ts` with mocked embeddings ledger data that includes `final_route_target="embeddings"`, then assert that an operator can filter to embeddings, select the row, and see the request id plus persisted route/outcome detail fields.
3. If the new browser proof reveals wording drift, make narrow follow-up edits in `docs/embeddings-reference-migration.md` and/or `tests/test_embeddings_reference_migration.py` so both continue to describe Observability as a secondary inspection surface for the same request-id correlation path.
4. Finish by rerunning the browser proof and the executable migration proof, and keep the persisted-evidence boundary metadata-only throughout.

## Must-Haves

- [ ] `console/e2e/observability.spec.ts` explicitly proves embeddings rows are filterable and inspectable in Observability with request-id-based correlation cues.
- [ ] Any supporting doc/test edits keep the proof order honest: public `/v1/embeddings` request and usage-ledger correlation remain primary, while Observability is corroboration of the same durable row.

## Verification

- `npm --prefix console run playwright test e2e/observability.spec.ts`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`
- `rg -n 'X-Request-ID|/v1/admin/usage/ledger|Observability|request id' docs/embeddings-reference-migration.md tests/test_embeddings_reference_migration.py console/e2e/observability.spec.ts`

## Observability Impact

- Signals added/changed: the browser proof locks the operator-side inspection path for embeddings rows using request id, route target, and persisted route/outcome metadata.
- How a future agent inspects this: run the Playwright observability spec first, then compare its assertions with `tests/test_embeddings_reference_migration.py` and the migration guide wording.
- Failure state exposed: broken filter wiring, missing detail fields, or proof-order drift between docs/tests/UI becomes an explicit end-to-end failure instead of a subjective review issue.

## Inputs

- `console/e2e/observability.spec.ts` — current operator proof focused on generic ledger filtering and dependency health.
- `tests/test_embeddings_reference_migration.py` — executable source of truth for the public embeddings request-id correlation path.
- `docs/embeddings-reference-migration.md` — human-readable migration proof that should continue to treat Observability as corroboration.
- `console/src/components/ledger/ledger-filters.tsx` — updated embeddings filter surface from T01.
- `console/src/components/ledger/ledger-request-detail.tsx` — richer request explanation surface from T02.

## Expected Output

- `console/e2e/observability.spec.ts` — embeddings-aware end-to-end operator proof.
- `tests/test_embeddings_reference_migration.py` — preserved or minimally clarified executable proof wording if needed.
- `docs/embeddings-reference-migration.md` — preserved or minimally clarified operator-corroboration wording if needed.
- `console/src/components/ledger/ledger-filters.tsx` — consumed by the browser proof for embeddings filtering.
- `console/src/components/ledger/ledger-request-detail.tsx` — consumed by the browser proof for embeddings request inspection.
