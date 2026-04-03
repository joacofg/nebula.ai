# S01 Research — Define page roles and evidence boundaries

## Summary

S01 directly owns **R050** (Observability has a single primary role as request investigation) and **R051** (request detail remains the authoritative persisted evidence record), and it supports **R055** (no dashboard/routing-studio/parallel-workflow drift). It also needs to lay the product-language spine that later slices will use for **R052–R054**.

The important finding: the current console already contains most of the intended philosophy in copy and tests, but the hierarchy is not yet structurally disciplined enough. `console/src/app/(console)/observability/page.tsx` explicitly says “Selected request evidence first”, yet the rendered order is:
1. filters
2. **supporting context**
3. **selected request**
4. dependency health

That means the page identity is asserted in prose while contradicted by page sequencing. Request detail itself is in better shape: `console/src/components/ledger/ledger-request-detail.tsx` is already the authoritative persisted-evidence surface with restrained interpretation layered on top. Policy preview is also structurally close to the target state, but it lives in later slices; for S01 the relevant point is to define its role boundary, not to redesign it yet.

This slice should therefore produce the explicit page-role/evidence-boundary contract and lock it in tests/docs before S02–S04 start changing layout or supporting seams.

## Relevant requirements

### Owned here
- **R050** — Observability leads with one selected request investigation flow rather than competing equally with tenant summary, recommendation, cache, or dependency panels.
- **R051** — Request detail shows the persisted route/provider/fallback/calibration/policy evidence as the authoritative record, with only restrained interpretation layered on top.

### Supported here
- **R055** — Clarify page identity without widening into a dashboard, routing studio, or alternate operator workflow.
- **Sets direction for later slices:**
  - **R052** — policy preview as save / don’t-save decision flow
  - **R053** — supporting context subordinate to primary evidence
  - **R054** — next operator action legible from page structure, not prose alone

## Skill-informed implementation notes

- From the installed **react-best-practices** skill: preserve existing simple client-query structure and avoid speculative abstractions. This slice should define seams and wording/tests first, not introduce new shared UI frameworks or refactor TanStack Query flows without need.
- From the installed **frontend-design** skill: structure must carry meaning. For this milestone that translates to page order and section dominance doing the work, not copy-only cleanup.

## Skill discovery

Relevant technology-specific skills not currently installed:

- **Next.js / App Router**
  - Suggested skill: `wshobson/agents@nextjs-app-router-patterns`
  - Install: `npx skills add wshobson/agents@nextjs-app-router-patterns`
  - Why relevant: highest install count from search; directly relevant to route-level page structure work in `console/src/app/(console)/*`.

- **TanStack Query**
  - Suggested skill: `deckardger/tanstack-agent-skills@tanstack-query-best-practices`
  - Install: `npx skills add deckardger/tanstack-agent-skills@tanstack-query-best-practices`
  - Why relevant: useful if later slices need to tighten fetch sequencing or selected-request data dependencies without adding redundant queries.

No install needed for this slice; current repo patterns are already clear enough.

## Implementation landscape

### 1. Observability page: existing philosophy is present, but sequencing still dilutes the role
- **File:** `console/src/app/(console)/observability/page.tsx`
- **What it does now:**
  - Fetches tenants, usage ledger, runtime health, and tenant recommendations.
  - Auto-selects the first tenant and first ledger row.
  - Renders four major surface groups:
    1. page intro
    2. `LedgerFilters`
    3. **Supporting context** (recommendations, calibration summary, cache posture)
    4. **Selected request** (table + `LedgerRequestDetail`)
    5. **Dependency health**
- **Important current wording:**
  - Header: “Selected request evidence first”
  - Supporting section: “Grounded follow-up guidance for the selected request”
  - Selected-request section: “Inspect one persisted ledger row before reading tenant context”
