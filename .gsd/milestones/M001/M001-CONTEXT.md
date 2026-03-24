# M001: API Adoption Happy Path

**Gathered:** 2026-03-23
**Status:** Ready for planning

## Project Description

Nebula is already reasonably strong as infrastructure. What is still weak is the adoption path: how a team plugs their app into Nebula, how much code they need to change, what API contract they should rely on, and what they gain on day 1. This milestone turns that weak spot into an explicit product surface.

The intended product stance is hybrid:
- OpenAI-compatible inference surface for fast adoption
- Nebula-native admin/control surfaces for governance, routing, observability, and hosted capabilities

The reason for the hybrid stance is explicit. A pure Nebula-native API increases adoption friction. A pure compatibility layer undersells Nebula’s unique value. v3.0 should give easy entry plus differentiated control.

## Why This Milestone

Nebula can already do meaningful routing, fallback, policy, and operator visibility work, but if the integration model stays fuzzy the product remains technically interesting and harder to adopt, demo, and sell. This milestone exists to make the adoption path legible and credible: fast to start, honest about compatibility boundaries, and backed by real migration proof.

## User-Visible Outcome

### When this milestone is complete, the user can:

- point a common chat-completions-style application at Nebula through a documented happy path and complete the integration in under 30 minutes
- inspect a real migration example that replaces direct provider calls with Nebula and see routing, policy, observability, and provider abstraction value on day 1

### Entry point / environment

- Entry point: documented gateway API path, migration guide, quickstart, reference integration, and operator console proof surfaces
- Environment: local dev and self-hosted production-like Compose environment
- Live dependencies involved: gateway API, PostgreSQL governance store, Qdrant cache, operator console, optional local/premium providers

## Completion Class

- Contract complete means: the supported adoption surface is explicit, tested against the live product contract, and documented with clear boundaries and unsupported areas
- Integration complete means: a real reference application or service calls Nebula instead of a direct provider path and the assembled docs + product proof remain consistent
- Operational complete means: the integrated story exposes routing, fallback, policy outcome, and recorded usage behavior clearly enough for a team evaluating adoption

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- a developer can follow the documented happy path and complete a working chat-completions integration quickly without reverse-engineering the product
- a realistic application or service can switch from direct provider usage to Nebula with minimal code changes and still work end-to-end
- the user can see where compatibility ends and where Nebula-specific value begins without ambiguity or marketing hand-waving

## Risks and Unknowns

- Compatibility sprawl — if the compatibility promise grows too broad, the milestone will turn into surface-area maintenance instead of adoption proof
- Weak migration proof — if the reference integration feels like a toy, it will not persuade platform-minded teams
- Conceptual model mismatch — if tenant, app, workload, and operator boundaries remain vague, production usage will still feel fuzzy even with better docs
- Docs/product drift — if the documented contract does not match live behavior, the adoption story collapses on contact

## Existing Codebase / Prior Art

- `src/nebula/api/routes/chat.py` — existing public `POST /v1/chat/completions` route with streaming support and Nebula metadata headers
- `src/nebula/models/openai.py` — current OpenAI-like request/response models for chat completions
- `src/nebula/services/chat_service.py` — routing, cache, fallback, and usage-ledger orchestration already in place
- `tests/test_chat_completions.py` — proves current OpenAI-like payload and SSE behavior
- `src/nebula/api/routes/admin.py` — operator/admin surfaces including playground, tenant, policy, API keys, and ledger access
- `console/src/app/(console)/playground/page.tsx` — current operator-facing proof surface for prompt routing sandbox
- `README.md` and `docs/architecture.md` — current product framing and trust-boundary documentation

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R001 — establish the fast adoption inference path
- R002 — define the stable compatibility boundary
- R003 — prove the under-30-minute happy path
- R004 — provide real migration proof
- R005 — make day-1 operational value obvious
- R006 — clarify the production structuring model
- R007 — shape guidance for multiple ICPs
- R009 — keep routing and failure behavior visible during adoption
- R010 — document unsupported features explicitly

## Scope

### In Scope

- define and document the bounded OpenAI-compatible adoption surface for common chat-completions use
- produce a quickstart and migration path from direct provider usage to Nebula
- create at least one realistic reference integration
- make the tenant / app / workload / operator model explicit enough for production-minded teams
- make day-1 routing, policy, observability, and provider abstraction value visible in the adoption story

### Out of Scope / Non-Goals

- billing or commercial packaging systems
- broad enterprise RBAC redesign
- major hosted control-plane expansion beyond what directly supports adoption
- deep new provider or orchestration work unless it directly improves integration DX
- broad multi-language SDK ecosystem work in this milestone

## Technical Constraints

- The compatibility promise should stay tight and reliable rather than broad and aspirational.
- The milestone should use existing repo-native proof surfaces where possible instead of inventing parallel demo systems.
- The metadata-only hosted trust boundary remains intact; adoption work must not smuggle in broader hosted authority.
- Existing live behavior is brownfield prior art: the milestone should align docs and proof with the actual contract, not rewrite the product story from scratch.

## Integration Points

- `POST /v1/chat/completions` — primary inference adoption path
- `X-Nebula-*` response headers — immediate routing, cache, fallback, and policy evidence
- usage ledger and admin APIs — after-the-fact proof of what the gateway persisted and why
- operator console Playground and Observability — current product surfaces that can reinforce day-1 value
- self-hosted Compose stack — canonical production-like environment for credible adoption proof

## Open Questions

- How much of the tenant / app / workload model should become product surface in M001 versus documentation only? — Current thinking: make it explicit now, but keep enforcement lightweight unless adoption proof demands more.
- Should embeddings join the adoption surface now? — Current thinking: no, not unless later planning shows it is table stakes for the ICP.
- How much new runtime/admin work is truly needed? — Current thinking: keep M001 mostly docs + proof + targeted product shaping, not a broad runtime expansion milestone.
