# M007: M007

**Vision:** Make Nebula’s operator surfaces feel like a coherent decision system rather than a collection of proof surfaces. Tighten page roles, evidence hierarchy, simulation comparison flow, and request investigation flow so the console becomes easier to trust and easier to act from, without widening into analytics-product sprawl, visual-only polish work, or unrelated routing R&D.

## Success Criteria

- An operator can open Observability and understand within seconds that one selected request is the primary investigation object and that surrounding cards are supporting context.
- An operator can use request detail as the authoritative persisted evidence record without it being overshadowed by summaries or helper panels.
- An operator can compare baseline versus simulated policy outcomes and make a clear save / don’t-save decision from the policy surface.
- The clarified console remains bounded: no broad analytics dashboard, routing studio, alternate workflow, or redesign-only milestone emerges.
- Focused verification proves the assembled operator workflow is more legible and trustworthy to operate.

## Slices

- [x] **S01: Define page roles and evidence boundaries** `risk:high` `depends:[]`
  > After this: After this: Nebula has one explicit operator-surface model that says what Observability, request detail, and policy preview are for, what evidence leads, and what context stays secondary.

- [x] **S02: Tighten supporting evidence and preview contracts** `risk:medium` `depends:[S01]`
  > After this: After this: the supporting data and UI seams needed for clearer page roles exist without introducing a new dashboard or routing-research scope.

- [x] **S03: Rework Observability around a primary investigation flow** `risk:high` `depends:[S01,S02]`
  > After this: After this: an operator can open Observability and immediately understand one selected request as the lead investigation object, with all other cards clearly supporting that investigation.

- [x] **S04: Rework policy preview into a comparison-and-decision flow** `risk:medium` `depends:[S01,S02]`
  > After this: After this: an operator can use policy preview to compare baseline versus simulated outcomes and decide whether to save without the page feeling like a blended editor and analytics surface.

- [x] **S05: Integrated operator proof and close-out** `risk:low` `depends:[S03,S04]`
  > After this: After this: one integrated proof path shows the clarified operator surfaces work together as a coherent decision system without dashboard drift or redesign sprawl.

## Boundary Map

## Boundary Map

### S01 → S02
Produces:
- Operator surface role map for `/observability`, ledger request detail, and `/policy`
- Explicit primary-vs-supporting evidence rules for each surface
- Page-purpose wording targets that downstream implementation and tests can lock

Consumes:
- Existing operator vocabulary and trust-boundary patterns from M005 and M006

### S02 → S03
Produces:
- Bounded admin/UI contract adjustments needed to express request-first and decision-first page roles cleanly
- Stable supporting-context data seams for Observability that keep selected request evidence primary

Consumes from S01:
- Page role map and evidence hierarchy rules

### S02 → S04
Produces:
- Stable preview/comparison contract expectations for baseline vs simulated policy decisions
- Explicit separation between editable controls and decision-review evidence

Consumes from S01:
- Page role map and evidence hierarchy rules

### S03 → S05
Produces:
- Request-investigation-first Observability flow with clearly subordinate recommendation, calibration, cache, and dependency context
- Updated Observability verification seams proving page identity and action legibility

Consumes from S02:
- Supporting evidence contract adjustments

### S04 → S05
Produces:
- Policy preview flow centered on save / don’t-save decision review
- Updated policy verification seams proving baseline-vs-preview comparison remains bounded and legible

Consumes from S02:
- Preview/comparison contract adjustments

### S01 → S05
Produces:
- Canonical operator page-role model used to judge final integrated clarity

Consumes:
- none (first slice)
