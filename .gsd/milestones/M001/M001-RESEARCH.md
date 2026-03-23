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

# Architecture Research

**Domain:** Optional hosted control plane for an existing self-hosted Nebula gateway
**Researched:** 2026-03-18
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Hosted Nebula Control Plane                         │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────────────────┐  │
│  │ Hosted Console │  │ Fleet API      │  │ Hosted Metadata Store         │  │
│  │ Next.js        │  │ FastAPI        │  │ deployments / commands /      │  │
│  │ inventory UI   │  │ registration   │  │ heartbeat snapshots / audit   │  │
│  └───────┬────────┘  │ status / cmds  │  └──────────────┬────────────────┘  │
│          │           └────────┬───────┘                 │                   │
├──────────┴────────────────────┴─────────────────────────┴───────────────────┤
│                    Trust Boundary: outbound-only link                       │
├──────────────────────────────────────────────────────────────────────────────┤
│  Mutual registration token + deployment key + signed polling/ack channel   │
├──────────────────────────────────────────────────────────────────────────────┤
│                     Self-Hosted Customer Deployment                         │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌──────────────────────────┐  ┌──────────────────────┐ │
│  │ Existing       │  │ New Hosted Sync Agent    │  │ Existing Local       │ │
│  │ FastAPI        │  │ register / heartbeat /   │  │ Next.js Console      │ │
│  │ gateway        │  │ fetch+ack commands       │  │ same-origin admin    │ │
│  │ serve traffic  │  └────────────┬─────────────┘  │ workflows            │ │
│  └───────┬────────┘               │                └──────────┬───────────┘ │
│          │                        │                           │             │
├──────────┴────────────────────────┴───────────────────────────┴─────────────┤
│                        Local Governance Boundary                            │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────────────┐ │
│  │ PostgreSQL   │  │ Qdrant       │  │ Providers                          │ │
│  │ canonical    │  │ semantic     │  │ Ollama / premium endpoints         │ │
│  │ policy state │  │ cache        │  │ request execution path             │ │
│  └──────────────┘  └──────────────┘  └────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Hosted Fleet API | Registration handshake, deployment inventory, command queue, heartbeat ingestion | New FastAPI service or a new bounded area inside a hosted FastAPI app |
| Hosted metadata store | Persist deployment identity, hosted-visible config snapshot, status history, remote-management audit | New PostgreSQL schema owned by hosted plane |
| Hosted console | Fleet inventory, deployment detail, last-seen, health summary, queued command status | New hosted Next.js surface; do not reuse the self-hosted console session model |
| Hosted sync agent | Outbound-only client from self-hosted deployment to hosted plane for register, heartbeat, command polling, acknowledgements | New service in `src/nebula/services/` started from the existing `ServiceContainer` lifespan |
| Existing gateway runtime | Continue serving `/v1/chat/completions`, local admin APIs, health endpoints, policy enforcement | Existing FastAPI app, minimally extended |
| Existing governance store | Remains source of truth for enforced tenants, keys, policies, and usage ledger | Existing local PostgreSQL schema |

## Recommended Project Structure

```text
src/
├── nebula/                                # Existing self-hosted gateway
│   ├── api/
│   │   ├── routes/
│   │   │   ├── admin.py                   # Modified: local-only remote-op apply/preview endpoints
│   │   │   └── hosted_agent.py            # New: local agent status/debug endpoints if exposed
│   ├── core/
│   │   ├── config.py                      # Modified: hosted link config and capability flags
│   │   └── container.py                   # Modified: wire hosted sync services into lifespan
│   ├── models/
│   │   ├── governance.py                  # Unchanged for runtime policy
│   │   └── control_plane.py               # New: registration, heartbeat, command contracts
│   ├── services/
│   │   ├── runtime_health_service.py      # Modified: emit hosted-sync-specific dependency state
│   │   ├── deployment_identity_service.py # New: persistent deployment ID and key material
│   │   ├── hosted_registration_service.py # New: claim/link/register flow
│   │   ├── hosted_heartbeat_service.py    # New: snapshot + send heartbeat
│   │   ├── hosted_command_service.py      # New: poll, validate, ack commands
│   │   └── remote_management_service.py   # New: enforce allowlist of remotely applied actions
│   └── db/
│       └── migrations/                    # Modified: deployment_identity / remote-op audit tables
├── control-plane/                         # New hosted backend
│   ├── api/                               # registration, fleet, commands, audit APIs
│   ├── services/                          # fleet identity, heartbeat aggregation, command queue
│   ├── models/                            # hosted deployment contracts
│   └── db/                                # hosted metadata persistence
└── control-plane-console/                 # New hosted fleet UI
    ├── app/                               # hosted inventory and deployment detail routes
    ├── components/                        # fleet tables, health cards, command forms
    └── lib/                               # hosted auth + fleet API client
```

### Structure Rationale

- **`src/nebula/`:** Keep the customer-hosted gateway authoritative for runtime behavior. Add a narrow outbound integration layer instead of mixing hosted concerns into `ChatService`, `PolicyService`, or provider adapters.
- **`control-plane/`:** Hosted state and APIs need separate ownership because they model deployments and operator actions, not request execution.
- **`control-plane-console/`:** The current self-hosted console trusts `NEBULA_ADMIN_API_KEY` against one deployment. Hosted fleet UX needs multi-deployment auth, inventory pages, and command workflows, so it should not be bolted onto the existing console proxy model.

## Architectural Patterns

### Pattern 1: Deployment Identity as a First-Class Local Asset

**What:** Each self-hosted deployment gets a durable `deployment_id`, local private credential, hosted-issued key, and capability manifest persisted locally. Registration creates the hosted relationship; restarts do not.
**When to use:** Immediately. Without stable identity, last-seen status, fleet inventory, and command targeting all become brittle.
**Trade-offs:** Requires new local persistence and rotation flows, but avoids tying identity to mutable hostnames or manual database edits.

**Example:**
```python
class DeploymentIdentity(BaseModel):
    deployment_id: str
    organization_id: str | None
    display_name: str
    hosted_base_url: AnyHttpUrl
    issued_at: datetime
    key_id: str
    capabilities: set[str]
```

### Pattern 2: Outbound Polling Channel, Not Hosted-Initiated Reach-In

**What:** The self-hosted gateway opens the relationship by registering, heartbeating, and polling for commands over HTTPS. The hosted plane never needs direct inbound access into the customer network.
**When to use:** Default for pilot-safe hybrid control planes.
**Trade-offs:** Command execution is eventually consistent instead of instantaneous, but the trust boundary stays clear and firewall-friendly.

**Example:**
```python
async def sync_once() -> None:
    await registration_service.ensure_linked()
    await heartbeat_service.publish_snapshot()
    commands = await command_service.poll_pending(limit=10)
    for command in commands:
        result = await remote_management_service.apply_if_allowed(command)
        await command_service.acknowledge(command.id, result)
```

### Pattern 3: Remote Management as Intent Queue Plus Local Apply

