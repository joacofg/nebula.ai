# M009: Outcome-Grounded Routing Quality

**Gathered:** 2026-04-27
**Status:** Ready for planning

## Project Description

Create M009: Outcome-Grounded Routing Quality. This milestone improves Nebula’s routing core using bounded recent tenant-scoped outcome evidence so the gateway can make measurably better local-vs-premium choices while remaining explainable, simulation-verifiable, and operator-controlled. The work extends the existing routing, usage-ledger, simulation, and Observability seams rather than creating a new product surface.

## Why This Milestone

Nebula already has a strong operator control plane, request-first evidence surfaces, calibrated routing semantics, and bounded governance. The remaining gap is that the router still depends primarily on prompt-complexity heuristics plus the existing calibrated-routing layer. M009 exists to deepen the routing engine itself: improve live decision quality first, preserve replay credibility second, and expose the same decision factors on the existing request-level evidence seams third.

## User-Visible Outcome

### When this milestone is complete, the user can:

- trust that Nebula’s live local-vs-premium route choices reflect bounded recent tenant-scoped outcome evidence rather than prompt heuristics alone
- replay a policy or routing change against the same outcome-grounded routing semantics used by live runtime
- inspect, on the selected request row, whether the route decision was grounded, thin, stale, or degraded and which outcome factors actually influenced it
- review one integrated proof path showing a real routed request, the correlated persisted evidence, the replay parity story, and an honest degraded-path explanation without dashboard or hosted-authority drift

### Entry point / environment

- Entry point: live `POST /v1/chat/completions` routing behavior, `POST /v1/admin/tenants/{tenant_id}/policy/simulate`, `GET /v1/admin/usage/ledger`, and the existing request-first Observability / request-detail surfaces
- Environment: existing self-hosted gateway plus operator console
- Live dependencies involved: router service, policy service, usage ledger / governance store, policy simulation service, operator console Observability surfaces, and the existing hosted metadata-only boundary as supporting context only

## Completion Class

- Contract complete means: one typed outcome-evidence and additive score contract is shared across runtime routing, replay, persistence, and operator evidence without widening Nebula’s public API or hosted boundary.
- Integration complete means: a real routed request, the persisted usage-ledger row, replay through policy simulation, and request-first operator inspection all tell the same grounded or degraded routing story.
- Operational complete means: when outcome evidence is missing, stale, thin, or inconsistent, Nebula degrades explicitly to simpler behavior, preserves service continuity, and records honest request-level evidence rather than blocking requests or pretending precision.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- a real `POST /v1/chat/completions` request can route differently because of bounded recent tenant-scoped outcome evidence
- the same request yields a correlated persisted ledger row that records the actual outcome-grounded route factors that influenced the decision
- `POST /v1/admin/tenants/{tenant_id}/policy/simulate` replays the same outcome-grounded semantics as runtime for the same tenant traffic class
- the selected request in request detail / Observability explains whether the decision was grounded, thin, stale, or degraded without becoming a tenant-summary-first dashboard
- at least one happy-path request and one degraded-path request are proven end to end so the milestone does not depend on a best-case-only story

## Architectural Decisions

### Shared outcome-evidence contract

**Decision:** Use one shared backend contract for recent tenant-scoped outcome evidence and route-score factors so runtime routing, replay, persistence, and operator evidence all reuse the same semantics.

**Rationale:** The main trust risk in this milestone is runtime/replay drift. One shared evidence seam keeps live routing, simulation, and request-level explanation aligned and avoids UI or docs inventing their own routing story.

**Alternatives Considered:**
- Separate runtime and replay evidence logic — rejected because it would erode replay credibility.
- UI-derived interpretation logic — rejected because request evidence should be rendered, not invented, in the console.

### Bounded additive scoring

**Decision:** Extend routing with a bounded additive scoring model rather than a larger branch tree or an opaque learned optimizer.

**Rationale:** The existing router already uses additive factor semantics. A bounded additive model is the best fit for Nebula’s need for explicit factors, request-level persistence, deterministic replay, and operator-readable explanation.

**Alternatives Considered:**
- Larger rule-branch routing — rejected because it becomes brittle once multiple outcome pressures interact.
- Adaptive / learned weighting — rejected because it would increase black-box and replay-risk drift.

