# M010: Production Resilience and Failure Proof

**Gathered:** 2026-05-24
**Status:** Ready for planning

## Project Description

Create M010: Production Resilience and Failure Proof. This milestone makes Nebula trustworthy under real dependency outages, degraded infrastructure, and recovery scenarios by proving how the gateway, admin surfaces, and operator workflows behave when PostgreSQL, Qdrant, premium providers, or hosted metadata services are impaired. The work strengthens existing runtime, health, evidence, and operator seams rather than creating a new operations product.

## Why This Milestone

Nebula now has a mature routing and operator-control story through M009, but the next trust gap is operational: teams need confidence that the system fails safely, tells the truth during incidents, and can be recovered with bounded, verified steps. Right now the product is strong on decision quality and request-level evidence, but its production resilience story is more implied than explicitly assembled. M010 exists to make failure behavior, degraded continuity, and recovery proof first-class without widening into broad chaos engineering, a new NOC dashboard, or hosted authority.

## User-Visible Outcome

### When this milestone is complete, the user can:

- observe how Nebula serves, degrades, or fails when a core dependency is unavailable, using existing runtime and operator surfaces rather than log spelunking
- verify from existing health and observability surfaces what dependency failed, what fallback or degraded behavior Nebula entered, and whether the system has recovered cleanly
- follow a documented recovery path for the highest-value outage classes and confirm that post-recovery behavior and evidence integrity are trustworthy
- review one integrated proof path showing outage, truthful degraded behavior, operator visibility, and clean recovery without widening Nebula into a separate incident-management product

### Entry point / environment

- Entry point: live `POST /v1/chat/completions`, existing admin/health endpoints, usage-ledger/Observability inspection, and documented operator recovery steps
- Environment: self-hosted gateway plus existing operator console in production-like local/dev dependency setups
- Live dependencies involved: PostgreSQL governance store, Qdrant semantic cache, premium provider path, and hosted metadata/control-plane calls where already present

## Completion Class

- Contract complete means: dependency-specific degradation states, failure evidence, and recovery semantics are typed and shared across runtime truth and operator-readable surfaces without inventing false success or false precision.
- Integration complete means: real dependency outage and recovery scenarios can be exercised across serving path, health/admin evidence, and request-level/operator-visible proof.
- Operational complete means: Nebula preserves continuity where possible, fails closed or degraded where required, records truthful failure state, and provides verified recovery steps for the most important outage classes.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- a real dependency outage can be triggered for at least one critical serving dependency and Nebula degrades or fails safely with truthful request and health evidence
- a real dependency outage can be triggered for at least one supporting/non-serving dependency and Nebula preserves unaffected serving paths while exposing accurate degraded state to operators
- an operator can use existing health/admin/observability surfaces to identify the failed dependency, understand the current degraded mode, and confirm recovery
- at least one documented recovery path restores healthy behavior and trustworthy post-recovery evidence without relying on hidden manual state repair
- the final integrated proof covers outage, degraded runtime truth, operator-visible evidence, and recovery verification without turning into a new dashboard, chaos platform, or hosted-authoritative system

## Architectural Decisions

### Dependency-specific degradation over generic "unhealthy"

**Decision:** Model production resilience around explicit dependency-specific degradation states and recovery semantics rather than a single coarse unhealthy flag.

**Rationale:** Operators need to know what failed, what paths remain safe, and what recovery steps matter. A single coarse unhealthy state is too weak for production trust and blurs the difference between serving-critical and supporting dependency loss.

**Alternatives Considered:**
- One global unhealthy state — rejected because it hides safe-vs-unsafe behavior and weakens operator decision-making.
- Dependency-specific logs only — rejected because runtime truth must be visible through the shipped product surfaces, not only log inspection.

### Existing surfaces remain primary

**Decision:** Expose outage, degraded-mode, and recovery truth through existing health, admin, request-detail, and Observability surfaces rather than introducing a separate resilience dashboard.

**Rationale:** Nebula already established request-first evidence and bounded operator-surface discipline. M010 should strengthen those seams, not create a parallel operations product that competes with them.

