# S03 Research — Realistic migration proof

## Summary
- Active requirement owned here: **R022**. Supporting guardrail: **R024**.
- This slice is **targeted/light research**, not deep architecture work. The repo already has a proven migration pattern for chat in `docs/reference-migration.md` + `tests/test_reference_migration.py`; S03 should replicate that pattern for embeddings rather than inventing a new proof shape.
- The natural deliverables are:
  1. a new canonical migration doc for embeddings (likely parallel to `docs/reference-migration.md`), and
  2. an executable proof test (likely parallel to `tests/test_reference_migration.py`) that validates minimal caller diff + public response + `X-Request-ID` to usage-ledger correlation.
- The highest-risk mistake is not runtime wiring; it is **scope drift**: accidentally implying bearer auth, broader OpenAI embeddings parity, extra params like `encoding_format`, or a helper/SDK requirement. S02 already established the contract boundary in `docs/embeddings-adoption-contract.md`; S03 must stay inside it.

## Recommendation
- Follow the existing **chat migration proof pattern** exactly where it maps:
  - canonical prose doc anchored to an executable test
  - before/after code sample using the OpenAI Python client
  - minimal diff limited to `base_url`, `default_headers`, and the model value
  - proof sequence: successful public request first, then inspect response shape + `X-Request-ID` / `X-Nebula-*`, then correlate in `GET /v1/admin/usage/ledger?request_id=...`
- Do **not** introduce Playground or Observability into the embeddings migration proof. Per D016 and the knowledge base, S03 should prove the public caller swap; broader operator corroboration belongs later.
- Prefer a new test file focused only on embeddings migration proof rather than expanding `tests/test_reference_migration.py` if you want clean seams. If the planner prefers one canonical proof-family file, the alternative is adding embeddings cases into that existing file, but a separate file is cleaner and more slice-local.

## Implementation Landscape

### Files that already define the truth boundary
- `docs/embeddings-adoption-contract.md`
  - Canonical public embeddings boundary from S02.
  - Names the supported request shape (`model` + `input`), auth (`X-Nebula-API-Key`), success shape, `X-Request-ID`/`X-Nebula-*` evidence, ledger correlation, and explicit exclusions.
  - S03 migration wording must defer to this doc for contract details instead of restating broader semantics.
- `src/nebula/api/routes/embeddings.py`
  - Public route implementation.
  - Response headers on success are hard-coded and important for proof:
    - `X-Nebula-Tenant-ID`
    - `X-Nebula-Route-Target = embeddings`
    - `X-Nebula-Route-Reason = embeddings_direct`
    - `X-Nebula-Provider = ollama`
    - `X-Nebula-Cache-Hit = false`
    - `X-Nebula-Fallback-Used = false`
    - `X-Nebula-Policy-Mode = embeddings_direct`
    - `X-Nebula-Policy-Outcome = embeddings=completed`
  - Also records usage-ledger rows with:
    - `final_route_target = "embeddings"`
    - `final_provider = "ollama"`
    - `route_reason = "embeddings_direct"` on success
    - metadata-only persistence
- `src/nebula/models/openai.py`
  - Defines the narrow request/response schema for the public embeddings contract.
  - `EmbeddingsRequest` forbids extra fields and only allows `str | list[str]` input, flat list only.
  - `EmbeddingsResponse` currently returns:
    - `object = "list"`
    - `data[]` items with `object = "embedding"`, `index`, `embedding: list[float]`
    - `usage = {prompt_tokens: 0, total_tokens: 0}`
  - Important: there is **no** `completion_tokens` field in embeddings usage.
- `src/nebula/services/embeddings_service.py`
  - For migration-proof realism, this confirms the service forwards the requested model and preserves batch ordering.
  - Errors are explicit (`EmbeddingsValidationError`, `EmbeddingsUpstreamError`, `EmbeddingsEmptyResultError`), but S03 should focus primarily on happy-path migration proof.

