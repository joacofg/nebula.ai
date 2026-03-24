# Embeddings integrated adoption proof

This document assembles Nebula's embeddings adoption canonicals into one narrow, end-to-end proof path.

It exists so a reviewer can follow one joined story from the public `POST /v1/embeddings` request to durable operator evidence without turning this walkthrough into a second public contract. Keep these source documents in their canonical roles:

- [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md) — the only detailed public compatibility boundary for `POST /v1/embeddings`
- [`docs/embeddings-reference-migration.md`](embeddings-reference-migration.md) — the realistic before/after caller migration proof
- `tests/test_embeddings_reference_migration.py` — the executable proof for public response, `X-Request-ID`, and usage-ledger correlation
- `console/e2e/observability.spec.ts` — the UI corroboration proof for the persisted embeddings row in Observability

Use this walkthrough when you need one discoverable embeddings story that proves the already-shipped contract, migration path, and durable evidence flow agree.

## What this integrated proof establishes

The embeddings adoption story is complete only when one team can send one real public `POST /v1/embeddings` request, capture the public response evidence, and then corroborate that same request through the durable operator surfaces without widening Nebula into broader embeddings parity claims.

That joined proof stays grounded in this exact sequence:

1. one real public `POST /v1/embeddings` request
2. public `X-Request-ID` plus `X-Nebula-*` response headers
3. metadata-only correlation in `GET /v1/admin/usage/ledger?request_id=...`
4. Observability as secondary corroboration of the same persisted row

If that order changes, the proof weakens. Observability is not the adoption target, and it is not a substitute for the public response or the usage ledger.

## Canonical proof order

Follow this sequence in order and keep each seam explicit.

### 1. Start with the public request

Begin on the public route itself: `POST /v1/embeddings`.

The detailed request and response semantics live in [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md). This walkthrough depends on that contract rather than restating it. The migration framing for an existing caller lives in [`docs/embeddings-reference-migration.md`](embeddings-reference-migration.md).

At this first step, keep the public boundary narrow:

- use Nebula's shipped `POST /v1/embeddings` surface
- use the documented public auth path
- stay inside the tested `model` plus string-or-flat-list `input` contract
- do not expand this walkthrough into broader OpenAI embeddings parity or helper-SDK abstractions

### 2. Record `X-Request-ID` and the `X-Nebula-*` headers

After the public request succeeds, inspect the response headers before touching any admin-only surface.

The immediate public evidence includes:

- `X-Request-ID`
- `X-Nebula-Tenant-ID`
- `X-Nebula-Route-Target`
- `X-Nebula-Route-Reason`
- `X-Nebula-Provider`
- `X-Nebula-Cache-Hit`
- `X-Nebula-Fallback-Used`
- `X-Nebula-Policy-Mode`
- `X-Nebula-Policy-Outcome`

For the embeddings path, these headers prove on the public route itself that Nebula handled the request, resolved it through the direct embeddings path, and exposed the request id needed for later correlation.

If `X-Request-ID` is missing, or if the walkthrough skips the public `X-Nebula-*` evidence and jumps straight to an admin screen, the integrated adoption proof is incomplete.

### 3. Correlate the same request in the usage ledger

Use the `X-Request-ID` from the public response to inspect the persisted operator record in `GET /v1/admin/usage/ledger?request_id=...`.

This is the canonical durable proof seam because it shows that the same public embeddings request was recorded as metadata, not just observed transiently in a response.

The aligned fields should include at least:

- `request_id`
- `tenant_id`
- `requested_model`
- `final_route_target`
- `final_provider`
- `route_reason`
- `policy_outcome`
- `terminal_status`
- cache, fallback, token, and timing metadata

The joined proof must also preserve the redaction boundary already established by the tests: the usage ledger is metadata-only and must not expose raw embedding inputs or returned vectors.

### 4. Use Observability only as subordinate corroboration

Finish by validating that Observability can surface the same persisted embeddings row.

Observability is valuable because it lets operators filter to `embeddings`, inspect the matching request id, and review route/outcome details alongside dependency-health context. That makes it a useful corroboration surface for the same persisted row already proven by `GET /v1/admin/usage/ledger?request_id=...`.