**Alternatives Considered:**
- New resilience dashboard — rejected because it widens scope and creates another truth surface to keep in sync.
- Hidden internal-only state — rejected because resilience only builds trust if operators can actually inspect it.

### Recovery proof must be product-visible, not runbook-only

**Decision:** Treat recovery as complete only when restored health and trustworthy post-recovery behavior are visible through runtime and operator evidence, not just when the dependency is restarted.

**Rationale:** A restarted dependency is not enough if the product still hides stale failure state, resumes with bad assumptions, or records misleading evidence. Recovery proof needs to include both restored behavior and trustworthy visibility.

**Alternatives Considered:**
- Infrastructure restart as sufficient proof — rejected because it ignores product-state reconciliation.
- Runbook-only documentation without verification — rejected because production trust requires executable proof.

### Hosted remains informative, never authoritative

**Decision:** Hosted/control-plane metadata can reflect resilience state only as supporting context and must not become the authority for runtime health, outage classification, or recovery truth.

**Rationale:** Nebula’s trust boundary remains local-authority-first. M010 should improve resilience proof without making hosted state the source of truth during incidents.

**Alternatives Considered:**
- Hosted-central incident truth — rejected because it weakens the local-authority model.
- Ignoring hosted entirely — rejected because supporting context can still be useful as long as it stays clearly subordinate.

## Error Handling Strategy

Nebula should distinguish between serving-critical dependency failures, serving-optional dependency failures, and metadata-only dependency failures. When a dependency failure still permits safe serving, the gateway should continue on the healthy subset of behavior and record explicit degraded state instead of masking the incident. When a dependency failure makes a request path unsafe or dishonest to continue, the system should fail closed with specific, bounded error responses and truthful operator-visible evidence. Recovery should clear or supersede stale failure state explicitly so operators can distinguish current incidents from recovered ones.

Retries should stay bounded and dependency-aware. Serving-path retries must not turn dependency outages into latency storms or obscure root cause. Health and operator surfaces should expose the last meaningful failure state, time, and dependency classification without leaking secrets or raw stack traces. Recovery workflows should prefer explicit reconnection, re-check, and evidence-integrity confirmation over silent background healing claims.

## Risks and Unknowns

- Dependency behavior may differ sharply between PostgreSQL, Qdrant, premium providers, and hosted metadata — a generic resilience model could be too vague to be useful.
- Post-recovery state may look healthy while evidence or background workflows remain stale — this would create false confidence.
- Operator surfaces could become noisy or dashboard-like if resilience context is not kept subordinate to runtime truth and request evidence.
- Verification may be brittle if outage proof depends on ad hoc environment setup instead of deterministic dependency control.

## Existing Codebase / Prior Art

- `src/nebula/main.py` — application lifespan and dependency startup/shutdown orchestration that likely anchors resilience and recovery hooks.
- `src/nebula/core/container.py` — service wiring and dependency ownership boundary where resilience state may need to stay centralized.
- `src/nebula/services/governance_store.py` — PostgreSQL-backed truth/evidence seam whose outage behavior and recovery need explicit proof.
- `src/nebula/services/semantic_cache_service.py` — Qdrant-backed cache seam whose degradation should preserve safe serving semantics.
- `src/nebula/services/chat_service.py` — request orchestration and fallback behavior where truthful degraded serving must be exercised.
- `src/nebula/api/routes/admin.py` and existing health endpoints — existing admin and health truth surfaces to strengthen instead of replacing.
- `console/src/app/(console)/observability/page.tsx` and `console/src/components/health/*` — operator surfaces that should expose resilience state without becoming primary over request truth.
- `docs/m009-integrated-proof.md` and earlier integrated proof docs — pointer-first proof pattern to reuse for resilience close-out.

## Relevant Requirements

- R086 — prove core serving and operator workflows remain trustworthy under dependency outages, degraded infrastructure, and recovery scenarios
- R087 — gateway serving degrades explicitly and safely when core dependencies are unavailable without inventing false success or blocking unrelated healthy paths
- R088 — operators can see dependency degradation, last known failure state, and recovery status through existing health and observability surfaces
- R089 — Nebula provides documented and verified operator recovery paths for the most important dependency and data-state failures

