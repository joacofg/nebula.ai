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
