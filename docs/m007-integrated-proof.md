# M007 integrated proof

This document is Nebula's canonical integrated walkthrough for the M007 operator-surface close-out proof.

It assembles the already-shipped M007 seams into one strict review path without redefining their contracts, replaying their detailed UI copy, or implying broader product scope. Keep these sources in their canonical roles:

- `console/src/app/(console)/observability/page.tsx` — the selected-request-first Observability composition that keeps one persisted request investigation ahead of tenant-scoped follow-up context
- `console/src/components/ledger/ledger-table.tsx` — the bounded request-selection seam that promotes one persisted ledger row into the primary investigation
- `console/src/components/ledger/ledger-request-detail.tsx` — the authoritative request-detail seam for the selected persisted ledger row
- `console/src/app/(console)/policy/page.tsx` — the page-level policy entrypoint that resets preview state on tenant switch and keeps preview/save sequencing explicit
- `console/src/components/policy/policy-form.tsx` — the compare-before-save policy preview seam with bounded changed-request evidence and explicit non-save preview behavior
- `console/src/app/(console)/observability/page.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` — focused executable proof for selected-request-first Observability order and bounded supporting context
- `console/src/components/ledger/ledger-request-detail.test.tsx` and `console/src/components/ledger/ledger-table.test.tsx` — focused executable proof for authoritative request detail and bounded selection affordances
- `console/src/components/policy/policy-form.test.tsx` and `console/src/components/policy/policy-page.test.tsx` — focused executable proof for compare-before-save preview behavior, explicit preview/save separation, and anti-drift copy boundaries

Use this walkthrough when a reviewer needs one discoverable M007 story that proves selected-request-first Observability, authoritative request detail, and compare-before-save policy preview work together as one coherent operator decision flow without widening into dashboard, routing-studio, analytics-product, redesign-sprawl, or parallel-workflow scope.

## What this integrated proof establishes

The M007 proof is complete only when one reviewer can inspect the shipped operator surfaces in order and reach the same narrow conclusion throughout:

1. Observability starts from one selected persisted request instead of starting from tenant-wide context
2. the selected ledger row remains the authoritative evidence seam for route, provider, fallback, routing inspection, and policy outcome
3. ledger-table selection stays a bounded affordance for choosing the current investigation rather than becoming a second detail surface
4. supporting recommendation, calibration, cache, and dependency cards remain follow-up context for the same request investigation
5. policy editing keeps preview-before-save explicit, uses bounded comparison evidence, and does not blur preview with persistence
6. tenant switching and successful saves clear stale preview evidence at the real page entrypoint instead of preserving misleading draft conclusions
7. the assembled proof stays within the shipped operator-surface boundary and does not imply a dashboard concept, routing studio, analytics product, redesign program, or parallel operator workflow

If any step in this walkthrough starts treating supporting context as equal authority with the selected request, or treating preview output as a saved decision, the proof has drifted outside M007.

## Canonical proof order

Follow this sequence in order and keep each seam in its existing role.

### 1. Start with selected-request-first Observability composition

Begin with `console/src/app/(console)/observability/page.tsx`.

This is the canonical entry seam for M007 because it makes the page hierarchy explicit before any lower-level component detail is inspected. Reviewers should confirm here that Observability is composed around one investigation flow:

- the page starts from one selected persisted ledger row
- the primary section appears before supporting tenant context
- follow-up recommendation, calibration, cache, and dependency cards are described as subordinate to the same request investigation
- Observability remains an inspection surface, not a broader operator command center

The integrated proof starts here because later seams should reinforce this request-led hierarchy rather than competing with it.

### 2. Confirm the selected request is promoted through bounded table selection

Next inspect `console/src/components/ledger/ledger-table.tsx`.

This is the canonical request-selection seam for M007. The proof should show that the table does one narrow job well: it promotes a persisted ledger row into the current investigation without turning the table into a second explanation surface. Reviewers should confirm that:

