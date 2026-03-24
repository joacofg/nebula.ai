---
id: M002
milestone: M002
title: Production Structuring Model
status: completed
verification_status: passed
completed_at: 2026-03-23T21:17:00-03:00
integration_branch: codex/v3-api-adoption
code_change_verification:
  status: passed
  command: git diff --stat HEAD $(git merge-base HEAD main) -- ':!.gsd/'
  evidence: Non-.gsd changes exist across console operator surfaces, canonical docs, and supporting tests.
requirement_outcomes: []
summary: >-
  M002 closed successfully by aligning the highest-impact operator surfaces and the integrated
  production walkthrough to Nebula's real tenant/API-key runtime model, while deliberately
  keeping app/workload as conceptual guidance rather than first-class runtime or admin entities.
---

# M002: Production Structuring Model — Milestone Summary

## Milestone Outcome

M002 passed close-out verification in this worktree.

The milestone delivered the production-structuring model promised in the roadmap: operators now have one runtime-truthful story for how to structure production around tenants, API keys, tenant-selection rules, and operator corroboration surfaces. The assembled result stays within Nebula's current product truth. It does not invent backend entities, admin APIs, or fake runtime objects for apps or workloads.

The final integrated story now reads consistently across the touched console surfaces and the canonical composition doc:

1. structure production around real tenants and API keys
2. decide whether `X-Nebula-Tenant-ID` is required
3. send the real public `POST /v1/chat/completions` request first
4. capture `X-Request-ID` plus `X-Nebula-*` response headers
5. correlate the same request in the usage ledger
6. use Tenants, Playground, and Observability only as operator corroboration surfaces

## Code Change Verification

Required code-change verification was completed.

- Command run: `git diff --stat HEAD $(git merge-base HEAD main) -- ':!.gsd/'`
- Result: non-`.gsd/` changes are present
- Verified touched areas include:
  - `console/src/app/(console)/api-keys/page.tsx`
  - `console/src/app/(console)/playground/page.tsx`
  - `console/src/app/(console)/observability/page.tsx`
  - `console/src/app/(console)/tenants/page.tsx`
  - `console/src/components/api-keys/*`
  - `console/src/components/playground/*`
  - `console/src/components/tenants/*`
  - `docs/integrated-adoption-proof.md`
  - existing canonical docs referenced by the integrated walkthrough
  - supporting tests in `console/src/**.test.tsx`

This milestone therefore did not consist only of planning artifacts.

## Success Criteria Verification

### 1. A self-hosted operator can decide how to structure a production deployment around tenants and API keys without guessing what Nebula actually enforces.

**Status:** met

**Evidence:**
- S01 aligned API key issuance and inventory surfaces to real tenant-resolution behavior, including when tenant inference happens automatically and when a public caller must provide `X-Nebula-Tenant-ID`.
- S02 extended the same runtime-truth framing into the Tenants page and tenant editor, explicitly teaching that tenants are the enforced runtime boundary and API keys segment caller access.
- S03 assembled the end-to-end proof order in `docs/integrated-adoption-proof.md` and `.gsd/milestones/M002/slices/S03/S03-UAT.md` so the operator workflow starts from production structuring rather than console guesswork.

### 2. Docs and relevant operator surfaces consistently distinguish enforced runtime entities from conceptual guidance.

**Status:** met

**Evidence:**
- S01 reworded API Keys, Playground, and Observability to match the existing runtime/admin contract.
- S02 made the Tenants page and drawer explicit that app/workload naming is guidance carried through tenant names, API key names, and optional notes, not first-class product objects.
- S03 preserved the same distinction in the integrated walkthrough and UAT failure cues.
- Focused Vitest coverage now locks those boundaries in `console/src/app/(console)/tenants/page.test.tsx`, `console/src/components/tenants/tenant-editor-drawer.test.tsx`, `console/src/components/playground/playground-form.test.tsx`, `console/src/components/playground/playground-page.test.tsx`, and `console/src/app/(console)/observability/page.test.tsx`.

### 3. Multi-tenant key behavior and tenant-selection rules remain clear enough that production callers know when `X-Nebula-Tenant-ID` is required.

**Status:** met

**Evidence:**
- S01 clarified the meaning of `tenant_id` and `allowed_tenant_ids` in API-key creation and listing surfaces.
- S01's summary records the exact rule set: default `tenant_id` auto-resolves, a single allowed tenant is inferred, and multiple allowed tenants without a default require `X-Nebula-Tenant-ID`.
- S03 made the conditional tenant-header decision an explicit step before the first request in both the integrated walkthrough and the UAT script.

### 4. App and workload language is useful for teams but never misrepresented as a first-class runtime object unless implementation exists.

**Status:** met

**Evidence:**
- S02 explicitly reframed app/workload as conceptual guidance only.
- S02 added negative drift checks preventing `workspace`, `app`, or `workload` pseudo-entity semantics from reappearing in tenant surfaces.
- S03 preserved that same rule in the integrated proof and marked pseudo-entity drift as a failure cue.

## Definition of Done Verification

### All slice deliverables are complete

**Status:** met

Verified slices:
- `S01` summary exists and reports completion
- `S02` summary exists and reports completion
- `S03` summary exists and reports completion

### Shared documentation and operator-surface wording are actually aligned

**Status:** met

