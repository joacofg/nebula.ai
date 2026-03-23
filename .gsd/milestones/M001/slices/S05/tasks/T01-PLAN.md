---
estimated_steps: 5
estimated_files: 5
skills_used:
  - react-best-practices
---

# T01: Compose the canonical integrated adoption walkthrough

**Slice:** S05 — Final integrated adoption proof
**Milestone:** M001

## Description

Create the canonical S05 integrated-proof entry point that assembles the existing adoption canonicals into one discoverable walkthrough without duplicating setup, contract, or production-model content. This task defines the stable sequence that all later executable verification will assert.

## Steps

1. Add `docs/integrated-adoption-proof.md` as the final integrated adoption walkthrough that explicitly follows the proof order public `POST /v1/chat/completions` request → `X-Nebula-*` / `X-Request-ID` evidence → usage-ledger correlation → Playground corroboration → Observability corroboration.
2. Keep `docs/adoption-api-contract.md` and `docs/production-model.md` as linked canonicals instead of restating their contents, and preserve the S02 runtime-truth language around tenant, policy, API key, and operator boundaries.
3. Add only minimal cross-links in `README.md`, `docs/quickstart.md`, `docs/reference-migration.md`, and `docs/day-1-value.md` so the integrated-proof path is discoverable from the existing adoption map.
4. Make the document explicit that Playground is admin-only corroboration, not the public adoption target, and that the integrated story stays grounded in the public route.
5. Run link/content integrity checks for the integrated-proof vocabulary across the touched docs.

## Must-Haves

- [ ] `docs/integrated-adoption-proof.md` composes the existing canonicals without duplicating API contract or production-model details.
- [ ] The integrated-proof document and entry-point links preserve the exact proof order already established in S03/S04.
- [ ] The touched docs keep Playground framed as operator corroboration only.

## Verification

- `test -f docs/integrated-adoption-proof.md`
- `rg -n "integrated adoption|X-Request-ID|Playground|Observability|adoption-api-contract|production-model" README.md docs/integrated-adoption-proof.md docs/quickstart.md docs/reference-migration.md docs/day-1-value.md`

## Inputs

- `README.md` — current documentation map and adoption entry points
- `docs/quickstart.md` — canonical happy-path walkthrough to compose, not rewrite
- `docs/reference-migration.md` — canonical migration proof sequence and correlation language
- `docs/day-1-value.md` — canonical operator-visible value proof ordering
- `docs/adoption-api-contract.md` — canonical public API boundary to link instead of restating
- `docs/production-model.md` — canonical runtime-truth framing for tenant/operator/app/workload language

## Expected Output

- `docs/integrated-adoption-proof.md` — new canonical final integrated adoption walkthrough
- `README.md` — updated top-level entry point linking to the integrated proof
- `docs/quickstart.md` — minimal integrated-proof cross-link
- `docs/reference-migration.md` — minimal integrated-proof cross-link
- `docs/day-1-value.md` — minimal integrated-proof cross-link

## Observability Impact

- Signals clarified: the canonical proof order becomes explicitly inspectable in one doc — public `POST /v1/chat/completions` request, public `X-Nebula-*` / `X-Request-ID` evidence, usage-ledger correlation, Playground corroboration, and Observability corroboration.
- Inspection path for future agents: read `docs/integrated-adoption-proof.md` first, then follow its canonical links to `docs/adoption-api-contract.md`, `docs/production-model.md`, `docs/reference-migration.md`, and `docs/day-1-value.md` to confirm the public/admin boundary and proof ordering stayed aligned.
- Failure visibility improved: copy drift is now easier to spot when Playground is framed as an adoption target, when `X-Request-ID` drops out of the joined story, or when touched docs stop exposing the integrated-proof vocabulary verified by ripgrep.
