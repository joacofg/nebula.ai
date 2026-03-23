# M002: Production Structuring Model

**Vision:** Nebula gives operators one clear, runtime-truthful way to structure tenants, API keys, applications, workloads, and admin responsibilities for production use without overpromising entities or controls that do not exist.

## Success Criteria

- A self-hosted operator can decide how to structure a production deployment around tenants and API keys without guessing what Nebula actually enforces.
- Docs and relevant operator surfaces consistently distinguish enforced runtime entities from conceptual guidance.
- Multi-tenant key behavior and tenant-selection rules remain clear enough that production callers know when `X-Nebula-Tenant-ID` is required.
- App and workload language is useful for teams but never misrepresented as a first-class runtime object unless implementation exists.

## Key Risks / Unknowns

- Production-structuring ambiguity may live more in product surfaces than docs — fixing docs alone might not retire the real risk.
- Teams may need stronger app/workload framing than M001 provides — but introducing real entities would widen scope fast.
- Existing operator UI wording may conflict with the canonical docs and erode trust.

## Proof Strategy

- Product-surface ambiguity beyond docs → retire in S01 by proving the most important operator-facing surfaces tell the same tenant/API-key structuring story as the canonicals.
- Need for stronger app/workload framing without runtime redesign → retire in S02 by proving teams can apply guidance consistently without first-class app/workload entities.
- Final production-model coherence across docs and operator flow → retire in S03 by proving the assembled guidance works as one end-to-end structuring walkthrough.

## Verification Classes

- Contract verification: targeted docs integrity checks, relevant backend/admin tests, and any affected console tests for wording/behavior seams
- Integration verification: real operator flow across docs plus console/admin surfaces using the current tenant and API-key model
- Operational verification: none beyond preserving existing self-hosted governance behavior
- UAT / human verification: confirm the production-structuring story reads coherently to an operator making real environment decisions

## Milestone Definition of Done

This milestone is complete only when all are true:

- all slice deliverables are complete
- shared documentation and operator-surface wording are actually aligned
- the real operator entrypoints exist and are exercised against the current runtime model
- success criteria are re-checked against live behavior, not just planning artifacts
- final integrated acceptance scenarios pass

## Requirement Coverage

- Covers: R006, R012
- Partially covers: R011
- Leaves for later: R013, R014
- Orphan risks: none yet

## Slices

- [ ] **S01: Operator structuring truth surface** `risk:high` `depends:[]`
  > After this: the highest-impact operator-facing docs and product surfaces agree on the tenant/API-key/runtime-truth model, and the biggest production-structuring contradiction is removed.
- [ ] **S02: App/workload guidance without fake runtime entities** `risk:medium` `depends:[S01]`
  > After this: a team can map apps and workloads onto Nebula's real tenant/key model using concrete guidance without the product pretending app/workload are enforced objects.
- [ ] **S03: Integrated production-structuring walkthrough** `risk:low` `depends:[S01,S02]`
  > After this: one end-to-end production-structuring story is demoable across the canonicals and operator surfaces as a coherent operator workflow.

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
