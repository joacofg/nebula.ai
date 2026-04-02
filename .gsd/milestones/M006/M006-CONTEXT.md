# M006: Outcome-Aware Routing Calibration — Context

**Gathered:** 2026-04-01
**Status:** Ready for planning

## Project Description

Create M006: Outcome-Aware Routing Calibration. The milestone closes the remaining routing gap from M005 by turning Nebula’s heuristic-first router into an interpretable, outcome-aware calibrated router that uses recent tenant-scoped ledger evidence, keeps runtime and simulation aligned, exposes calibration state through existing operator surfaces, and validates R039 without widening Nebula into a black-box optimizer, analytics product, hosted-authority expansion, or new public API program.

## Why This Milestone

M005 finished the first real decisioning control-plane milestone, but R039 is still active. The current router exposes richer route signals and route-score evidence, yet route choice still depends mostly on token thresholds, coarse complexity tiers, keyword hints, and policy overrides. M006 exists to finish that seam by making the routing core itself materially better while preserving Nebula’s anti-sprawl posture.

## User-Visible Outcome

### When this milestone is complete, the user can:

- trust that Nebula’s route choice reflects recent tenant-scoped observed outcomes rather than prompt heuristics alone
- inspect whether a request used calibrated routing or fell back to heuristic-only behavior
- preview policy changes against the same calibration semantics used at runtime
- see calibration evidence and degraded-mode state through existing Observability and ledger inspection surfaces
- review one integrated proof path showing better route quality without black-box or analytics drift

### Entry point / environment

- Entry point: routing behavior, policy simulation replay, Observability / ledger detail, and supporting docs under `docs/`
- Environment: existing self-hosted gateway plus operator console
- Live dependencies involved: router service, policy service, policy simulation service, governance store / usage ledger, operator console Observability surfaces, and benchmark / evaluation artifacts

## Completion Class

- Contract complete means: calibrated routing semantics, degraded fallback semantics, and calibration evidence shapes are explicit in runtime, simulation, ledger, and docs without widening Nebula’s public API or persistence boundary.
- Integration complete means: runtime routing, simulation replay, ledger evidence, and Observability all tell the same calibration story for the same tenant and request class.
- Operational complete means: operators can tell when calibrated routing is active, when it is degraded or disabled, and can use the small tenant-scoped control as a safe rollout valve without losing trust in preview behavior.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Nebula routes a real request using interpretable outcome-aware calibration rather than only token-count heuristics.
- A replayed policy simulation produces the same calibrated-versus-degraded routing semantics as live runtime for the same kind of traffic.
- Operators can inspect persisted calibration evidence and degraded-mode state through existing ledger / Observability surfaces.
- A small tenant-scoped control can safely disable or gate calibrated routing without changing the public API contract.
- The assembled milestone improves routing quality without turning into black-box routing, analytics product work, hosted-authority drift, or broad console redesign.

## Risks and Unknowns

- Calibration scoring could become too clever and stop being explainable — that would invalidate the milestone’s core trust claim.
- Runtime and replay could drift if calibration inputs are derived differently in live routing and simulation.
- Evidence windows could become noisy or unstable if tenant-scoped aggregation rules are not bounded and deterministic.
- Operator surfaces could become verbose if calibration evidence is rendered like analytics instead of decision support.
- A tenant control surface could sprawl if it grows beyond a small rollout / safety valve.

## Existing Codebase / Prior Art

- `src/nebula/services/router_service.py` — current route choice still resolves mostly from token thresholds, complexity tiers, keyword hints, and policy overrides; this is the main M006 pressure point.
- `src/nebula/services/policy_service.py` — current policy evaluation already centralizes routing mode, budget, model constraints, and downgrade / denial semantics that M006 must stay aligned with.
- `src/nebula/services/policy_simulation_service.py` — replay already reconstructs route decisions from persisted metadata and route signals, so parity with runtime calibration is a first-class requirement.
- `src/nebula/models/governance.py` — current typed governance and ledger shapes are the right seam for adding calibration evidence without inventing a new API family.
- `console/src/components/ledger/ledger-request-detail.tsx` — existing request-detail surface already renders route and budget evidence in a bounded operator-readable format.
- `docs/route-decision-vocabulary.md` and `docs/v4-integrated-proof.md` — current explanation and proof seams should be extended rather than replaced.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R039 — validate the move from heuristic-first routing to explicit outcome-aware calibrated routing
- R045 — calibration derives from recent tenant-scoped observed outcomes
- R046 — operators can inspect calibration evidence in existing evidence surfaces
- R047 — calibrated routing fails safe to explicit heuristic behavior when evidence is missing, stale, or low-confidence
- R048 — policy simulation replay uses the same calibration semantics as live runtime routing
- R049 — preserve anti-sprawl scope discipline while improving routing quality

## Scope

### In Scope

- a narrow calibration layer over the existing router rather than a broader per-request classifier
- tenant-scoped calibration input derived from existing usage-ledger metadata
- explicit additive scoring and calibrated-vs-heuristic mode markers
- deterministic sufficiency / staleness / degraded-mode rules
- runtime and replay parity for calibration behavior
- bounded calibration evidence in existing Observability / ledger inspection surfaces
- a small tenant-scoped calibrated-routing control as a rollout / safety valve
- integrated proof and evaluation updates for calibrated routing quality

### Out of Scope / Non-Goals

- raw prompt or response persistence expansion for calibration
- black-box ML routing or autonomous optimization
- automatic policy mutation or save-on-preview behavior
- a broad analytics dashboard or routing studio UX
- hosted control-plane authority over routing decisions
- new public API families for calibration control or evidence
- a broad console redesign beyond focused inspection / control additions

## Technical Constraints

- Prefer explicit additive scoring over hidden weighting systems.
- Reuse existing ledger-backed evidence only; do not add raw payload capture.
- Keep calibration tenant-scoped, bounded, and deterministic.
- Preserve the non-mutating simulation contract.
- Reuse existing Observability / ledger evidence surfaces instead of introducing a parallel dashboard.
- Preserve the hosted metadata-only trust boundary and M005’s anti-sprawl posture.

## Integration Points

- `RouterService` — calibrated route choice and degraded-mode signaling
- `PolicyService` — policy-aligned calibration control and budget / routing-mode interplay
- `PolicySimulationService` — runtime/replay parity
- `GovernanceStore` and `UsageLedgerRecord` — calibration evidence persistence / retrieval
- `console/src/components/ledger/*` and `console/src/app/(console)/observability/*` — operator inspection surfaces
- `docs/route-decision-vocabulary.md`, `docs/evaluation.md`, and the new integrated proof artifact — assembled explanation and verification path

## Open Questions

- What is the smallest additive calibration model that materially improves routing while remaining operator-readable?
- Which recent-outcome signals are strong enough to use without making tenant-scoped evidence noisy?
- Should the tenant-scoped calibrated-routing control be strictly on/off, or should it support a very small additional mode without creating a tuning surface?
- How should degraded / stale / insufficient-evidence states be surfaced so operators understand them immediately without reading raw internals?
