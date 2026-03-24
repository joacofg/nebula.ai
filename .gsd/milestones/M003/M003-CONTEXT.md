# M003: Broader Adoption Surface — Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

## Project Description

Create M003: Broader Adoption Surface. Objective: extend Nebula beyond the initial chat-completions adoption path with one narrowly scoped, high-demand public surface, likely embeddings, using a tight compatibility boundary, canonical docs, realistic migration proof, and only minimal optional helper ergonomics. Preserve v3 guardrails: no broad parity push, no SDK sprawl, no major hosted-plane expansion, and no infrastructure work that does not directly improve adoption proof.

## Why This Milestone

Nebula's current v3 adoption story is convincing for chat completions, but it still leaves a common adjacent surface uncovered. Embeddings is the strongest next step because it is high-demand, already has internal prior art in the repo, and can extend the same compatibility-first adoption story without reopening a broad OpenAI-parity program. This milestone exists to prove Nebula can widen its public adoption surface carefully, not to increase feature count for its own sake.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Point a common OpenAI-style embeddings caller at Nebula through a real public `/v1/embeddings` path with minimal changes.
- Read one canonical set of docs that defines the supported embeddings boundary, shows a realistic migration proof, and names what is still out of scope.

### Entry point / environment

- Entry point: `POST /v1/embeddings` plus canonical adoption docs under `docs/`
- Environment: local dev and self-hosted runtime, with proof grounded in real gateway behavior
- Live dependencies involved: FastAPI public API, existing auth/governance path, internal Ollama-backed embeddings service, existing durable backend/operator evidence surfaces

## Completion Class

- Contract complete means: tests and docs prove a strict happy-path embeddings request/response boundary with explicit exclusions.
- Integration complete means: a real embeddings request flows through Nebula's public API into the existing embeddings capability and can be correlated to durable backend/operator evidence.
- Operational complete means: none beyond the existing gateway lifecycle; this milestone should not introduce new infrastructure or supervision concerns.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- A realistic OpenAI-style embeddings caller can switch to Nebula with minimal caller changes and receive a usable embeddings response.
- The same request can be explained through durable backend/operator evidence without needing Nebula-specific helper code.
- The canonical docs, migration proof, and runtime behavior all agree on the same narrow public promise and explicit non-goals.

## Risks and Unknowns

- Internal embeddings capability may not map cleanly onto a public compatibility promise — exposing too much would accidentally widen Nebula's maintenance contract.
- Durable evidence for embeddings adoption may exist only partially today — if proof requires new surfaces, scope could drift into console or infrastructure work.
- Optional parameter expectations from OpenAI-style clients can create hidden parity pressure — this milestone should resist that unless a parameter is essential to credible adoption proof.

## Existing Codebase / Prior Art

- `src/nebula/services/embeddings_service.py` — existing internal Ollama-backed embeddings capability; currently used internally, not exposed as a public adoption surface.
- `src/nebula/core/container.py` — wires the embeddings service into runtime health and semantic cache flows.
- `src/nebula/core/config.py` — already defines embedding model and dimension settings.
- `src/nebula/api/routes/chat.py` — the current public compatibility pattern and response-header proof surface for the chat adoption path.
- `.gsd/REQUIREMENTS.md` / `R011` — existing deferred requirement naming a possible future public embeddings adoption path.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R020 — Establish the public embeddings adoption path itself.
- R021 — Define the contract boundary and exclusions canonically.
- R022 — Prove realistic caller migration.
- R023 — Preserve failure visibility and durable proof for embeddings adoption.
- R024 — Preserve v3 guardrails while widening the adoption surface.

## Scope

### In Scope

- A strict happy-path public `/v1/embeddings` surface.
- Canonical docs for supported embeddings behavior and explicit exclusions.
- One realistic migration proof for a common OpenAI-style embeddings caller.
- Durable backend/operator evidence sufficient to validate and explain the embeddings request.

### Out of Scope / Non-Goals

- Broad embeddings-option parity.
- A general OpenAI API parity expansion.
- New helper libraries or wrapper bundles unless a specific proof gap forces a tiny optional artifact.
- Hosted-plane growth beyond what directly reinforces the adoption proof.
- Infrastructure work that does not directly improve the embeddings adoption story.

## Technical Constraints

- Preserve the v3 guardrails exactly: no broad parity push, no SDK sprawl, no major hosted-plane expansion, and no infrastructure work that does not directly improve adoption proof.
- Default to a strict happy-path contract: `input` + `model`, string input and simple batch input, standard float embedding response shape.
- Treat unsupported or deferred edges as explicit documentation scope, not silent omissions.
- Prefer backend/public proof over new console work; add operator-surface work only if needed to keep the migration proof credible.

## Integration Points

- Public FastAPI API surface — expose the embeddings route through the same authenticated public boundary style as chat.
- Internal embeddings service — power the public response through the existing Ollama-backed capability where it maps cleanly.
- Governance/authentication path — keep the public auth and tenant behavior aligned with the existing adoption contract.
- Durable backend/operator evidence surfaces — provide a trustworthy correlation path for the embeddings request.
- Canonical docs in `docs/` — define the public boundary and migration story without duplicating or drifting from runtime truth.

## Open Questions

- Which existing durable evidence surface is sufficient for embeddings proof without forcing new console work? — Current thinking: reuse backend/operator evidence where possible and only add UI work if there is a clear trust gap.
- Does any optional embeddings parameter materially affect adoption credibility? — Current thinking: no; stay strict unless planning or implementation finds one parameter is unavoidable for the realistic migration proof.