### Existing migration-proof pattern to copy
- `docs/reference-migration.md`
  - This is the exact template for slice structure and tone.
  - Key sections worth mirroring:
    - “What this migration proves”
    - “Before” / “After” / “Before-after diff”
    - “What stayed the same”
    - “How to confirm the migration worked”
    - “Minimal verification path”
    - “What not to use as migration proof”
  - The embeddings version should likely keep the same structure, but adjust proof specifics to embeddings response shape and avoid chat-only claims.
- `tests/test_reference_migration.py`
  - Canonical executable proof source for the chat migration doc.
  - Pattern established here:
    1. mount stubbed runtime
    2. send one public request using the realistic migration payload
    3. capture `X-Request-ID`
    4. fetch `/v1/admin/usage/ledger?request_id=...`
    5. assert public response shape and headers
    6. assert ledger row matches public evidence
  - There is also a second test covering the special tenant-header rule for ambiguous multi-tenant keys. For embeddings, this may be optional unless the slice explicitly wants to prove tenant-header behavior for this route too.

### Existing embeddings tests that reduce uncertainty
- `tests/test_embeddings_api.py`
  - Already proves authenticated single and batch success responses.
  - Already proves response body shape, request-id presence, auth reuse, unsupported-shape rejection, and upstream-failure mapping.
  - Good source for exact response JSON expectations.
- `tests/test_governance_api.py` (function `test_embeddings_requests_can_be_correlated_through_usage_ledger`)
  - Already proves the durable evidence path:
    - public `/v1/embeddings` request
    - `X-Request-ID`
    - ledger lookup by request id
    - metadata-only boundary (`input` and `embedding` absent from ledger row)
  - This is the strongest building block for S03’s executable migration proof.
- `tests/support.py`
  - `configured_app()`, `auth_headers()`, `admin_headers()` are the standard testing harness.
  - `configured_app()` creates a migrated test DB and app instance; use this instead of building custom fixtures.

## Natural seams for the planner

### Seam 1: executable proof first
Build the test before or alongside the doc. It is the authoritative source for the migration guide, and it will force exact decisions about:
- which realistic caller shape to use
- which headers to assert
- which ledger fields must align
- whether tenant-header edge cases are in or out for this slice

Most likely file choices:
- new file: `tests/test_embeddings_reference_migration.py` (cleanest seam)
- alternative: extend `tests/test_reference_migration.py` with embeddings-specific tests (less clean because the existing file is very chat- and Playground-specific)

### Seam 2: canonical prose doc derived from test
After the test exists, author a dedicated migration doc, likely one of:
- `docs/embeddings-reference-migration.md` (most symmetric with `docs/reference-migration.md`)
- less ideal: append migration content to `docs/embeddings-adoption-contract.md` (not recommended because D018/S02 require that file to remain the canonical contract, not a mixed contract + migration guide)

The doc should explicitly say its source of truth is the new test file, the same way `docs/reference-migration.md` points to `tests/test_reference_migration.py`.

### Seam 3: discoverability / cross-links (optional but likely needed)
If a new doc is added, expect at least lightweight cross-links from:
- `docs/embeddings-adoption-contract.md` → migration proof doc
- possibly `README.md` or another docs index if S03 wants discoverability parity

Keep this pointer-only. Do not create a second contract narrative.

## What to build or prove first
1. **Realistic caller target and diff**
   - Prove that a common OpenAI-style embeddings caller can target Nebula with minimal changes.
   - The believable example is almost certainly the OpenAI Python SDK embeddings client, analogous to the chat proof:
     ```python
     from openai import OpenAI
     client = OpenAI(...)
     response = client.embeddings.create(...)
     ```
   - The proof should keep request-body shape OpenAI-like within Nebula’s narrow supported boundary: `model` + string or flat list-of-strings `input`.
2. **Public evidence path**
   - Assert that the migrated request returns the OpenAI-like embeddings body and `X-Request-ID`/`X-Nebula-*` headers.
3. **Durable evidence path**
   - Assert `GET /v1/admin/usage/ledger?request_id=...` matches the public request on at least: `request_id`, `tenant_id`, `requested_model`, `final_route_target`, `final_provider`, `terminal_status`, `route_reason`, `policy_outcome`.
   - Also assert raw `input` and vectors are absent from persisted evidence, because that is part of the credibility boundary from S01/S02.

