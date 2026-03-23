# Project Research Summary

**Project:** Nebula.ai
**Domain:** Hybrid hosted control plane for a self-hosted B2B AI gateway
**Researched:** 2026-03-18
**Confidence:** MEDIUM

## Executive Summary

Nebula v2.0 should be scoped as an optional hosted control plane layered onto an already-working self-hosted gateway. The research is consistent on the core product shape: a hosted metadata-and-intent plane that registers deployments, shows fleet inventory and status, documents the trust boundary clearly, and offers one narrow remote-management workflow. Experts build this kind of product with an outbound-only control link, a durable local deployment identity, lease-style heartbeats, and a strict separation between hosted visibility and local enforcement.

The recommended approach is additive. Reuse Nebula's FastAPI backend, Next.js console patterns, and PostgreSQL/Alembic path. Add a hosted FastAPI fleet API, a separate hosted fleet UI, and a small embedded sync client inside the self-hosted gateway that handles registration, heartbeat publication, and polling for an allowlisted command journal. The hosted plane should know deployment metadata, status freshness, versions, capabilities, and remote-action history, but it must not become authoritative for request routing, provider credentials, policy decisions, or serving continuity.

The main risks are trust-boundary drift, weak enrollment identity, and accidental dependence on the hosted plane for runtime reliability. Those risks are mitigated by freezing the protocol boundary early, using short-lived bootstrap enrollment plus rotating per-deployment credentials, keeping hosted communication asynchronous and outside the request path, and limiting v2.0 remote management to one idempotent, low-blast-radius action with TTL, audit, and local authorization checks.

## Key Findings

### Recommended Stack

Nebula does not need a new platform stack for v2.0. The correct move is to extend the existing architecture with hosted-control-plane-specific components only where the product boundary changes: a hosted FastAPI service, PostgreSQL tables for fleet state and command audit, a separate hosted Next.js surface, and a lightweight outbound client in the self-hosted gateway. That keeps v2.0 additive and avoids introducing brokers, sidecars, or a second backend framework before the hosted model is proven.

**Core technologies:**
- FastAPI `0.115.x`: hosted fleet API and embedded control-plane client lifecycle support via lifespan hooks.
- PostgreSQL `16+`: deployment registry, heartbeats, health snapshots, registration tokens, remote-command journal, and audit history.
- Next.js `15.2.2`: hosted inventory UI, deployment detail pages, and trust-boundary documentation.
- `httpx` outbound HTTPS: registration, heartbeat, and command polling initiated only from customer environments.
- `PyJWT 2.12.1` + `cryptography 46.0.5`: signed bootstrap and command envelopes with per-deployment identity.
- `zod 4.3.6`: strict runtime validation for hosted UI payloads while contracts stabilize.

### Expected Features

The v2.0 milestone should prove hosted value without weakening the self-hosted story. Table stakes are explicit enrollment, stable fleet identity, scoped heartbeat semantics, clear trust-boundary disclosure, and one safe remote action. Differentiators are mainly clarity features that make hybrid behavior legible rather than broader control surfaces.

**Must have (table stakes):**
- Deployment registration and claim flow with revoke and re-link support.
- Fleet inventory with stable deployment identity, labels, environment, versions, and last-seen state.
- Scoped heartbeat/status model that reports control-plane freshness separately from local runtime health.
- Trust-boundary visibility in UI/docs stating what leaves the environment and what remains local.
- One narrow remote-action queue with audit trail.

**Should have (competitive):**
- Three-lane status view: control-plane link, local policy/runtime health, and remote-action eligibility.
- Per-deployment telemetry disclosure card showing exported metadata classes.
- Diagnostic-rich heartbeat failures with actionable reason codes.

**Defer (v2.x / v3+):**
- Approval-gated remote actions beyond the initial allowlist.
- Broader fleet actions, release orchestration, or rich hosted policy control.
- Self-serve SaaS onboarding, billing, and broad RBAC redesign.

**Anti-features to reject in v2.0:**
- Arbitrary shell or terminal access from the hosted plane.
- Push-based config mutation that applies immediately from cloud.
- Default streaming of prompts, responses, request logs, or provider secrets to hosted systems.
- Expanding the milestone into a full SaaS account-lifecycle project.

### Architecture Approach

The architecture should preserve a hard control-plane/data-plane split. The self-hosted gateway remains authoritative for serving, policy enforcement, secrets, and local governance state. The hosted plane owns fleet identity, hosted-visible metadata, status aggregation, docs, and a bounded command-intent queue. The trust boundary is outbound-only: the gateway registers, heartbeats, and polls over HTTPS, then validates and applies any allowed remote intent locally.