**What:** Hosted operators create intents such as "rotate bootstrap key", "toggle hosted enrollment", or "request policy sync preview". The local deployment validates policy, applies only allowlisted actions, writes local audit records, then acknowledges outcome.
**When to use:** For every hosted-initiated mutation. Do not let the hosted plane write directly into local governance tables.
**Trade-offs:** Slightly more implementation than direct writes, but preserves local authority and clean failure recovery.

## Data Flow

### Request Flow

```text
Hosted operator action
    ↓
Hosted Fleet API writes command → hosted command queue
    ↓
Self-hosted sync agent polls queue on next interval
    ↓
RemoteManagementService validates command type, capability, and local safety gates
    ↓
Allowed local service executes mutation against local governance store or config material
    ↓
Result written to local audit table and acked back to hosted plane
    ↓
Hosted inventory updates command status for the operator
```

### State Management

```text
Local authoritative state
    ↓
DeploymentIdentityService + RuntimeHealthService build a hosted-safe snapshot
    ↓
Heartbeat payload sent outbound to hosted plane
    ↓
Hosted metadata store updates last_seen, version, dependency summary, command progress

Hosted desired state
    ↓
Command queue only
    ↓
Local validation and apply
```

### Key Data Flows

1. **Registration flow:** Operator creates or obtains a one-time enrollment token in the hosted plane, the self-hosted deployment exchanges it for a durable deployment identity and hosted-issued credentials, then stores those credentials locally in PostgreSQL or mounted secret storage. No manual hosted or local database edits.
2. **Heartbeat flow:** The existing `RuntimeHealthService` produces dependency status; a new heartbeat service converts that into a hosted-safe snapshot containing deployment identity, version, runtime profile, capabilities, and summary health. Do not send prompts, responses, raw usage ledger rows, API keys, or tenant secrets.
3. **Hosted metadata flow:** Hosted persistence stores inventory fields such as `deployment_id`, `display_name`, `registered_at`, `last_seen_at`, `nebula_version`, `runtime_profile`, `overall_status`, dependency summary, and command history. This is metadata only, not runtime policy source of truth.
4. **Remote-management flow:** Hosted operators enqueue a small set of commands. The local deployment applies only commands that are both capability-allowed and locally configured as permitted. Suggested v2-safe command set: enrollment disable/re-enable, bootstrap/admin credential rotation request, metadata label update, and policy preview/sync import that still requires local apply semantics.
5. **Failure-reporting flow:** If a remote command fails, the failure is terminal for that command instance, locally audited, and visible in hosted status. It must not poison the serving path or block later heartbeats.

## Integration Points

### New vs Modified Components

| Area | New vs Modified | Integration Point | Notes |
|------|-----------------|------------------|-------|
| `src/nebula/core/config.py` | Modified | Add `NEBULA_HOSTED_CONTROL_PLANE_ENABLED`, hosted base URL, enrollment token path, heartbeat interval, remote-management allowlist | Hosted integration must be explicitly opt-in |
| `src/nebula/core/container.py` | Modified | Construct and lifecycle-manage deployment identity, registration, heartbeat, command, and remote-management services | Reuse FastAPI lifespan rather than spawning a second process first |
| `src/nebula/services/runtime_health_service.py` | Modified | Add hosted-sync dependency status and compact heartbeat serialization method | Hosted disconnect should report `degraded`, not `not_ready` |
| Local database schema | Modified | Add deployment identity table, hosted credential material, command audit table, last successful heartbeat table | Keep separate from tenant/policy tables |
| `src/nebula/services/*` | New | Outbound control-plane client services | Keep contracts isolated from request-serving code |
| Hosted Fleet API | New | Registration endpoints, heartbeat ingest, command queue, deployment inventory APIs | Separate bounded context from runtime gateway |
| Hosted console | New | Fleet inventory and command UX | Do not reuse local admin-key session model |

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Hosted control plane | Outbound HTTPS client from self-hosted gateway | Prefer short-lived requests plus polling over persistent inbound tunnels for v2 validation |
| Local PostgreSQL | Direct local persistence for identity, audit, and runtime governance | Remains authoritative for enforced local behavior |
| Qdrant | No direct hosted integration | Expose only health summary in heartbeat |
| Providers | No hosted control path | Hosted plane must never directly route or proxy inference traffic |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `RuntimeHealthService` ↔ `HostedHeartbeatService` | Direct service call | Reuse existing health semantics; add hosted-safe projection |
| Hosted sync services ↔ local governance/config services | Direct local service calls | Local services remain the only writers of authoritative runtime state |
| Hosted console ↔ hosted Fleet API | HTTP/JSON | Inventory and command UX only |
| Self-hosted console ↔ self-hosted admin API | Existing HTTP/JSON proxy | Preserve current local operator workflow as independent fallback |

## Trust Boundaries

### Hosted Control Plane May Know

- Deployment identity and display metadata
- Nebula version and runtime profile
- Last-seen timestamp and heartbeat freshness
- Aggregated dependency state such as `ready`, `degraded`, `not_ready`
- Hosted-approved capability flags
- Remote-command history and outcome summaries

### Hosted Control Plane Must Not Be Authoritative For

- Chat request execution path
- Tenant/API-key authentication
- Final policy enforcement
- Raw prompt/response content
- Provider credentials
- Local governance database writes

### Local Deployment Must Decide

- Whether hosted linking is enabled at all
- Which remote-management capabilities are allowed
- Whether a hosted command is valid for the current runtime state
- Whether serving remains available while hosted connectivity is absent

## Failure Handling

### Failure Modes and Expected Behavior

| Failure | Expected Local Behavior | Expected Hosted Behavior |
|---------|-------------------------|--------------------------|
| Hosted plane unreachable | Keep serving traffic; mark hosted sync dependency `degraded`; retry with backoff | Show deployment as stale after heartbeat TTL expires |
| Registration token invalid/expired | Keep running unlinked; expose explicit local error | Reject enrollment; no partial fleet record |
| Hosted-issued credential revoked | Stop heartbeats and command polling; keep serving traffic; require relink flow | Mark deployment disconnected and reject further sync |
| Command execution fails locally | Record local audit failure; ack failure; continue future polling | Show command failed with reason; do not assume desired state applied |
| Local PostgreSQL unavailable | Hosted sync pauses because identity/audit state is local; runtime already becomes `not_ready` under existing rules | Show stale deployment after TTL |
| Heartbeat payload schema mismatch after upgrade skew | Fail that heartbeat safely, keep runtime serving, surface version incompatibility locally | Mark deployment unhealthy/incompatible, not deleted |

### Failure-Handling Rules

1. Hosted connectivity is optional for serving. Never gate `/v1/chat/completions` on hosted-plane reachability.
2. Registration is atomic. Either the deployment gets durable credentials and identity persisted locally, or it remains unregistered.
3. Commands are idempotent. Every command needs a stable `command_id` so retries do not replay destructive actions.
4. Heartbeats are snapshots, not deltas. The hosted plane should be able to recover inventory state from the latest valid heartbeat plus command audit history.
5. Hosted stale-state semantics must use explicit TTLs. Recommend `last_seen_at` plus `status_fresh_until` instead of inferring from UI polling.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-20 deployments | Polling plus direct PostgreSQL-backed command queue is sufficient |
| 20-500 deployments | Add heartbeat ingestion batching, command pagination, and better hosted fleet indexes by org and stale status |
| 500+ deployments | Split heartbeat ingest from operator APIs and move command dispatch/audit onto dedicated workers |

