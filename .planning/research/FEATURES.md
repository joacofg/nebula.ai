# Feature Research

**Domain:** B2B LLM gateway and operator platform
**Researched:** 2026-03-15
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| OpenAI-compatible gateway API | Teams want drop-in compatibility for existing SDK clients | MEDIUM | Nebula already has a solid base here |
| Provider routing and fallback | Buyers expect reliability across model/provider failures | MEDIUM | Core to the product promise |
| Cost and usage visibility | Cost optimizer products must prove where spend goes | MEDIUM | Usage ledger + dashboard are essential |
| Tenant/API-key policy controls | B2B buyers need bounded access and governance | MEDIUM | Already partially present in Nebula |
| Operator-friendly setup and docs | Infrastructure products lose trust quickly if deployment is unclear | MEDIUM | Critical for demos and pilots |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Route metadata and savings visibility in a playground | Makes cost optimization tangible during demos and trials | MEDIUM | Strong fit for a university demo and future sales story |
| Self-hosted deployment with opinionated defaults | Helps teams who want cost control without sending all traffic to a third-party gateway SaaS | MEDIUM | Best initial market wedge |
| Policy-aware routing by tenant | Turns Nebula into a platform control point, not just a proxy | HIGH | Strong B2B value if hardened well |
| Benchmark-based proof of savings and reliability | Converts product claims into measurable evidence | MEDIUM | Important for thesis/demo and future product marketing |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Customer self-serve signup and billing in v1 | Feels like a “real SaaS” feature | Pulls focus into auth, billing, support, and account lifecycle complexity | Keep admin-managed onboarding for v1 |
| Broad enterprise identity stack immediately | Sounds attractive for B2B credibility | SSO/SCIM/compliance work can consume the roadmap before the core product is proven | Defer to post-pilot stage |
| End-user chat application features | Easy to demo superficially | Dilutes the gateway/product-platform narrative | Build an operator playground instead |

## Feature Dependencies

```text
Operator console
    └──requires──> stable admin APIs
                       └──requires──> durable governance store

Playground metadata view ──requires──> reliable route/cost/cache headers

Benchmark proof ──enhances──> sales/demo narrative

Hosted demo mode ──conflicts──> local-Ollama assumptions in cheap/free hosting
```

### Dependency Notes

- **Operator console requires stable admin APIs:** The UI should not invent backend behavior; Phase 1 hardening should happen before heavy UI work
- **Stable admin APIs require a durable governance story:** Schema churn and implicit bootstrap logic make UI iteration risky
- **Playground metadata requires reliable headers and ledger logic:** Demo credibility depends on route/cost feedback being correct
- **Hosted demo mode conflicts with local-Ollama assumptions:** Free hosting is easier if the demo uses premium-only routing and externalized state

## MVP Definition

### Launch With (v1)

- [ ] Self-hosted deployment path with production-safe configuration and persistence guidance — essential for pilot adoption
- [ ] Operator console for tenants, API keys, policy, and ledger visibility — essential for B2B operability
- [ ] Playground showing route/provider/cache/fallback/cost metadata — essential for demoability
- [ ] Benchmark and documentation pack proving savings/reliability story — essential for trust

### Add After Validation (v1.x)

- [ ] Additional provider profiles and richer routing heuristics — add once the current gateway path is operationally solid
- [ ] Stronger observability and traces — add when early pilots need deeper incident analysis
- [ ] Hosted demo deployment mode — add after the self-hosted package is coherent

### Future Consideration (v2+)

- [ ] Customer self-serve onboarding, billing, and account lifecycle — defer until there is real buyer validation
- [ ] Enterprise identity/compliance surface — defer until the target customers require it
- [ ] Marketplace-style provider catalog and advanced workflow automation — defer until the core wedge is proven

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Self-hosted deployment baseline | HIGH | MEDIUM | P1 |
| Operator console | HIGH | MEDIUM | P1 |
| Playground with metadata | HIGH | MEDIUM | P1 |
| Governance hardening | HIGH | MEDIUM | P1 |
| Benchmark proof package | HIGH | MEDIUM | P1 |
| Hosted demo mode | MEDIUM | MEDIUM | P2 |
| Additional providers | MEDIUM | MEDIUM | P2 |
| Self-serve onboarding | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| LLM gateway | Portkey positions an AI gateway with reliability and control | LiteLLM positions a unified model gateway/proxy | Keep Nebula self-hosted-first with cost optimization as the central story |
| Observability | Helicone focuses heavily on logs, analytics, and monitoring | Langfuse focuses on LLM engineering observability/evaluation | Keep observability operator-focused and tied to savings proof |
| Budgets / controls | LiteLLM exposes budgets and virtual keys | Portkey emphasizes policy/governance controls | Harden per-tenant policy and usage visibility before expanding scope |

## Sources

- [Portkey official product pages](https://portkey.ai/)
- [Helicone official product pages](https://www.helicone.ai/)
- [LiteLLM docs](https://docs.litellm.ai/)
- [Langfuse official site](https://langfuse.com/)

---
*Feature research for: B2B LLM gateway and operator platform*
*Researched: 2026-03-15*