- **Constraint for planner:** the selected-request-first model is already a documented/tested intention, so later execution should tighten structure around that intent rather than invent a new product philosophy.
- **Main risk:** if S03 tries to rework Observability before S01 defines the page-role contract, it will likely produce another copy-heavy iteration with the same structural contradiction.

### 2. Request detail already embodies the right evidence boundary
- **File:** `console/src/components/ledger/ledger-request-detail.tsx`
- **What it does now:**
  - Renders persisted request fields first (`request_id`, `tenant_id`, route/provider/model/status/token fields).
  - Adds bounded interpretation sections only when supporting data exists:
    - `Calibration evidence`
    - `Budget policy evidence`
    - `Routing inspection`
    - `Route signals`
- **Natural seam:** this component is the canonical implementation target for **R051**. It should remain the reference surface for “authoritative record first, restrained interpretation second.”
- **Constraint for planner:** later slices should avoid moving authority away from this component. If Observability changes, it should change how this component is framed/placed, not what “authority” means.

### 3. Policy page and form are already close to the target role, but S01 should only define the boundary
- **Files:**
  - `console/src/app/(console)/policy/page.tsx`
  - `console/src/components/policy/policy-form.tsx`
- **What they do now:**
  - Route wrapper loads tenant/options/policy and hands everything to `PolicyForm`.
  - `PolicyForm` has a clear “Preview before save” section with explicit controls:
    - `Preview impact`
    - `Save policy`
    - `Reset changes`
  - Preview output is bounded to replay evidence and changed-request samples.
  - Runtime-enforced controls and soft-budget advisory are already separated.
- **Important current wording:**
  - “Preview before save”
  - “Save remains explicit”
  - “Compact sample of requests whose route, status, policy outcome, or projected cost changed.”
- **Constraint for planner:** S01 should record this as the intended page role for later slices: a decision-review surface, not an analytics surface. But the actual save/don’t-save flow tightening belongs mainly to S04.

### 4. Supporting surfaces are distinct components already; hierarchy can be changed without backend work first
- **Files:**
  - `console/src/components/ledger/ledger-filters.tsx`
  - `console/src/components/ledger/ledger-table.tsx`
  - `console/src/components/health/runtime-health-cards` (imported, not read here)
- **Natural seams:**
  - `LedgerTable` is the request selection mechanism.
  - `LedgerRequestDetail` is the authoritative evidence sink.
  - Recommendations/calibration/cache/dependency cards are already isolated enough to be reordered or reframed later.
- **Implication:** S01 likely does **not** need backend/admin contract changes. The immediate need is page-role definition, structural priority rules, and tests that encode those rules.

## Existing tests and what they already prove

### Observability tests already encode the intended philosophy
- **Files:**
  - `console/src/app/(console)/observability/page.test.tsx`
  - `console/src/app/(console)/observability/observability-page.test.tsx`
- **What they lock today:**
  - Observability is framed around selected request evidence.
  - Supporting context is bounded and explicitly non-authoritative.
  - Calibration/cache/dependency surfaces are described as supporting context.
- **Gap:** these tests mostly assert wording presence, not structural dominance/order. They prove language discipline more than page-role dominance.
- **Planner implication:** S01 should likely add role-boundary assertions that are stronger than text snapshots — for example section order, section headings, or explicit “lead investigation object” semantics.

### Request detail tests are strong and should be treated as the R051 baseline
- **File:** `console/src/components/ledger/ledger-request-detail.test.tsx`
- **What they lock today:**
  - Persisted evidence fields stay primary.
  - Interpretation remains bounded.
  - Calibration/budget/routing explanations are supplementary and explicit.
  - No raw embedding text/vector or unrelated analytics drift.
- **Planner implication:** later slices should preserve these tests and only extend them when page-role definition requires stronger wording.

### Policy tests already support the future role contract
- **Files:**
  - `console/src/components/policy/policy-form.test.tsx`
  - `console/src/components/policy/policy-page.test.tsx`
