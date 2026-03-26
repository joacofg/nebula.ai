# M005: Adaptive Decisioning Control Plane

**Vision:** Turn Nebula's existing routing, policy, ledger, and semantic-cache surfaces into a stronger operator decisioning control plane. v4 should improve route quality, policy safety, spend control, and cache effectiveness through adaptive routing, simulation, hard guardrails, and recommendation-grade feedback while preserving Nebula's compatibility-first product shape and metadata-boundary discipline.

## Success Criteria

- Nebula routes requests using a materially richer and more explicit decision model than the current prompt-length-plus-keyword heuristic.
- An operator can preview the likely impact of a policy or routing change against recent real traffic before applying it.
- Tenant policy can enforce hard spend guardrails with legible downgrade or denial behavior.
- Operators get actionable feedback about routing, policy, and cache changes that would likely improve cost, latency, or reliability.
- Semantic cache behavior is inspectable and tunable enough to improve hit quality and savings intentionally.
- The milestone sharpens Nebula's v4 wedge without turning into broad API parity, SDK expansion, hosted-authority drift, or unrelated platform work.

## Key Risks / Unknowns

- Richer routing could become harder to understand than the problem it solves.
- Simulation could drift into a detached analytics layer instead of staying close to the real runtime model.
- Hard guardrails could create surprising application behavior if downgrade and denial semantics are not clean.
- Recommendation surfaces could look generic or hand-wavy if they are not grounded in real evidence.
- Cache tuning could sprawl beyond the smallest operator-visible surface that actually improves outcomes.

## Proof Strategy

- Routing-quality risk → retire in S01 by proving a concrete interpretable decision model and backend route-reason surface that are clearly better than the current heuristic.
- Change-safety risk → retire in S02 by proving a real simulation loop can replay recent ledger-backed traffic through candidate policy/routing changes before save.
- Spend-control risk → retire in S03 by proving hard guardrails can change runtime behavior predictably through downgrade or denial semantics.
- Actionability risk → retire in S04 by proving operators get grounded recommendations and cache-tuning visibility rather than just richer raw data.
- Scope-drift risk → retire in S05 by proving the final assembled story strengthens decisioning without widening Nebula into parity, SDK, hosted-authority, or generic platform work.

## Verification Classes

- Contract verification: policy-model, route-reason, and budget-behavior tests plus docs/artifact checks for canonical v4 decisioning guidance.
- Integration verification: backend routing/policy/cache behavior agrees with operator console surfaces and recorded evidence.
- Operational verification: operators can predict route, downgrade, and denial behavior from the configured controls and recommendation surfaces.
- UAT / human verification: a human operator can explain why Nebula chose a route, what a pending change would likely do, and which next action the product recommends.

## Milestone Definition of Done

This milestone is complete only when all are true:

- All slices deliver a real decisioning improvement, not just extra copy or aspirational scoring language.
- The backend decision logic, operator control surfaces, and recorded evidence all agree on the same routing and guardrail model.
- At least one integrated proof shows the operator loop end to end: inspect current behavior, simulate change, apply guardrail/policy update, and verify the outcome.
- Cache tuning and recommendations remain interpretable and narrow rather than growing into a separate analytics subsystem.
- Final integrated acceptance passes without widening Nebula into broad API parity, SDK sprawl, hosted authority, or unrelated platform work.

## Requirement Coverage

- Covers: R039, R040, R041, R042, R043, R044
- Partially covers: R012
- Leaves for later: R013, R025, R026, R027
- Orphan risks: none

## Slices

- [ ] **S01: Adaptive routing model** `risk:high` `depends:[]`
  > After this: Nebula has an interpretable routing decision model that uses explicit signals and records clearer route reasons than the current heuristic.

- [ ] **S02: Policy simulation loop** `risk:high` `depends:[S01]`
  > After this: An operator can simulate a candidate routing or policy change against recent ledger-backed traffic before saving it.

- [ ] **S03: Hard budget guardrails** `risk:medium` `depends:[S01]`
  > After this: Tenant policy can enforce hard spend limits with explicit downgrade or denial behavior and explainable recorded outcomes.

- [ ] **S04: Recommendations and cache controls** `risk:medium` `depends:[S02,S03]`
  > After this: Operators can see grounded next-best-action guidance and tune semantic-cache behavior with enough visibility to improve results intentionally.

- [ ] **S05: Integrated v4 proof** `risk:low` `depends:[S02,S03,S04]`
  > After this: The full v4 decisioning story is assembled end to end and stays narrow, interpretable, and convincingly better than the prior heuristic posture.

## Boundary Map

### S01 → S02

Produces:
- interpretable route-decision model
- richer route-reason vocabulary
- stable backend decision seams that simulation can replay

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- route and downgrade decision semantics that hard budget controls can reuse
- explicit recorded-outcome fields or reasoning needed to explain guardrail behavior

Consumes:
- nothing (first slice)

### S02 → S04

Produces:
- projected-impact outputs for candidate changes
- evidence-backed operator language for likely cost, latency, and reliability effects

Consumes from S01:
- route-decision model and reasons

### S03 → S04

Produces:
- enforced budget behavior and resulting outcome semantics
- concrete tradeoff points recommendations can reason about

Consumes from S01:
- route and downgrade semantics

### S02/S03/S04 → S05

Produces:
- assembled v4 proof package tying route quality, simulation, guardrails, recommendations, and cache controls into one operator loop

Consumes from S02:
- simulation workflow and projected-impact evidence

Consumes from S03:
- hard budget guardrails and outcome evidence

Consumes from S04:
- recommendation and cache-tuning surfaces
