# Roadmap: Nebula.ai

## Milestones

- ✅ **v1.0 Self-Hosted Operator Product** - Phases 1-5 (shipped 2026-03-17)
- 📋 **v2.0 Hosted Control Plane Validation** - Phases 6-10 (planned)

## Overview

Nebula v2.0 validates an optional hosted control plane layered onto the shipped self-hosted gateway. The milestone stays narrow: hosted surfaces manage metadata and control intent, all linking remains outbound-only, local runtime enforcement stays authoritative, and the only remote-management capability is one audited low-blast-radius action that improves pilot credibility without weakening the trust boundary.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 6: Trust Boundary and Hosted Contract** - Freeze the hybrid boundary, exported metadata rules, and hosted-visible control-plane semantics.
- [x] **Phase 7: Deployment Enrollment and Identity** - Give each self-hosted deployment a durable hosted identity with outbound-only linking and clean lifecycle controls. (completed 2026-03-21)
- [ ] **Phase 8: Fleet Inventory and Freshness Visibility** - Show honest deployment inventory, freshness, and compatibility state in the hosted plane.
- [ ] **Phase 9: Audited Remote Management** - Prove one narrow remote-management workflow with pull-based execution, local authorization, and audit history.
- [ ] **Phase 10: Pilot Proof and Failure-Safe Operations** - Validate outage-safe behavior and ship the pilot-ready docs and demo story.

## Phase Details

### Phase 6: Trust Boundary and Hosted Contract
**Goal**: Operators can understand and trust the hybrid hosted/self-hosted boundary before any deployment is linked.
**Depends on**: Phase 5
**Requirements**: TRST-01, TRST-02
**Success Criteria** (what must be TRUE):
  1. Hosted UI and architecture surfaces clearly distinguish hosted metadata and control intent from locally authoritative runtime-enforced state.
  2. Operators can inspect a concrete description of what data leaves the self-hosted environment by default.
  3. Hosted surfaces explicitly exclude raw prompts, responses, provider credentials, and authoritative runtime policy state from the default exported set.
**Plans**: 3 plans

Plans:
- [x] 06-01-PLAN.md — Freeze the hosted/local contract and exported metadata schema
- [x] 06-02-PLAN.md — Define trust-boundary language, failure semantics, and disclosure surfaces
- [x] 06-03-PLAN.md — Publish the hosted UI and architecture narrative for the boundary

### Phase 7: Deployment Enrollment and Identity
**Goal**: Self-hosted deployments can register with the hosted plane through an explicit outbound-only identity flow that operators can safely manage.
**Depends on**: Phase 6
**Requirements**: ENRL-01, ENRL-02, ENRL-03
**Success Criteria** (what must be TRUE):
  1. Operator can register a self-hosted Nebula deployment with the hosted control plane without manual database edits.
  2. A self-hosted gateway completes an outbound-only linking flow using short-lived enrollment credentials and deployment-scoped steady-state credentials.
  3. Operator can revoke, unlink, and relink a deployment without duplicate or ghost active inventory records.
**Plans**: 3 plans

Plans:
- [x] 07-01-PLAN.md — Hosted registration: DB schema, enrollment service, admin API for slot creation and token generation
- [x] 07-02-PLAN.md — Outbound linking: enrollment exchange endpoint, gateway startup hook, local identity storage
- [x] 07-03-PLAN.md — Lifecycle management: revoke, unlink, relink endpoints and console deployment UI

### Phase 8: Fleet Inventory and Freshness Visibility
**Goal**: Operators can use the hosted plane for honest fleet visibility without confusing hosted freshness with local runtime authority.
**Depends on**: Phase 7
**Requirements**: INVT-01, INVT-02, INVT-04
**Success Criteria** (what must be TRUE):
  1. Hosted inventory lists each linked deployment with identity, environment label, Nebula version, registration time, and last-seen time.
  2. Hosted views show connected, degraded, stale, or offline freshness semantics with explicit reason codes instead of overstated runtime-health claims.
  3. Hosted deployment detail surfaces capability and compatibility state and fails unsupported actions closed.
**Plans**: 3 plans

Plans:
- [x] 08-01-PLAN.md — Hosted heartbeat ingest: models, DB migration, ingest service, freshness calculation, endpoint, and TypeScript types
- [x] 08-02-PLAN.md — Gateway heartbeat sender: credential storage fix, background task, lifespan wiring, backend tests
- [ ] 08-03-PLAN.md — Frontend fleet inventory UI: FreshnessBadge, DependencyHealthPills, extended table and drawer

### Phase 9: Audited Remote Management
**Goal**: The hosted plane proves limited management value through one safe remote action that is pulled outbound and enforced locally.
**Depends on**: Phase 8
**Requirements**: RMGT-01, RMGT-02, RMGT-03
**Success Criteria** (what must be TRUE):
  1. Operator can queue one allowlisted, non-serving-impacting remote-management action for a linked deployment.
  2. A linked deployment polls for remote actions outbound, applies them only after local authorization checks, and records queued, applied, or failed outcomes.
  3. Remote-management actions expire safely, remain idempotent, and cannot directly mutate local runtime policy or provider credentials from the hosted plane.
**Plans**: 3 plans

Plans:
- [ ] 09-01: Define the initial allowlisted remote action and hosted queue contract
- [ ] 09-02: Implement outbound polling, local authorization, and apply/ack flows
- [ ] 09-03: Add TTL, idempotency, and hosted/local audit history

### Phase 10: Pilot Proof and Failure-Safe Operations
**Goal**: Nebula can demonstrate that hosted-control-plane outages degrade visibility only and that the hybrid model is credible in pilot conversations.
**Depends on**: Phase 9
**Requirements**: INVT-03, TRST-03
**Success Criteria** (what must be TRUE):
  1. Loss of hosted control-plane connectivity does not break the self-hosted gateway's serving path and is surfaced as degraded or stale hosted visibility instead of runtime failure.
  2. Docs and demo materials explain hybrid onboarding, trust boundaries, remote-management safety limits, and hosted-control-plane outage behavior in a pilot-ready narrative.
  3. Pilot materials make explicit that the hosted plane is metadata-and-intent only while local enforcement remains authoritative.
**Plans**: 2 plans

Plans:
- [ ] 10-01: Validate outage-safe serving, stale visibility, and mixed hosted/local failure behavior
- [ ] 10-02: Produce the pilot docs, demo flow, and trust-boundary narrative

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Self-Hosted Foundation | v1.0 | 3/3 | Complete | 2026-03-17 |
| 2. Operator Console | v1.0 | 3/3 | Complete | 2026-03-17 |
| 3. Playground & Observability | v1.0 | 3/3 | Complete | 2026-03-17 |
| 4. Governance Hardening | v1.0 | 3/3 | Complete | 2026-03-17 |
| 5. Product Proof & Delivery | v1.0 | 3/3 | Complete | 2026-03-17 |
| 6. Trust Boundary and Hosted Contract | v2.0 | 0/3 | Not started | - |
| 7. Deployment Enrollment and Identity | v2.0 | 3/3 | Complete   | 2026-03-21 |
| 8. Fleet Inventory and Freshness Visibility | v2.0 | 2/3 | In Progress|  |
| 9. Audited Remote Management | v2.0 | 0/3 | Not started | - |
| 10. Pilot Proof and Failure-Safe Operations | v2.0 | 0/2 | Not started | - |
