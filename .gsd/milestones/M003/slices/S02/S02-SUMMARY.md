# Slice Summary — M003/S02: Canonical embeddings contract docs

## Outcome
S02 is complete. The slice established `docs/embeddings-adoption-contract.md` as the single canonical public contract for Nebula's narrow `POST /v1/embeddings` adoption surface and verified that repository entry docs now route readers to that file instead of creating competing sources of truth.

This slice delivered the documentation boundary required by R021 without widening the embeddings promise beyond the S01 runtime truth. The canonical doc now defines the supported request shape, `X-Nebula-API-Key` auth contract, success response shape, immediate response evidence headers, metadata-only usage-ledger correlation path, failure semantics, and explicit unsupported or deferred edges.

## What shipped
- Added and verified `docs/embeddings-adoption-contract.md` as the only detailed embeddings compatibility contract.
- Confirmed the doc is grounded in the real S01 route and focused tests rather than by analogy to chat completions.
- Updated discoverability surfaces so readers can find the contract from:
  - `README.md`
  - `docs/architecture.md`
- Preserved the narrow milestone boundary by documenting explicit exclusions such as bearer auth, `encoding_format`, alternate encodings, broader parity claims, and raw input/vector persistence.
- Confirmed the doc names the inspectable evidence surface for embeddings adoption:
  - `X-Request-ID`
  - `X-Nebula-Tenant-ID`
  - `X-Nebula-Route-Target`
  - `X-Nebula-Route-Reason`
  - `X-Nebula-Provider`
  - `X-Nebula-Cache-Hit`
  - `X-Nebula-Fallback-Used`
  - `X-Nebula-Policy-Mode`
  - `X-Nebula-Policy-Outcome`
  - `GET /v1/admin/usage/ledger?request_id=...`

## Verification run
All slice-plan verification checks passed in the assembled worktree.

### Focused runtime/documentation checks
- `/.venv/bin/python -m pytest tests/test_embeddings_api.py` → passed (`4 passed`)
- `/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` → passed (`1 passed`)
- `/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding` → passed (`6 passed`)
- `test -f docs/embeddings-adoption-contract.md && ! grep -q "TBD\|TODO" ... && [ "$(rg -c "^## " ...)" -ge 6 ]` → passed
- `rg -n "embeddings-adoption-contract|POST /v1/embeddings" README.md docs/architecture.md docs/embeddings-adoption-contract.md` → passed
- `rg -n "embeddings_validation_error|embeddings_upstream_error|embeddings_empty_result|X-Request-ID|/v1/admin/usage/ledger" src/nebula/api/routes/embeddings.py tests/test_embeddings_api.py tests/test_governance_api.py tests/test_service_flows.py docs/embeddings-adoption-contract.md` → passed

## Runtime-truth alignment confirmed
The canonical doc matches the assembled runtime/test boundary:
- request shape stays narrow: `model` plus `input` as string or flat list of strings
- auth stays on `X-Nebula-API-Key`
- success response stays OpenAI-like with float-vector `data` entries
- evidence is immediate via `X-Request-ID` and `X-Nebula-*` headers, then durable via metadata-only usage-ledger lookup
- failure classes remain explicit and inspectable:
  - request-shape validation → `422`
  - embeddings validation error → `422`
  - upstream or empty-result failures → `502`
  - missing/invalid API key → `401`
- the durable evidence story remains redacted: no raw embedding inputs or vectors are promised in ledger/admin evidence

## Patterns established
- Treat `docs/embeddings-adoption-contract.md` as the sole detailed public embeddings boundary, mirroring the earlier chat-contract pattern but without reusing wording by assumption.
- Derive each contract statement from route code and focused tests, especially for headers, ledger semantics, and unsupported shapes.
- Keep entry docs pointer-only: use README and architecture docs for discoverability and endpoint inventory, not as secondary contract documents.
- Preserve milestone guardrails by naming unsupported and deferred edges explicitly instead of implying future parity.

## Requirement impact
- **R021** moved from `active` to `validated`.
  - Proof now includes the canonical doc, entry-doc discoverability, and passing focused coverage against the runtime path.
- **R024** was preserved, but not yet fully validated here; this slice supports the guardrail by documenting only the narrow embeddings boundary.

## Decisions and knowledge captured
- Added decision **D018**: make `docs/embeddings-adoption-contract.md` the single canonical public embeddings contract and keep README/architecture pointer-only.
- Added knowledge entry: embeddings docs composition should keep the contract centralized in `docs/embeddings-adoption-contract.md` and avoid duplicating detailed request/response/header/failure semantics elsewhere.

## What the next slices should know
### For S03
- Reuse the vocabulary from the canonical contract exactly: `X-Nebula-API-Key`, `POST /v1/embeddings`, `X-Request-ID`, and metadata-only ledger correlation.
- Do not introduce migration guidance that implies unsupported options like bearer auth, `encoding_format`, or alternate encodings.
- Minimal-change proof should treat this document as the contract source and should not expand the caller diff beyond what the doc names.

### For S04
- The evidence story is already defined narrowly: response headers first, then `GET /v1/admin/usage/ledger?request_id=...`.
- Preserve the redaction boundary: backend/operator proof is metadata-only.
- Failure correlation should use the existing route-reason vocabulary already documented here (`embeddings_validation_error`, `embeddings_upstream_error`, `embeddings_empty_result`).

## Slice assessment
S02 closed the contract-sprawl risk for M003. Nebula now has one inspectable, discoverable, test-backed embeddings boundary document that explains both what is supported and what is intentionally out of scope, without creating a broader parity promise.