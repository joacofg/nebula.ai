# M007: Operator Decision Clarity — Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

## Project Description

M007 is a product-clarity milestone for Nebula’s operator console. The goal is not to make the UI prettier. The goal is to remove page identity blur so the console feels like a coherent decision system rather than a collection of proof surfaces. The key pages already carry the right raw ingredients — selected request evidence, simulation preview, recommendation context, calibration posture, cache posture, and dependency health — but some of them still feel assembled rather than purpose-built.

The most important page-role decisions from discussion are now explicit: Observability should be a request investigation surface first; request detail should remain the authoritative persisted evidence record with restrained interpretation layered on top; policy preview should support a save / don’t-save decision workflow rather than reading like a mixed settings form plus analytics panel.

## Why This Milestone

Nebula’s backend decisioning story is now stronger after M005 and M006, but the operator surfaces are carrying too many roles at once. That weakens trust: even correct evidence can feel messy if the operator cannot tell what the page is for, what evidence leads, what context is secondary, and what action follows.

This milestone matters now because the right next step is to sharpen the product, not rush open-source-readiness and not open a new routing R&D program. Page identity blur is the clearest current product weakness, and fixing it should make Nebula feel more legible and more trustworthy to operate.

## User-Visible Outcome

### When this milestone is complete, the user can:

- open Observability and immediately understand that one selected request is the primary investigation object, with all surrounding cards clearly subordinate to that investigation
- use policy preview to compare baseline versus simulated outcomes and make a deliberate save / don’t-save decision without the page feeling like a blended analytics surface

### Entry point / environment

- Entry point: operator console pages under `/observability`, ledger request detail, and `/policy`
- Environment: browser / local dev
- Live dependencies involved: gateway admin APIs, runtime health endpoint, existing replay/recommendation/ledger contracts

## Completion Class

- Contract complete means: the supporting admin/UI contracts expose the minimum fields and wording seams needed to express page roles without inventing a new dashboard or workflow family
- Integration complete means: Observability, request detail, and policy preview work together as a coherent operator decision flow with clear primary and secondary evidence boundaries
- Operational complete means: none beyond the existing console runtime lifecycle; this is a product-clarity milestone, not a deployment-lifecycle milestone

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- an operator can investigate a routed request in Observability and understand within seconds what evidence leads, what context is supporting, and what follow-up action the page implies
- an operator can use policy preview to compare baseline and simulated outcomes and reach a clear save / don’t-save decision without switching mental models mid-page
- the assembled console still stays within Nebula’s bounded wedge and does not become a broad dashboard, routing studio, or visual-only redesign

## Risks and Unknowns

- Page identity work could collapse into copy-only cleanup — that would leave the real hierarchy problem unsolved
- Supporting backend/UI contracts may not quite fit the clarified page roles — if so, the milestone needs bounded seam adjustments without drifting into new routing research
- Observability already carries many supporting cards; tightening its primary role without hiding too much useful operator detail will require disciplined sequencing

## Existing Codebase / Prior Art

- `console/src/app/(console)/observability/page.tsx` — already frames Observability as selected-request-first, but still carries multiple supporting roles that compete for page identity
- `console/src/components/ledger/ledger-request-detail.tsx` — authoritative persisted record plus restrained interpretation; this is the baseline to preserve, not replace
- `console/src/components/policy/policy-form.tsx` — current policy editor + replay preview surface that already contains the baseline/simulated comparison seam but still reads as somewhat dual-purpose
- `console/src/app/(console)/observability/page.test.tsx` and `observability-page.test.tsx` — existing tests already encode selected-request-first and bounded-supporting-context language, so M007 should tighten real page role rather than invent a new philosophy
- `docs/v4-integrated-proof.md` and `docs/m006-integrated-proof.md` — previous milestones already established that Observability and policy surfaces must stay bounded and subordinate to durable evidence rather than expanding into dashboard authority

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R050 — Observability has a single primary role as request investigation
- R051 — Request detail remains the authoritative persisted evidence record
- R052 — Policy preview supports a clear save / don’t-save decision workflow
- R053 — Supporting context stays subordinate to the primary evidence on each page
- R054 — Operators can tell what action follows from each decision surface without reading surrounding prose first
- R055 — Page identity is clarified without widening Nebula into a dashboard, routing studio, or parallel operator workflow

## Scope

### In Scope

- clarify page roles across Observability, request detail, and policy preview
- tighten evidence hierarchy so supporting context is visibly secondary to primary evidence
- make policy preview feel like decision review rather than mixed settings + analytics
- make bounded supporting contract changes where current UI seams cannot express the clarified roles cleanly
- re-prove the assembled operator workflow end to end

### Out of Scope / Non-Goals

- broad visual redesign or brand refresh
- new analytics dashboard, routing studio, or alternate operator workflow
- backend routing R&D or decisioning expansion unrelated to operator clarity
- trend-heavy tenant posture surface as a new product concept

## Technical Constraints

- Reuse existing operator surfaces and vocabulary where possible
- Backend changes are allowed only when they directly support clearer operator decisions
- Observability should remain request-investigation-first, not posture-summary-first
- Request detail must stay the authoritative persisted evidence record
- Policy preview must stay preview-before-save, with save remaining explicit

## Integration Points

- `GET /v1/admin/usage/ledger` — selected request evidence source
- `GET /v1/admin/tenants/{tenant_id}/recommendations` — supporting guidance source that must remain subordinate
- `POST /v1/admin/tenants/{tenant_id}/policy/simulate` — baseline vs replay comparison seam for decision review
- `/api/runtime/health` — supporting dependency context, not primary evidence

## Open Questions

- How much supporting contract tightening is actually required once page roles are clarified — current thinking: keep this bounded and only change what the clarified workflow cannot express with existing seams
- Whether request detail needs any reduction in interpretation or only stronger surrounding hierarchy — current thinking: preserve the current evidence-first stance and let surrounding page changes do most of the work
- How much of the page-identity problem can be solved by structure and sequencing versus copy — current thinking: structure must lead, copy can reinforce but not carry the milestone alone
