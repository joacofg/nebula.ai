# Nebula.ai

## What This Is

Nebula.ai is a self-hosted B2B AI gateway for product and engineering teams shipping LLM-powered features. It routes requests across local and premium providers, applies tenant policy controls, records usage, and exposes operator tooling so companies can reduce LLM cost without giving up reliability or control.

The first product shape is not a broad public SaaS. It is a deployable gateway plus operator console that a startup or scale-up team can run for itself, evaluate with real traffic patterns, and eventually trust as an internal platform component.

## Core Value

Reduce cost per successful LLM request while preserving reliability, control, and operator visibility.

## Requirements

### Validated

- ✓ OpenAI-compatible chat completions are exposed through `POST /v1/chat/completions` — existing
- ✓ Requests can route between local and premium providers with local-to-premium fallback — existing
- ✓ Semantic cache lookup/storage is wired to Qdrant and can short-circuit repeated prompts — existing
- ✓ Multi-tenant governance primitives exist for tenants, API keys, policy, and usage ledger — existing
- ✓ Benchmark tooling exists for route, cache, and fallback scenario runs — existing

### Active

- [ ] Nebula can be deployed through a documented self-hosted path suitable for demos and early customer pilots
- [ ] Operators can manage tenants, API keys, and routing policy through a small web console
- [ ] Operators can run prompts through a playground and immediately see route, provider, cache, fallback, latency, and cost metadata
- [ ] Policy and observability behavior is hardened enough to support real internal B2B usage
- [ ] Benchmarking and documentation clearly prove the product's cost-optimization value

### Out of Scope

- Public customer self-serve signup and billing — adds major auth, billing, and support scope before the core gateway is proven
- Hosted multi-tenant SaaS control plane — defer until the self-hosted product and operations model are validated
- Consumer-facing end-user chat product — Nebula is infrastructure, not the end-user application
- Broad enterprise features like SSO, SCIM, procurement workflows, and compliance packaging — premature for the current stage
- Mobile apps — not relevant to the operator-first product surface

## Context

Nebula is currently a brownfield Python/FastAPI project with a working gateway core, SQLite-backed governance store, Qdrant semantic cache integration, Ollama local provider support, and an OpenAI-compatible premium provider path. The codebase already demonstrates routing, fallback, tenant policy, usage ledger recording, and benchmark execution.

The project is also a university final project, so it must read as a complete software engineering effort: product framing, architecture, code quality, documentation, measurable evaluation, and a strong live demo. That makes a polished operator-facing UI valuable, but only if it strengthens the gateway story instead of distracting from it.

The best initial market fit is startup and scale-up product teams building AI features without a dedicated ML platform team. They are cost-sensitive, move quickly, and can adopt a self-hosted gateway without the enterprise feature burden required by large organizations. AI agencies and consultancies are a secondary adjacent segment, but the roadmap should optimize for internal product teams first.

## Constraints

- **Tech stack**: Keep the existing Python/FastAPI gateway core — replatforming would waste working leverage
- **Product scope**: Self-hosted first — a fully hosted SaaS can come later after the deployment and operations story is proven
- **UI scope**: Build a focused operator console and playground, not a broad customer product UI
- **Project type**: Must support both a strong demo and written documentation for academic evaluation
- **Timeline**: There is time to build deliberately through December 2026, so prefer coherent architecture over rushed shortcuts

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Target startup and scale-up AI product teams first | Best fit for a self-hosted cost-optimization gateway without enterprise overhead | — Pending |
| Keep v1 onboarding admin-managed, not self-serve | Avoid auth/billing/account lifecycle scope before the core operator workflow is solid | — Pending |
| Add a small operator web console plus playground | Improves demoability and product completeness for a B2B infrastructure product | — Pending |
| Keep the backend as FastAPI and add a separate frontend for the console | Preserves the gateway core while allowing a more credible operator UX | — Pending |
| Prioritize self-hosted production readiness before public launch concerns | The current product gap is operational trust, not more speculative surface area | — Pending |

---
*Last updated: 2026-03-15 after initialization*
