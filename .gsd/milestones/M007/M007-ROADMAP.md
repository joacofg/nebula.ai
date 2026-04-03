# M007: 

## Vision
Make Nebula’s operator surfaces feel like a coherent decision system rather than a collection of proof surfaces. Tighten page roles, evidence hierarchy, simulation comparison flow, and request investigation flow so the console becomes easier to trust and easier to act from, without widening into analytics-product sprawl, visual-only polish work, or unrelated routing R&D.

## Slice Overview
| ID | Slice | Risk | Depends | Done | After this |
|----|-------|------|---------|------|------------|
| S01 | Define page roles and evidence boundaries | high | — | ✅ | After this: Nebula has one explicit operator-surface model that says what Observability, request detail, and policy preview are for, what evidence leads, and what context stays secondary. |
| S02 | Tighten supporting evidence and preview contracts | medium | S01 | ✅ | After this: the supporting data and UI seams needed for clearer page roles exist without introducing a new dashboard or routing-research scope. |
| S03 | Rework Observability around a primary investigation flow | high | S01, S02 | ✅ | After this: an operator can open Observability and immediately understand one selected request as the lead investigation object, with all other cards clearly supporting that investigation. |
| S04 | Rework policy preview into a comparison-and-decision flow | medium | S01, S02 | ✅ | After this: an operator can use policy preview to compare baseline versus simulated outcomes and decide whether to save without the page feeling like a blended editor and analytics surface. |
| S05 | Integrated operator proof and close-out | low | S03, S04 | ⬜ | After this: one integrated proof path shows the clarified operator surfaces work together as a coherent decision system without dashboard drift or redesign sprawl. |
