# S05 Research — Integrated operator proof and close-out

## Summary

S05 is light close-out work, not a new feature slice. The core console seams already exist and are tested: Observability is selected-request-first (`console/src/app/(console)/observability/page.tsx`), request detail remains the authoritative persisted evidence seam (`console/src/components/ledger/ledger-request-detail.tsx`), and policy preview is compare-before-save (`console/src/components/policy/policy-form.tsx`, `console/src/app/(console)/policy/page.tsx`).

The missing work is assembly proof. This slice owns **R055** directly and supports close-out validation for **R050-R054**. The natural deliverable is a new pointer-only integrated proof doc for M007, plus discoverability links from `README.md` and `docs/architecture.md`, followed by a focused assembled verification run across the existing Vitest suites that already encode the hierarchy and anti-drift boundaries.

The main risk is not implementation complexity. It is proof drift: writing an integrated doc that restates contracts, invents a broader dashboard story, or blurs the established page roles. Follow the existing pointer-only pattern from `docs/v4-integrated-proof.md` and `docs/m006-integrated-proof.md` instead of creating a prose-heavy spec.

## Requirement Focus

S05 directly supports or closes:

- **R050** — Observability has a single primary role as request investigation.
- **R051** — Request detail remains the authoritative persisted evidence record.
- **R052** — Policy preview supports a clear save / don’t-save decision workflow.
- **R053** — Supporting context stays subordinate to the primary evidence on each page.
- **R054** — Operators can tell what action follows from each decision surface without reading surrounding prose first.
- **R055** — Page identity is clarified without widening Nebula into a dashboard, routing studio, or parallel operator workflow. **This is the primary S05-owned requirement.**

The requirements file already maps `M007/S05` as supporting R050-R054 and primary owner for R055. S05 should therefore prove the assembled story rather than introduce a new behavior seam.

## Relevant skill guidance

From `react-best-practices`:

- Keep changes local to existing page/component seams; do not introduce unnecessary client state or orchestration.
- Prefer reusing existing surfaces and focused tests over adding new abstraction for close-out-only work.

That aligns with the established M007 pattern from prior slices: tighten structure, wording, and verification in place rather than widening the console.

## Implementation Landscape

### Existing integrated-proof pattern to copy

Two docs already establish the exact close-out pattern S05 should follow:

- `docs/v4-integrated-proof.md`
- `docs/m006-integrated-proof.md`

Both are pointer-only walkthroughs with the same structure:

- state what the proof establishes
- define a strict review order
- point to canonical sources instead of restating contracts
- include a concise “minimal operator walkthrough”
- explicitly list failure modes that reveal scope drift

S05 should create the M007 equivalent rather than invent a different doc style.

### Observability seam

Primary file:

- `console/src/app/(console)/observability/page.tsx`

What it already does:

- page hero frames Observability as **selected request evidence first**
- first major section is **Inspect one persisted ledger row before reading tenant context**
- second major section is **Follow-up context for the selected request**
- follow-up cards explicitly point toward policy preview as the next comparison surface
- supporting cards remain inspection-only and explicitly secondary

Supporting files:

- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/ledger/ledger-table.test.tsx`

The page tests already lock:

- top-level section order
- selected-request-first framing
- explicit anti-drift assertions against `dashboard`, `routing studio`, and `analytics`
- policy-preview follow-up wording
- scoped assertions for duplicated labels and request IDs

`ledger-table.test.tsx` separately locks the bounded selector seam (`Current investigation`, `Select request`) without turning the table into a second detail surface.

### Request-detail authority seam

Primary file:

- `console/src/components/ledger/ledger-request-detail.tsx`

What it already does:

- names the persisted ledger row as the **authoritative evidence row**
- keeps calibration, budget, routing inspection, and route signals subordinate to that request
- does not read like a tenant summary or analytics card

Existing test file:

- `console/src/components/ledger/ledger-request-detail.test.tsx`

S05 likely does not need to change this component unless an integrated-proof doc or discoverability link reveals a wording mismatch. Treat it as stable.

### Policy compare-before-save seam

Primary files:

- `console/src/components/policy/policy-form.tsx`
- `console/src/app/(console)/policy/page.tsx`

What they already do:

- policy page frames load baseline → compare draft → save explicitly
- preview is clearly non-saving (`Preview before save`, `Save remains explicit`)
- preview derives decision summary from bounded simulation evidence
- changed-request sample remains subordinate supporting evidence
- tenant change and successful save clear stale preview state

Existing tests:

- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`

These already lock:

- decision-first preview hierarchy
- bounded sample wording
- preview/save separation
- anti-drift assertions against dashboard/routing-studio/analytics-product framing
- reset semantics on tenant switch and save success

