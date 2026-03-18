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
