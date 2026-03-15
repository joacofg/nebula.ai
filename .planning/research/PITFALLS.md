# Pitfalls Research

**Domain:** B2B LLM gateway and operator platform
**Researched:** 2026-03-15
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Claiming cost optimization without proving it

**What goes wrong:**
The product says it saves money, but operators cannot see route decisions, avoided spend, or benchmark evidence.

**Why it happens:**
Teams build the gateway mechanics first and postpone reporting/evaluation.

**How to avoid:**
Make benchmark evidence, route metadata, and ledger visibility a core milestone rather than a polish task.

**Warning signs:**
- Demos rely on verbal explanation instead of visible evidence
- Ledger lacks enough data to explain a request outcome

**Phase to address:**
Phase 3 and Phase 4

---

### Pitfall 2: Letting control-plane features outrun the reliable gateway core

**What goes wrong:**
UI, onboarding, and future SaaS ideas grow faster than deployment hardening, policy correctness, and backend durability.

**Why it happens:**
Operator-facing features are easier to demo than infrastructure trust work.

**How to avoid:**
Ship deployment, migration, and governance hardening before expanding into self-serve or hosted-SaaS scope.

**Warning signs:**
- New UI screens appear before runtime health/readiness improves
- Schema changes still depend on implicit bootstrap logic

**Phase to address:**
Phase 1

---

### Pitfall 3: Building enterprise scope too early

**What goes wrong:**
The roadmap gets consumed by SSO, billing, compliance, and account lifecycle work before the core market wedge is proven.

**Why it happens:**
B2B products often imitate larger incumbents too early.

**How to avoid:**
Target startup and scale-up teams first, keep onboarding admin-managed, and defer enterprise procurement features.

**Warning signs:**
- Roadmap items mention SSO, SCIM, billing, or hosted control plane before self-hosted pilots
- Demo value becomes unclear because too much scope is “coming soon”

**Phase to address:**
Phase 0 scope discipline, reinforced through all phases

---

### Pitfall 4: Hiding operational failures behind “optional” infrastructure

**What goes wrong:**
Cache or provider failures silently degrade the product, so operators cannot distinguish optimization success from degraded mode.

**Why it happens:**
Optional services are treated as implementation details instead of product behavior.

**How to avoid:**
Expose cache/provider health clearly in the API and operator console, and test degraded modes explicitly.

**Warning signs:**
- Cache disables itself with only logs and no operator signal
- Benchmark failures are hard to diagnose because process logs are discarded

**Phase to address:**
Phase 1 and Phase 3

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keeping all gateway orchestration in one service file | Faster initial delivery | High change risk and weak separation of concerns | Acceptable only until the first production-hardening phase |
| Using SQLite bootstrap DDL as the migration system | Very quick setup | Fragile schema evolution | Acceptable for local dev only |
| Treating no-op policy fields as “future ready” | Avoids making a decision now | Confusing product behavior and false operator expectations | Never acceptable once UI exposes the policy |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| LLM providers | Assume every provider exposes identical response and streaming semantics | Normalize responses behind provider adapters and test each path |
| Qdrant | Assume cache enablement equals healthy cache behavior | Surface cache health separately from cache configuration |
| Hosting platforms | Assume free hosting supports local inference and persistent disk | Design hosted demo mode separately from self-hosted mode |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Embedding on every cache lookup/store | Cache overhead can offset savings | Measure cache hit value and optimize embedding path | Breaks when traffic or prompt volume grows |
| Serial SQLite writes for all governance/ledger activity | Latency spikes and contention | Move to Postgres or buffered writes for serious usage | Breaks under multi-user/operator or higher request load |
| Large-file orchestration in one service | Slow iteration and regression risk | Extract focused collaborators before feature growth continues | Breaks as more provider/policy cases are added |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Shipping with default admin/bootstrap secrets | Unauthorized access in any shared environment | Require explicit secrets outside local mode |
| Over-collecting prompts/responses by default | Customer privacy and trust risk | Keep capture opt-in, explicit, and enforced if introduced |
| Treating admin key auth as the final product auth model | Weak operator UX and security posture | Keep v1 admin-managed but plan stronger operator auth later |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing only raw logs instead of request outcome summaries | Operators cannot quickly understand value | Expose route, provider, cache, fallback, latency, and cost in one view |
| Building a consumer-style chat UI | Confuses the product narrative | Build an operator playground centered on diagnostics and controls |
| Hiding deployment complexity in docs | Users fail setup and lose trust | Provide one opinionated self-hosted path first |

## "Looks Done But Isn't" Checklist

- [ ] **Deployment:** Often missing secret rotation and migration guidance — verify a fresh operator can deploy from docs alone
- [ ] **Policy controls:** Often missing runtime enforcement — verify UI/API settings change actual request behavior
- [ ] **Playground:** Often missing believable metadata — verify every demo request shows route/provider/cache/fallback/cost information
- [ ] **Benchmarks:** Often missing reproducibility — verify reports can be regenerated from committed commands and datasets

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Weak savings evidence | MEDIUM | Expand ledger/reporting, add benchmark baselines, update demo flow |
| Overgrown product scope | HIGH | Cut roadmap back to self-hosted operator product and defer SaaS/enterprise features |
| Fragile persistence story | MEDIUM | Introduce migrations and durable storage before adding more admin surface |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Unproven savings claims | Phase 4 | Benchmark reports and playground metadata show measurable outcomes |
| UI outrunning backend trust | Phase 1 | Self-hosted deployment and runtime health are solid before major UI expansion |
| Enterprise scope too early | Phase 1 roadmap framing | v1 excludes self-serve billing/SSO/hosted control plane |
| Silent degraded mode | Phase 3 | Operator console and APIs expose cache/provider health and degraded behavior |

## Sources

- Existing Nebula codebase map and concerns audit
- [LiteLLM docs](https://docs.litellm.ai/)
- [Portkey official site](https://portkey.ai/)
- [Helicone official site](https://www.helicone.ai/)

---
*Pitfalls research for: B2B LLM gateway and operator platform*
*Researched: 2026-03-15*