**Evidence:**
- S01 aligned API Keys, Playground, and Observability wording to runtime truth.
- S02 aligned the Tenants shell and tenant editor to the same tenant/API-key model.
- S03 linked the canonicals together in `docs/integrated-adoption-proof.md` without reintroducing conflicting abstractions.

### The real operator entrypoints exist and are exercised against the current runtime model

**Status:** met

**Evidence:**
- Real operator entrypoints exist in the assembled state: Tenants, API Keys, Playground, and Observability pages are present in `console/src/app/(console)/...`.
- The current worktree still contains the supporting backend and doc proof files referenced by the integrated story, including `docs/production-model.md`, `docs/quickstart.md`, `docs/reference-migration.md`, `docs/day-1-value.md`, `docs/adoption-api-contract.md`, and `tests/test_reference_migration.py`.
- Focused console verification was rerun successfully in this close-out:
  - `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx 'src/app/(console)/observability/page.test.tsx'`
  - Result: **6 files passed, 16 tests passed**

### Success criteria are re-checked against live behavior, not just planning artifacts

**Status:** met

**Evidence:**
- Close-out reran the focused Vitest contract suite in the assembled worktree.
- The integrated walkthrough and UAT artifacts are present and non-empty.
- The diff against `main` confirms the milestone produced real code/doc/test changes rather than summary-only planning work.

### Final integrated acceptance scenarios pass

**Status:** met

**Evidence:**
- S03 validation recorded pass status in `.gsd/milestones/M002/M002-VALIDATION.md`.
- `docs/integrated-adoption-proof.md` and `.gsd/milestones/M002/slices/S03/S03-UAT.md` are present and aligned to the final proof order.
- The combined focused console suite passed again during milestone close-out.

## Cross-Slice Integration Verification

Cross-slice integration worked as intended.

- **S01 → S02:** S02 successfully built tenant-page guidance on top of S01's stable tenant/API-key/runtime-truth framing without reopening tenant-selection semantics.
- **S01 → S03:** S03 used S01's clarified tenant/header/operator-boundary rules to assemble the integrated proof order.
- **S02 → S03:** S03 preserved S02's app/workload guidance-only boundary and did not expand scope into new runtime/admin entities.

No cross-slice mismatch was found in the assembled state.

## Verification Evidence

### Commands run during close-out

- `git diff --stat HEAD $(git merge-base HEAD main) -- ':!.gsd/'`
- `find .gsd/milestones/M002 -maxdepth 3 -type f | sort`
- `find docs -maxdepth 1 -type f | sort`
- `find console/src/app/'(console)' -maxdepth 3 -type f | sort | rg 'api-keys/page|playground/page|observability/page|tenants/page|page.test'`
- `find console/src/components -maxdepth 3 -type f | sort | rg 'api-key-table|create-api-key-dialog|playground-form|playground-page|tenant-editor-drawer|tenant-table'`
- `find tests -maxdepth 1 -type f | sort | rg 'reference_migration|chat_completions|response_headers|governance_api|admin_playground_api'`
- `npm --prefix console run test -- --run 'src/app/(console)/tenants/page.test.tsx' src/components/tenants/tenant-editor-drawer.test.tsx src/components/tenants/tenant-table.test.tsx src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx 'src/app/(console)/observability/page.test.tsx'`

### Verification result

**Passed**

- Code changes exist outside `.gsd/`
- All slices are complete
- Success criteria are satisfied
- Definition of done is satisfied
- Integrated proof artifacts exist
- Focused runtime-truth console tests pass in the assembled worktree

## Requirement Status Transitions

No requirement status transitions were validated in this milestone close-out.

- `R006` remains **validated** and gained stronger product-surface proof.
- `R012` remains **deferred** by design; the milestone proved stronger guidance without introducing first-class app/workload runtime or admin entities.
- `R011`, `R013`, and `R014` remain **deferred**.

Because no requirement changed status, `.gsd/REQUIREMENTS.md` did not require a status update.

## Requirement Outcome Notes

- **R006:** strengthened through console truth-surface alignment and the integrated production-structuring walkthrough.
- **R012:** intentionally still deferred; M002 proved the non-expansion path rather than implementing new app/workload objects.

## Decisions / Notable Changes

- No new backend fields, entities, or admin APIs were introduced during M002.
- Operator truth surfaces were reinforced rather than expanded.
- Decision `D013` records the final integrated-proof pattern used for milestone close-out.

## Reusable Lessons / Knowledge Extracted

The following milestone-level lessons are important for future work:

- For operator-trust work, derive wording from existing runtime/admin contracts rather than from aspirational UX abstractions.
- For copy-heavy truth surfaces, focused positive assertions plus explicit negative drift checks are a better guardrail than broad snapshots.
- Keep production-structuring walkthroughs composition-first: source docs own setup, contract, and operating-model details; the integrated guide should compose them rather than duplicate them.
- Preserve the proof order `production structuring -> public request -> headers/request id -> usage ledger -> Playground corroboration -> Observability persisted explanation`. Reversing that order is a product-story regression.

## Final Assessment

M002 is complete and passes milestone close-out verification.

It delivered a coherent production-structuring model grounded in Nebula's real tenant/API-key runtime behavior, strengthened operator-facing truth surfaces in the console, and closed with an integrated walkthrough that preserves the correct adoption and corroboration order without introducing fake app/workload entities.
