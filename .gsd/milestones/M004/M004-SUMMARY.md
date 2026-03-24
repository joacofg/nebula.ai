---
milestone: M004
title: Hosted Adoption Reinforcement
status: completed
verification: pass
integration_branch: codex/v3-api-adoption
closed_at: 2026-03-24
code_change_verification:
  base_branch: codex/v3-api-adoption
  merge_base: 1fa3876db9bf7df4763dd6c24956b53cd757bb05
  non_gsd_changes_present: true
  evidence:
    - console/src/lib/hosted-contract.ts
    - console/src/components/deployments/fleet-posture.ts
    - console/src/components/deployments/fleet-posture-summary.tsx
    - console/src/components/deployments/deployment-table.tsx
    - console/src/components/deployments/remote-action-card.tsx
    - console/src/app/(console)/deployments/page.tsx
    - console/src/app/trust-boundary/page.tsx
    - console/playwright.config.ts
    - docs/hosted-reinforcement-boundary.md
    - docs/hosted-integrated-adoption-proof.md
requirement_outcomes:
  - id: R014
    from_status: deferred
    to_status: validated
    proof: M004 assembled the hosted reinforcement boundary (S01), metadata-backed fleet posture UX (S02), integrated adoption proof (S03), and targeted close-out refinements with fresh Vitest, Playwright, backend pytest, and source/doc artifact verification in S04.
  - id: R032
    from_status: active
    to_status: validated
    proof: S02 added the deployments-page fleet posture summary and shared posture derivation, and close-out reran focused Vitest coverage proving linked/current, pending, stale/offline, and bounded-action-blocked fleet reading.
  - id: R033
    from_status: active
    to_status: validated
    proof: S02 made linked, pending, stale, offline, revoked, unlinked, and bounded-action-blocked states legible in the deployments table, with passing helper/table tests and integrated proof reuse.
  - id: R034
    from_status: active
    to_status: validated
    proof: S01 centralized the trust-boundary vocabulary in console/src/lib/hosted-contract.ts, and S04 reran Vitest, Playwright, backend pytest, and grep/artifact checks to verify hosted wording remains metadata-only and non-authoritative.
  - id: R035
    from_status: active
    to_status: validated
    proof: S02 introduced getBoundedActionAvailability() as the shared bounded-action seam and reused it across the table and RemoteActionCard, with passing helper and component coverage.
  - id: R036
    from_status: active
    to_status: validated
    proof: S02 delivered a real multi-deployment summary surface above the deployments inventory, reducing the need to reconstruct fleet posture from separate views; focused tests and S03/S04 walkthrough evidence validated the outcome.
  - id: R037
    from_status: active
    to_status: validated
    proof: S03 created docs/hosted-integrated-adoption-proof.md and browser proof in console/e2e/trust-boundary.spec.ts and console/e2e/deployments-proof.spec.ts; S04 reran the suite successfully.
  - id: R038
    from_status: active
    to_status: validated
    proof: S03/S04 proved hosted statuses, freshness meaning, dependency context, and evidence framing are easier to interpret in context through the integrated walkthrough and passing verification bar.
---

# Milestone Summary — M004: Hosted Adoption Reinforcement

## Outcome
M004 completed Nebula’s hosted adoption reinforcement milestone by improving hosted onboarding clarity, multi-deployment fleet understanding, and operator confidence without expanding hosted authority. The milestone stayed inside the metadata-only trust boundary established for the hosted plane: hosted surfaces became easier to read and more confidence-building, but they did not become authoritative for serving-time health, routing, fallback, or policy enforcement.

The assembled milestone now includes:
- a canonical hosted reinforcement wording seam in `console/src/lib/hosted-contract.ts`
- a public hosted trust-boundary entrypoint in `console/src/app/trust-boundary/page.tsx`
- a real hosted fleet-posture reading surface on the deployments page via `console/src/components/deployments/fleet-posture.ts`, `fleet-posture-summary.tsx`, and `deployment-table.tsx`
- aligned bounded-action framing in `console/src/components/deployments/remote-action-card.tsx`
- canonical proof artifacts in `docs/hosted-reinforcement-boundary.md` and `docs/hosted-integrated-adoption-proof.md`
- executable browser proof that exercises the real hosted walkthrough against the console production-style standalone server

## Code Change Verification
Per close-out requirements, non-`.gsd/` implementation changes were verified before marking the milestone complete.

