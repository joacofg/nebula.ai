# S03: Realistic migration proof

**Goal:** Prove that a believable OpenAI-style embeddings caller can switch from a direct provider path to Nebula's public `POST /v1/embeddings` route with only minimal caller changes while staying inside the narrow contract documented in `docs/embeddings-adoption-contract.md`.
**Demo:** A reader can compare a direct-provider embeddings caller with a Nebula-targeted version, run the executable proof in `tests/test_embeddings_reference_migration.py`, and see the same request succeed through `POST /v1/embeddings`, return an OpenAI-like embeddings body plus `X-Request-ID` / `X-Nebula-*` headers, and correlate to a metadata-only usage-ledger row through `GET /v1/admin/usage/ledger?request_id=...`.

## Must-Haves

- `tests/test_embeddings_reference_migration.py` proves a realistic minimal-change embeddings caller swap against the real public `POST /v1/embeddings` path.
- The proof asserts both application-facing success shape and durable backend evidence: response body, `X-Request-ID`, `X-Nebula-*` headers, and matching usage-ledger correlation.
- The migration proof stays inside the S02 contract: `X-Nebula-API-Key` auth, `model` plus string-or-flat-list `input`, no bearer-auth claim, no `encoding_format`, no broader embeddings-parity implication.
- A canonical migration guide under `docs/` mirrors the existing reference-migration pattern, points to the executable proof as source of truth, and shows the honest before/after caller diff.
- Discoverability/cross-links keep `docs/embeddings-adoption-contract.md` as the canonical contract and present the migration guide as proof of minimal caller change rather than a second contract document.
- The slice directly advances active requirement `R022` and supports `R024` by proving adoption without helper stacks, SDK sprawl, console-first proof, or broader parity work.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py -k upstream_failures`
- `test -f docs/embeddings-reference-migration.md && ! grep -q "TBD\|TODO" docs/embeddings-reference-migration.md && [ "$(rg -c "^## " docs/embeddings-reference-migration.md)" -ge 6 ]`
- `rg -n "tests/test_embeddings_reference_migration.py|X-Nebula-API-Key|X-Request-ID|/v1/admin/usage/ledger|What this migration proves|What not to use as migration proof" docs/embeddings-reference-migration.md`
- `rg -n "embeddings-reference-migration" docs/embeddings-adoption-contract.md README.md docs/architecture.md docs/*.md`

## Observability / Diagnostics

- Runtime signals: successful migration-proof requests must emit `X-Request-ID` plus `X-Nebula-Tenant-ID`, `X-Nebula-Route-Target`, `X-Nebula-Route-Reason`, `X-Nebula-Provider`, `X-Nebula-Cache-Hit`, `X-Nebula-Fallback-Used`, `X-Nebula-Policy-Mode`, and `X-Nebula-Policy-Outcome` on the public `/v1/embeddings` response.
- Inspection surfaces: the executable proof and migration guide must both use `GET /v1/admin/usage/ledger?request_id=...` as the durable backend inspection path keyed by the public `X-Request-ID`.
- Failure visibility: the proof should keep failure diagnosis localizable by asserting the exact route/evidence fields for the happy path and preserving the metadata-only ledger boundary so later slices can inspect mismatches without needing raw payload persistence.
- Redaction constraints: neither the proof nor the guide should imply that ledger/admin evidence stores raw `input` text or returned embedding vectors.

## Integration Closure

- Upstream surfaces consumed: `src/nebula/api/routes/embeddings.py`, `src/nebula/models/openai.py`, `src/nebula/services/embeddings_service.py`, `docs/embeddings-adoption-contract.md`, `docs/reference-migration.md`, `tests/test_governance_api.py`, `tests/test_embeddings_api.py`, `tests/support.py`
- New wiring introduced in this slice: a new executable migration-proof test and a dedicated embeddings migration guide wired back to the canonical contract doc
- What remains before the milestone is truly usable end-to-end: S04 still needs to expand the same request into a broader durable evidence explanation, and S05 must assemble contract, migration, and evidence into one final adoption package

## Tasks

- [x] **T01: Add executable embeddings migration proof coverage** `est:55m`
  - Why: R022 closes only if the believable caller swap is executable, not just described; the test must lock the exact minimal-change path and public-to-ledger evidence story before prose is written.
  - Files: `tests/test_embeddings_reference_migration.py`, `tests/test_governance_api.py`, `tests/support.py`, `src/nebula/api/routes/embeddings.py`, `src/nebula/models/openai.py`, `src/nebula/services/embeddings_service.py`
  - Do: Create a dedicated embeddings migration proof test file that mirrors the existing chat reference-migration pattern without bringing in Playground or console flows; use `configured_app()` and a deterministic embeddings-service stub, send an authenticated public `/v1/embeddings` request with a realistic OpenAI-style body, capture `X-Request-ID`, query `/v1/admin/usage/ledger?request_id=...`, and assert the public body, `X-Nebula-*` headers, ledger metadata, and metadata-only redaction boundary all agree; keep the request/example inside the canonical embeddings contract and avoid unsupported options or helper abstractions.
  - Verify: `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`
  - Done when: the new test file passes and proves that an OpenAI-style embeddings caller can hit Nebula's public route with only the documented auth/base-URL changes while producing correlatable public and ledger evidence.
- [x] **T02: Publish the embeddings migration guide and wire discoverability** `est:40m`
  - Why: The migration proof only helps adoption if humans can find and trust it; the guide must be derived from the executable proof and clearly separated from the canonical contract doc.
  - Files: `docs/embeddings-reference-migration.md`, `docs/embeddings-adoption-contract.md`, `README.md`, `docs/architecture.md`, `tests/test_embeddings_reference_migration.py`, `docs/reference-migration.md`
  - Do: Write `docs/embeddings-reference-migration.md` using the existing reference-migration doc structure, but scoped to embeddings: explain what the migration proves, show before/after and diff using the OpenAI Python client, keep the auth/body examples inside the narrow contract, document how to confirm success via `X-Request-ID` / `X-Nebula-*` and the usage ledger, and explicitly say what does not count as migration proof; then add pointer-only cross-links from `docs/embeddings-adoption-contract.md` and the repo entry docs so readers can discover the new guide without creating a second contract source.
  - Verify: `test -f docs/embeddings-reference-migration.md && ! grep -q "TBD\|TODO" docs/embeddings-reference-migration.md && [ "$(rg -c "^## " docs/embeddings-reference-migration.md)" -ge 6 ] && rg -n "tests/test_embeddings_reference_migration.py|X-Nebula-API-Key|X-Request-ID|/v1/admin/usage/ledger|What this migration proves|What not to use as migration proof" docs/embeddings-reference-migration.md && rg -n "embeddings-reference-migration" docs/embeddings-adoption-contract.md README.md docs/architecture.md docs/*.md`
  - Done when: the guide exists as the human-readable migration proof, names the executable test as source of truth, and all discoverability edits keep `docs/embeddings-adoption-contract.md` as the canonical embeddings contract while exposing the new migration proof.

## Files Likely Touched

- `tests/test_embeddings_reference_migration.py`
- `docs/embeddings-reference-migration.md`
- `docs/embeddings-adoption-contract.md`
- `README.md`
- `docs/architecture.md`
