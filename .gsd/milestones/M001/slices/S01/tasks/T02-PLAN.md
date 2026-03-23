---
estimated_steps: 4
estimated_files: 3
skills_used:
  - best-practices
---

# T02: Publish the canonical adoption contract and align entry docs

**Slice:** S01 — Adoption API contract and compatibility boundary
**Milestone:** M001

## Description

Turn the proven contract into one canonical, easy-to-find adoption artifact. This task should write the public compatibility boundary in plain language for downstream quickstart and migration work, then align top-level docs to reference that source instead of scattering partial promises across the repo.

## Steps

1. Create `docs/adoption-api-contract.md` as the canonical public contract doc for `POST /v1/chat/completions`, grounded in the behaviors proven by `tests/test_chat_completions.py`, `tests/test_response_headers.py`, and `tests/test_admin_playground_api.py`.
2. In that doc, describe the supported request/response shape, Nebula auth headers, model naming guidance, streaming behavior, and Nebula response-header evidence, then include a clearly labeled unsupported/deferred section that names omitted or intentionally unproven compatibility features.
3. Update `README.md` to point adopters directly to `docs/adoption-api-contract.md` when they need the supported API boundary, and keep the top-level story concise instead of duplicating contract detail.
4. Update `docs/architecture.md` so its request-flow and operator-evidence language references the canonical adoption contract where appropriate, preserving the distinction between the public API and the admin Playground path.

## Must-Haves

- [ ] `docs/adoption-api-contract.md` explicitly distinguishes supported public adoption behavior from unsupported or deferred compatibility claims.
- [ ] The doc calls out Nebula-specific auth and `X-Nebula-*` response headers as part of the adoption contract.
- [ ] The doc states that admin Playground is not the public adoption path and is intentionally non-streaming.
- [ ] `README.md` and `docs/architecture.md` link to the canonical contract doc instead of each becoming competing sources of truth.

## Verification

- `test -f docs/adoption-api-contract.md && grep -c "^## " docs/adoption-api-contract.md | awk '{exit !($1 >= 6)}'`
- `! rg -n "TBD|TODO" docs/adoption-api-contract.md`
- `rg -n "adoption-api-contract|X-Nebula-API-Key|X-Nebula-Route-Target|unsupported|deferred|Playground" README.md docs/architecture.md docs/adoption-api-contract.md`

## Inputs

- `tests/test_chat_completions.py` — executable proof for public non-streaming and streaming behavior
- `tests/test_response_headers.py` — executable proof for response-header and failure-path metadata
- `tests/test_admin_playground_api.py` — executable proof for the admin Playground boundary
- `README.md` — top-level product entry docs that must link to the canonical contract
- `docs/architecture.md` — architecture narrative that must align with the contract boundary

## Expected Output

- `docs/adoption-api-contract.md` — canonical adoption API contract and compatibility-boundary document
- `README.md` — top-level doc updated to point adopters at the canonical contract
- `docs/architecture.md` — architecture doc aligned to the canonical contract and public/admin boundary

## Observability Impact

- Signals clarified: the canonical contract doc now names the inspectable public response headers (`X-Nebula-*`), the required public auth header (`X-Nebula-API-Key`), and the admin Playground boundary including `X-Request-ID` and usage-ledger correlation.
- Inspection path for future agents: verify the written contract against `tests/test_chat_completions.py`, `tests/test_response_headers.py`, `tests/test_admin_playground_api.py`, `docs/adoption-api-contract.md`, and `GET /v1/admin/usage/ledger` for Playground evidence language.
- Failure visibility improved: if public/docs behavior drifts, the mismatch should become visible via targeted ripgrep checks for contract terms, pytest contract suites, or missing/incorrect header language in the canonical document rather than only by reading scattered repo prose.
