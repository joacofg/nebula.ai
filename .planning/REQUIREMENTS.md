# Requirements: Nebula.ai

**Defined:** 2026-03-15
**Core Value:** Reduce cost per successful LLM request while preserving reliability, control, and operator visibility.

## v1 Requirements

### Platform Foundation

- [x] **PLAT-01**: Operator can deploy Nebula through one documented self-hosted path without manual code edits
- [x] **PLAT-02**: Operator can run Nebula outside local development with non-default secrets and explicit environment configuration
- [x] **PLAT-03**: Operator can evolve governance persistence through an explicit migration workflow
- [x] **PLAT-04**: Operator can verify gateway readiness, cache health, and governance-store health before sending production traffic

### Operator Console

- [x] **CONS-01**: Operator can open a web console and authenticate as an administrator for a Nebula deployment
- [x] **CONS-02**: Operator can create, view, update, and deactivate tenants from the console
- [x] **CONS-03**: Operator can create and revoke API keys from the console
- [x] **CONS-04**: Operator can update tenant routing policy from the console

### Playground & Observability

- [x] **PLAY-01**: Operator can send a test prompt through Nebula from a playground UI
- [ ] **PLAY-02**: Playground shows route target, provider, cache-hit status, fallback status, latency, and policy outcome for each request
- [ ] **OBS-01**: Operator can inspect usage-ledger entries by tenant, route outcome, and time window
- [ ] **OBS-02**: Operator can see whether cache and upstream providers are healthy or degraded

### Governance & Routing

- [ ] **GOV-01**: Tenant policy changes affect runtime behavior for routing mode, fallback enablement, semantic-cache enablement, and premium-model allowlists
- [ ] **GOV-02**: Admin and tenant operations return clear error states for invalid credentials, inactive tenants, and disallowed routing choices
- [ ] **ROUT-01**: Nebula records enough metadata per request to explain why a route was chosen and whether a fallback occurred

### Evaluation & Product Proof

- [ ] **EVAL-01**: Operator can run a repeatable benchmark suite that compares local, premium, cache-hit, and fallback scenarios
- [ ] **EVAL-02**: Benchmark artifacts summarize latency, route outcome, token usage, and estimated premium cost
- [ ] **DOCS-01**: Repository documentation includes a demo script, deployment guide, and architecture explanation suitable for academic review and pilot onboarding

## v2 Requirements

### Hosted Product Expansion

- **HOST-01**: Customer can access Nebula through a hosted control plane
- **HOST-02**: Customer can onboard a workspace without manual admin intervention

### Enterprise Readiness

- **ENT-01**: Operator can authenticate through SSO
- **ENT-02**: Organization can manage users and roles beyond a single admin key
- **ENT-03**: Product includes compliance and procurement-ready operational controls

### Commercialization

- **COMM-01**: Customer billing and plan enforcement are integrated into the product
- **COMM-02**: Product supports broader provider catalog management and pricing policy controls

## Out of Scope

| Feature | Reason |
|---------|--------|
| Public customer self-serve signup | Too much auth/billing/account lifecycle scope for the current milestone |
| End-user chat application | Nebula is infrastructure, not the end-user product |
| Mobile apps | Not relevant to the operator workflow |
| Broad enterprise identity/compliance scope | Premature before the self-hosted operator product is validated |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PLAT-01 | Phase 1 | Complete |
| PLAT-02 | Phase 1 | Complete |
| PLAT-03 | Phase 1 | Complete |
| PLAT-04 | Phase 1 | Complete |
| CONS-01 | Phase 2 | Complete |
| CONS-02 | Phase 2 | Complete |
| CONS-03 | Phase 2 | Complete |
| CONS-04 | Phase 2 | Complete |
| PLAY-01 | Phase 3 | Complete |
| PLAY-02 | Phase 3 | Pending |
| OBS-01 | Phase 3 | Pending |
| OBS-02 | Phase 3 | Pending |
| GOV-01 | Phase 4 | Pending |
| GOV-02 | Phase 4 | Pending |
| ROUT-01 | Phase 4 | Pending |
| EVAL-01 | Phase 5 | Pending |
| EVAL-02 | Phase 5 | Pending |
| DOCS-01 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-15*
*Last updated: 2026-03-16 after 03-01 completion*
