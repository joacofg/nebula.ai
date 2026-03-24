# S02: Canonical embeddings contract docs

**Goal:** Publish one canonical embeddings adoption contract doc that defines the real `POST /v1/embeddings` boundary, supported behavior, and explicit exclusions without creating duplicate or broader parity promises elsewhere.
**Demo:** A reader can find `docs/embeddings-adoption-contract.md` from repo entry docs, see the test-backed supported request/response and evidence contract for embeddings, and verify that the linked docs point back to the canonical file instead of restating drifting details.

## Must-Haves

- One canonical public embeddings contract doc exists under `docs/` and is grounded in S01 runtime/test truth.
- The canonical doc names the supported request shape, auth contract, response shape, response headers/evidence, failure semantics, and explicit unsupported/deferred edges.
- `README.md` and `docs/architecture.md` link to the canonical embeddings contract for discoverability without duplicating the detailed contract inline.
- The verification path proves both runtime-truth alignment and doc discoverability.
- The slice advances active requirement `R021` directly and preserves the milestone guardrail from `R024` by documenting a narrow boundary only.

## Proof Level

- This slice proves: contract
- Real runtime required: no
- Human/UAT required: yes

## Verification

- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding`
- `test -f docs/embeddings-adoption-contract.md && ! grep -q "TBD\|TODO" docs/embeddings-adoption-contract.md && [ "$(rg -c "^## " docs/embeddings-adoption-contract.md)" -ge 6 ]`
- `rg -n "embeddings-adoption-contract|POST /v1/embeddings" README.md docs/architecture.md docs/embeddings-adoption-contract.md`
- `rg -n "embeddings_validation_error|embeddings_upstream_error|embeddings_empty_result|X-Request-ID|/v1/admin/usage/ledger" src/nebula/api/routes/embeddings.py tests/test_embeddings_api.py tests/test_governance_api.py tests/test_service_flows.py docs/embeddings-adoption-contract.md`

## Observability / Diagnostics

- Public success responses on `POST /v1/embeddings` emit `X-Request-ID` plus `X-Nebula-Tenant-ID`, `X-Nebula-Route-Target`, `X-Nebula-Route-Reason`, `X-Nebula-Provider`, `X-Nebula-Cache-Hit`, `X-Nebula-Fallback-Used`, `X-Nebula-Policy-Mode`, and `X-Nebula-Policy-Outcome`; the canonical doc must name these as the inspectable runtime evidence surface.
- Every embeddings request records a usage-ledger row keyed by `request_id`, with metadata-only fields such as tenant, requested model, final route target/provider, route reason, terminal status, and policy outcome; the doc must explain that `/v1/admin/usage/ledger` is the durable operator lookup path without implying prompt or vector capture.
- Failure visibility must stay inspectable: request-shape rejections surface FastAPI/Pydantic `422` validation output, while provider failures map to `422` or `502` with route-specific ledger `terminal_status` / `route_reason` values like `provider_error`, `embeddings_validation_error`, `embeddings_upstream_error`, and `embeddings_empty_result`.
- Redaction boundary: no raw embedding inputs or returned vectors are promised in ledger/admin evidence; only request metadata and correlation identifiers are documented.

## Integration Closure

- Upstream surfaces consumed: `src/nebula/api/routes/embeddings.py`, `src/nebula/models/openai.py`, `tests/test_embeddings_api.py`, `tests/test_governance_api.py`, `tests/test_service_flows.py`, `docs/adoption-api-contract.md`
- New wiring introduced in this slice: repository entry docs point readers to `docs/embeddings-adoption-contract.md` as the single detailed embeddings boundary
- What remains before the milestone is truly usable end-to-end: S03 still needs a realistic caller migration proof built on this vocabulary, and S04 still needs the durable evidence story assembled around the same request path

## Tasks

- [x] **T01: Author the canonical embeddings contract document** `est:45m`
  - Why: R021 is primarily a documentation boundary requirement, so the slice closes only when a single canonical file states the supported embeddings contract and exclusions from runtime truth.
  - Files: `docs/embeddings-adoption-contract.md`, `docs/adoption-api-contract.md`, `src/nebula/api/routes/embeddings.py`, `src/nebula/models/openai.py`, `tests/test_embeddings_api.py`, `tests/test_governance_api.py`, `tests/test_service_flows.py`
  - Do: Write `docs/embeddings-adoption-contract.md` using the chat contract doc as the structural pattern; document only the S01-proven embeddings scope, auth, request shape, response shape, response headers, evidence correlation, failure semantics, and explicit unsupported/deferred claims; include a local verification section that points to the focused embeddings tests and doc checks; keep wording narrow so the doc does not imply broader OpenAI embeddings parity.
  - Verify: `test -f docs/embeddings-adoption-contract.md && ! grep -q "TBD\|TODO" docs/embeddings-adoption-contract.md && [ "$(rg -c "^## " docs/embeddings-adoption-contract.md)" -ge 6 ] && rg -n "X-Nebula-API-Key|X-Request-ID|unsupported|deferred|/v1/admin/usage/ledger" docs/embeddings-adoption-contract.md`
  - Done when: `docs/embeddings-adoption-contract.md` is the only detailed embeddings contract file, it cites the runtime/test-backed boundary accurately, and it explicitly names both supported behavior and exclusions.
- [ ] **T02: Link entry docs back to the canonical embeddings contract** `est:25m`
  - Why: The contract only stays canonical if readers can discover it from the repo entry points without those entry docs becoming competing sources of truth.
  - Files: `README.md`, `docs/architecture.md`, `docs/embeddings-adoption-contract.md`
  - Do: Update `README.md` and `docs/architecture.md` to mention the narrow public embeddings surface and link to `docs/embeddings-adoption-contract.md`; keep these edits pointer-only by adding discoverability and endpoint inventory references rather than duplicating request/response details from the canonical doc.
  - Verify: `rg -n "embeddings-adoption-contract|POST /v1/embeddings" README.md docs/architecture.md docs/embeddings-adoption-contract.md`
  - Done when: both entry docs clearly point readers to `docs/embeddings-adoption-contract.md` and neither file restates the embeddings contract in enough detail to become a second source of truth.

## Files Likely Touched

- `docs/embeddings-adoption-contract.md`
- `README.md`
- `docs/architecture.md`