- the current row is marked with explicit bounded selector semantics such as `aria-selected`, pressed button state, and labels like `Current investigation`
- unselected rows remain discoverable as request selectors only
- the table points operators toward the detail view below instead of duplicating detailed explanation inside the table itself

If this seam starts presenting itself as an alternate detail panel or tenant-wide analysis surface, the M007 proof has widened unnecessarily.

### 3. Use request detail as the authoritative evidence seam

Then inspect `console/src/components/ledger/ledger-request-detail.tsx`.

This is the canonical authoritative explanation seam for M007 because it keeps one persisted ledger row as the source of truth for the current investigation. Reviewers should confirm that the component explains the selected request directly through persisted fields such as:

- `request_id`
- route target and provider
- route reason and policy outcome
- fallback and cache state
- routing inspection and calibration context when available
- structured budget-policy evidence when present

The key boundary here is that tenant-scoped calibration or supporting context may help explain the selected request, but they do not replace the persisted request row as the authoritative evidence seam.

### 4. Move to policy preview only after the selected request story is clear

After the selected request and its supporting context are clear, inspect `console/src/components/policy/policy-form.tsx`.

This is the canonical compare-before-save seam for M007. The integrated proof should show that policy editing keeps the operator decision flow explicit:

- preview compares a candidate draft against recent persisted baseline traffic
- preview output is explicitly non-saving
- changed-request samples stay bounded and support the decision instead of turning into a broader analytics surface
- baseline-versus-draft consequence wording appears before the bounded changed-request sample
- the next step points operators toward either more iteration or an explicit save

This matters because M007 is proving controlled operator review, not a new workflow engine or proactive optimization system.

### 5. Confirm the policy page entrypoint preserves preview/save boundaries

Next inspect `console/src/app/(console)/policy/page.tsx`.

This page-level seam closes the authoring side of the proof because it owns tenant switching, preview mutation, and save mutation wiring. Reviewers should confirm that:

- preview and save remain separate mutations
- tenant switches clear stale preview evidence
- successful saves clear stale preview evidence
- the page framing continues to describe preview as a comparison step before persistence

This is the point where misleading state can creep in. If stale preview evidence survives tenant changes or successful saves, operators can read outdated conclusions as current truth.

### 6. Finish with the focused executable proof seams

Finally inspect the focused Vitest seams in this order:

- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/components/ledger/ledger-table.test.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`

These files are the code-backed close-out proof for M007 because they lock the page order, scoped authority boundaries, bounded selector semantics, preview-before-save behavior, and anti-drift copy boundaries directly in the shipped worktree.

## How the canonical sources fit together

Use this map when deciding which source to open for detail.

| Need | Canonical source | Why it stays separate |
|---|---|---|
| Request-first Observability page hierarchy | `console/src/app/(console)/observability/page.tsx` | Keeps top-level operator composition and follow-up ordering tied to the shipped page |
| Bounded request-selection affordance | `console/src/components/ledger/ledger-table.tsx` | Keeps row selection semantics narrow instead of widening the table into a second detail surface |
| Authoritative selected-request explanation | `console/src/components/ledger/ledger-request-detail.tsx` | Keeps persisted request evidence primary and tenant context subordinate |
| Compare-before-save page entry and reset behavior | `console/src/app/(console)/policy/page.tsx` | Keeps preview/save wiring and stale-state clearing tied to the real page entrypoint |
| Preview-before-save comparison and bounded changed-request evidence | `console/src/components/policy/policy-form.tsx` | Keeps draft comparison, next-step wording, and explicit non-save behavior anchored to the shipped form |
| Executable request-first and anti-drift proof | focused Vitest files under `console/src/app/(console)/observability/` and `console/src/components/{ledger,policy}/` | Keeps the close-out story grounded in scoped assertions instead of prose-only interpretation |

## Minimal operator walkthrough

Use this concise path when you need the full M007 proof in one review sequence:

1. Start in `console/src/app/(console)/observability/page.tsx` and confirm the page leads with one selected persisted request before any supporting tenant context.
2. In `console/src/components/ledger/ledger-table.tsx`, confirm the current investigation is chosen through bounded selector semantics rather than a second explanation surface.
3. In `console/src/components/ledger/ledger-request-detail.tsx`, confirm the selected persisted ledger row remains the authoritative request-evidence seam.
4. Return to `console/src/app/(console)/observability/page.tsx` and confirm recommendation, calibration, cache, and dependency cards describe themselves as supporting follow-up context for that same request.
5. In `console/src/components/policy/policy-form.tsx`, confirm policy preview compares draft versus baseline before save, keeps preview explicitly non-saving, and bounds changed-request evidence.
6. In `console/src/app/(console)/policy/page.tsx`, confirm tenant switching and successful saves clear stale preview evidence at the real page entrypoint.
7. Use the focused Vitest seams to confirm the shipped worktree still enforces page order, request-detail authority, bounded selector semantics, preview-before-save behavior, and explicit anti-drift wording.

That is Nebula's canonical integrated M007 proof path.

## What this walkthrough intentionally does not duplicate

This document does not become a second UI spec, component contract, or test narrative.

It intentionally does not duplicate:

- the full page copy and composition details already shipped in `console/src/app/(console)/observability/page.tsx`
- the complete selection semantics already implemented in `console/src/components/ledger/ledger-table.tsx`
- the full persisted-field rendering and explanation logic already implemented in `console/src/components/ledger/ledger-request-detail.tsx`
- the complete preview, validation, and save behavior already implemented in `console/src/components/policy/policy-form.tsx`
- the page-entrypoint query and mutation wiring already implemented in `console/src/app/(console)/policy/page.tsx`
- the full scoped assertions already encoded in the focused Vitest files for Observability, request detail, ledger table, policy form, and policy page

If one of those details changes, update the canonical source rather than copying replacement detail into this walkthrough.

## Failure modes this integrated proof makes obvious

These failure modes are the review shortcuts that reveal M007 proof drift before a reviewer has to infer it from scattered code and test files.

The integrated proof has failed if any of these become true:

- Observability no longer starts from one selected persisted request before supporting context
- supporting recommendation, calibration, cache, or dependency cards stop describing themselves as subordinate follow-up context for the selected request
- ledger-table selection stops being a bounded selector seam and starts behaving like a second detail surface
- request detail stops presenting the persisted ledger row as the authoritative evidence seam
- policy preview stops being clearly separated from save behavior
- preview evidence becomes unbounded or starts reading like a broader analytics surface
- tenant switching or successful saves stop clearing stale preview evidence
- the walkthrough starts implying a dashboard, routing studio, analytics product, redesign-sprawl initiative, or parallel operator workflow as a positive product claim

## Related docs and code-backed seams

- `console/src/app/(console)/observability/page.tsx` — selected-request-first Observability composition
- `console/src/components/ledger/ledger-table.tsx` — bounded current-investigation selector semantics
- `console/src/components/ledger/ledger-request-detail.tsx` — authoritative selected-request evidence seam
- `console/src/components/policy/policy-form.tsx` — compare-before-save preview seam
- `console/src/app/(console)/policy/page.tsx` — policy page entrypoint, preview wiring, and stale-preview reset behavior
- `console/src/app/(console)/observability/page.test.tsx` — focused request-first page-order proof
- `console/src/app/(console)/observability/observability-page.test.tsx` — focused supporting-context boundary proof
- `console/src/components/ledger/ledger-request-detail.test.tsx` — focused authoritative request-detail proof
- `console/src/components/ledger/ledger-table.test.tsx` — focused bounded selector proof
- `console/src/components/policy/policy-form.test.tsx` — focused preview-before-save and anti-drift copy proof
- `console/src/components/policy/policy-page.test.tsx` — focused page-entrypoint reset and preview/save separation proof