But keep the boundary explicit:

- Observability is subordinate to the public response plus usage-ledger correlation path
- Observability must not replace `X-Request-ID` as the proof seam
- Observability must not replace `GET /v1/admin/usage/ledger?request_id=...` as the durable evidence source
- Observability remains an operator-facing corroboration surface, not the public adoption contract

If this order is inverted, the walkthrough stops proving the public adoption path and starts overstating an admin UI.

## How the canonical docs fit together

Use this map when deciding which source to open for detail.

| Need | Canonical source | Why it stays separate |
|---|---|---|
| Detailed `POST /v1/embeddings` request/response boundary, exclusions, and failure semantics | [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md) | Prevents this walkthrough from becoming a second public contract |
| Realistic before/after caller migration | [`docs/embeddings-reference-migration.md`](embeddings-reference-migration.md) | Keeps the human-readable migration diff focused and narrow |
| Executable proof of public response, headers, and usage-ledger correlation | `tests/test_embeddings_reference_migration.py` | Keeps the joined story anchored to runtime-checked evidence |
| UI corroboration of the persisted embeddings row | `console/e2e/observability.spec.ts` | Keeps Observability proof tied to the operator UI instead of prose alone |

## Minimal integrated walkthrough

Use this concise path when you need the full embeddings proof in one sequence:

1. Start from the public `POST /v1/embeddings` path described by [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md).
2. If you are migrating an existing caller, apply the narrow before/after diff in [`docs/embeddings-reference-migration.md`](embeddings-reference-migration.md).
3. Send one real embeddings request and confirm the response body still looks like an OpenAI-like embeddings payload.
4. Record `X-Request-ID` and inspect the `X-Nebula-*` headers on that public response.
5. Query `GET /v1/admin/usage/ledger?request_id=...` for the same request id and confirm the persisted metadata lines up with the public evidence.
6. Confirm the durable row remains metadata-only and does not expose raw embedding inputs or vectors.
7. Use Observability to filter to the `embeddings` route target and inspect the same request as UI corroboration of that persisted row.

That is the narrow integrated adoption proof for embeddings.

## What this walkthrough intentionally does not duplicate

This document should not become a second detailed contract, migration guide, or operator runbook.

It intentionally does not restate:

- the complete `POST /v1/embeddings` request and response semantics already defined in [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md)
- the complete before/after code diff and migration commentary already documented in [`docs/embeddings-reference-migration.md`](embeddings-reference-migration.md)
- the full executable assertions already proven in `tests/test_embeddings_reference_migration.py`
- the complete Observability UI flow already exercised in `console/e2e/observability.spec.ts`
- broader hosted-plane, parity, helper-SDK, or unrelated infrastructure claims outside this embeddings adoption slice

If one of those details changes, update the canonical source rather than copying it here.

## Failure modes this integrated proof makes obvious

This walkthrough is useful because it makes scope drift and proof drift visible.

The integrated proof has failed if any of these become true:

- the public `POST /v1/embeddings` request is no longer the first proof step
- `X-Request-ID` is missing from the joined path
- the public `X-Nebula-*` headers are not treated as the first explainability surface
- `GET /v1/admin/usage/ledger?request_id=...` is omitted, replaced, or no longer lines up with the public request
- Observability is described as more authoritative than the public response plus usage ledger
- the walkthrough starts redefining request semantics instead of delegating them to [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md)
- the walkthrough starts replacing the migration proof instead of delegating the realistic caller diff to [`docs/embeddings-reference-migration.md`](embeddings-reference-migration.md)
- raw embedding inputs, vectors, provider secrets, or hosted-plane expansion appear in the assembled proof artifacts

## Related sources

- [`docs/embeddings-adoption-contract.md`](embeddings-adoption-contract.md) — canonical public embeddings contract
- [`docs/embeddings-reference-migration.md`](embeddings-reference-migration.md) — canonical migration proof for an existing caller
- `tests/test_embeddings_reference_migration.py` — executable public-to-ledger proof source
- `console/e2e/observability.spec.ts` — Observability corroboration proof
