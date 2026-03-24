---
estimated_steps: 3
estimated_files: 8
skills_used:
  - react-best-practices
---

# T02: Wire entry docs to the new canonical adoption story and lock verification to existing evidence

**Slice:** S02 — Happy-path quickstart and production model
**Milestone:** M001

## Description

Update the repository entry docs so readers are funneled to the new canonical quickstart and production-model docs instead of piecing together the adoption story across multiple pages. Close the slice by verifying those docs stay aligned with the already-tested backend and console evidence surfaces.

## Steps

1. Update `README.md`, `docs/self-hosting.md`, and `docs/architecture.md` to point explicitly to `docs/quickstart.md` and `docs/production-model.md` wherever the happy path or operating model is currently fragmented, while preserving `docs/adoption-api-contract.md` as the only canonical public compatibility boundary.
2. Add any missing cross-links inside `docs/quickstart.md` and `docs/production-model.md` so a reader can move cleanly between deployment, public-client request semantics, and operator confirmation surfaces without dead ends or contradictory wording.
3. Run the slice doc-integrity checks plus the referenced backend and console test commands, then capture any required wording adjustments so the final docs are backed by the existing public-path, governance, Playground, and ledger evidence.

## Must-Haves

- [ ] Entry docs route adopters to one canonical quickstart and one canonical production-model doc instead of duplicating drifting guidance.
- [ ] Slice verification is runnable and still points at the evidence suites that back the docs' claims: public chat completions, governance/admin flows, and admin Playground correlation.

## Verification

- `rg -n "docs/quickstart.md|docs/production-model.md|adoption-api-contract|self-hosting|Playground|Observability|usage ledger" README.md docs/self-hosting.md docs/architecture.md docs/quickstart.md docs/production-model.md && ! rg -n "TODO|TBD" README.md docs/quickstart.md docs/production-model.md docs/self-hosting.md docs/architecture.md`
- `pytest tests/test_chat_completions.py tests/test_governance_api.py tests/test_admin_playground_api.py -q && npm --prefix console run test -- --run`

## Observability Impact

- Signals added/changed: no new runtime signals; this task deliberately binds docs to the existing `X-Nebula-*`, `X-Request-ID`, and usage-ledger evidence surfaces.
- How a future agent inspects this: read `README.md`, `docs/self-hosting.md`, `docs/architecture.md`, `docs/quickstart.md`, and `docs/production-model.md`, then run the referenced pytest and console test commands.
- Failure state exposed: broken links, placeholder text, or test failures reveal where the docs have drifted from the public client path, admin surfaces, or operator evidence.

## Inputs

- `docs/quickstart.md` — canonical happy-path doc produced by T01
- `docs/production-model.md` — canonical operating-model doc produced by T01
- `README.md` — repo entrypoint that must route readers to the new canonical docs
- `docs/self-hosting.md` — deployment runbook that must point to the quickstart and production model
- `docs/architecture.md` — architecture overview that must point to the production model and retain the contract boundary link pattern
- `tests/test_chat_completions.py` — public-path evidence suite backing quickstart claims
- `tests/test_governance_api.py` — governance/admin evidence suite backing tenant and API-key claims
- `tests/test_admin_playground_api.py` — Playground and usage-ledger correlation evidence suite backing operator confirmation claims

## Expected Output

- `README.md` — updated entry doc that links to the canonical quickstart and production-model docs
- `docs/self-hosting.md` — updated deployment runbook with explicit quickstart / operating-model pointers
- `docs/architecture.md` — updated architecture doc with explicit production-model pointer and preserved contract-boundary references
- `docs/quickstart.md` — finalized quickstart doc with resolved cross-links
- `docs/production-model.md` — finalized production-model doc with resolved cross-links