### Diff check run
- `git diff --stat HEAD $(git merge-base HEAD codex/v3-api-adoption) -- ':!.gsd/'`

### Result
Non-`.gsd/` changes are present. The milestone did not produce planning artifacts only.

### Representative implementation/doc files
- `console/src/lib/hosted-contract.ts`
- `console/src/components/deployments/fleet-posture.ts`
- `console/src/components/deployments/fleet-posture-summary.tsx`
- `console/src/components/deployments/deployment-table.tsx`
- `console/src/components/deployments/deployment-detail-drawer.tsx`
- `console/src/components/deployments/remote-action-card.tsx`
- `console/src/app/(console)/deployments/page.tsx`
- `console/src/app/trust-boundary/page.tsx`
- `console/playwright.config.ts`
- `docs/hosted-reinforcement-boundary.md`
- `docs/hosted-integrated-adoption-proof.md`

## Success Criteria Verification

### 1. A self-hosted operator can open the hosted console and understand fleet posture across multiple deployments without ambiguity about what is linked, pending, stale, offline, or blocked for bounded hosted actions.
**Verified:** Yes.

**Evidence:**
- S02 added a top-of-page fleet summary and scan-time row interpretation on the deployments page.
- `console/src/components/deployments/fleet-posture.ts` derives linked, pending, stale, offline, revoked, unlinked, and bounded-action states from existing metadata.
- Passing focused Vitest coverage: `fleet-posture.test.ts`, `fleet-posture-summary.test.tsx`, `deployment-table.test.tsx`, `remote-action-card.test.tsx`, and `src/app/(console)/deployments/page.test.tsx`.
- Passing Playwright proof in `console/e2e/deployments-proof.spec.ts` demonstrates the mixed-fleet walkthrough.

### 2. Hosted surfaces make onboarding and fleet state easier to interpret across deployments while remaining clearly descriptive and metadata-backed.
**Verified:** Yes.

**Evidence:**
- S01 centralized allowed descriptive hosted claims and operator reading guidance in `console/src/lib/hosted-contract.ts`.
- S02 wired those cues into the deployments entrypoint and summary/table scan surfaces.
- Grep/artifact checks confirm the required descriptive-only wording appears in the intended console and doc surfaces.
- S03 and S04 integrated those surfaces into one proof path instead of isolated components.

### 3. The metadata-only trust boundary is clearer after the milestone, not blurrier, and the hosted console never reads as authoritative for local runtime enforcement.
**Verified:** Yes.

**Evidence:**
- S01 established explicit prohibited authority claims and bounded-action guardrails in the shared contract seam.
- The public trust-boundary page and trust-boundary card reuse the canonical contract.
- S03’s integrated proof explicitly states hosted is not in the request-serving path and local runtime remains authoritative even when hosted is stale or offline.
- S04 re-ran the full verification bar to confirm no hosted-authority drift.

### 4. At least one integrated proof shows how hosted surfaces reinforce adoption and operator confidence without becoming authoritative for local enforcement.
**Verified:** Yes.

**Evidence:**
- `docs/hosted-integrated-adoption-proof.md` is the canonical integrated walkthrough artifact.
- Passing Playwright coverage: `console/e2e/trust-boundary.spec.ts` and `console/e2e/deployments-proof.spec.ts`.
- Passing backend contract verification: `tests/test_hosted_contract.py` and `tests/test_remote_management_api.py`.

### 5. The resulting hosted experience materially helps multi-deployment evaluators and operators, not just a single-node demo.
**Verified:** Yes.

**Evidence:**
- S02 was explicitly built around multi-deployment understanding from one deployments surface.
- Fleet summary counts and mixed-state scan cues are designed for linked/current, pending, stale, offline, revoked, unlinked, and unsupported deployments in one view.
- S03/S04 proof and UAT evidence use mixed-fleet interpretation, not a single-node-only path.

### Unmet success criteria
None.

## Definition of Done Verification

### All slices complete
Verified from milestone contents:
- S01 complete
- S02 complete
- S03 complete
- S04 complete

### All slice summaries exist
Verified:
- `.gsd/milestones/M004/slices/S01/S01-SUMMARY.md`
- `.gsd/milestones/M004/slices/S02/S02-SUMMARY.md`
- `.gsd/milestones/M004/slices/S03/S03-SUMMARY.md`
- `.gsd/milestones/M004/slices/S04/S04-SUMMARY.md`