### Request-first operator evidence remains primary

**Decision:** Keep request detail and selected-request Observability as the primary operator surfaces for outcome-grounded routing evidence; tenant-level context remains supporting only.

**Rationale:** Nebula already established a request-first operator hierarchy in M007. Preserving that hierarchy is the strongest protection against analytics-product drift in this milestone.

**Alternatives Considered:**
- New routing-quality dashboard — rejected because it would widen product scope and compete with request evidence.
- Tenant-summary-first explanation — rejected because it weakens the authoritative persisted request row.

### Hosted remains informational only

**Decision:** Hosted or fleet-level state must not participate in live route choice, outcome-evidence derivation, or evidence truth for M009.

**Rationale:** Nebula’s strongest current trust-boundary claim is local authority with metadata-only hosted reinforcement. M009 should improve routing quality without weakening that claim.

**Alternatives Considered:**
- Hosted-assisted routing signals — rejected because they would blur authority and widen scope.
- Fleet-level calibration source — rejected because the milestone is explicitly tenant-scoped and locally authoritative.

## Error Handling Strategy

Outcome-grounded routing should fail safe to explicit simpler behavior rather than blocked behavior. If recent outcome evidence is missing, stale, thin, inconsistent, or unavailable because of a lookup/aggregation problem, runtime routing should continue using the simpler scoring path that the current system can already support, record that the request used degraded or evidence-thin behavior, and preserve service continuity. Policy simulation replay should also continue, but it must degrade explicitly and surface approximation notes instead of pretending full precision. Evidence-summary failures should remain visible to operators through the existing request-level and supporting context surfaces, but they must not become a new serving-path single point of failure.

Retries inside route-decision logic should stay minimal. If outcome-evidence lookup fails at decision time, the router should degrade immediately instead of adding retry mazes that increase latency and blur causality. Operator-facing errors and evidence states should stay specific and bounded: explain grounded vs thin/stale/degraded behavior in request-first language, never leak raw internal exceptions, and never use vague “AI confidence” wording. Hosted state remains informational only and must not affect route choice even when stale or unavailable.

## Risks and Unknowns

- The outcome-evidence model could become noisy if the recent window is too broad or the factor set is too large — that would reduce route quality and operator trust.
- Runtime and replay could drift if score factors are computed differently or if persisted evidence is insufficient for reconstruction.
- Request-level evidence could become verbose or dashboard-like if factor presentation is not kept tightly scoped to the selected request.
- The milestone could succeed technically but fail product-wise if tenant summaries or operator furniture start overshadowing request evidence.

## Existing Codebase / Prior Art

- `src/nebula/services/router_service.py` — current additive route-score contract and prompt-complexity routing baseline that M009 will deepen.
- `src/nebula/services/policy_service.py` — central routing/policy enforcement seam that must stay aligned with any richer outcome-informed decisions.
- `src/nebula/services/policy_simulation_service.py` — replay path that already reconstructs decisions from persisted metadata and must preserve runtime/replay parity.
- `src/nebula/services/governance_store.py` — existing tenant-scoped usage-ledger and calibration/evidence derivation seam to extend rather than replace.
- `src/nebula/models/governance.py` — typed governance and request-evidence shapes that should carry richer route factors without widening into a second API family.
- `console/src/app/(console)/observability/page.tsx` — selected-request-first Observability hierarchy that must stay intact.
- `console/src/components/ledger/ledger-request-detail.tsx` — authoritative request-level evidence surface for presenting route factors and evidence state.
- `docs/route-decision-vocabulary.md`, `docs/m006-integrated-proof.md`, and `docs/v4-integrated-proof.md` — existing pointer-only proof and vocabulary seams that should be extended rather than duplicated.

## Relevant Requirements

- R073 — runtime routing uses recent tenant-scoped outcome evidence to improve local-vs-premium decisions
- R074 — replay uses the same outcome-grounded semantics as live runtime
- R075 — persisted request evidence records the actual route factors that influenced the decision
- R076 — operators can inspect grounded vs thin/stale/degraded routing on existing request-first surfaces
- R077 — outcome-grounded routing fails safe to explicit simpler behavior when evidence is weak or unavailable
- R078 — the milestone proves routing improvement without widening into analytics, black-box optimization, or hosted authority

