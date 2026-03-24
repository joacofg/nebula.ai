# S02: Canonical embeddings contract docs — Research

**Date:** 2026-03-23

## Summary

S02 primarily owns **R021** and supports the milestone guardrail **R024**. This is light research: the runtime contract already exists from S01, and the main work is to document that narrow embeddings boundary canonically without creating a second source of truth or accidentally implying broader parity.

The existing documentation pattern is already established in the repo: `docs/adoption-api-contract.md` is the single canonical public contract for chat, while `docs/quickstart.md`, `docs/reference-migration.md`, `docs/day-1-value.md`, and `docs/integrated-adoption-proof.md` link back to that contract instead of restating it. S02 should follow that same rule for embeddings: add one canonical embeddings contract doc under `docs/`, ground every supported claim in S01 tests/runtime behavior, and then add only lightweight entry-point links elsewhere. Per loaded project knowledge, this avoids contract drift and preserves the “one canonical boundary” rule.

The runtime truth to document is narrow and already test-backed: `POST /v1/embeddings` with `X-Nebula-API-Key`, request body `model` + `input`, where `input` is either a single non-blank string or a flat non-empty list of non-blank strings; extra fields are forbidden; the response is an OpenAI-style embeddings payload with `object: "list"`, ordered `data[]`, float vectors, and `usage` limited to `prompt_tokens` and `total_tokens` at `0` today. The route also emits `X-Request-ID` plus `X-Nebula-*` metadata and records metadata-only usage-ledger evidence keyed by request ID. Unsupported/deferred edges should be stated explicitly, especially broader OpenAI embeddings options.

## Recommendation

Create a new canonical doc, likely `docs/embeddings-adoption-contract.md`, modeled closely on `docs/adoption-api-contract.md`.

Recommended approach:
- Make the new embeddings doc the **only** canonical public compatibility boundary for `POST /v1/embeddings`.
- State up front that tests and runtime behavior are authoritative, using S01 coverage as the backing proof.
- Document only what S01 actually proves: auth shape, request shape, response shape, response headers/evidence, failure semantics, and explicit unsupported/deferred claims.
- Update entry docs (`README.md` and `docs/architecture.md`) to reference the embeddings contract briefly, but do not duplicate request/response details there.

This aligns with the repo’s established doc composition rule and the loaded `accessibility`/`best-practices`-adjacent instruction to prefer clear explicit boundaries over ambiguous prose. More importantly, it satisfies **R021** without violating **R024**: the slice should document a narrow boundary, not expand capability.

## Implementation Landscape

### Key Files

- `docs/adoption-api-contract.md` — Existing canonical contract pattern for chat. This is the closest template for structure, tone, and “tests are authoritative” wording. Reuse its composition strategy, not its chat-specific content.
- `src/nebula/api/routes/embeddings.py` — Runtime truth for headers, status mapping, route reason strings, provider name, and ledger recording behavior. Supported claims in the new doc should be derived from this file.
- `src/nebula/models/openai.py` — Source of truth for request/response schema details:
  - `EmbeddingsRequest` forbids extra fields and only accepts `model` + `input`
  - `input` supports string or flat list of strings only
  - blank model/input values are rejected
  - `EmbeddingsResponse` returns `object`, `data`, `model`, and `usage`
- `tests/test_embeddings_api.py` — Primary contract proof for public happy path, auth reuse, unsupported shape rejection, and upstream failure mapping.
- `tests/test_governance_api.py` (`test_embeddings_requests_can_be_correlated_through_usage_ledger`) — Proof for `X-Request-ID` → usage-ledger correlation and the metadata-only evidence constraint.
- `tests/test_service_flows.py` — Proof for low-level request-shape validation and service invariants like batch ordering, blank-input rejection, upstream failure, and empty-result handling.
- `README.md` — Documentation map and selected endpoints. Should link to the embeddings contract doc and may add `POST /v1/embeddings` to the public endpoint inventory.
- `docs/architecture.md` — High-level request-flow/runtime-components doc. Should mention embeddings as an additional narrow public surface and point to the canonical embeddings contract doc rather than restating details.
- `docs/quickstart.md` / `docs/reference-migration.md` — Likely downstream consumers, but for S02 keep edits minimal: only add links if needed. Do not expand them into canonical embeddings references unless the planner decides a tiny cross-link is necessary for discoverability.

