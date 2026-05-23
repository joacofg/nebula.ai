# M005: M005: Adaptive Decisioning Control Plane

**Vision:** Turn Nebula's existing routing, policy, ledger, and semantic-cache surfaces into a stronger operator decisioning control plane. v4 should improve route quality, policy safety, spend control, and cache effectiveness through adaptive routing, simulation, hard guardrails, and recommendation-grade feedback while preserving Nebula's compatibility-first product shape and metadata-boundary discipline.

## Success Criteria

- Nebula routes requests using a materially richer and more explicit decision model than the current prompt-length-plus-keyword heuristic.
- An operator can preview the likely impact of a policy or routing change against recent real traffic before applying it.
- Tenant policy can enforce hard spend guardrails with legible downgrade or denial behavior.
- Operators get actionable feedback about routing, policy, and cache changes that would likely improve cost, latency, or reliability.
- Semantic cache behavior is inspectable and tunable enough to improve hit quality and savings intentionally.
- The milestone sharpens Nebula's v4 wedge without turning into broad API parity, SDK expansion, hosted-authority drift, or unrelated platform work.

## Slices

- [x] **S01: Adaptive routing model** `risk:high` `depends:[]`
  > After this: Nebula has an interpretable routing decision model that uses explicit signals and records clearer route reasons than the current heuristic.

- [x] **S02: Policy simulation loop** `risk:high` `depends:[S01]`
  > After this: An operator can simulate a candidate routing or policy change against recent ledger-backed traffic before saving it.

- [x] **S03: Hard budget guardrails** `risk:medium` `depends:[S01]`
  > After this: Tenant policy can enforce hard spend limits with explicit downgrade or denial behavior and explainable recorded outcomes.

- [x] **S04: Recommendations and cache controls** `risk:medium` `depends:[S02,S03]`
  > After this: Operators can see grounded next-best-action guidance and tune semantic-cache behavior with enough visibility to improve results intentionally.

- [x] **S05: Integrated v4 proof** `risk:low` `depends:[S02,S03,S04]`
  > After this: The full v4 decisioning story is assembled end to end and stays narrow, interpretable, and convincingly better than the prior heuristic posture.

## Boundary Map

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
