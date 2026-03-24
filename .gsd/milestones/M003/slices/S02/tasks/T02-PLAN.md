---
estimated_steps: 3
estimated_files: 3
skills_used:
  - best-practices
---

# T02: Link entry docs back to the canonical embeddings contract

**Slice:** S02 — Canonical embeddings contract docs
**Milestone:** M003

## Description

Make the new embeddings contract discoverable from Nebula's main documentation entry points without creating a second source of truth. This task should add concise references in the repo-level docs so readers find the canonical embeddings boundary quickly, while keeping detailed request/response semantics confined to `docs/embeddings-adoption-contract.md`.

## Steps

1. Update `README.md` to add the embeddings contract doc to the documentation map and, if helpful, include `POST /v1/embeddings` in the selected public endpoint inventory.
2. Update `docs/architecture.md` to mention embeddings as a narrow public adoption surface and point readers to `docs/embeddings-adoption-contract.md` for the canonical contract instead of restating request/response details there.
3. Re-read the changed sections to ensure both files are pointer-only: they should improve discoverability and boundary clarity without duplicating enough detail to drift from the canonical doc later.

## Must-Haves

- [ ] `README.md` links to `docs/embeddings-adoption-contract.md` in the repo’s discoverability path.
- [ ] `docs/architecture.md` references the embeddings surface and points to the canonical doc without becoming a competing contract source.

## Verification

- `rg -n "embeddings-adoption-contract|POST /v1/embeddings" README.md docs/architecture.md docs/embeddings-adoption-contract.md`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py && /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings && /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding`

## Inputs

- `docs/embeddings-adoption-contract.md` — canonical embeddings boundary that entry docs must link to rather than restate.
- `README.md` — repo landing page and documentation map that should surface the embeddings contract.
- `docs/architecture.md` — high-level runtime guide that should acknowledge the embeddings surface and defer contract details to the canonical doc.

## Expected Output

- `README.md` — updated documentation map and/or endpoint inventory pointing to the canonical embeddings contract.
- `docs/architecture.md` — updated high-level architecture narrative that references the embeddings contract doc.

## Observability Impact

This task changes discoverability and documentation-boundary signals rather than runtime behavior. Future agents should inspect `README.md` and `docs/architecture.md` with `rg -n "embeddings-adoption-contract|POST /v1/embeddings" README.md docs/architecture.md docs/embeddings-adoption-contract.md` to verify that entry docs point to the canonical embeddings contract without restating it as a second source of truth. Runtime observability for the endpoint itself remains the same as T01: `POST /v1/embeddings` emits `X-Request-ID` plus the documented `X-Nebula-*` headers, and durable lookup remains `/v1/admin/usage/ledger` keyed by request id.
