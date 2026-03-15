# Phase 1: Self-Hosted Foundation - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Make Nebula deployable and operationally safe beyond local development. This phase delivers the self-hosted runtime baseline, explicit deployment shape, durable persistence direction, migrations, and health/readiness behavior. It does not add the operator UI or new product capabilities.

</domain>

<decisions>
## Implementation Decisions

### Deployment shape
- The primary supported deployment target is a single Linux VM.
- Docker Compose is the canonical packaging and runtime path for this phase.
- Phase 1 should target a customer-pilot / serious-demo level of operational quality, not just an academic demo.

### Runtime profile
- The canonical documented runtime profile is premium-first.
- Local routing remains supported, but as an advanced/optional mode rather than the default deployment story.
- Nebula should still preserve and demonstrate the local-to-premium optimization story through development and benchmark workflows.

### Persistence strategy
- PostgreSQL is the canonical governance datastore for deployable environments.
- SQLite remains supported for local development only.
- Deployable environments require explicit migrations rather than bootstrap-only schema creation.
- Governance data and usage ledger data should remain in the same Postgres database for now.

### Health and degraded behavior
- Startup should fail only for invalid configuration or missing dependencies required by the premium-first deployment mode.
- Qdrant/cache failure should not block startup; Nebula should run in an explicit degraded mode.
- Local Ollama unavailability should not block startup in the premium-first profile; Nebula should report local optimization as degraded.
- Phase 1 should keep `/health` but add readiness and dependency-detail behavior so operators can distinguish "serving traffic" from "fully optimized."

### Claude's Discretion
- Exact Compose service layout and file organization
- Exact readiness endpoint shape and naming
- Exact Postgres library/migration tool selection, as long as it fits the phase decisions above

</decisions>

<specifics>
## Specific Ideas

- The deployment story should be opinionated and narrow: one serious self-hosted path, not multiple equal paths.
- Premium-first deployment truth matters more than preserving local-Ollama assumptions in the canonical docs.
- Degraded mode should be visible to operators rather than silently tolerated.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase framing
- `.planning/PROJECT.md` — Product thesis, market fit, scope boundaries, and Phase 1 constraints
- `.planning/REQUIREMENTS.md` — Phase 1 requirements `PLAT-01` through `PLAT-04`
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, and plan structure
- `.planning/STATE.md` — Current project focus and active blockers for this phase

### Existing codebase context
- `.planning/codebase/STACK.md` — Current runtime stack, external dependencies, and configuration surface
- `.planning/codebase/ARCHITECTURE.md` — Existing gateway architecture and runtime data flow
- `.planning/codebase/STRUCTURE.md` — Current repository structure and likely integration points
- `.planning/codebase/CONCERNS.md` — Existing deployment, persistence, and degraded-mode concerns to address in this phase

### Research context
- `.planning/research/SUMMARY.md` — Recommended product direction and phase ordering rationale
- `.planning/research/STACK.md` — Recommended self-hosted stack direction including Next.js, Postgres, and Qdrant
- `.planning/research/PITFALLS.md` — Phase-relevant warnings about proof, scope, persistence, and degraded operation

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/nebula/main.py`: central app factory and current `/health` endpoint
- `src/nebula/core/config.py`: environment-backed settings model and startup validation hook
- `src/nebula/core/container.py`: single runtime composition root where deployment-profile decisions will surface
- `src/nebula/services/governance_store.py`: current persistence layer and schema/bootstrap logic to replace or refactor
- `src/nebula/services/semantic_cache_service.py`: current degraded cache behavior and Qdrant integration
- `docker-compose.yml`: existing Compose foothold, currently only for Qdrant
- `Makefile`: existing developer command surface for setup, run, smoke tests, and benchmarks

### Established Patterns
- FastAPI + Pydantic settings are the established runtime boundary; deployment work should preserve that rather than introduce parallel config systems.
- The app already supports graceful degradation in some paths, especially the semantic cache. Phase 1 should formalize that behavior instead of adding silent fallbacks.
- Provider and service composition is centralized in `ServiceContainer`, so deployment profile toggles should be expressed there or through settings, not ad hoc route logic.

### Integration Points
- Startup validation and non-local secret enforcement will integrate into `src/nebula/core/config.py` and `src/nebula/main.py`.
- Health/readiness behavior will likely extend `src/nebula/main.py` and inspect services initialized in `ServiceContainer`.
- Migration and datastore changes will center on `src/nebula/services/governance_store.py` and related configuration.
- Packaging and self-hosted topology will extend `docker-compose.yml`, add deployment artifacts, and update `README.md` / docs.

</code_context>

<deferred>
## Deferred Ideas

- Operator web console — Phase 2
- Playground and operator-facing observability UI — Phase 3
- Hosted SaaS control plane or public self-serve onboarding — future phases

</deferred>

---

*Phase: 01-self-hosted-foundation*
*Context gathered: 2026-03-15*
