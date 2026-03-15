# Roadmap: Nebula.ai

## Overview

This roadmap turns Nebula from a promising gateway prototype into a self-hosted B2B product that a startup or scale-up engineering team can evaluate, operate, and eventually trust. The sequence is deliberate: make the backend deployable and trustworthy first, then add the operator surface, then strengthen product proof around governance, observability, and measurable savings.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Self-Hosted Foundation** - Make Nebula deployable and operationally safe beyond local development
- [ ] **Phase 2: Operator Console** - Add the admin UI for tenants, API keys, and policy management
- [ ] **Phase 3: Playground & Observability** - Expose the product’s routing and cost behavior in an operator-facing workflow
- [ ] **Phase 4: Governance Hardening** - Close policy/runtime gaps and strengthen the control plane
- [ ] **Phase 5: Product Proof & Delivery** - Finish benchmark proof, documentation, and pilot/demo packaging

## Phase Details

### Phase 1: Self-Hosted Foundation
**Goal**: Nebula can be deployed and operated through a credible self-hosted path with explicit runtime health and durable persistence direction.
**Depends on**: Nothing (first phase)
**Requirements**: [PLAT-01, PLAT-02, PLAT-03, PLAT-04]
**Success Criteria** (what must be TRUE):
  1. Operator can deploy Nebula from documented steps without manual code edits.
  2. Nebula refuses unsafe non-local startup defaults and uses explicit runtime configuration.
  3. Persistence changes follow a migration workflow instead of implicit bootstrap-only schema creation.
  4. Operators can verify readiness for gateway, governance store, and cache before trusting the deployment.
**Plans**: 3/3 plans executed

Plans:
- [x] 01-01: Define the self-hosted packaging and runtime topology
- [x] 01-02: Harden configuration, secrets, and health/readiness behavior
- [x] 01-03: Introduce a durable persistence and migration path

### Phase 2: Operator Console
**Goal**: Operators can manage the deployment through a focused web console instead of raw API calls only.
**Depends on**: Phase 1
**Requirements**: [CONS-01, CONS-02, CONS-03, CONS-04]
**Success Criteria** (what must be TRUE):
  1. Operator can authenticate into the console for a Nebula deployment.
  2. Operator can create and manage tenants from the UI.
  3. Operator can create and revoke API keys from the UI.
  4. Operator can inspect and update tenant routing policy from the UI.
**Plans**: 3 plans

Plans:
- [ ] 02-01: Stand up the frontend shell and admin authentication model
- [ ] 02-02: Implement tenant and API key workflows
- [ ] 02-03: Implement tenant policy management workflows

### Phase 3: Playground & Observability
**Goal**: Nebula visibly demonstrates how it routes, caches, falls back, and records request outcomes.
**Depends on**: Phase 2
**Requirements**: [PLAY-01, PLAY-02, OBS-01, OBS-02]
**Success Criteria** (what must be TRUE):
  1. Operator can run prompts from a playground against the live gateway.
  2. Each playground request displays provider, route target, cache/fallback status, latency, and policy outcome.
  3. Operator can inspect usage-ledger data through the console with meaningful filters.
  4. Operator can tell when cache or provider dependencies are degraded.
**Plans**: 3 plans

Plans:
- [ ] 03-01: Build the playground request/response workflow
- [ ] 03-02: Surface route and cost metadata in the UI
- [ ] 03-03: Build observability views for ledger and dependency health

### Phase 4: Governance Hardening
**Goal**: Policy controls and runtime behavior are aligned well enough for real B2B internal use.
**Depends on**: Phase 3
**Requirements**: [GOV-01, GOV-02, ROUT-01]
**Success Criteria** (what must be TRUE):
  1. Policy controls exposed in the API/UI always correspond to enforced runtime behavior.
  2. Invalid or forbidden admin and tenant operations return clear, predictable error states.
  3. Operators can explain request routing decisions from recorded metadata and runtime outputs.
**Plans**: 2 plans

Plans:
- [ ] 04-01: Align policy surface with enforced backend behavior
- [ ] 04-02: Harden request metadata, errors, and governance tests

### Phase 5: Product Proof & Delivery
**Goal**: Nebula has a measurable product story and polished documentation suitable for demos, academic evaluation, and pilot onboarding.
**Depends on**: Phase 4
**Requirements**: [EVAL-01, EVAL-02, DOCS-01]
**Success Criteria** (what must be TRUE):
  1. Operator can run repeatable benchmarks and generate artifacts that compare route outcomes and estimated spend.
  2. Demo materials clearly show how Nebula saves cost and handles degraded scenarios.
  3. Documentation explains setup, architecture, and evaluation in a way that another engineer can follow.
**Plans**: 3 plans

Plans:
- [ ] 05-01: Strengthen benchmark workflows and reports
- [ ] 05-02: Produce deployment, architecture, and demo documentation
- [ ] 05-03: Polish the end-to-end pilot/demo package

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Self-Hosted Foundation | 3/3 | Awaiting verification | - |
| 2. Operator Console | 0/3 | Not started | - |
| 3. Playground & Observability | 0/3 | Not started | - |
| 4. Governance Hardening | 0/2 | Not started | - |
| 5. Product Proof & Delivery | 0/3 | Not started | - |
