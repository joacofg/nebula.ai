# M002: M002: Production Structuring Model

**Vision:** Nebula gives operators one clear, runtime-truthful way to structure tenants, API keys, applications, workloads, and admin responsibilities for production use without overpromising entities or controls that do not exist.

## Success Criteria

- A self-hosted operator can decide how to structure a production deployment around tenants and API keys without guessing what Nebula actually enforces.
- Docs and relevant operator surfaces consistently distinguish enforced runtime entities from conceptual guidance.
- Multi-tenant key behavior and tenant-selection rules remain clear enough that production callers know when `X-Nebula-Tenant-ID` is required.
- App and workload language is useful for teams but never misrepresented as a first-class runtime object unless implementation exists.

## Slices

- [x] **S01: Operator structuring truth surface** `risk:high` `depends:[]`
  > After this: the highest-impact operator-facing docs and product surfaces agree on the tenant/API-key/runtime-truth model, and the biggest production-structuring contradiction is removed.

- [x] **S02: App/workload guidance without fake runtime entities** `risk:medium` `depends:[S01]`
  > After this: a team can map apps and workloads onto Nebula's real tenant/key model using concrete guidance without the product pretending app/workload are enforced objects.

- [x] **S03: Integrated production-structuring walkthrough** `risk:low` `depends:[S01,S02]`
  > After this: one end-to-end production-structuring story is demoable across the canonicals and operator surfaces as a coherent operator workflow.

## Boundary Map

## Boundary Map

### S01 → S02

Produces:
- a stable operator-facing tenant/API-key/runtime-truth framing that downstream guidance can rely on

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- aligned core wording and structuring rules for tenant selection, key scope, and operator responsibilities

Consumes:
- nothing (first slice)