## Scope

### In Scope

- a bounded recent tenant-scoped outcome-evidence contract shared by runtime routing, replay, persistence, and operator evidence
- additive route-score factors for outcome quality pressures such as recent success/failure, fallback pressure, latency, and cost, as long as they remain bounded and explicit
- deterministic sufficiency, staleness, thin-evidence, and degraded-state rules
- request-level persistence of the actual route factors used by live runtime
- replay parity for the richer routing contract through the existing policy simulation seam
- focused request-first operator explanation on existing Observability and request-detail surfaces
- a final integrated proof path covering both a happy path and an honest degraded path

### Out of Scope / Non-Goals

- a new analytics-style routing dashboard or tenant-summary-first product surface
- adaptive or learned route optimization beyond explicit additive scoring
- hosted or fleet-level authority for route choice, calibration, or evidence truth
- a broad new public API surface for routing controls or outcome evidence
- raw prompt or response persistence expansion
- autonomous policy mutation or self-applying optimization behavior

## Technical Constraints

- Keep routing bounded, additive, deterministic, and operator-readable.
- Reuse recent tenant-scoped usage-ledger evidence only; do not introduce hosted or cross-tenant authority.
- Preserve the non-mutating replay contract and explicit approximation notes.
- Keep request-level evidence primary on operator surfaces; tenant summary context remains supporting only.
- Preserve the metadata-only hosted boundary and local runtime authority.
- Extend existing typed governance and route-signal seams rather than inventing a parallel API family.

## Integration Points

- `RouterService` — live outcome-grounded route choice and degraded-state signaling
- `PolicyService` — policy-aligned enforcement and route-decision integration
- `PolicySimulationService` — runtime/replay parity for the richer score contract
- `GovernanceStore` / usage ledger — tenant-scoped outcome evidence derivation and persisted route-factor truth
- `console/src/components/ledger/*` and `console/src/app/(console)/observability/*` — request-first operator explanation surfaces
- existing public `POST /v1/chat/completions` response headers and `GET /v1/admin/usage/ledger` correlation story — integrated proof seam

## Testing Requirements

Require four verification layers. First, unit/contract coverage for outcome-evidence derivation, additive scoring logic, and state transitions between grounded, thin, stale, and degraded behavior. Second, backend integration coverage proving live routing uses the shared outcome-evidence contract, replay uses the same semantics, and persisted request rows capture the actual route factors used. Third, focused console tests proving request detail and Observability expose grounded/thin/stale/degraded state on existing request-first surfaces without dashboard drift. Fourth, final integrated verification proving both a happy-path request and a degraded-path request across public request → persisted ledger row → replay parity → request-first operator inspection. The milestone is not complete if only backend math or only UI copy is verified.

## Acceptance Criteria

- **S01:** A deterministic recent tenant-scoped outcome-evidence contract exists, including explicit sufficient/thin/stale/degraded state rules and typed backend coverage.
- **S02:** A real `POST /v1/chat/completions` request can route differently because of recent tenant-scoped outcome evidence, and the persisted request row records the actual factors used.
- **S03:** `POST /v1/admin/tenants/{tenant_id}/policy/simulate` replays the same outcome-grounded semantics as runtime and marks degraded or approximate behavior honestly when evidence is incomplete.
- **S04:** The selected request in request detail / Observability explains whether routing was grounded, thin, stale, or degraded, and keeps tenant summary context secondary to the persisted request row.
- **S05:** One integrated proof covers a happy-path routed request and an honest degraded-path request without widening Nebula into analytics-product work, black-box optimization, hosted authority, or broad public API expansion.

## Open Questions

- Which exact recent-outcome signals are strong enough to influence live routing without making the model noisy? — Current thinking: favor a small set tied directly to success/failure, fallback pressure, latency pressure, and premium cost pressure.
- How wide should the recent tenant-scoped evidence window be? — Current thinking: keep it bounded and deterministic rather than long-horizon or historical-average heavy.
- How much “quality delta” should replay claim beyond route/cost/status change? — Current thinking: stay explicit and approximation-aware rather than inventing predictive certainty.