## Specific implementation constraints
- Keep the proof inside the S02 contract:
  - auth must be `X-Nebula-API-Key`, not bearer auth
  - no `encoding_format`
  - no alternate encodings
  - no token-array inputs
  - no nested input arrays
- Keep the migration “minimal change” claim honest:
  - base URL changes to Nebula `/v1`
  - provider API key arg becomes unused placeholder for SDK construction if needed
  - `default_headers={"X-Nebula-API-Key": ...}` is the real auth mechanism
  - body shape stays embeddings-like
- Do not over-claim model portability.
  - The route forwards the requested `model`, but S03 should not imply broad provider alias compatibility beyond the tested example.
  - A realistic example can use `nomic-embed-text` because it already matches the route/service/tests.
- Keep the proof backend-first.
  - The knowledge base says embeddings adoption proof should reuse the usage ledger and avoid new helper layers or console-first proof machinery.

## Likely shape of the new executable proof
A strong happy-path test would look like this:
- create app with `configured_app()`
- replace `app.state.container.embeddings_service.create_embeddings` with a deterministic stub that returns 1 or 2 vectors
- `POST /v1/embeddings` with `headers={"X-Nebula-API-Key": "nebula-dev-key"}` and a realistic body
- capture `request_id = response.headers["X-Request-ID"]`
- `GET /v1/admin/usage/ledger?request_id={request_id}` with admin headers
- assert:
  - `response.status_code == 200`
  - body object is `list`
  - `data[0].object == "embedding"`
  - returned `model` equals requested/stubbed model
  - usage fields are zeroed as currently implemented
  - headers match the embeddings route constants
  - ledger row count is 1
  - ledger fields line up with public headers
  - `input` and `embedding` are absent from ledger row

Optional second test if planner wants stronger realism:
- batch input preserves order and still correlates through ledger

Less necessary for this slice:
- upstream failure proof (already covered in S01)
- tenant ambiguity / `X-Nebula-Tenant-ID` edge case unless the planner wants direct symmetry with chat migration guidance

## Verification plan
Focused checks that should confirm S03 without reopening unrelated areas:
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`
  - or the exact target file if added elsewhere
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings`
- optional broader confidence check:
  - `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding`
- doc integrity / discoverability greps once a new migration doc exists:
  - `rg -n "embeddings.*migration|OpenAI|X-Request-ID|/v1/admin/usage/ledger" docs/<new-doc>.md`
  - `rg -n "embeddings-reference-migration|reference migration|migration proof" docs/embeddings-adoption-contract.md README.md docs/architecture.md docs/*.md`

## Skill-relevant guidance
- Installed skills already relevant:
  - `test` — useful if the executor wants help generating/refining the new pytest coverage.
- Relevant skill rules from the prompt:
  - use the existing testing pattern rather than hand-rolled app setup (`tests/support.py` already provides the seam)
  - for React/console skills: not relevant here; this slice should avoid console expansion
  - for browser/agent-browser: not relevant unless someone later wants manual UAT, which is outside this research slice
- Suggested external skills not installed (do not install automatically):
  - `jezweb/claude-skills@fastapi` — high install count; relevant if future work needs more FastAPI-specific route/test patterns
  - `bobmatnyc/claude-mpm-skills@pytest` — useful for pytest-heavy refinement
  - `diskd-ai/openai-api@openai-api` — somewhat relevant for SDK/request-shape semantics, but lower confidence because this slice already has enough in-repo prior art

## Sources
- `docs/reference-migration.md`
- `tests/test_reference_migration.py`
- `docs/embeddings-adoption-contract.md`
- `src/nebula/api/routes/embeddings.py`
- `src/nebula/models/openai.py`
- `src/nebula/services/embeddings_service.py`
- `tests/test_embeddings_api.py`
- `tests/test_governance_api.py`
- `tests/support.py`
- `README.md`