### Runtime facts the doc can safely claim

From `src/nebula/api/routes/embeddings.py` and tests:
- Public path: `POST /v1/embeddings`
- Auth: `X-Nebula-API-Key`
- Existing public auth contract is reused; missing/invalid key returns `401`
- Response emits:
  - `X-Request-ID`
  - `X-Nebula-Tenant-ID`
  - `X-Nebula-Route-Target: embeddings`
  - `X-Nebula-Route-Reason: embeddings_direct`
  - `X-Nebula-Provider: ollama`
  - `X-Nebula-Cache-Hit: false`
  - `X-Nebula-Fallback-Used: false`
  - `X-Nebula-Policy-Mode: embeddings_direct`
  - `X-Nebula-Policy-Outcome: embeddings=completed`
- Success response shape:
  - top-level `object: "list"`
  - `data[]` entries with `object: "embedding"`, `index`, and float `embedding`
  - response `model`
  - `usage` containing `prompt_tokens` and `total_tokens` only
- Supported input shapes:
  - single string
  - flat list of strings
- Explicitly rejected today:
  - blank model
  - blank string input
  - empty input list
  - nested lists
  - non-string entries
  - extra request fields such as `encoding_format`
- Failure semantics proven today:
  - `401` for missing/invalid public auth
  - `422` for unsupported request shape before runtime
  - `502` for upstream provider failure
- Durable evidence:
  - same request correlates through `/v1/admin/usage/ledger?request_id=...`
  - ledger row includes metadata like `final_route_target`, `final_provider`, `terminal_status`, `route_reason`, `policy_outcome`
  - raw `input` and vectors are intentionally not persisted

### Explicit exclusions to document

The doc should explicitly mark these as unsupported/deferred unless S01 proves otherwise:
- broad OpenAI embeddings parity
- OpenAI bearer auth on the public path
- extra embeddings request options such as `encoding_format`, `dimensions`, or `user`
- nested token-array inputs or other non-string input forms
- claims about non-zero token accounting in embeddings `usage`
- claims about alternative providers, fallback behavior, streaming, or cache behavior on the embeddings route
- claims that admin Playground is an embeddings adoption path (it is chat-only/operator-only in current docs/tests)

### Build Order

1. **Draft the canonical embeddings contract doc first** using `docs/adoption-api-contract.md` as the pattern.
   - This is the slice’s primary deliverable and directly satisfies R021.
   - Build it from the test-backed truth in `tests/test_embeddings_api.py`, `tests/test_governance_api.py`, `tests/test_service_flows.py`, and the route/schema files.
2. **Add repository-level discoverability links** after the canonical doc exists.
   - Minimal likely edits: `README.md`, `docs/architecture.md`.
   - If adding links elsewhere, keep them pointer-only.
3. **Run focused verification** to prove prose still matches runtime truth.
   - Prefer existing embeddings tests plus a simple grep/read check that the new doc is linked from entry docs.

### Verification

Focused runtime/contract verification:
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding`

Doc-alignment checks:
- verify the new canonical file exists under `docs/`
- verify it has substantive sections analogous to the chat contract doc (scope, request contract, auth, response behavior, headers/evidence, failures, unsupported/deferred claims, local verification)
- `rg -n "embeddings-adoption-contract|/v1/embeddings" README.md docs/architecture.md docs/*.md`
- confirm README and architecture point to the canonical embeddings doc rather than restating the request/response contract inline

### Natural seams

- **Doc authoring task:** create the canonical embeddings contract file from runtime/test truth.
- **Doc-linking task:** update README and architecture for discoverability.
- These are low-risk and mostly independent once the canonical filename is chosen.

### Skills

Installed skills directly relevant to this slice:
- `best-practices` — relevant for keeping doc scope disciplined and avoiding unsupported claims.

Promising non-installed skills discovered:
- `wshobson/agents@fastapi-templates` — install with `npx skills add wshobson/agents@fastapi-templates`
- `mindrally/skills@fastapi-python` — install with `npx skills add mindrally/skills@fastapi-python`

These are optional only; this slice does not require extra FastAPI skill support because the implementation is documentation-first and the FastAPI route already exists.
