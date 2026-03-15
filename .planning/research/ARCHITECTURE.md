# Architecture Research

**Domain:** B2B LLM gateway and operator platform
**Researched:** 2026-03-15
**Confidence:** HIGH

## Standard Architecture

### System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      Operator Surface                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Admin UI     │  │ Playground   │  │ Docs / Runbooks  │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                   │            │
├─────────┴─────────────────┴───────────────────┴────────────┤
│                      Gateway Control Layer                  │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐  │
│  │ FastAPI Gateway: auth, routing, policy, ledger, API   │  │
│  └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                         Data / Integrations                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Postgres     │  │ Qdrant       │  │ LLM Providers    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Gateway API | Normalize requests, enforce policy, route traffic, expose admin APIs | FastAPI service with typed models and service layer |
| Operator console | Tenant, key, policy, playground, ledger workflows | Next.js admin app |
| Governance store | Durable tenants, keys, policies, and usage ledger | PostgreSQL with migrations |
| Semantic cache | Similarity-based response reuse | Qdrant or equivalent vector store |
| Provider adapters | Connect to local and premium model backends | HTTP clients behind a shared provider interface |

## Recommended Project Structure

```text
src/
├── nebula/                  # Existing gateway backend
│   ├── api/                 # Public and admin HTTP routes
│   ├── services/            # Routing, policy, governance, cache
│   ├── providers/           # Provider adapters
│   └── observability/       # Metrics, logging, middleware
├── web/                     # New operator console
│   ├── app/                 # Next.js routes and layouts
│   ├── components/          # UI building blocks
│   ├── lib/                 # API client, auth/session helpers
│   └── features/            # Tenants, keys, playground, ledger
└── infra/                   # Deployment and runtime packaging
```

### Structure Rationale

- **`src/nebula/`:** Preserve and evolve the current backend instead of mixing in UI concerns
- **`web/`:** Keep the operator surface independent so UI scope can move quickly without destabilizing the gateway
- **`infra/`:** Give deployment and packaging first-class visibility, because this product must be runnable by others

## Architectural Patterns

### Pattern 1: Control Plane + Data Plane Split

**What:** Separate operator/admin workflows from request-serving gateway logic
**When to use:** When the product is infrastructure that still needs a UI
**Trade-offs:** Cleaner product boundaries, but requires API discipline

### Pattern 2: Provider Strategy Interface

**What:** Put each upstream model provider behind a common interface
**When to use:** When routing/fallback must remain provider-agnostic
**Trade-offs:** Slight abstraction cost, but much easier provider expansion and testing

### Pattern 3: Policy Resolution Before Execution

**What:** Resolve routing constraints, cache toggles, and budget/allowlist checks before calling providers
**When to use:** Always for B2B infrastructure products with governance requirements
**Trade-offs:** More up-front decision logic, but clearer auditability and safer behavior

## Data Flow

### Request Flow

```text
Client SDK
    ↓
FastAPI route → auth/policy → cache lookup → provider selection → provider call
    ↓               ↓             ↓               ↓                  ↓
HTTP response ← metadata ← cache store ← ledger write ← result normalization
```

### State Management

```text
Operator UI
    ↓ (fetch/mutate)
Admin API → governance store / ledger
    ↓
UI query cache and view state
```

### Key Data Flows

1. **Gateway request flow:** Client request enters the API, receives policy resolution, optionally hits cache, then executes against the selected provider and records usage
2. **Operator workflow flow:** Admin UI mutates tenants/policies/keys and reads ledger data from durable backend APIs

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-10 internal teams | Monolith backend plus small operator UI is fine |
| Early pilots / multiple customers | Move governance persistence to Postgres, improve health/readiness signals, externalize config and secrets |
| Larger rollout | Add stronger tracing, background jobs, and clearer separation between admin/control and high-throughput request paths |

### Scaling Priorities

1. **First bottleneck:** Durable state and migrations, not raw request throughput
2. **Second bottleneck:** Observability and operator debugging when something fails in provider or cache paths

## Anti-Patterns

### Anti-Pattern 1: Building the dashboard directly into the gateway backend

**What people do:** Mix HTML/server template concerns into the API service
**Why it's wrong:** Slows UI iteration and muddies the gateway boundary
**Do this instead:** Keep a dedicated operator frontend

### Anti-Pattern 2: Treating a demo-time SQLite store as the production architecture

**What people do:** Keep bootstrap DDL as the only persistence strategy
**Why it's wrong:** Makes schema changes and concurrent usage fragile
**Do this instead:** Add explicit migrations and a durable database path

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| LLM providers | Synchronous HTTP provider adapters | Preserve a common interface for routing/fallback |
| Qdrant | Vector similarity store | Keep cache optional but observable |
| Postgres | Governance persistence | Use migrations and stable schema ownership |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `web/` ↔ FastAPI admin API | HTTP/JSON | Keep API contracts explicit and versionable |
| Routes ↔ service layer | Direct function calls | Preserve thin route handlers |
| Service layer ↔ providers/store/cache | Interface-driven calls | Enables testing and later expansion |

## Sources

- [Next.js 16 official release](https://nextjs.org/blog/next-16)
- [PostgreSQL documentation](https://www.postgresql.org/docs/)
- [LiteLLM docs](https://docs.litellm.ai/)
- [Qdrant docs](https://qdrant.tech/documentation/)

---
*Architecture research for: B2B LLM gateway and operator platform*
*Researched: 2026-03-15*