**Major components:**
1. Hosted Fleet API: registration, heartbeat ingestion, inventory, command queue, and audit APIs.
2. Hosted metadata store: deployment records, freshness/state, capability metadata, command journal, and action results.
3. Hosted console: multi-deployment fleet UI, deployment detail pages, and trust-boundary explanation.
4. Self-hosted sync agent: embedded client for link, heartbeat, command polling, and acknowledgements.
5. Local governance/runtime services: authoritative local writers for policy, credentials, runtime state, and remote-action application.

**Trust boundary and failure model:**
- Hosted may know deployment identity, display metadata, versions, capabilities, last-seen/freshness, coarse health summaries, and remote-action outcomes.
- Hosted must not be authoritative for request execution, tenant/API-key auth, final policy enforcement, provider credentials, or raw prompt/response content.
- If the hosted plane is unavailable, Nebula keeps serving locally, marks hosted sync as degraded, and lets the hosted UI age into stale/offline via TTL semantics.
- Heartbeats must be leases, not truth. Model `last_seen`, `reported_at`, `expires_at`, freshness state, and capability/version metadata explicitly.

**Remote-management constraints:**
- Customer environments initiate all control-plane traffic outbound.
- Commands are pull-based, TTL-bound, idempotent, audited, and validated locally before execution.
- Start with one non-serving-impacting action only, such as diagnostics-bundle request or credential rotation request.
- No inbound tunnels, no SSH, no arbitrary scripts, no direct hosted writes into local governance tables.

### Critical Pitfalls

1. **Blurring hosted metadata with local enforcement** — freeze the contract early so hosted stays advisory and local remains authoritative for serving and policy.
2. **Weak enrollment identity and shared secrets** — use short-lived bootstrap enrollment, then rotate to per-deployment operational credentials with revoke/re-link flows.
3. **Putting hosted reachability on the serving path** — run sync asynchronously, cache last valid local state, and require that hosted outages degrade visibility only.
4. **Misleading heartbeat semantics** — model leases with stale/unknown/offline states and separate connectivity freshness from local gateway health.
5. **Shipping broad remote management too early** — constrain v2.0 to a tiny allowlist with TTL, idempotency, audit, and local authorization.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Trust Boundary and Protocol Contract
**Rationale:** Every later feature depends on a frozen definition of identity, exported metadata, freshness semantics, capabilities, and control-plane failure behavior.
**Delivers:** Hosted-safe schemas for registration, heartbeat, inventory, and command envelopes; outbound-only trust model; status semantics; explicit data-egress contract.
**Addresses:** Trust-boundary visibility, scoped status model, remote-management constraints.
**Avoids:** Trust-boundary drift, data exfiltration, version/capability ambiguity.

### Phase 2: Enrollment and Deployment Identity
**Rationale:** Fleet inventory and safe remote actions are not credible until each self-hosted gateway has a durable identity and revocable operational credentials.
**Delivers:** Local `deployment_id`, credential storage, one-time claim flow, revoke/re-link/unlink lifecycle, hosted deployment registry.
**Addresses:** Deployment registration and claim flow, stable fleet identity.
**Uses:** FastAPI lifespan integration, PostgreSQL identity tables, `PyJWT`/`cryptography`.
**Avoids:** Weak registration, ghost deployments, ownership-transfer failures.

### Phase 3: Heartbeats, Inventory, and Hosted UX Honesty
**Rationale:** Once identity exists, the fastest proof of hosted value is reliable fleet visibility with explicit freshness and compatibility semantics.
**Delivers:** Outbound heartbeat pipeline, hosted inventory pages, deployment detail views, version/compatibility badges, stale/offline/degraded states, telemetry disclosure UI/docs.
**Addresses:** Fleet inventory, heartbeat/status model, trust-boundary visibility, version visibility.
**Uses:** Hosted FastAPI fleet API, PostgreSQL metadata store, hosted Next.js console, `zod`.
**Avoids:** Misleading green status, hidden data egress, confusing hybrid UX.

### Phase 4: Narrow Remote Management with Audit
**Rationale:** Remote action should come only after identity and status are trustworthy, otherwise the system becomes unsafe and hard to reason about.
**Delivers:** Pull-based command journal, local allowlist enforcement, idempotent action handling, action TTL/dedupe, local and hosted audit views, one safe support workflow.
**Addresses:** Narrow remote-action queue with audit trail.
**Implements:** Intent queue plus local apply pattern.
**Avoids:** Broad remote execution, replay bugs, hidden config mutation.

