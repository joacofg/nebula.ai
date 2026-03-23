# M001: API Adoption Happy Path

**Vision:** Make Nebula easy to plug into for common chat-completions usage, define the compatibility boundary clearly, and prove migration with a real reference integration that shows routing, policy, observability, and provider abstraction value on day 1.

## Success Criteria

- A developer can integrate a common chat-completions use case with Nebula using the documented happy path in under 30 minutes.
- Nebula exposes a stable and clearly bounded OpenAI-compatible inference path for the most common chat-completions app flows.
- The product documentation makes it obvious where compatibility ends and where Nebula-specific value begins.
- At least one realistic reference integration proves an app can call Nebula instead of a provider directly with minimal code changes.
- The tenant / app / workload / operator model is explicit enough that teams know how to structure production usage.
- The adoption story is credible for startup product teams, platform teams, and enterprise/self-hosted operators.
- Routing, policy, observability, and provider abstraction value are visible immediately during adoption, not buried behind later setup.

## Key Risks / Unknowns

- Compatibility sprawl — a broad promise would create implementation and maintenance drag that weakens the milestone.
- Weak reference proof — a toy integration would undercut the whole adoption claim.
- Production-model ambiguity — unclear tenant / app / workload framing would leave serious teams unsure how to structure usage.
- Docs/product mismatch — if the live API contract and the written story diverge, adoption trust collapses.

## Proof Strategy

- Compatibility sprawl → retire in S01 by proving the supported contract is explicit, narrow, and grounded in the live product behavior.
- Weak reference proof → retire in S03 by proving a realistic app or service migrates with minimal code changes.
- Production-model ambiguity → retire in S02 by proving the quickstart and operating model are concrete enough for a team to follow without guessing.
- Docs/product mismatch → retire in S05 by proving the assembled docs, reference flow, and operator-visible evidence all align in one end-to-end adoption walkthrough.

## Verification Classes

- Contract verification: tests, artifact checks, and documentation-to-live-contract reconciliation against the existing gateway behavior
- Integration verification: real reference app or service calls Nebula through the live gateway path and produces operator-visible evidence
- Operational verification: self-hosted production-like Compose path proves the adoption story in a real environment with real subsystem boundaries
- UAT / human verification: judgment on clarity, credibility, and whether the reference path actually feels adoptable in practice

## Milestone Definition of Done

This milestone is complete only when all are true:

- all slice deliverables are complete
- shared components are actually wired together
- the real entrypoint exists and is exercised
- success criteria are re-checked against live behavior, not just artifacts
- final integrated acceptance scenarios pass

## Requirement Coverage

- Covers: R001, R002, R003, R004, R005, R006, R007, R008, R009, R010
- Partially covers: R011, R012
- Leaves for later: R013, R014
- Orphan risks: none

## Slices

- [x] **S01: Adoption API contract and compatibility boundary** `risk:high` `depends:[]`
  > After this: Nebula exposes a clearly bounded chat-completions adoption surface, with supported and unsupported behaviors documented against the live product contract.

- [ ] **S02: Happy-path quickstart and production model** `risk:medium` `depends:[S01]`
  > After this: A team can follow a concrete quickstart, understand tenant / app / workload / operator structure, and reach a working integration path without guessing.

- [ ] **S03: Reference migration integration** `risk:high` `depends:[S01,S02]`
  > After this: A realistic app or service uses Nebula instead of a direct provider call path with minimal code changes and working end-to-end proof.

- [ ] **S04: Day-1 value proof surface** `risk:medium` `depends:[S01,S03]`
  > After this: The adoption materials and product surfaces make routing, policy, observability, and provider abstraction visibly valuable on the first integration.

- [ ] **S05: Final integrated adoption proof** `risk:medium` `depends:[S02,S03,S04]`
  > After this: The complete v3.0 adoption story is exercised as one joined system: docs, migration path, live reference flow, and operator-visible value all align.

## Boundary Map

### S01 → S02

Produces:
- explicit supported request/response contract for the public chat-completions adoption path
- explicit unsupported/deferred feature list for compatibility boundaries
- compatibility rules for headers, streaming behavior, auth expectations, and model naming guidance

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- stable migration target for a reference app to call
- documented adoption assumptions for base URL, API key usage, request shape, and expected response evidence

Consumes:
- nothing (first slice)

### S01 → S04

Produces:
- compatibility vs Nebula-native boundary that explains what day-1 value must be surfaced outside pure parity

Consumes:
- nothing (first slice)

### S02 → S03

Produces:
- quickstart path and production-model language the reference integration must embody
- tenant / app / workload / operator framing to keep the migration example realistic

Consumes from S01:
- public compatibility contract and migration target

### S03 → S04

Produces:
- working end-to-end reference integration with request flow and operator-visible evidence
- credible migration diff showing minimal code change expectations

Consumes from S01:
- public compatibility contract and supported feature boundary

Consumes from S02:
- quickstart and production-model guidance

### S02 → S05

Produces:
- documented happy path and production structuring model used in final integrated proof

Consumes from S01:
- bounded compatibility contract

### S03 → S05

Produces:
- live migration proof artifact and runnable reference path

Consumes from S01:
- stable adoption surface

Consumes from S02:
- quickstart assumptions and operating model

### S04 → S05

Produces:
- operator-facing value proof tying routing, policy, observability, and provider abstraction back to the adoption story

Consumes from S01:
- compatibility vs Nebula-native boundary

Consumes from S03:
- working reference integration outputs
