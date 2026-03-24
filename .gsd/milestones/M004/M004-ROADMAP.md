# M004: Hosted Adoption Reinforcement

**Vision:** Improve Nebula’s hosted and control-plane adoption touches only where they make onboarding, fleet understanding, and operator confidence materially better, while preserving the metadata-only trust boundary and keeping local runtime enforcement authoritative. The milestone should focus on reinforcement, not authority: hosted surfaces become clearer, more confidence-building, and more useful for evaluators and operators across one or more deployments without becoming the serving-time source of truth.

## Success Criteria

- A self-hosted operator can open the hosted console and understand fleet posture across multiple deployments without ambiguity about what is linked, pending, stale, offline, or blocked for bounded hosted actions.
- Hosted surfaces make onboarding and fleet state easier to interpret across deployments while remaining clearly descriptive and metadata-backed.
- The metadata-only trust boundary is clearer after the milestone, not blurrier, and the hosted console never reads as authoritative for local runtime enforcement.
- At least one integrated proof shows how hosted surfaces reinforce adoption and operator confidence without becoming authoritative for local enforcement.
- The resulting hosted experience materially helps multi-deployment evaluators and operators, not just a single-node demo.

## Key Risks / Unknowns

- Clearer fleet summaries may accidentally imply hosted authority over runtime truth — that would undermine the milestone even if the UX becomes easier to read.
- The current hosted deployment model may not expose enough descriptive signal for a truthful fleet posture layer — pushing too far could create pressure for scope drift.
- More status cues could turn the hosted console into a noisy dashboard instead of a confidence-building adoption surface.

## Proof Strategy

- Hosted-authority drift risk → retire in S01 by proving the allowed reinforcement scope, vocabulary, and trust-boundary guardrails are explicit enough that downstream UI work stays descriptive.
- Fleet-posture truthfulness risk → retire in S02 by proving a real hosted console posture layer can be built from existing deployment, freshness, dependency, and bounded-action facts without faking authority.
- Confidence-story credibility risk → retire in S03 by proving one integrated walkthrough and focused validation show hosted reinforcement helping onboarding and fleet understanding while local runtime enforcement remains authoritative.
- Noise/regression risk → retire in S04 by proving any issues discovered during integrated proof are closed with targeted refinements rather than broader expansion.

## Verification Classes

- Contract verification: focused Vitest coverage for new hosted posture summaries, deployment interpretation components, and trust-boundary wording; artifact checks for docs and proof files; source checks for schema/model alignment where relevant.
- Integration verification: real console wiring across deployment inventory, detail interpretation, trust-boundary module, and bounded remote-action surfaces, backed by the existing admin/deployment API shapes.
- Operational verification: hosted freshness and outage semantics remain visibility-only; local serving authority is still explained as local even when hosted data is stale or offline.
- UAT / human verification: confirm the hosted console now reads as a clear non-authoritative fleet posture surface for a multi-deployment evaluator.

## Milestone Definition of Done

This milestone is complete only when all are true:

- All slice deliverables are complete and the hosted console exposes a real fleet posture reading surface, not just isolated deployment details.
- The hosted posture summaries, trust-boundary wording, and bounded remote-action framing are actually wired together.
- The real hosted console entrypoint exists and is exercised through the deployment-management workflow and integrated proof.
- The success criteria are re-checked against live behavior and proof artifacts, not just static copy changes.
- Final integrated acceptance passes without making the hosted plane feel authoritative for serving-time health, routing, fallback, or policy enforcement.

## Requirement Coverage

- Covers: R032, R033, R034, R035, R036, R037, R038
- Partially covers: R014
- Leaves for later: R039, R040
- Orphan risks: none

## Slices

- [x] **S01: Hosted reinforcement boundary** `risk:high` `depends:[]`
  > After this: The hosted reinforcement guardrails are explicit in code/doc language, so downstream slices can improve fleet posture and confidence without drifting into hosted authority.

- [ ] **S02: Fleet posture UX** `risk:high` `depends:[S01]`
  > After this: An operator can open the hosted console and immediately read fleet posture across deployments — linked vs pending, current vs stale/offline, bounded-action blocked states, and confidence cues — without mistaking hosted state for local runtime authority.

- [ ] **S03: Confidence proof and trust walkthrough** `risk:medium` `depends:[S01,S02]`
  > After this: One integrated proof shows the hosted console reinforcing onboarding clarity and multi-deployment understanding while keeping local runtime enforcement authoritative.

- [ ] **S04: Targeted reinforcement refinements** `risk:low` `depends:[S02,S03]`
  > After this: Any wording, evidence-mapping, or interpretation gaps found during the integrated proof are closed without widening hosted scope.

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
