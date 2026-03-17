# Nebula.ai

## What This Is

Nebula.ai is a shipped self-hosted B2B AI gateway for product and engineering teams running LLM-powered features with operator controls, route visibility, and cost-aware evaluation built in. The v1.0 product includes the gateway, governance layer, operator console, playground, observability surfaces, and benchmark/documentation package needed for demos, pilot onboarding, and academic review.

## Core Value

Reduce cost per successful LLM request while preserving reliability, control, and operator visibility.

## Current State

- **Shipped version:** v1.0
- **Product shape:** Self-hosted gateway plus operator console
- **Primary workflows shipped:** deployment, admin auth, tenant/API-key/policy management, Playground, Observability, benchmark proof, docs/demo package
- **Codebase snapshot:** Python/FastAPI gateway, Next.js console, PostgreSQL-ready governance persistence, Qdrant semantic cache, Ollama local provider path, premium-provider routing, benchmark/report tooling
- **Closeout status:** Milestone audit passed requirements and integration, with accepted human-review tech debt in Phase 1 and Phase 4

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

- [ ] Hosted control-plane direction and onboarding model for the next product stage
- [ ] Stronger organization/user model beyond a single admin key
- [ ] Enterprise-facing identity and operational controls once the self-hosted product is validated
- [ ] Expanded provider catalog, pricing policy controls, and commercialization surface

### Out of Scope

- Public customer self-serve signup and billing for now
- Consumer-facing chat application
- Mobile apps
- Broad enterprise procurement/compliance packaging before the next milestone defines concrete demand

## Next Milestone Goals

- Decide whether Nebula should stay strictly self-hosted in the next milestone or begin a hosted control-plane track.
- Replace the single-admin-key trust model with a more deliberate org/user/auth story.
- Decide which enterprise/commercial requirements actually matter based on the shipped v1.0 product shape.
- Preserve the benchmark-led proof narrative while expanding the product only where it strengthens operator value.

## Context

Nebula now reads like a complete brownfield product instead of a gateway prototype. It has a documented deployment path, credible runtime operations, operator-facing management surfaces, routed request explainability, and a benchmark/documentation layer that supports both product demos and academic evaluation.

The best near-term fit is still startup and scale-up teams that need infrastructure-level cost control without building a full internal ML platform. The next milestone should validate whether that product shape stays self-hosted-first or needs a hosted control-plane layer.

## Constraints

- **Tech stack**: Keep the existing Python/FastAPI gateway core and Next.js console
- **Product scope**: Expand only where it strengthens operator trust, control, or adoption
- **Project type**: Continue to support both live demo quality and written academic documentation
- **Roadmap discipline**: Define the next milestone from fresh requirements rather than carrying this archive forward informally

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

---
*Last updated: 2026-03-17 after v1.0 milestone closeout*