## Scope

### In Scope

- explicit dependency-specific degraded/failure/recovery semantics for the most important runtime dependencies
- truthful serving behavior under PostgreSQL, Qdrant, premium provider, and hosted-metadata impairment where applicable
- operator-visible failure and recovery state through existing health/admin/request-detail/Observability seams
- verified operator recovery paths for the highest-value outage classes
- final integrated proof covering outage, degraded behavior, operator inspection, and recovery confirmation
- process tightening if needed to make resilience proof durable and repeatable

### Out of Scope / Non-Goals

- a broad chaos-engineering platform or arbitrary fault-injection framework
- a new NOC-style dashboard or incident-management surface
- hosted-authoritative health or recovery control
- broad infrastructure automation unrelated to Nebula’s shipped product behavior
- exhaustive proof for every possible dependency or deployment topology in one milestone

## Technical Constraints

- Preserve local runtime authority; hosted remains supporting only.
- Prefer explicit degraded semantics over vague healthy/unhealthy labels.
- Keep operator proof on existing surfaces; avoid dashboard sprawl.
- Preserve truthful request and evidence behavior even when some supporting systems fail.
- Recovery proof must include post-recovery evidence integrity, not just service reachability.
- Verification should be deterministic enough to re-run in development and milestone close-out.

## Integration Points

- FastAPI lifespan and dependency startup/shutdown — resilience state ownership, reconnection, and recovery verification
- PostgreSQL governance store — request evidence, policy/admin truth, and serving-critical persistence behavior
- Qdrant semantic cache — serving-optional cache degradation and continuity proof
- Premium provider adapters — upstream outage and fallback/degraded semantics
- Existing health/admin endpoints — dependency-specific failure and recovery truth
- Observability and request-detail console surfaces — operator inspection of degraded and recovered state
- Hosted metadata/control-plane surfaces — supporting resilience context only where already present

## Testing Requirements

Require four verification layers. First, contract coverage for dependency-state classification, degraded/recovered state transitions, and operator-visible evidence vocabulary. Second, backend integration coverage that exercises real dependency outage classes and proves safe serving, fail-closed behavior where required, and truthful persistence/health signals. Third, focused console and admin verification proving operators can identify the failed dependency, current degraded mode, and recovery status using existing surfaces. Fourth, integrated operational proof that at least one outage-and-recovery path is exercised end to end and confirms restored healthy behavior plus trustworthy post-recovery evidence. The milestone is not complete if it only adds health flags or only documents recovery without executable proof.

## Acceptance Criteria

- **S01:** Nebula has a typed dependency-state and degraded-mode contract that distinguishes serving-critical, serving-optional, and metadata-only dependency failures and is proved through focused backend tests.
- **S02:** At least one serving-critical outage and one serving-optional outage are exercised end to end, proving truthful request behavior, safe degradation or fail-closed behavior, and correct health/admin evidence.
- **S03:** Existing health/admin/Observability surfaces show dependency-specific failure state, last meaningful failure context, and recovery status without becoming a new dashboard-first workflow.
- **S04:** A documented operator recovery path for the highest-value outage classes is verified end to end, including restored health and trustworthy post-recovery behavior/evidence.
- **S05:** One integrated proof assembles outage trigger, degraded runtime truth, operator-visible evidence, and successful recovery confirmation while preserving local authority and bounded product scope.

## Open Questions

- Which outage classes are the highest-value first proof target? — Current thinking: start with PostgreSQL, Qdrant, and premium provider impairment because they map directly to operator trust in serving and evidence.
- How much historical failure context should product surfaces retain after recovery? — Current thinking: enough to explain the last meaningful incident and recovery, but not enough to turn resilience state into a new analytics workflow.
- Should hosted surfaces expose any resilience context in M010? — Current thinking: only if they can do so as clearly subordinate metadata, never as runtime truth or recovery authority.
