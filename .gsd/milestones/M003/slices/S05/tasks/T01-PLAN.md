---
estimated_steps: 5
estimated_files: 6
skills_used:
  - review
  - test
---

# T01: Author the embeddings integrated adoption walkthrough

**Slice:** S05 — Final adoption assembly
**Milestone:** M003

## Description

Create the missing embeddings equivalent of `docs/integrated-adoption-proof.md`. This task should add a single joined walkthrough at `docs/embeddings-integrated-adoption-proof.md` that assembles the already-shipped embeddings contract, migration proof, and durable evidence path into one credible story without creating a second contract source. The new doc must preserve the established proof order from prior slices: public `POST /v1/embeddings` first, `X-Request-ID` plus `X-Nebula-*` headers second, `GET /v1/admin/usage/ledger?request_id=...` third, and Observability only as secondary corroboration of the same persisted row.

## Steps

1. Read `docs/integrated-adoption-proof.md`, `docs/embeddings-adoption-contract.md`, `docs/embeddings-reference-migration.md`, `tests/test_embeddings_reference_migration.py`, and `console/e2e/observability.spec.ts` to mirror the established joined-proof structure without widening scope.
2. Write `docs/embeddings-integrated-adoption-proof.md` with sections for what the integrated proof establishes, canonical proof order, how the canonical docs fit together, a minimal integrated walkthrough, what the walkthrough intentionally does not duplicate, and failure modes that make scope drift obvious.
3. Keep detailed request/response semantics, exclusions, and auth claims delegated to `docs/embeddings-adoption-contract.md`; keep the realistic caller diff delegated to `docs/embeddings-reference-migration.md` and `tests/test_embeddings_reference_migration.py`.
4. Explicitly state that Observability is subordinate to the public response plus usage-ledger correlation path and must not replace `X-Request-ID` or `GET /v1/admin/usage/ledger?request_id=...` as the proof seam.
5. Verify the new doc exists, is non-placeholder, and contains the required canonical links and guardrail sections.

## Must-Haves

- [ ] `docs/embeddings-integrated-adoption-proof.md` exists and assembles the embeddings adoption story without redefining the detailed `POST /v1/embeddings` contract.
- [ ] The new walkthrough preserves the proof order public request -> `X-Request-ID`/`X-Nebula-*` -> usage ledger -> Observability corroboration and names failure modes that would violate `R024`.

## Verification

- `test -f docs/embeddings-integrated-adoption-proof.md && ! grep -q "TBD\|TODO" docs/embeddings-integrated-adoption-proof.md && [ "$(rg -c "^## " docs/embeddings-integrated-adoption-proof.md)" -ge 6 ]`
- `python - <<'PY'
from pathlib import Path
text = Path('docs/embeddings-integrated-adoption-proof.md').read_text()
for needle in ['docs/embeddings-adoption-contract.md','docs/embeddings-reference-migration.md','POST /v1/embeddings','X-Request-ID','/v1/admin/usage/ledger','Observability','What this walkthrough intentionally does not duplicate','Failure modes this integrated proof makes obvious']:
    assert needle in text, needle
PY`

## Inputs

- `docs/integrated-adoption-proof.md` — structural precedent for a final joined adoption walkthrough.
- `docs/embeddings-adoption-contract.md` — canonical detailed embeddings boundary that the new doc must defer to.
- `docs/embeddings-reference-migration.md` — human-readable migration proof that the new doc should assemble, not replace.
- `tests/test_embeddings_reference_migration.py` — executable proof source for the public-response and usage-ledger path.
- `console/e2e/observability.spec.ts` — existing corroboration proof for embeddings in Observability.

## Expected Output

- `docs/embeddings-integrated-adoption-proof.md` — embeddings-specific final assembly walkthrough tying contract, migration, and durable evidence into one narrow proof package.

## Observability Impact

This task does not introduce new runtime signals, but it changes how future agents and reviewers inspect the existing embeddings proof path. The walkthrough must explicitly name the canonical evidence chain — public `POST /v1/embeddings`, `X-Request-ID` plus `X-Nebula-*` headers, `GET /v1/admin/usage/ledger?request_id=...`, and Observability as secondary corroboration — so a future agent can inspect the same signals without promoting Observability above the public response or ledger row. The visible failure state for this task is documentation drift: if the walkthrough omits `X-Request-ID`, breaks the public-to-ledger correlation story, or implies that Observability can replace the public request path, the assembled proof becomes misleading even though runtime behavior remains unchanged.
