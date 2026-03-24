---
estimated_steps: 4
estimated_files: 5
skills_used:
  - best-practices
---

# T02: Publish the embeddings migration guide and wire discoverability

**Slice:** S03 — Realistic migration proof
**Milestone:** M003

## Description

Turn the executable embeddings migration proof into the canonical human-readable guide for adopters. This task should create a dedicated `docs/embeddings-reference-migration.md` file that follows the same credible before/after pattern as the chat migration guide, but remains explicitly subordinate to `docs/embeddings-adoption-contract.md` for contract details. The doc must show an honest OpenAI Python client diff, explain how to confirm the migration through `X-Request-ID`, `X-Nebula-*`, and usage-ledger correlation, and make clear what does not count as migration proof. It should also add light discoverability links so readers can find the guide from the embeddings contract and entry docs without turning those files into duplicate contract surfaces.

## Steps

1. Read `docs/reference-migration.md`, `tests/test_embeddings_reference_migration.py`, and `docs/embeddings-adoption-contract.md` so the guide structure, examples, and claims are derived from the executable proof and canonical contract.
2. Write `docs/embeddings-reference-migration.md` with sections for what the migration proves, starting assumptions, before/after code, before/after diff, what stayed the same, how to confirm the migration worked, minimal verification path, and what not to use as migration proof.
3. Keep the code examples realistic and narrow: use the OpenAI Python client, change only the base URL, placeholder `api_key`, `default_headers={"X-Nebula-API-Key": ...}`, and the tested embeddings model/body; do not imply bearer auth, helper SDKs, `encoding_format`, or broader parity.
4. Add pointer-only cross-links from `docs/embeddings-adoption-contract.md` and any needed doc-entry surfaces so adopters can discover the guide while the contract doc remains the sole detailed boundary definition.

## Must-Haves

- [ ] `docs/embeddings-reference-migration.md` names `tests/test_embeddings_reference_migration.py` as the source of truth and gives a believable minimal-change embeddings migration example.
- [ ] Cross-links make the migration guide discoverable without turning `docs/embeddings-adoption-contract.md`, `README.md`, or `docs/architecture.md` into a second detailed embeddings contract.

## Verification

- `test -f docs/embeddings-reference-migration.md && ! grep -q "TBD\|TODO" docs/embeddings-reference-migration.md && [ "$(rg -c "^## " docs/embeddings-reference-migration.md)" -ge 6 ]`
- `rg -n "tests/test_embeddings_reference_migration.py|X-Nebula-API-Key|X-Request-ID|/v1/admin/usage/ledger|What this migration proves|What not to use as migration proof" docs/embeddings-reference-migration.md && rg -n "embeddings-reference-migration" docs/embeddings-adoption-contract.md README.md docs/architecture.md docs/*.md`

## Inputs

- `docs/reference-migration.md` — existing canonical migration-guide structure and tone to mirror for embeddings.
- `tests/test_embeddings_reference_migration.py` — executable source of truth for examples, headers, and ledger-correlation language.
- `docs/embeddings-adoption-contract.md` — canonical contract vocabulary and exclusions that the migration guide must defer to.
- `README.md` — repo entry doc that may need a pointer to the new migration guide.
- `docs/architecture.md` — high-level doc that may need a discoverability link without duplicating contract details.

## Expected Output

- `docs/embeddings-reference-migration.md` — canonical human-readable embeddings migration proof derived from the executable test.
- `docs/embeddings-adoption-contract.md` — updated pointer section or related-doc link to the migration guide.
- `README.md` — updated documentation map if needed to surface the new guide.
- `docs/architecture.md` — updated pointer-only discoverability link if needed.

## Observability Impact

- Signals preserved: the guide must point readers to the same public proof signals exercised by `tests/test_embeddings_reference_migration.py`, specifically `X-Request-ID`, the embeddings `X-Nebula-*` response headers, and `GET /v1/admin/usage/ledger?request_id=...`.
- Inspection path for future agents: validate the human-readable guide against the executable proof test first, then confirm discoverability through pointer-only links in `docs/embeddings-adoption-contract.md`, `README.md`, and `docs/architecture.md`.
- Failure visibility added by this task: documentation drift becomes locally diagnosable by the doc verification commands, especially missing guide sections, omitted proof headers, or broken discoverability links, without changing runtime behavior.