### Scaling Priorities

1. **First bottleneck:** Hosted inventory churn from heartbeat writes, not self-hosted inference throughput.
2. **Second bottleneck:** Command idempotency, auditability, and version-skew handling across mixed deployment versions.

## Anti-Patterns

### Anti-Pattern 1: Making the Hosted Plane the Runtime Source of Truth

**What people do:** Treat hosted desired state as if the self-hosted gateway should blindly mirror it.
**Why it's wrong:** A hosted outage or auth issue then becomes a serving-path risk and collapses the self-hosted trust story.
**Do this instead:** Keep hosted state advisory and intent-based; local services remain authoritative for enforcement.

### Anti-Pattern 2: Sending Rich Operational Data Because It Is Easy to Serialize

**What people do:** Ship full health payloads, ledger rows, prompts, or config blobs to the hosted plane.
**Why it's wrong:** It expands the trust boundary before the hybrid value is proven and creates avoidable privacy concerns.
**Do this instead:** Start with a compact hosted-safe heartbeat schema and add fields only when a concrete hosted feature requires them.

### Anti-Pattern 3: Reusing the Self-Hosted Console as the Hosted Control Plane

**What people do:** Point the existing Next.js proxy UI at multiple deployments.
**Why it's wrong:** The current console assumes one admin key and one same-origin backend. Fleet inventory, hosted auth, and remote commands are different concerns.
**Do this instead:** Keep the self-hosted console as the local fallback UI and build a separate hosted fleet UI.

## Suggested Build Order

1. **Local deployment identity foundation**
   Add config flags, local identity persistence, durable `deployment_id`, and credential storage. Nothing else is reliable before identity exists.
2. **Hosted registration handshake**
   Build enrollment-token exchange and relink flows. This removes manual database edits and creates the trust anchor for every later feature.
3. **Heartbeat and hosted inventory**
   Extend `RuntimeHealthService` into a hosted-safe snapshot, ingest it in the hosted plane, and build fleet last-seen/version/status views.
4. **Hosted/local trust-boundary docs and local fallback UX**
   Document exactly what leaves the environment and make local status visible when the hosted plane is disconnected.
5. **Narrow remote-management queue**
   Implement a minimal command allowlist with idempotent local apply plus audit. Start with non-serving-critical actions only.
6. **Version-skew and failure-hardening**
   Add schema versioning, retries, stale markers, revoke/relink flows, and compatibility checks after the happy path works.

## Sources

- Local project architecture and deployment docs:
  - `/Users/joaquinfernandezdegamboa/Documents/Playground/.planning/PROJECT.md`
  - `/Users/joaquinfernandezdegamboa/Documents/Playground/.planning/codebase/ARCHITECTURE.md`
  - `/Users/joaquinfernandezdegamboa/Documents/Playground/.planning/codebase/STACK.md`
  - `/Users/joaquinfernandezdegamboa/Documents/Playground/docs/architecture.md`
  - `/Users/joaquinfernandezdegamboa/Documents/Playground/docs/self-hosting.md`
- FastAPI lifespan and app startup patterns: https://fastapi.tiangolo.com/advanced/events/
- PostgreSQL current documentation for durable local state and notification primitives: https://www.postgresql.org/docs/current/
- Kubernetes lease and heartbeat model as a reference pattern for last-seen semantics and stale detection: https://kubernetes.io/docs/concepts/architecture/leases/

---
*Architecture research for: Nebula v2.0 hosted control plane validation*
*Researched: 2026-03-18*

# Stack Research

**Domain:** Hybrid hosted control plane for an existing self-hosted AI gateway
**Researched:** 2026-03-18
**Confidence:** HIGH

## Recommended Stack

This milestone should stay additive. Nebula already has the right base stack: Python/FastAPI for control APIs, Next.js for operator UI, and PostgreSQL-ready persistence. The hosted-control-plane validation should add a hosted FastAPI deployment, a small outbound control-plane client inside the existing gateway, and a few narrowly scoped libraries for signing, validation, and documentation.

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI | Keep current `0.115.x` line | Hosted control-plane API and embedded self-hosted control-plane client lifecycle | Nebula already uses FastAPI. Reusing it avoids a second backend framework, and FastAPI's lifespan model is the right place to start/stop a lightweight heartbeat + command-poll loop inside the existing gateway process. |
| PostgreSQL | `16+` (`17.x` if provisioning fresh hosted infra) | Deployment registry, registration tokens, heartbeats, health snapshots, remote-command journal | This workload is relational, audit-heavy, and small enough for a single transactional store. Reuse the existing SQLAlchemy/Alembic path instead of adding Redis streams, Kafka, or a separate fleet DB. |
| Next.js | Keep current `15.2.2` line | Hosted inventory UI, deployment detail pages, trust-boundary docs | Nebula already ships a Next.js console. Extend it with hosted-plane pages instead of introducing a second console or docs site. The UI only talks to the hosted FastAPI API; it should never connect directly to customer gateways. |
| Outbound HTTPS control link | Existing `httpx` + deployment-scoped auth | Registration, heartbeat/status push, command polling from the self-hosted gateway to the hosted plane | This keeps the trust boundary explicit: customer environments initiate all control-plane traffic outbound, and hosted-plane loss cannot break local serving. It also avoids opening inbound management ports into customer environments. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `PyJWT` | `2.12.1` | Signed registration tokens and signed remote-command envelopes | Use for bootstrap tokens and deployment-scoped auth assertions. Prefer asymmetric signing so the hosted plane can verify commands without sharing a symmetric secret everywhere. |
| `cryptography` | `46.0.5` | Ed25519 key generation, signing, verification, key serialization | Use with `PyJWT` for EdDSA signing. This is the narrow crypto addition that supports trusted linking and allowlisted remote commands without inventing a custom signing scheme. |
| `zod` | `4.3.6` | Runtime validation of hosted API payloads in the Next.js console | Use on the console for deployment health, status, and command-result payloads. This keeps the new hosted inventory views strict even when backend contracts evolve during the pilot. |
| `@next/mdx` | Match `next@15.2.2` (`15.2.x`) | Trust-boundary and hybrid-architecture documentation inside the existing console | Use only if the trust-boundary docs should live as versioned MDX pages in the operator console. If static React pages are enough, this can stay deferred. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Alembic | Migrate new hosted-control-plane tables | Add separate revisions for hosted inventory/command tables. Do not bypass migrations with manual SQL or admin database edits. |
| OpenAPI from FastAPI | Contract source for registration, heartbeat, inventory, and command APIs | Treat these schemas as the canonical hosted-control-plane contract and reuse them in docs and frontend typing. |

