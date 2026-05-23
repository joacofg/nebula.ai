# M004: M004: Hosted Adoption Reinforcement

**Vision:** Improve Nebula’s hosted and control-plane adoption touches only where they make onboarding, fleet understanding, and operator confidence materially better, while preserving the metadata-only trust boundary and keeping local runtime enforcement authoritative. The milestone should focus on reinforcement, not authority: hosted surfaces become clearer, more confidence-building, and more useful for evaluators and operators across one or more deployments without becoming the serving-time source of truth.

## Success Criteria

- A self-hosted operator can open the hosted console and understand fleet posture across multiple deployments without ambiguity about what is linked, pending, stale, offline, or blocked for bounded hosted actions.
- Hosted surfaces make onboarding and fleet state easier to interpret across deployments while remaining clearly descriptive and metadata-backed.
- The metadata-only trust boundary is clearer after the milestone, not blurrier, and the hosted console never reads as authoritative for local runtime enforcement.
- At least one integrated proof shows how hosted surfaces reinforce adoption and operator confidence without becoming authoritative for local enforcement.
- The resulting hosted experience materially helps multi-deployment evaluators and operators, not just a single-node demo.

## Slices

- [x] **S01: Hosted reinforcement boundary** `risk:high` `depends:[]`
  > After this: The hosted reinforcement guardrails are explicit in code/doc language, so downstream slices can improve fleet posture and confidence without drifting into hosted authority.

- [x] **S02: Fleet posture UX** `risk:high` `depends:[S01]`
  > After this: An operator can open the hosted console and immediately read fleet posture across deployments — linked vs pending, current vs stale/offline, bounded-action blocked states, and confidence cues — without mistaking hosted state for local runtime authority.

- [x] **S03: Confidence proof and trust walkthrough** `risk:medium` `depends:[S01,S02]`
  > After this: One integrated proof shows the hosted console reinforcing onboarding clarity and multi-deployment understanding while keeping local runtime enforcement authoritative.

- [x] **S04: Targeted reinforcement refinements** `risk:low` `depends:[S02,S03]`
  > After this: Any wording, evidence-mapping, or interpretation gaps found during the integrated proof are closed without widening hosted scope.

## Boundary Map

## Boundary Map

### S01 → S02

Produces:
- locked hosted reinforcement vocabulary for fleet posture, confidence cues, and non-authoritative status interpretation
- explicit trust-boundary guardrails for what hosted summaries may and may not imply
- stable acceptance criteria for using existing deployment metadata in hosted posture UI

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- milestone-level trust-boundary framing for integrated proof
- explicit rule that local runtime enforcement remains authoritative even when hosted data is stale or offline

Consumes:
- nothing (first slice)

### S02 → S03

Produces:
- hosted fleet posture summary surfaces in the console
- clearer deployment-state interpretation across linked, pending, stale, offline, revoked, unlinked, and bounded-action-blocked cases
- trust-boundary-aware confidence cues grounded in existing deployment facts

Consumes from S01:
- hosted reinforcement vocabulary and trust-boundary guardrails

### S02 → S04

Produces:
- concrete UI seams, wording, and evidence points that can be evaluated during integrated proof

Consumes from S01:
- hosted reinforcement vocabulary and trust-boundary guardrails

### S03 → S04

Produces:
- integrated proof artifact for hosted adoption reinforcement
- focused validation findings showing any remaining clarity or interpretation gaps

Consumes from S01:
- trust-boundary framing and local-authority rule

Consumes from S02:
- hosted fleet posture summary surfaces and deployment interpretation UI
