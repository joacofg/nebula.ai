# Project Research Summary

**Project:** Nebula.ai
**Domain:** B2B LLM gateway and operator platform
**Researched:** 2026-03-15
**Confidence:** HIGH

## Executive Summary

Nebula.ai fits best as a self-hosted B2B infrastructure product for startup and scale-up teams shipping AI features without a dedicated ML platform team. In that segment, the strongest wedge is not “all-in-one enterprise AI platform”; it is a deployable gateway that reduces cost, improves reliability, and gives operators enough control to trust it in internal production workflows.

The recommended approach is to keep the current FastAPI gateway core, add a focused operator console in Next.js, and harden the deployment/governance/observability story before expanding into self-serve onboarding or hosted SaaS scope. The main risk is drifting into surface-level demo work while the underlying runtime and persistence story remain fragile.

## Key Findings

### Recommended Stack

The current backend direction is sound: FastAPI for the gateway, Qdrant for semantic cache, and provider adapters for local/premium execution. The primary architectural change should be a durable governance store with migrations and a separate operator UI. That combination preserves the working backend while making the product look and behave like something a B2B buyer could actually adopt.

**Core technologies:**
- FastAPI: gateway/admin API — preserves the existing working architecture
- Next.js 16.x: operator console — best fit for a polished admin/playground experience
- PostgreSQL: durable governance/ledger store — needed for a more credible deployment story
- Qdrant: semantic cache store — already aligned with the product’s optimization path

### Expected Features

The launch product should focus on the features buyers expect from an AI gateway, plus one strong differentiator: making savings and routing decisions visible.

**Must have (table stakes):**
- OpenAI-compatible gateway API — users expect easy adoption
- Policy and usage visibility — users expect control and proof of spend behavior
- Reliable routing and fallback — users expect infrastructure resilience
- Deployable self-hosted setup — users expect to be able to run the product

**Should have (competitive):**
- Operator playground with route/provider/cache/fallback/cost visibility — differentiator
- Benchmark reports that prove cost optimization and reliability claims — differentiator

**Defer (v2+):**
- Customer self-serve onboarding and billing — not essential for launch

### Architecture Approach

Use a control-plane/data-plane split: keep the FastAPI service responsible for request handling, policy enforcement, routing, and ledger recording, while a separate Next.js console acts as the operator surface for administration and demos.

**Major components:**
1. Gateway API — request routing, fallback, policy enforcement
2. Governance persistence — tenants, keys, policies, usage ledger
3. Operator console — admin workflows and playground
4. Benchmark/reporting layer — measurable product proof

### Critical Pitfalls

1. **Claiming cost optimization without proof** — make reports and route metadata part of the core roadmap
2. **Letting UI outrun backend trust** — ship deployment and persistence hardening first
3. **Building enterprise scope too early** — stay focused on startup/scale-up teams and admin-managed onboarding
4. **Hiding degraded modes** — expose cache and provider health clearly

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Self-Hosted Foundation
**Rationale:** Trust starts with deployability and runtime safety
**Delivers:** Deployment path, durable persistence direction, runtime health hardening
**Addresses:** Table-stakes deployability and operator trust
**Avoids:** UI-first scope drift

### Phase 2: Operator Console
**Rationale:** Once the backend is trustworthy enough, the operator surface becomes the best demo and daily-use interface
**Delivers:** Tenant/key/policy workflows and a real admin console
**Uses:** Next.js UI stack and stable admin APIs
**Implements:** Control-plane surface

### Phase 3: Playground and Observability
**Rationale:** The product must make route/cost/cache outcomes visible
**Delivers:** Playground, ledger views, degraded-mode visibility
**Uses:** Existing metadata headers and ledger backbone

### Phase 4: Benchmark Proof
**Rationale:** Nebula’s value proposition must be measurable, not just described
**Delivers:** Report generation, benchmark baselines, demo evidence

### Phase 5: Productization
**Rationale:** Finish documentation, packaging, and demo narrative so the system reads as a complete product
**Delivers:** End-to-end docs, polished workflows, pilot-ready packaging

### Phase Ordering Rationale

- Deployment and persistence come before UI because B2B infrastructure trust matters more than cosmetics
- The operator console comes before broader product expansion because it improves demoability and operations without changing the product wedge
- Benchmark proof comes before hosted-SaaS aspirations because cost savings are the core claim to validate

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Durable persistence and self-hosted packaging choices
- **Phase 2:** UI information architecture for operator workflows

Phases with standard patterns:
- **Phase 4:** Benchmark/report generation has an existing foundation in the repo

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Based on current codebase plus official framework/database docs |
| Features | HIGH | Strongly supported by current gateway market patterns |
| Architecture | HIGH | Fits both the codebase and the product narrative |
| Pitfalls | HIGH | Directly informed by current Nebula gaps and common gateway product failure modes |

**Overall confidence:** HIGH

### Gaps to Address

- Free-hosted demo mode is possible only with product compromises; the main roadmap should remain self-hosted-first
- The current roadmap should decide whether prompt/response capture is a true feature or should stay out of v1 entirely

## Sources

### Primary (HIGH confidence)
- [Next.js 16 official release](https://nextjs.org/blog/next-16) — verified UI platform direction
- [PostgreSQL docs and versioning policy](https://www.postgresql.org/docs/) — verified supported durable database options
- [Redis 8 docs](https://redis.io/docs/latest/develop/whats-new/8-0/) — verified optional supporting infrastructure direction

### Secondary (MEDIUM confidence)
- [LiteLLM docs](https://docs.litellm.ai/) — market pattern reference for gateway/budget controls
- [Portkey official site](https://portkey.ai/) — market pattern reference for gateway positioning
- [Helicone official site](https://www.helicone.ai/) — market pattern reference for observability positioning

---
*Research completed: 2026-03-15*
*Ready for roadmap: yes*
