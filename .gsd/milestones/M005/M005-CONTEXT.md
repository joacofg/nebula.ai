# M005: Adaptive Decisioning Control Plane — Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

## Project Description

Create M005: Adaptive Decisioning Control Plane. Objective: turn Nebula's current routing, policy, usage-ledger, and semantic-cache surfaces into a stronger operator decisioning system. The milestone should improve how Nebula makes routing choices and how operators make change decisions by adding adaptive routing inputs, policy simulation, hard budget guardrails, cache tuning visibility, and recommendation-grade feedback. Preserve Nebula's existing guardrails: no broad API-parity push, no large SDK program, no hosted authority drift, and no unrelated app-platform expansion.

## Why This Milestone

Nebula now has credible adoption proof, operator evidence surfaces, and hosted reinforcement. What still feels underpowered is the decision loop itself. The current router is intentionally simple, the policy surface is explicit but shallow, budget handling is mostly advisory, and the cache remains powerful but opaque. v4 should therefore focus on decision quality and actionability, not on adding more public API surface area.

This milestone exists to move Nebula from "gateway with explainable outcomes" toward "control plane that improves those outcomes safely."

## User-Visible Outcome

### When this milestone is complete, the user can:

- configure and trust richer routing behavior that accounts for real operator constraints rather than only prompt heuristics
- simulate a policy or routing change against real recent traffic before applying it
- enforce harder spend guardrails with graceful downgrade behavior
- see which policy, routing, or cache changes are likely to improve cost, latency, or reliability
- inspect and tune semantic-cache behavior with enough visibility to improve savings without guessing

### Entry point / environment

- Entry points: policy editor, Observability, routing behavior, and supporting docs under `docs/`
- Environment: existing self-hosted gateway plus operator console
- Live dependencies involved: routing service, policy service, usage ledger, semantic cache, runtime health, and the existing admin console

## Completion Class

- Contract complete means: the new routing, simulation, and guardrail semantics are explicit in policy/runtime/docs and do not silently widen Nebula's public API promise.
- Integration complete means: operator-facing control surfaces and backend decision logic agree on how routing, simulation, budget enforcement, and cache tuning work.
- Operational complete means: operators can make better routing and budget decisions with lower risk, using real Nebula evidence rather than intuition alone.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Nebula routes more intentionally than the current prompt-length-plus-keyword heuristic.
- An operator can safely preview the likely effect of a policy or routing change before applying it.
- Hard spend guardrails can change runtime behavior predictably and legibly.
- Cache tuning and recommendation surfaces improve the savings/reliability story without becoming opaque or over-automated.
- The assembled milestone improves decision quality and operator control without turning into broad parity, SDK, or hosted-authority work.

## Risks and Unknowns

- Adaptive routing can become overcomplicated quickly if the scoring model is not interpretable.
- Policy simulation could drift into a separate analytics product if it stops being tied to the real ledger and live runtime model.
- Hard budget controls may create confusing request behavior unless downgrade and denial semantics are explicit.
- Recommendation surfaces can feel fake if they are not grounded in existing evidence and well-defined tradeoffs.
- Cache tuning can sprawl if it turns into a full cache-management subsystem rather than a focused control plane.

## Existing Codebase / Prior Art

- `src/nebula/services/router_service.py` — current route choice is still largely prompt-length and keyword based; this is the main v4 pressure point.
- `src/nebula/models/governance.py` — current policy already exposes routing mode, model allowlist, semantic cache toggle, fallback toggle, max per-request premium cost, and soft budget.
- `console/src/components/policy/policy-form.tsx` — current operator policy workflow is explicit but lacks simulation and projected impact.
- `console/src/app/(console)/observability/page.tsx` — current Observability is strong at post-hoc explanation but weak at next-best action.
- `src/nebula/services/semantic_cache_service.py` — current semantic cache is real and potentially valuable but largely opaque to operators.
- `src/nebula/benchmarking/run.py` and usage-ledger evidence — existing proof machinery can be repurposed into a stronger recommendation and scorecard loop.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R039 — richer route selection based on explicit decision signals and outcome-aware scoring
- R040 — policy/routing simulation against real recent traffic
- R041 — hard spend guardrails with graceful downgrade behavior
- R042 — recommendation-grade operator feedback
- R043 — inspectable and tunable semantic-cache behavior
- R044 — preserve v4 scope discipline around decisioning

## Scope

### In Scope

- adaptive routing inputs and explicit route-decision reasoning
- policy and routing simulation grounded in real ledger history
- hard spend guardrails and clear downgrade/deny semantics
- recommendation and projected-impact surfaces tied to existing evidence
- semantic-cache visibility and tuning that materially improves operator control
- integrated proof and docs that show the decisioning loop clearly

### Out of Scope / Non-Goals

- broad new public API endpoints or general OpenAI parity work
- a large Nebula-specific SDK or helper-library program
- hosted/control-plane authority over local runtime enforcement
- commercial billing, packaging, or enterprise role redesign
- a generic app/workload management platform
- opaque fully autonomous optimization that operators cannot interpret

## Technical Constraints

- Keep the public API promise narrow and compatible-first; v4 should improve internal decision quality and operator controls first.
- Prefer explicit decision signals and explainable scoring over black-box routing.
- Reuse the usage ledger and current observability surfaces as the factual basis for simulation and recommendations wherever possible.
- Treat cache tuning as an operator control-plane enhancement, not a new data platform.
- Preserve the hosted metadata-only trust boundary and local runtime authority.

## Integration Points

- Routing service and chat path decision logic
- Governance policy model and admin policy APIs
- Usage ledger and Observability request-detail flow
- Semantic cache service and related runtime-health context
- Operator console pages for Policy and Observability
- Docs and proof artifacts under `docs/`

## Open Questions

- What is the smallest interpretable routing score model that materially beats the current heuristic?
- Should budget guardrails prefer downgrade, deny, or hybrid behavior by default?
- Which simulation outputs are enough to build operator trust without turning into a full analytics product?
- How much cache visibility is needed before the feature becomes high-friction rather than empowering?