### Discoverability seams

Files:

- `README.md`
- `docs/architecture.md`

Current pattern:

- both docs link to earlier integrated proof docs (`docs/v4-integrated-proof.md`, `docs/m006-integrated-proof.md`, etc.)
- both act as discoverability maps, not duplicate contracts

S05 should add one new M007 proof link to both files. Keep it in the same pointer-only style; do not restate M007 semantics inline.

### Project-state seam

File:

- `.gsd/PROJECT.md`

Current state says M007 S01-S04 are complete and S05 is next. Expect S05 execution to update this file at summary/close-out time, but research itself only needs to note it as a likely touched file.

## Recommended task split

### Task 1 — Create the M007 integrated proof artifact and wire discoverability

Files likely touched:

- `docs/m007-integrated-proof.md` (new)
- `README.md`
- `docs/architecture.md`

Why this is the first task:

- it defines the exact assembled proof order the verification task should then execute against
- it is low risk and establishes the close-out vocabulary without touching console behavior
- it is the primary delivery vehicle for R055 scope discipline

Recommended content shape for the new doc:

1. what the integrated proof establishes
2. canonical proof order
   - start with Observability as selected-request-first investigation
   - confirm request detail as authoritative persisted evidence
   - move to policy preview as compare-before-save decision surface
   - finish with the anti-drift scope conclusion
3. how the canonical sources fit together
4. minimal operator walkthrough
5. what the walkthrough intentionally does not duplicate
6. failure modes this integrated proof makes obvious

Important constraint:

- keep it pointer-only like `docs/m006-integrated-proof.md`
- do not restate request/response contracts, component copy, or test details inline
- do not invent a new product category such as dashboard, studio, or workflow engine

### Task 2 — Run assembled close-out verification and tighten tests only if the assembled story is missing a guard

Primary files likely touched only if needed:

- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`

Default expectation:

- this is mostly a verification task, not a rewrite task
- existing tests already cover the assembled story well
- only add or tighten assertions if the integrated proof reveals a missing cross-surface anti-drift guard

Natural verification bundle:

```bash
npm --prefix console run test -- --run \
  src/app/'(console)'/observability/page.test.tsx \
  src/app/'(console)'/observability/observability-page.test.tsx \
  src/components/ledger/ledger-request-detail.test.tsx \
  src/components/ledger/ledger-table.test.tsx \
  src/components/policy/policy-form.test.tsx \
  src/components/policy/policy-page.test.tsx
```

What that bundle already proves together:

- Observability is request-investigation-first
- request detail remains authoritative
- policy preview is compare-before-save
- supporting context stays subordinate
- next actions are legible from page structure and headings/copy
- anti-drift language blocks dashboard, routing studio, and analytics framing

## Verification guidance

Primary close-out verification should be the assembled focused Vitest suite above.

Secondary file checks:

- confirm `docs/m007-integrated-proof.md` exists
- confirm `README.md` links to it
- confirm `docs/architecture.md` links to it
- confirm the new doc itself only points to canonical sources rather than duplicating contracts

If executor wants a quick grep-style sanity check after edits:

```bash
rg -n "m007-integrated-proof|M007 integrated proof|Operator Decision Clarity" README.md docs/architecture.md docs/m007-integrated-proof.md
```

## Risks / pitfalls

- **Doc drift into a second spec.** The new integrated proof should not become a replacement for page/component/test truth.
- **Scope drift.** Any wording that implies dashboard, routing studio, analytics product, or a broader redesign regresses R055.
- **Unnecessary console churn.** Most of the console behavior is already encoded and passing; avoid changing working UI code just to “make close-out feel substantial.”
- **Forgetting ledger-table coverage.** `ledger-table.test.tsx` is part of the selected-request-first story, even if no code changes land there.

## Skill discovery suggestions

Relevant installed skill already present:

- `react-best-practices` — relevant for Next.js/React refactors, though S05 is mostly proof assembly, not a deep component rewrite.

Promising uninstalled external skill discovered:

- `wshobson/agents@nextjs-app-router-patterns` — install with `npx skills add wshobson/agents@nextjs-app-router-patterns`

This is only potentially useful if execution ends up touching Next.js route structure more than expected. It is not required for the likely S05 path.

## Recommendation

Plan S05 as a **two-task close-out slice**:

1. **Integrated proof doc + discoverability links** (`docs/m007-integrated-proof.md`, `README.md`, `docs/architecture.md`)
2. **Assembled verification pass** over the existing focused console Vitest suite, with test edits only if the assembled story reveals a real missing guard

Do not plan backend work unless execution finds an actual proof gap. The codebase already has the seams S05 needs; this slice is about assembling and validating them without widening scope.