- **What they lock today:**
  - Preview is explicit and non-saving.
  - Changed-request sample remains compact.
  - Runtime controls vs advisory controls are separated.
- **Planner implication:** S01 can reference these as prior art for the “decision surface” role without changing them yet, unless it wants to add one high-level wording guardrail for consistency.

## Recommended slice decomposition

### First thing to build/prove
1. **Codify the role contract** for the three surfaces in one place:
   - Observability = request investigation first
   - Request detail = authoritative persisted evidence record
   - Policy preview = save / don’t-save decision review
   - Supporting context = subordinate, never peer-authoritative
2. **Lock the hierarchy in tests** before changing supporting contracts.

This is the risk-reducing move because the current page already says the right things but still leaves room for structural regression.

### Natural task seams

#### Task seam A — research/contract artifact
- Likely outputs:
  - slice research artifact (this task)
  - maybe a concise product/decision doc or milestone/slice-level summary of page roles if planner wants a durable textual contract
- Why separate: gives S02–S04 a non-ambiguous target.

#### Task seam B — Observability role-boundary tests and possibly light structural cleanup
- Primary files:
  - `console/src/app/(console)/observability/page.tsx`
  - `console/src/app/(console)/observability/page.test.tsx`
  - `console/src/app/(console)/observability/observability-page.test.tsx`
- Likely work:
  - tighten section order and heading hierarchy
  - ensure selected request is the page’s lead investigation object in structure, not just prose
  - keep supporting context explicitly subordinate
- This is probably the highest-risk execution seam for the milestone.

#### Task seam C — request-detail authority guardrails
- Primary files:
  - `console/src/components/ledger/ledger-request-detail.tsx`
  - `console/src/components/ledger/ledger-request-detail.test.tsx`
- Likely work:
  - minor wording or section-order adjustments only if needed to sharpen “authoritative persisted record” language
  - avoid feature expansion
- This seam is lower risk; current implementation is already close.

#### Task seam D — page-role alignment hooks for later slices
- Primary files:
  - `console/src/app/(console)/policy/page.tsx`
  - `console/src/components/policy/policy-form.tsx`
  - relevant tests
- Likely work in S01: mostly identification, not implementation.
- Main value: tell S04 exactly what role must be preserved when the comparison flow is reworked.

## What to avoid

- Do **not** widen scope into a new dashboard shell, posture homepage, or multi-panel analytics framing. That would violate **R055** and regress the existing bounded wedge.
- Do **not** move authority from `LedgerRequestDetail` into recommendation/calibration/cache summary cards.
- Do **not** treat policy preview as a new workflow family. The current `PolicyForm` already shows the correct bounded shape.
- Do **not** solve this slice with copy alone. The page order contradiction in Observability is the clearest sign that structure has to do real work.

## Verification guidance

### Best focused verification commands for later execution

Primary console suites:
```bash
npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx
```

If S01 only changes Observability/request-detail tests and structure, the minimum relevant subset is:
```bash
npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx
```

### What the verification should prove
- Observability leads with one selected request investigation object.
- Supporting context is visibly subordinate in both wording **and structure/order**.
- Request detail remains the authoritative persisted evidence record.
- No new dashboard/analytics/routing-studio framing appears.
- Policy page language still reads as preview-before-save, not analytics, even if unchanged in this slice.

## Recommendation

Treat S01 as a **product contract + hierarchy guardrail** slice, not a broad implementation slice.

Planner should prioritize:
1. strengthening the explicit page-role contract in tests and durable wording,
2. correcting the biggest current contradiction — Observability’s selected-request-first claim versus supporting-context-first layout,
3. preserving `LedgerRequestDetail` as the authoritative persisted evidence baseline,
4. handing later slices a clear rule: any added supporting evidence must remain secondary to the lead decision object for that page.

That gives S02–S04 a stable target and reduces the risk of repeated “cleaner copy, same page blur” iterations.