## Integration Points With Existing Nebula

### FastAPI integration

- Add a hosted control-plane API service using the same FastAPI stack already used by the gateway.
- Add a small `control_plane_client` module inside the existing self-hosted gateway.
- Start the client from FastAPI lifespan, not from ad hoc request handlers.
- Use the client for:
  - one-time registration / re-link flows
  - periodic heartbeat with `deployment_id`, version, last-seen, and summarized local health
  - polling for one allowlisted remote command type

Recommended hosted tables:

- `deployments`
- `deployment_registrations`
- `deployment_heartbeats`
- `deployment_health_snapshots`
- `remote_commands`
- `remote_command_results`
- `registration_tokens`

### Next.js integration

- Extend the existing console with hosted-only pages:
  - `/deployments`
  - `/deployments/[id]`
  - `/docs/trust-boundary`
- Continue using the existing React Query data-fetching pattern for hosted APIs.
- Do not add direct browser-to-gateway communication. All inventory and health data should come from the hosted FastAPI service.

### Existing observability integration

- Reuse the already-validated local health and ledger surfaces as the source of truth for hosted summaries.
- Only send summarized deployment metadata to the hosted plane:
  - version
  - last seen
  - dependency health rollup
  - coarse status counters if needed
- Do not send raw prompts, responses, full request logs, or policy evaluation internals to the hosted plane in this milestone.

## Safe Remote-Management Recommendation

Use a **pull-based, allowlisted command journal** backed by PostgreSQL.

For this milestone, support only one remote command category:

- `request_diagnostics_bundle` or an equivalently narrow, non-serving-impacting support action

Why this path fits the milestone:

- It proves the hosted plane can initiate a management workflow.
- It does not grant shell access, port tunnels, or general remote execution.
- It does not alter local request serving, routing, or enforcement policy.
- If the hosted plane disappears, the gateway continues serving normally.

Do not implement push execution, SSH, reverse tunnels, or arbitrary script execution.

## Installation

```bash
# Python additions for hosted control-plane auth/signing
pip install PyJWT==2.12.1 cryptography==46.0.5

# Optional console additions for strict payload validation and in-console docs
cd console
npm install zod@4.3.6
npm install @next/mdx@15.2.2 @mdx-js/loader @mdx-js/react @types/mdx
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Postgres-backed registration + command journal | Redis streams / RabbitMQ / Kafka | Use a broker only if Nebula later needs high-volume async fan-out across many deployments. That is premature for hosted-control-plane validation. |
| Embedded control-plane client inside the existing gateway process | Separate sidecar/agent binary | Use a sidecar later if operator requirements demand separate upgrade cadence, separate failure domains, or non-Python environments. For v2.0 validation, embedded is faster and easier to trust. |
| Signed bootstrap tokens + deployment-scoped outbound auth | Mutual TLS device identity | Use mTLS later for enterprise hardening or procurement-driven device identity. It adds more operational overhead than this validation milestone needs. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Celery + Redis/RabbitMQ for the single remote-management flow | FastAPI explicitly positions heavier queue systems for multi-process or multi-server heavy background work. Nebula's v2.0 control-plane flow is small and bounded. | FastAPI lifespan task + Postgres command journal |
| Inbound remote management channels: SSH, reverse tunnels, WebSocket command sockets, gRPC tunnels | They blur the hosted/self-hosted trust boundary and create harder pilot conversations around access and failure modes. | Outbound HTTPS polling from the gateway |
| A separate docs stack such as Docusaurus just for trust-boundary explanation | It creates a second source of truth and delays the milestone. | Host the trust-boundary narrative in the existing Next.js console, optionally with MDX |
| Broad remote config mutation of routing/policy/runtime enforcement | This is exactly where trust breaks first in a hybrid model. | One non-serving-impacting allowlisted command only |

## Stack Patterns by Variant

**If the goal is fastest pilot validation:**
- Use one hosted FastAPI service, one hosted PostgreSQL database, and an embedded gateway client.
- Because this is enough to validate registration, inventory, status, docs, and a single safe remote-management flow.

**If a pilot customer later requires stricter hosted-plane identity controls:**
- Add mTLS for deployment identity on top of the same API and database model.
- Because the data model and outbound polling pattern still hold; only the auth layer gets stronger.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `fastapi 0.115.x` | `pydantic 2.x` | Matches Nebula's current backend baseline and avoids a framework migration during the milestone. |
| `PyJWT 2.12.1` | `cryptography 46.0.5` | PyJWT's EdDSA support relies on `cryptography`. |
| `@next/mdx 15.2.x` | `next 15.2.2` | Keep MDX on the same major/minor line as the existing console to avoid introducing a framework upgrade into this milestone. |
| `zod 4.3.6` | `react 19` / `next 15.2.2` | Frontend-only runtime validation; no backend coupling. |

## Sources

- FastAPI Lifespan Events — https://fastapi.tiangolo.com/advanced/events/ — verified FastAPI lifespan is the right app-level lifecycle hook for a small embedded control-plane client
- FastAPI Background Tasks — https://fastapi.tiangolo.com/tutorial/background-tasks/ — verified FastAPI itself points heavier queue systems like Celery at larger multi-process workloads, which supports not adding one yet
- Next.js MDX Guide — https://nextjs.org/docs/app/guides/mdx — verified in-console MDX is the simplest way to publish trust-boundary docs without a second site
- PyJWT usage docs — https://pyjwt.readthedocs.io/en/stable/usage.html — verified EdDSA support for signed tokens/command envelopes
- cryptography Ed25519 docs — https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/ — verified current Python crypto support for Ed25519 signing and verification
- PyPI `PyJWT` index — https://pypi.org/project/PyJWT/ — verified current package version (`2.12.1`) on 2026-03-18
- PyPI `cryptography` index — https://pypi.org/project/cryptography/ — verified current package version (`46.0.5`) on 2026-03-18
- npm `zod` package — https://www.npmjs.com/package/zod — verified current package version (`4.3.6`) on 2026-03-18

---
*Stack research for: hybrid hosted control plane for Nebula v2.0*
*Researched: 2026-03-18*

# Feature Research

**Domain:** Hosted control plane for self-hosted Nebula gateway deployments
**Researched:** 2026-03-18
**Confidence:** MEDIUM

## Feature Landscape

Scope note: this document covers only the new hosted-control-plane behavior for Nebula v2.0 validation. It assumes Nebula already ships self-hosted deployment, operator auth, tenant management, API keys, policy editing, playground, observability, and docs/demo proof.

### Table Stakes (Users Expect These)

Features users assume exist in a credible pilot. Missing these makes the hosted plane feel like a demo instead of an operational product.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Deployment registration and claim flow | Credible hybrid products use an explicit enrollment step so operators can attach a self-hosted node to a hosted account without database edits or inbound exposure. | MEDIUM | Depend on existing Nebula deployment flow, operator auth, and tenant model. Use a one-time enrollment token or install command, stable deployment ID, environment labels, and revocation/re-registration path. |
| Fleet inventory with stable identity | Operators expect a hosted list of linked deployments with name, tenant, environment, version, and last-seen metadata. | MEDIUM | Depend on existing tenant management and observability metadata. Minimum fields: deployment ID, customer-chosen label, environment, gateway version, connector version if separate, first seen, last heartbeat, last config sync result. |
| Heartbeat and scoped status model | Adjacent products consistently show connected/degraded/disconnected state plus last contact time; pilots need this before any remote action is credible. | MEDIUM | Depend on registration and observability plumbing. Status must be scoped: control-plane connectivity, not blanket runtime health. Add reason codes such as auth failure, version mismatch, clock skew, network unreachable. |
| Trust-boundary visibility in UI and docs | Buyers expect a hybrid product to state exactly what leaves the environment, what remains local, and whether the hosted plane can affect serving. | LOW | Depend on existing docs/demo package and policy/observability surfaces. Show outbound-only link, metadata classes exported, secrets handling, and that request routing/policy enforcement remain local when the hosted plane is unreachable. |
| Version and compatibility visibility | Hosted inventory is expected to show version drift and whether a deployment can safely use a hosted feature or action. | LOW | Depend on inventory. Keep this to version reporting and compatibility badges for v2.0; do not expand into full release orchestration yet. |
| Narrow remote-action queue with audit trail | A pilot hosted plane usually needs at least one remotely initiated action to prove value beyond passive inventory. | HIGH | Depend on registration, heartbeat, audit logging, and operator permissions. Keep the action set small: request support bundle upload, request config/policy bundle pull, rotate registration credential, or trigger a safe connector reconnect. No arbitrary shell, no persistent tunnel by default. |

### Differentiators (Competitive Advantage)

Features that are not required for pilot credibility, but would make Nebula’s hybrid story materially stronger.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Explicit three-lane status view: control-plane link, local policy enforcement, and remote-action eligibility | Prevents the most common hybrid-product ambiguity: “green” status that only means the agent is online, not that the gateway is healthy or safely manageable. | MEDIUM | Builds on existing observability and denied-path explainability. This is a strong fit for Nebula because operators already think in terms of route, policy, and runtime evidence. |
| Per-deployment telemetry disclosure card | Turns the trust boundary into a product feature: operators can see which metadata fields are exported and which data classes never leave the environment. | LOW | Reuse existing documentation work and expose it in-product. Strong pilot differentiator because it supports security review without adding heavy compliance scope. |
| Approval-gated remote action execution | Hosted operator requests an action, but the local deployment or local admin must approve or has preconfigured allowlists. This is safer than direct push control. | HIGH | Good follow-on if v2.0 needs stronger trust posture. Depends on the remote-action queue and existing console auth. Better fit than broad RBAC redesign because scope stays narrow. |
| Diagnostic-rich heartbeat failures | Status entries that explain why a deployment is offline or degraded reduce support load and make pilots look more mature. | MEDIUM | Add actionable failure classes: invalid token, TLS trust failure, proxy/firewall block, version skew, rejected action policy. This builds directly on the heartbeat model instead of widening product scope. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that sound attractive in a hosted plane but are the wrong move for Nebula v2.0 validation.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Arbitrary shell / terminal access from the hosted plane | It looks like the fastest way to prove “remote management.” | It blows up the trust boundary, raises procurement and security objections, and shifts Nebula toward a remote-admin product instead of an AI gateway. | Ship an allowlisted action queue with audit logs and explicit local execution semantics. |
| Push-based config mutation that applies immediately from the cloud | Teams want centralized control and faster incident response. | It weakens the self-hosted reliability story, risks surprise config drift, and makes hosted outages feel dangerous. | Use signed desired-state bundles that the deployment pulls, validates, and applies locally, ideally with dry-run or approval support. |
| Streaming prompts, responses, or full request logs to the hosted plane by default | It seems useful for fleet observability and support. | It contradicts the hybrid trust story and turns a metadata plane into a data-plane replication problem. | Keep hosted inventory at metadata level only; rely on local observability for request content and expose only aggregate or explicitly opted-in diagnostics. |
| Full SaaS account lifecycle expansion in the same milestone | Hosted products often bundle org invites, billing, self-serve signup, and rich RBAC. | Nebula’s current milestone is validating hosted control-plane value, not launching a public SaaS. This scope would drown the core signal. | Reuse existing operator auth and tenant model, keep account workflows narrow, and defer self-serve/billing/RBAC redesign. |

## Feature Dependencies

```text
Deployment registration and claim flow
    └──requires──> Existing self-hosted deployment path
    └──requires──> Existing operator auth + tenant management

