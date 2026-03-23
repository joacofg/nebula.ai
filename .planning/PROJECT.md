# Nebula.ai

## What This Is

Nebula.ai is a shipped self-hosted B2B AI gateway for product and engineering teams running LLM-powered features with operator controls, route visibility, and cost-aware evaluation built in. The current shipped product includes the gateway, governance layer, operator console, playground, observability surfaces, benchmark/documentation package, and an optional hosted control plane for bounded onboarding and fleet-management workflows.

## Core Value

Reduce cost per successful LLM request while preserving reliability, control, and operator visibility.

## Current State

- **Shipped version:** v2.0
- **Product shape:** Self-hosted gateway plus operator console, with an optional hosted control plane for onboarding, fleet visibility, and one audited remote-management action
- **Primary workflows shipped:** deployment, admin auth, tenant/API-key/policy management, Playground, Observability, benchmark proof, docs/demo package, hosted deployment enrollment, fleet inventory, trust-boundary disclosure, outage-safe hosted visibility, and audited credential rotation
- **Codebase snapshot:** Python/FastAPI gateway, Next.js console, PostgreSQL-ready governance persistence, Qdrant semantic cache, Ollama local provider path, premium-provider routing, benchmark/report tooling
- **Closeout status:** v2.0 archived on 2026-03-23
- **Active milestone:** None

## Next Milestone Goals

- Decide whether hosted operations should expand beyond one audited action into approval-gated remote workflows.
- Define the next hosted account-model boundary: richer hosted user/org/RBAC flows or public self-serve signup and billing.
- Choose whether the next milestone should deepen hosted diagnostics/remediation or broaden fleet orchestration.

## Archived Planning Context

<details>
<summary>v2.0 validation context</summary>

## Requirements

### Validated

- ✓ Self-hosted deployment path without manual code edits — v1.0
- ✓ Explicit runtime configuration, secrets, and readiness behavior — v1.0
- ✓ Migration-backed governance persistence — v1.0
- ✓ Operator console auth, tenant management, API keys, and policy editing — v1.0
- ✓ Playground request execution with route/cache/fallback/policy metadata — v1.0
- ✓ Observability ledger filters and dependency health views — v1.0
- ✓ Runtime governance enforcement and denied-path explainability plumbing — v1.0
- ✓ Benchmark-backed product proof, architecture docs, and demo materials — v1.0

### Active

- [x] Hosted control plane can register and identify self-hosted Nebula deployments without manual database edits
- [x] Hybrid trust boundary is explicit between hosted metadata/control surfaces and locally enforced runtime behavior — Phase 06
- [x] Operators can see deployment health, status, and version in a hosted plane without weakening self-hosted serving reliability
- [x] Nebula offers at least one safe remote-management flow that is credible for pilot conversations
- [x] Docs and demo narrative explain why the hybrid model exists, what remains self-hosted, and how trust boundaries work — Phase 06

### Out of Scope

- Public self-serve signup and billing before the hybrid pilot story is validated
- Broad RBAC redesign beyond what the hosted-control-plane workflow strictly needs
- Deep enterprise procurement or compliance packaging before the product boundary is proven
- Expanding provider and commercialization features in parallel with the control-plane validation work

## Milestone Status: v2.0 Hosted Control Plane Validation

**Result:** The hosted control plane validation milestone is complete. Nebula now ships a bounded hybrid model where hosted surfaces remain metadata-and-intent only, linking stays outbound-only, and local runtime enforcement remains authoritative.

**Target features:**
- Hosted deployment registration and trusted linking flow for self-hosted gateways
- Hosted deployment inventory with identity, last-seen status, version, and health summary
- Explicit architecture and docs for what metadata leaves the customer environment and what remains locally enforced
- A narrow, safe remote-management capability that proves hybrid control-plane value without breaking runtime trust boundaries
- Pilot-ready docs, demo flow, and architecture narrative for hosted-control-plane onboarding

## Context

Nebula now reads like a complete brownfield product instead of a gateway prototype. It has a documented deployment path, credible runtime operations, operator-facing management surfaces, routed request explainability, and a benchmark/documentation layer that supports both product demos and academic evaluation.

The best near-term fit is still startup and scale-up teams that need infrastructure-level cost control without building a full internal ML platform. The current milestone is validating whether that self-hosted-first product should stay standalone or gain an optional hosted control plane for onboarding, fleet visibility, and limited remote management.

## Constraints

- **Tech stack**: Keep the existing Python/FastAPI gateway core and Next.js console while layering any hosted control plane onto the current architecture
- **Product scope**: Expand only where it strengthens operator trust, onboarding, control, or adoption for the hybrid model
- **Project type**: Continue to support both live demo quality and written academic documentation
- **Trust boundary**: Loss of hosted control-plane connectivity must not break the self-hosted gateway's core serving path
- **Roadmap discipline**: Define v2.0 from fresh requirements rather than carrying the v1.0 archive forward informally

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Target startup and scale-up AI product teams first | Best fit for a self-hosted cost-optimization gateway without enterprise overhead | ✓ Good |
| Keep v1 onboarding admin-managed, not self-serve | Avoid auth/billing/account lifecycle scope before the core operator workflow is solid | ✓ Good |
| Add a small operator web console plus playground | Improves demoability and product completeness for a B2B infrastructure product | ✓ Good |
| Keep the backend as FastAPI and add a separate frontend for the console | Preserves the gateway core while allowing a more credible operator UX | ✓ Good |
| Prioritize self-hosted production readiness before public launch concerns | The current product gap is operational trust, not speculative surface area | ✓ Good |
| Docker Compose is the single supported self-hosted entrypoint for v1.0 | Keeps the operator deployment story narrow and documented in one place | ✓ Good |
| Playground metadata and persisted ledger outcome should remain visibly separate | Preserves operator clarity between immediate response evidence and recorded usage | ✓ Good |
| Product proof should stay benchmark-led rather than becoming a generic demo tour | Keeps the product story measurable and grounded in real routing/cost behavior | ✓ Good |
| v2.0 validates a hybrid hosted-control-plane direction rather than jumping to full SaaS | Hosted management improved onboarding and pilot credibility without weakening the self-hosted trust boundary | ✓ Good |

</details>

---
*Last updated: 2026-03-23 after archiving the v2.0 milestone*
