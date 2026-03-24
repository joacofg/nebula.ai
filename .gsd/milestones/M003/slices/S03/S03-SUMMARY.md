# S03 Summary — Realistic migration proof

## Slice Summary

**Slice:** S03 — Realistic migration proof  
**Milestone:** M003 — Broader Adoption Surface  
**Status:** Done  
**Outcome:** Nebula now has a believable, executable embeddings migration proof showing that an existing OpenAI-style embeddings caller can switch from a direct provider path to Nebula's public `POST /v1/embeddings` route with only narrow caller changes, while preserving OpenAI-like response shape and correlating the same request to durable metadata-only usage-ledger evidence.

### What this slice actually delivered

- Added `tests/test_embeddings_reference_migration.py` as the executable source of truth for embeddings adoption proof.
- Locked a realistic minimal-change migration path around:
  - the same OpenAI-style embeddings call shape,
  - Nebula public `POST /v1/embeddings`,
  - `X-Nebula-API-Key` auth,
  - `X-Request-ID` plus `X-Nebula-*` response evidence,
  - `GET /v1/admin/usage/ledger?request_id=...` correlation.
- Proved the public response and the durable backend evidence agree on the same request without persisting raw `input` text or returned embedding vectors.
- Added `docs/embeddings-reference-migration.md` as the human-readable migration guide derived from the executable proof.
- Wired discoverability from `README.md`, `docs/architecture.md`, and `docs/embeddings-adoption-contract.md` while keeping `docs/embeddings-adoption-contract.md` as the only canonical embeddings contract.

### Verification rerun results

All slice-plan verification checks passed in the assembled worktree:

- `python -m pytest tests/test_embeddings_reference_migration.py` ✅
- `python -m pytest tests/test_embeddings_api.py` ✅
- `python -m pytest tests/test_governance_api.py -k embeddings` ✅
- `python -m pytest tests/test_embeddings_api.py -k upstream_failures` ✅
- migration-guide file/content/discoverability checks ✅

### Observability / diagnostics confirmed

The slice plan required verification of the proof surfaces, and they are working as intended:

- public `/v1/embeddings` responses expose `X-Request-ID`
- public responses expose the expected `X-Nebula-*` evidence headers
- `GET /v1/admin/usage/ledger?request_id=...` returns a correlatable metadata-only row
- the migration proof explicitly verifies that raw inputs and embedding vectors do **not** appear in persisted ledger evidence

## What changed

### Executable proof

`tests/test_embeddings_reference_migration.py` now proves the narrow happy path end to end:

- sends an authenticated public embeddings request
- captures `X-Request-ID`
- validates the OpenAI-like embeddings response body
- asserts exact `X-Nebula-*` runtime evidence headers
- queries the usage ledger by `request_id`
- confirms public evidence and persisted metadata agree
- confirms the persistence boundary remains metadata-only

This gives downstream slices a concrete proof artifact rather than prose-only migration guidance.

### Human-readable migration guide

`docs/embeddings-reference-migration.md` now provides:

- a clear statement of what the migration proves
- a realistic before/after using the OpenAI Python client
- an honest minimal diff: base URL + `X-Nebula-API-Key` default header + placeholder SDK api key
- a verification path centered on `X-Request-ID`, `X-Nebula-*`, and usage-ledger correlation
- explicit “what not to use as migration proof” guidance to prevent parity creep and fake proof claims

### Discoverability without contract drift

Entry docs now point readers to the migration guide without duplicating the contract:

- `docs/embeddings-adoption-contract.md` links to the migration guide as subordinate proof
- `README.md` includes the guide in the docs index
- `docs/architecture.md` points to the guide for the minimal-change walkthrough

This preserves the M003 rule that `docs/embeddings-adoption-contract.md` remains the only detailed public embeddings boundary.

## Requirement impact

### R022

R022 is now **validated**.

Evidence:

- executable proof in `tests/test_embeddings_reference_migration.py`
- canonical migration guide in `docs/embeddings-reference-migration.md`
- passing reruns of the slice verification suite
- explicit narrow-scope guardrails in both test and docs

### R024 support

S03 materially strengthens R024 but does not validate it alone.

This slice stayed within scope by:

- reusing the OpenAI-style client pattern instead of introducing helper SDKs
- reusing the existing public route and usage ledger instead of adding new operator stacks
- avoiding bearer-auth claims, unsupported request options, and broader embeddings parity promises
- using pointer-only discoverability edits rather than creating a second contract surface

R024 still depends on S04/S05 for milestone-wide close-out.

## Patterns established for downstream slices

- **Embeddings migration proof pattern:** pair one public `/v1/embeddings` request with exact response-header assertions and request-id usage-ledger correlation.
- **Dual-sided proof rule:** application-facing success is not enough; migration proof must also show durable operator evidence.
- **Metadata-only evidence guardrail:** usage-ledger correlation should expose route/provider/policy outcome details but never raw embeddings inputs or vectors.
- **Docs composition rule:** the migration guide can explain the caller diff and proof steps, but contract semantics still belong only in `docs/embeddings-adoption-contract.md`.

## Gotchas / lessons worth carrying forward

- Do not widen the migration diff beyond the real public contract. The happy path is base URL + `X-Nebula-API-Key`; the proof should not imply bearer auth or unsupported options.
- Do not treat “SDK returned vectors” as sufficient proof. The trustworthy proof boundary is public response evidence plus `request_id` ledger correlation.
- For embeddings adoption, reusing the existing metadata-only ledger is enough to prove durable evidence without adding new persistence surfaces.

## What the next slice should know

S04 can build directly on this slice's proof artifact.

Inputs now available to S04:

- a stable executable migration proof
- a canonical human-readable migration guide
- a concrete request/evidence sequence to expand:
  1. public `POST /v1/embeddings`
  2. `X-Request-ID` and `X-Nebula-*` capture
  3. `GET /v1/admin/usage/ledger?request_id=...`

What remains for S04 is not to re-prove the caller swap, but to deepen the durable evidence explanation around the same request while preserving the metadata-only boundary and avoiding new helper or console-first proof surfaces.

## UAT readiness

This slice is ready for human evaluation. A reviewer can now:

- read the migration guide,
- compare the before/after caller diff,
- run the executable pytest proof,
- verify the request-id/ledger evidence story,
- confirm the docs stay narrow and do not imply broad embeddings parity.