Fleet inventory with stable identity
    └──requires──> Deployment registration and claim flow

Heartbeat and scoped status model
    └──requires──> Fleet inventory with stable identity
    └──requires──> Connector-to-hosted authenticated channel

Trust-boundary visibility in UI and docs
    └──requires──> Heartbeat/status field definitions
    └──requires──> Existing docs/demo narrative

Version and compatibility visibility
    └──requires──> Fleet inventory with stable identity

Narrow remote-action queue with audit trail
    └──requires──> Deployment registration and claim flow
    └──requires──> Heartbeat and scoped status model
    └──requires──> Existing auth/audit surfaces

Approval-gated remote action execution
    └──enhances──> Narrow remote-action queue with audit trail

Streaming request data to hosted plane
    └──conflicts──> Trust-boundary visibility in UI and docs
```

### Dependency Notes

- **Fleet inventory requires deployment registration:** the hosted plane cannot show stable deployment records until each self-hosted gateway has a durable identity and claim flow.
- **Heartbeat/status requires an authenticated outbound channel:** without a connector identity and signed heartbeat payloads, “last seen” is weak and remote actions are unsafe.
- **Trust-boundary visibility requires precise field definitions:** Nebula cannot honestly claim what the hosted plane sees until registration, heartbeat, and inventory payloads are concretely defined.
- **Narrow remote actions require auditability first:** once the hosted plane can initiate actions, audit logs and permission checks stop being optional.
- **Streaming request data conflicts with the hybrid story:** it turns the hosted plane into a shadow observability backend and undermines the explicit local-enforcement boundary.

## MVP Definition

### Launch With (v2.0 validation)

Minimum feature set needed to validate whether the hosted-control-plane direction is worthwhile.

- [ ] Deployment registration and claim flow — proves operators can attach self-hosted Nebula deployments without manual database work.
- [ ] Fleet inventory with identity, last seen, version, and environment labels — gives the hosted plane a useful operator surface on day one.
- [ ] Scoped heartbeat/status model — validates whether hosted visibility is trustworthy instead of vague.
- [ ] Trust-boundary visibility in UI/docs — necessary for pilot credibility and security conversations.
- [ ] One narrow remote action with audit trail — enough to prove the hosted plane adds operational value beyond passive inventory.

### Add After Validation (v2.x)

Features worth adding once pilots confirm the hybrid model is desirable.

- [ ] Approval-gated remote action execution — add when pilot users ask for tighter local control over hosted-initiated actions.
- [ ] Diagnostic-rich heartbeat failures — add when support friction shows that “offline” is too coarse.
- [ ] Compatibility and version drift guidance — add when more than one supported connector/gateway version is active in the field.

### Future Consideration (v3+)

Features to defer until the product boundary is proven and the trust model is accepted.

- [ ] Broader fleet actions across many deployments — defer until targeting, rollback, and blast-radius controls are justified.
- [ ] Rich hosted policy orchestration and release channels — defer until Nebula decides the hosted plane should own more lifecycle state.
- [ ] Self-serve SaaS onboarding, billing, and broad RBAC redesign — defer until hybrid adoption is validated commercially.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Deployment registration and claim flow | HIGH | MEDIUM | P1 |
| Fleet inventory with stable identity | HIGH | MEDIUM | P1 |
| Heartbeat and scoped status model | HIGH | MEDIUM | P1 |
| Trust-boundary visibility in UI and docs | HIGH | LOW | P1 |
| Narrow remote-action queue with audit trail | HIGH | HIGH | P1 |
| Version and compatibility visibility | MEDIUM | LOW | P2 |
| Diagnostic-rich heartbeat failures | MEDIUM | MEDIUM | P2 |
| Approval-gated remote action execution | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for v2.0 validation
- P2: Valuable follow-on once the hosted pattern is proven
- P3: Defer unless pilot feedback specifically demands it

## Competitor Feature Analysis

| Feature | AWS Systems Manager / Azure Arc | Portainer Edge / Cloudflare Tunnel / Replicated | Our Approach |
|---------|----------------------------------|-------------------------------------------------|--------------|
| Registration | Uses explicit activation/onboarding flows with managed-node identity and account linkage. | Uses agent or tunnel enrollment tied to a hosted account or customer instance. | One-time Nebula deployment claim flow with stable deployment ID and revocation path. |
| Inventory | Shows node metadata such as identity, tags, agent version, and connection state. | Shows edge endpoints, instances, or tunnels with state and labels. | Hosted deployment list with environment, tenant, versions, and last-seen data only. |
| Heartbeat | Uses agent check-in / connection status but does not imply every workload is healthy. | Uses connector status with clear online/down/degraded semantics. | Explicitly scope status to control-plane connectivity and separate it from local serving health. |
| Remote management | Offers powerful fleet command/extension features. | Often offers support-oriented or edge-focused remote actions, sometimes including tunnels. | Ship only one allowlisted action path for v2.0; avoid shell access and broad mutation. |
| Trust boundary | Enterprise tools document metadata and agent behavior, but the boundary is often buried in docs. | Tunnel/control-plane docs often clarify that connector health is not origin-service health. | Make the boundary visible in product UI and demo narrative, not just documentation footnotes. |

## Sources

- Nebula project context: `/Users/joaquinfernandezdegamboa/Documents/Playground/.planning/PROJECT.md`
- Cloudflare Tunnel monitoring docs: https://developers.cloudflare.com/tunnel/monitoring/ (HIGH for status-scope pattern)
- AWS Systems Manager Run Command docs: https://docs.aws.amazon.com/systems-manager/latest/userguide/send-commands-multiple.html (HIGH for remote-action breadth and fleet-targeting pattern)
- Azure Arc overview and connected machine guidance: https://learn.microsoft.com/azure/azure-arc/overview and related connected machine docs (MEDIUM for managed-node inventory and hybrid identity pattern)
- Portainer Edge Agent documentation: https://docs.portainer.io/admin/environments/add/docker/edge-agent (MEDIUM for outbound registration and edge inventory pattern)
- Replicated Vendor Platform docs: https://docs.replicated.com/ (MEDIUM for hosted metadata/instance visibility pattern)

## Recommendation

For Nebula v2.0, treat the hosted plane as a metadata-and-intent layer, not a remote-control surface. The table stakes are enrollment, inventory, scoped heartbeat semantics, explicit trust-boundary disclosure, and one narrow audited remote action. That is enough to test whether customers value hosted visibility and safe operational assistance without undermining the self-hosted reliability story Nebula already established in v1.0.

---
*Feature research for: Hosted control plane for self-hosted Nebula deployments*
*Researched: 2026-03-18*

# Pitfalls Research

**Domain:** Hybrid hosted control plane for a self-hosted AI gateway
**Researched:** 2026-03-18
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Blurring the trust boundary between hosted metadata and local enforcement

**What goes wrong:**
The hosted plane starts acting like part of the request-serving path or like the source of truth for runtime policy enforcement. Pilot buyers then hear "self-hosted" in marketing but discover that real control lives in Nebula Cloud.

**Why it happens:**
Teams add hosted inventory, health, and remote actions incrementally and never freeze a hard contract for what is metadata, what is advisory control, and what remains locally enforced.

**How to avoid:**
Write an explicit boundary before implementation: hosted plane may store deployment identity, last-seen state, version, capability metadata, and queued management intents; the local gateway remains the enforcement point for request routing, provider credentials, policy decisions, and serving continuity. Document "control plane down" behavior as a product requirement, not an implementation detail.

**Warning signs:**
- Hosted connectivity is required for the gateway to start or to evaluate request policy
- UI copy says "managed" without stating what is still enforced locally
- Engineers need to ask whether a given setting is authoritative in cloud or on-box

**Phase to address:**
Phase 1: Trust boundary and protocol contract

---

### Pitfall 2: Using weak deployment registration and long-lived shared secrets

**What goes wrong:**
A copied registration token, reused bootstrap secret, or environment-wide API key can enroll the wrong gateway, impersonate an existing deployment, or keep talking to the hosted plane after ownership should have changed.

**Why it happens:**
Bootstrap is treated as a convenience flow instead of an identity problem. Teams use one token for both first-linking and long-term communication, or they never separate enrollment credentials from rotating operational credentials.

**How to avoid:**
Use a one-time or short-lived bootstrap flow to link a deployment, then issue separate rotating credentials for steady-state communication. Prefer outbound mutual authentication with per-deployment identity. If cloud metadata can attest the instance, use it; otherwise require explicit operator confirmation. Support revoke, re-link, and ownership transfer as first-class lifecycle flows.

**Warning signs:**
- The same secret appears in docs for bootstrap and ongoing heartbeats
- Multiple deployments can be linked by the same token without approval
- There is no credible answer for "how do we revoke a stolen registration token?"

**Phase to address:**
Phase 2: Secure enrollment and identity lifecycle

---

### Pitfall 3: Making the hosted plane part of the serving reliability path

**What goes wrong:**
Self-hosted gateways lose serving capability, degrade policy correctness, or block startup when the hosted plane is slow or unavailable. The product stops being credibly self-hosted the first time a control-plane outage happens.

**Why it happens:**
Status sync, config fetch, or remote command polling is implemented inline with request handling or startup readiness. Engineers optimize for "single source of truth" instead of local survivability.

**How to avoid:**
Keep registration, heartbeats, and remote-management polling asynchronous and outside the request path. Cache the last valid local config. Make hosted-originated changes explicit, versioned, and applied locally only after validation. Define a degraded mode where the gateway keeps serving and the hosted UI shows "stale/unknown" rather than "down."

**Warning signs:**
- Request latency rises when hosted APIs are slow
- Gateway startup fails if Nebula Cloud is unreachable
- Operators cannot explain what happens during a hosted outage

**Phase to address:**
Phase 1: Trust boundary and protocol contract, then Phase 5: Pilot resilience drills

---

### Pitfall 4: Treating heartbeats as truth instead of as a lease with staleness semantics

**What goes wrong:**
The hosted console shows deployments as healthy when they are partitioned, shows them as dead during temporary network loss, or hides uncertainty behind a single green badge. Operators make decisions from stale status.

**Why it happens:**
Teams implement "last ping wins" status with no lease duration, no stale state, no distinction between app heartbeat and runtime health, and no server-side interpretation rules.

**How to avoid:**
Model heartbeats as leases with explicit expiry windows and separate fields for `last_seen`, `reported_at`, `expires_at`, and local health summary. Distinguish `healthy`, `degraded`, `stale`, `offline`, and `unknown`. Tie status visibility to monotonic sequence numbers or timestamps and include version/capability metadata so status is interpretable.

**Warning signs:**
- "Online" means only "we received an HTTP POST recently"
- There is no `stale` or `unknown` state in the UI
- Heartbeats come from a sidecar that can live while the actual gateway is unhealthy

**Phase to address:**
Phase 3: Heartbeats, status model, and hosted UX honesty

---

### Pitfall 5: Shipping broad remote management before proving a narrow safe command set

**What goes wrong:**
Remote management expands from "safe pilot value" into shell-like control, arbitrary config mutation, or destructive operations that customers will not trust. One bad remote action can damage the entire hybrid story.

**Why it happens:**
Once a command channel exists, every missing operational feature looks easy to add. Product pressure pushes the system from narrow management intents into generic remote execution.

**How to avoid:**
Start with a tiny allowlist of idempotent, low-blast-radius actions such as "request config reload," "rotate hosted-plane credentials," or "run connectivity self-check." Require explicit action type, issuer, TTL, idempotency key, audit trail, result code, and local authorization policy. Reject arbitrary shell execution and hidden config patching.

**Warning signs:**
- Remote management is described as "we can just send commands"
- There is no per-action approval, TTL, or replay protection
- Engineers propose SSH-like fallbacks for operational convenience

**Phase to address:**
Phase 4: Narrow remote management with audit and rollback

---

### Pitfall 6: Exfiltrating too much tenant data to make hosted visibility feel useful

**What goes wrong:**
Prompts, responses, provider secrets, customer identifiers, or detailed local topology leak into the hosted plane because the team uses request payloads to power status pages and support workflows. Trust erodes immediately, especially for self-hosted buyers.

**Why it happens:**
Hosted UX is easier to build when raw payloads are centralized. Teams blur diagnostic metadata with customer content and fail to enforce data minimization at the protocol level.

**How to avoid:**
Define a strict hosted metadata schema: deployment identity, software version, heartbeat state, coarse health, and explicit remote-action audit data only. Make any request or content telemetry opt-in and separately governed. Redact secrets before serialization, and state in docs exactly what leaves the environment by default.

**Warning signs:**
- Hosted APIs accept arbitrary JSON "status blobs"
- Support/debug workflows depend on shipping prompts or raw provider errors by default
- Docs cannot answer "what data leaves the box?" in one paragraph

**Phase to address:**
Phase 1: Trust boundary and protocol contract, reinforced in Phase 5: Pilot docs and demo narrative

---

### Pitfall 7: Ignoring revocation, unlink, and ghost deployment cleanup

**What goes wrong:**
A deployment is cloned, rebuilt, renamed, or retired, but the hosted plane still shows it as active, still accepts old credentials, or cannot cleanly transfer ownership. Inventory becomes untrustworthy and support workflows get messy fast.

**Why it happens:**
Teams design the happy-path enroll flow only. They skip tombstones, explicit unlink states, key rotation, and duplicate-identity handling because the first demo only needs "register once."

**How to avoid:**
Design the full lifecycle: enroll, rotate, unlink, revoke, retire, and reclaim. Store immutable deployment IDs separate from human-readable names. Detect duplicate identities, show conflicts in the UI, and make stale records expire or archive automatically.

**Warning signs:**
- Deleting a deployment in cloud does not invalidate its communication credentials
- Reinstalling the same deployment creates multiple indistinguishable records
- There is no operator flow for "this machine is gone, remove its trust"

**Phase to address:**
Phase 2: Secure enrollment and identity lifecycle

---

### Pitfall 8: Skipping version and capability negotiation

**What goes wrong:**
The hosted plane assumes every gateway supports the same heartbeat fields, action types, and config semantics. Older deployments then misreport health, reject actions, or apply incompatible changes.

**Why it happens:**
Teams control both sides early on and hard-code payload shapes instead of designing a versioned protocol with capability discovery.

**How to avoid:**
Version the registration, heartbeat, and action schemas from the start. Require deployments to report software version and capabilities. Gate remote actions on capability checks. Maintain a compatibility matrix and fail closed when the hosted plane wants an unsupported action.

**Warning signs:**
- Heartbeat or command payloads have no schema version
- Hosted code dispatches actions by assumed product version instead of negotiated capability
- Upgrade guidance says "deploy latest everywhere" because mixed versions break

**Phase to address:**
Phase 1: Trust boundary and protocol contract, then Phase 5: Pilot upgrade and rollback validation

## Technical Debt Patterns

Shortcuts that look acceptable in a pilot but become expensive quickly.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Reusing one static registration secret for enroll plus runtime heartbeats | Very fast first demo | Impersonation risk, no clean rotation, weak ownership transfer | Never |
| Treating hosted status as a free-form JSON blob from the gateway | Fast UI iteration | Unstable schema, impossible compatibility guarantees, accidental data leakage | Only for throwaway prototypes, not v2.0 validation |
| Building remote management as arbitrary config patch delivery | Flexible feature velocity | Hidden blast radius, hard rollback, no trustable audit story | Never |
| Inferring deployment identity from hostname alone | Easy onboarding | Clones collide, rebuilds fork inventory, ghost records accumulate | Never |
| Polling hosted config on every request to keep state "fresh" | Simplifies consistency reasoning | Breaks self-hosted reliability and increases latency | Never |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Hosted registration API | Accepting blind enrollments from any bearer of a token | Use one-time bootstrap plus per-deployment operational credentials and explicit operator confirmation |
| Gateway heartbeat pipeline | Reporting from a process that is not the actual request-serving runtime | Report both agent connectivity and local gateway health, and show them separately |
| Local persistence | Storing hosted-issued config only in memory | Persist the last accepted local state and require explicit revalidation on updates |
| Hosted UI | Presenting a single "healthy" badge for all conditions | Separate connectivity freshness, local runtime health, and remote-action status |
| Remote command queue | Allowing actions to execute after long offline periods without TTL or dedupe | Require TTL, idempotency keys, action status transitions, and local replay rejection |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| High-frequency heartbeats with verbose payloads | Control-plane write amplification, noisy dashboards, expensive retention | Send small lease updates on a sane interval and separate detailed diagnostics from heartbeat cadence | Usually breaks first at multi-deployment pilot scale, not massive scale |
| Fan-out polling from every deployment on a short interval | Spiky hosted load and thundering herd behavior | Jitter polling, back off on failures, and avoid tight loops for command retrieval | Breaks as soon as dozens of deployments reconnect after an outage |
| Status recomputation from raw event history on every page load | Slow fleet inventory pages and misleading stale summaries | Materialize latest deployment state and append audit events separately | Breaks once operators manage more than a handful of deployments |
| Shipping full diagnostic payloads for every heartbeat | Storage cost and privacy risk increase together | Keep heartbeats tiny and move detailed diagnostics behind explicit local export flows | Breaks during real pilot traffic and support usage |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Using shared or non-expiring enrollment credentials | Deployment impersonation and unauthorized fleet joins | One-time bootstrap, short TTL, rotate to per-deployment credentials after linking |
| Allowing hosted-originated actions without local authorization checks | Cloud compromise becomes gateway compromise | Enforce allowlisted actions and local policy checks before execution |
| Sending plaintext secrets in remote action payloads or audit logs | Credential leakage through hosted logs and support tooling | Use local secret references or encrypted parameter stores, never plaintext action arguments |
| Treating "outbound-only" as sufficient security by itself | False confidence; stolen credentials still grant control-plane access | Combine outbound transport with strong identity, revocation, scoping, and auditability |
| Failing to scope identity claims narrowly enough | Token replay across environments or tenants | Bind credentials to deployment ID, tenant/account, environment, and capability set |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Saying "self-hosted" without a concrete hosted-data disclosure | Buyers assume hidden SaaS dependence and lose trust | Put the trust boundary and default data egress in the first screen and first doc page |
| Showing "online" with no freshness window | Operators over-trust stale data | Show last seen, freshness state, and which signals are locally reported versus cloud-observed |
| Hiding remote actions inside generic settings saves | Operators cannot tell what was requested remotely versus changed locally | Surface remote actions as discrete audited events with actor, time, target, and outcome |
| Making unlink/revoke a support-only operation | Operators fear lock-in and shadow records | Provide visible self-service unlink and credential rotation flows |

## "Looks Done But Isn't" Checklist

- [ ] **Registration:** Often missing ownership transfer and duplicate identity handling — verify reinstallation, cloning, and revoke/re-link flows
- [ ] **Heartbeats:** Often missing `stale` and `unknown` semantics — verify the UI becomes honest during packet loss and hosted outages
- [ ] **Hosted visibility:** Often missing a strict metadata contract — verify docs state exactly what leaves the environment by default
- [ ] **Remote management:** Often missing TTL, idempotency, and replay protection — verify queued actions cannot execute twice or days later
- [ ] **Hybrid reliability:** Often missing outage drills — verify the self-hosted serving path continues during total hosted-plane loss
- [ ] **Versioning:** Often missing capability negotiation — verify older gateways are shown accurately and unsupported actions fail closed

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Blurred trust boundary shipped to pilots | HIGH | Freeze new hosted features, publish a hard boundary doc, move any runtime-critical logic back on-box, and rerun outage drills |
| Weak registration secrets leaked or reused | HIGH | Revoke bootstrap tokens, rotate all operational credentials, force re-link where identity cannot be proven, and audit past enrollments |
| Misleading heartbeat semantics | MEDIUM | Introduce stale/offline states, backfill lease expiry fields, and annotate prior status records as unreliable if needed |
| Unsafe remote management action shipped | HIGH | Disable the action type server-side, invalidate queued actions, publish audit guidance, and reduce the command surface to an allowlist |
| Ghost deployments and duplicate identities | MEDIUM | Add tombstones and conflict detection, merge or archive records, and require fresh attestations for ambiguous deployments |
| Version skew breaking hosted actions | MEDIUM | Gate actions by capability, hotfix schema negotiation, and document a minimum supported version for pilots |

## Pitfall-to-Phase Mapping

Suggested phase structure for this milestone:
- Phase 1: Trust boundary and protocol contract
- Phase 2: Secure enrollment and identity lifecycle
- Phase 3: Heartbeats, status model, and hosted UX honesty
- Phase 4: Narrow remote management with audit and rollback
- Phase 5: Pilot docs, resilience drills, and upgrade validation

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Blurred hosted/local trust boundary | Phase 1 | Hosted outage drill proves serving still works and docs clearly state local enforcement boundaries |
| Weak registration identity | Phase 2 | Bootstrap token reuse, stolen token, revoke, and ownership transfer scenarios all fail safely |
| Hosted plane on serving path | Phase 1, then Phase 5 | Gateway continues serving with cloud disconnected and status degrades honestly to stale/unknown |
| Misleading heartbeat semantics | Phase 3 | UI and API expose freshness windows and differentiate local runtime health from connectivity |
| Over-broad remote management | Phase 4 | Every remote action is allowlisted, idempotent, TTL-bound, audited, and locally authorized |
| Excessive data egress to hosted plane | Phase 1, then Phase 5 | Data disclosure doc matches observed network payloads in test captures |
| Missing revoke/unlink lifecycle | Phase 2 | Reinstall, retire, unlink, and clone scenarios do not create ghost or privileged stale records |
| Version/capability mismatch | Phase 1, then Phase 5 | Mixed-version pilot test shows unsupported actions fail closed without corrupting status |

## Sources

- [Kubernetes Leases](https://kubernetes.io/docs/concepts/architecture/leases/) - official lease-based heartbeat pattern; HIGH confidence
- [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/) - outbound-only, redundant connector pattern; HIGH confidence
- [Cloudflare control/data plane separation pattern](https://developers.cloudflare.com/reference-architecture/diagrams/storage/durable-object-control-data-plane-pattern/) - separation rationale; MEDIUM confidence for Nebula adaptation
- [Tailscale KB: What happens when the coordination server is down?](https://tailscale.com/kb/1023/troubleshooting#what-happens-when-the-coordination-server-is-down) - self-hosted connectivity should survive control-plane loss; HIGH confidence
- [SPIFFE/SPIRE configuring node attestation](https://spiffe.io/docs/latest/deploying/configuring/) - attested workload/node identity patterns; HIGH confidence
- [Elastic Agent command reference](https://www.elastic.co/docs/reference/fleet/agent-command-reference) - enrollment workflow, tags, and privilege constraints in managed-agent systems; MEDIUM confidence
- [AWS Systems Manager Run Command](https://docs.aws.amazon.com/systems-manager/latest/userguide/running-commands.html) - remote command logging and secret-handling constraints; HIGH confidence

---
*Pitfalls research for: Hybrid hosted control plane for a self-hosted AI gateway*
*Researched: 2026-03-18*