### Phase 5: Resilience, Compatibility, and Pilot Hardening
**Rationale:** The happy path is not enough for roadmap confidence; Nebula needs proof that hosted outages, revocations, and mixed versions fail safely.
**Delivers:** Hosted-outage drills, stale-state validation, capability negotiation, revoke/relink hardening, version-skew checks, mixed-version guidance, operator docs/demo narrative.
**Addresses:** Diagnostic-rich heartbeat failures and compatibility guidance.
**Avoids:** Hosted-plane reliability coupling, unsupported-action failures, pilot trust erosion.

### Phase Ordering Rationale

- Identity follows protocol contract because enrollment, heartbeat, and command flows all need stable schemas and capability rules.
- Inventory comes before remote action because operators must trust what deployment they are looking at, whether it is fresh, and what it supports before cloud-initiated actions are acceptable.
- Remote management is deliberately late and narrow because it is the highest trust-risk surface in the milestone.
- Resilience and mixed-version hardening are a distinct final phase so outage behavior and compatibility are validated against the implemented system, not assumed in design.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Credential model choice and schema-version negotiation need explicit decisions if enterprise attestation or mTLS is considered.
- **Phase 2:** Enrollment UX and ownership-transfer flows need validation against Nebula's existing operator/tenant model.
- **Phase 4:** The exact first remote action should be researched against support workflows so the allowlist proves value without widening risk.
- **Phase 5:** Mixed-version support policy, upgrade sequencing, and outage-drill criteria need concrete validation before pilot rollout.

Phases with standard patterns (skip research-phase):
- **Phase 3:** Heartbeat ingestion, fleet inventory, lease/staleness semantics, and hosted UI inventory patterns are well documented and already strongly covered in the research.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Strongly grounded in Nebula's current stack plus official FastAPI, PostgreSQL, PyJWT, cryptography, and Next.js references. |
| Features | MEDIUM | Product scoping is coherent and benchmarked against adjacent tools, but differentiator choices still need pilot validation. |
| Architecture | MEDIUM | The outbound-only split is well supported, but hosted console boundaries and local-vs-hosted auth details still require implementation-level decisions. |
| Pitfalls | MEDIUM | Risks are well framed from official patterns and adjacent systems, but some mitigation details depend on Nebula's final enrollment and command model. |

**Overall confidence:** MEDIUM

### Gaps to Address

- Hosted authentication model for the new fleet console is not fully resolved; planning should decide whether it reuses current operator identity or introduces a hosted-only auth boundary.
- The exact v2.0 remote action is still open; choose one support-safe action and reject broader requests during milestone planning.
- Local storage choice for deployment credentials and key rotation semantics needs a concrete implementation decision.
- Compatibility policy for mixed Nebula versions is not yet specified; planning should define minimum supported versions and failure-closed behavior.
- The line between "version visibility" and "release orchestration" must stay explicit so roadmap scope does not expand accidentally.

## Sources

### Primary (HIGH confidence)
- FastAPI lifespan docs — app lifecycle for embedded sync client and background services.
- PostgreSQL current docs — durable identity, lease-style state, and audit persistence.
- PyJWT usage docs — signed bootstrap and command token handling.
- cryptography Ed25519 docs — per-deployment signing and verification primitives.
- Next.js MDX guide — in-console trust-boundary documentation option.
- Kubernetes Leases — lease-based heartbeat and stale-state semantics.

### Secondary (MEDIUM confidence)
- Cloudflare Tunnel docs — outbound-only connector and status-monitoring patterns.
- AWS Systems Manager Run Command docs — remote-action breadth, audit, and secret-handling reference.
- Azure Arc overview / connected machine docs — managed-node identity and hybrid inventory patterns.
- Portainer Edge Agent docs — outbound registration and fleet inventory references.
- Replicated Vendor Platform docs — hosted instance visibility and support-oriented control-plane patterns.
- Tailscale coordination-server behavior docs — self-hosted connectivity should survive control-plane loss.
- SPIFFE/SPIRE node attestation docs — stronger future identity model patterns if enterprise hardening is needed.
- Elastic Agent command reference — enrollment and managed-command constraints.

---
*Research completed: 2026-03-18*
*Ready for roadmap: yes*
