# M002: Production Structuring Model

**Gathered:** 2026-03-23
**Status:** Ready for planning

## Project Description

Nebula is a self-hosted semantic AI gateway with a stable public chat-completions adoption path and operator-facing governance surfaces. M001 proved the initial API-adoption happy path. M002 focuses on making production structuring decisions clearer for real teams: how to model tenant, application, workload, and operator boundaries across documentation and product surfaces without inventing runtime entities that do not exist yet.

## Why This Milestone

M001 documented the current runtime truth: tenant, policy, API key, and operator admin session are the authoritative enforced entities today, while app and workload remain conceptual guidance only. That is enough for an initial adoption proof, but not yet strong enough for teams deciding how to structure real production rollouts, multi-team ownership, or tenant/key conventions. M002 exists to reduce that ambiguity without expanding scope into a large runtime redesign unless the evidence demands it.

## User-Visible Outcome

### When this milestone is complete, the user can:

- understand how to map a real team, application, and workload structure onto Nebula's current tenant and API-key model without guessing
- use docs and operator surfaces that consistently reinforce the same production-structuring guidance

### Entry point / environment

- Entry point: docs, admin console surfaces, and existing `/v1/admin/*` governance flows
- Environment: self-hosted local dev and production-like operator workflows
- Live dependencies involved: database, console, gateway admin APIs

## Completion Class

- Contract complete means: documentation and product-surface wording consistently describe current runtime entities and any required headers/selection rules without contradiction
- Integration complete means: operator-facing docs and relevant console/admin surfaces tell the same structuring story for tenant, API key, and multi-tenant selection behavior
- Operational complete means: none beyond preserving the current self-hosted/operator lifecycle and metadata-only trust boundary

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- a self-hosted operator can decide how to structure a real team/application/workload setup using one coherent production-model story
- docs and product surfaces agree on what is enforced today versus what is guidance only
- no new wording accidentally promotes app/workload to first-class runtime entities unless implementation really exists

## Risks and Unknowns

- Production-model guidance may still be too abstract for larger teams — if so, documentation-only clarification may be insufficient
- Console/admin wording may drift from docs — if product surfaces contradict the canonicals, adoption trust regresses
- There may be real demand for stronger runtime app/workload structure — if that shows up, the milestone may need a narrow product-surface extension instead of docs-only refinement

## Existing Codebase / Prior Art

- `docs/production-model.md` — current canonical runtime-truth explanation for tenant, API key, operator, app, and workload boundaries
- `docs/quickstart.md` — current self-hosted setup and first-request flow that already references the production model
- `docs/reference-migration.md` — current migration proof that depends on the tenant-header rule staying precise
- `console/` — operator UI surfaces that may need wording and framing alignment with the docs
- `src/nebula/api/routes/admin.py` — existing admin/governance API surfaces behind the console

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R006 — clarify tenant, app, workload, and operator boundaries strongly enough for production usage
- R011 — deferred embeddings adoption path may depend on the production-structuring story, but is not part of this milestone by default
- R012 — decide whether app/workload should remain guidance only or become more explicit in product surfaces

## Scope

### In Scope

- clarifying the production structuring model around tenant, API key, operator, app, and workload boundaries
- aligning docs and any relevant operator-facing product surfaces to the same runtime truth
- tightening guidance for multi-tenant keys and tenant-selection behavior where ambiguity would affect production structuring

### Out of Scope / Non-Goals

- broad new runtime entities for apps or workloads unless narrow evidence proves they are required
- new public adoption endpoints or broad compatibility-surface expansion
- billing, enterprise RBAC redesign, or hosted-plane scope expansion beyond adoption/operator clarity

## Technical Constraints

- preserve the metadata-only hosted/control-plane trust boundary by default
- do not describe app/workload as first-class runtime entities unless code and admin APIs actually enforce them
- preserve the M001 canonicals: `docs/adoption-api-contract.md` remains the only public API contract; `docs/quickstart.md` remains the happy-path setup; `docs/production-model.md` remains the operating-model reference

## Integration Points

- `docs/*` canonicals — primary place where the structuring model must remain coherent
- operator console — must not contradict runtime-truth language from the docs
- governance store and admin APIs — current source of truth for what is actually enforceable

## Open Questions

- Do operators need stronger in-product guidance, or are tighter docs enough? — likely the first slice should answer this with the smallest real surface that removes ambiguity
- Is there a narrow way to make app/workload intent visible without inventing new runtime entities? — possibly through naming guidance, UI copy, or metadata framing rather than new core models
- Which current console pages create the most production-structuring ambiguity? — needs targeted inspection before slice planning