### Cross-slice integration works correctly
Verified:
- S01’s shared trust-boundary vocabulary is reused by S02 deployments surfaces.
- S02’s fleet-posture derivation and bounded-action semantics are reused by S03’s integrated proof.
- S04 refined wording and executable proof without adding new hosted scope.
- The final assembled verification bar passed in this worktree.

### Real hosted fleet posture reading surface exists
Verified:
- `console/src/app/(console)/deployments/page.tsx`
- `console/src/components/deployments/fleet-posture-summary.tsx`
- `console/src/components/deployments/deployment-table.tsx`

### Trust-boundary wording, posture summaries, and bounded remote-action framing are wired together
Verified through shared hosted-contract seam reuse and passing focused/frontend/browser coverage.

### Real hosted console entrypoint exists and is exercised through deployment workflow and integrated proof
Verified through:
- public trust-boundary page
- authenticated deployments page
- deployment detail drawer
- remote-action card
- passing Playwright walkthrough

### Final integrated acceptance passes without making hosted feel authoritative for serving-time health, routing, fallback, or policy enforcement
Verified.

## Verification Evidence

### Focused frontend verification
Command run:
- `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'`

Result:
- 8 test files passed
- 48 tests passed

### Browser proof verification
Command run:
- `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts`

Result:
- 3 Playwright tests passed
- Web server logged an `ECONNREFUSED 127.0.0.1:8000` fetch failure during startup data fetching, but the proof itself still passed and did not invalidate hosted reinforcement behavior.

### Backend contract verification
Command run:
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`

Result:
- 17 passed

### Source/doc artifact verification
Command run:
- `rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src docs && test -f docs/hosted-integrated-adoption-proof.md`

Result:
- Passed
- Required wording and proof artifact present

## Requirement Outcome Validation
The following requirement status transitions are supported by milestone evidence and were validated at close-out.

### R014 — deferred → validated
**Proof:** M004 as a whole now materially improves adoption and operator confidence through hosted reinforcement only: S01 locked the trust boundary, S02 delivered the fleet posture UX, S03 created the canonical integrated proof, and S04 reran the full close-out verification bar successfully.

### R032 — active → validated
**Proof:** S02 delivered the hosted fleet-posture summary surface and shared derivation seam; focused tests and the integrated walkthrough confirm operators can read linked/current, pending, stale/offline, and bounded-action-blocked states quickly.

### R033 — active → validated
**Proof:** S02 made mixed deployment states legible in the deployments inventory without requiring drawer-only inference, backed by helper and table coverage.

### R034 — active → validated
**Proof:** S01 created the canonical contract seam and S04 freshly verified the wording across focused tests, Playwright, backend pytest, and source/doc checks.

### R035 — active → validated
**Proof:** Bounded hosted action availability is now explicit and shared via `getBoundedActionAvailability()`, reused across the deployments table and `RemoteActionCard`, with passing focused coverage.

### R036 — active → validated
**Proof:** The deployments page now gives fleet-level summary counts and guidance before row inspection, helping multi-deployment evaluators understand onboarding and freshness posture from one surface.

### R037 — active → validated
**Proof:** The canonical integrated proof doc and browser walkthroughs now exist and passed in this worktree.

### R038 — active → validated
**Proof:** Hosted statuses, freshness semantics, dependency context, and evidence framing are easier to interpret in context, and that interpretation is locked by focused frontend and browser verification.

## Cross-Cutting Patterns and Lessons
- Keep hosted trust-boundary wording in `console/src/lib/hosted-contract.ts` and compose it outward rather than creating page-local phrasing islands.
- Keep fleet posture, per-row interpretation, and bounded-action availability in one pure helper seam so summary, table, and remote-action surfaces cannot drift semantically.
- When the same shared contract phrase correctly appears in multiple surfaces, tests should verify reuse/presence rather than uniqueness.
- For Next.js standalone output, Playwright production verification should run the standalone server path instead of `next start`.
- Treat drawer freshness and dependency signals as supporting evidence that helps prioritize investigation, not as hosted authority over serving-time health.

## Final Verdict
**Milestone verdict: pass**

M004 is complete. The worktree contains real non-`.gsd/` implementation changes, all roadmap success criteria were met with specific evidence, the definition of done is satisfied, the assembled cross-slice experience works, and the validated requirement transitions are supported by fresh close-out verification.
