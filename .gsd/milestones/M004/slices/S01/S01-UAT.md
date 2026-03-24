# UAT — M004 / S01: Hosted reinforcement boundary

## Purpose
Validate that the hosted reinforcement boundary is now explicit, shared, and non-authoritative across the canonical contract seam, public trust-boundary surfaces, and deployment-management wording.

## Preconditions
- Use a worktree containing the S01 changes.
- Console dependencies are installed so the hosted trust-boundary page and deployment UI can render locally if needed.
- The tester can inspect source files and run the focused frontend verification suite.
- For optional live UI confirmation, have the console app running locally.

## Test Case 1 — Canonical shared contract exposes the hosted reinforcement rules
**Goal:** Confirm the shared hosted-contract seam is now the single source of truth for hosted reinforcement language.

1. Open `console/src/lib/hosted-contract.ts`.
2. Locate the exported `reinforcementContract` object.
3. Confirm it contains four sections:
   - `allowedDescriptiveClaims`
   - `prohibitedAuthorityClaims`
   - `operatorReadingGuidance`
   - `boundedActionPhrasing`
4. Confirm the allowed claims explicitly include all of these ideas:
   - metadata-backed and descriptive only
   - fleet posture is what deployments most recently reported
   - freshness is report recency rather than serving-time health
   - onboarding does not move request-serving or policy authority into hosted
   - remote actions stay bounded to audited credential rotation
5. Confirm the prohibited claims explicitly reject all of these ideas:
   - hosted serves traffic or is in the request-serving path
   - hosted has local runtime authority
   - hosted enforces tenant policy, routing, fallback, or provider selection
   - hosted holds provider credentials, raw prompts, raw responses, or tenant secrets by default
   - hosted freshness/fleet posture is authoritative health for serving traffic
6. Confirm `assertReinforcementContract()` exists and checks for required phrases before the content is returned.

**Expected outcome:** The shared module clearly defines the hosted reinforcement boundary in one place and fails fast if required trust-boundary wording drifts.

## Test Case 2 — Public trust-boundary card renders the shared guidance
**Goal:** Confirm the reusable public card presents the canonical hosted reinforcement guidance rather than local ad hoc wording.

1. Open `console/src/components/hosted/trust-boundary-card.tsx`.
2. Confirm it calls `getHostedContractContent()` and consumes `reinforcement` from the returned object.
3. Confirm the card renders sections for:
   - shared reading guidance
   - freshness states
   - reinforcement guardrails
   - bounded-action phrasing
4. Check that the card still shows the existing metadata-only and not-in-request-path framing.
5. Run:
   - `npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx`

**Expected outcome:** The card renders the canonical hosted reading guidance and guardrails sourced from the shared contract; the focused test passes.

## Test Case 3 — Public trust-boundary page reuses the shared non-authoritative wording
**Goal:** Confirm the public hosted trust-boundary page now tells the same story as the shared contract seam.

1. Open `console/src/app/trust-boundary/page.tsx`.
2. Confirm the page pulls `copy` and `reinforcement` from `getHostedContractContent()`.
3. Confirm the intro/body uses shared hosted-contract claims instead of page-local wording islands.
4. Confirm the page renders all of the following sections:
   - hosted fleet posture guidance
   - hosted outage behavior
   - reinforcement guardrails
   - remote-management safety limits
5. Confirm the reinforcement guardrails section renders the prohibited authority claims from the shared contract.
6. Run:
   - `npm --prefix console run test -- --run src/app/trust-boundary/page.test.tsx`

**Expected outcome:** The page reads as a canonical non-authoritative hosted trust-boundary surface and the focused test passes.

## Test Case 4 — Deployment-management hosted action copy stays bounded
**Goal:** Confirm deployment-facing hosted action wording is aligned to the shared contract and does not imply broader control.

1. Open `console/src/components/deployments/remote-action-card.tsx`.
2. Confirm it calls `getHostedContractContent()` and uses `reinforcement.boundedActionPhrasing.description` in the card body.
3. Confirm the nearby supporting sentence tells operators to use local runtime observability to confirm serving-time behavior.
4. Confirm the action itself is still `Rotate hosted-link credential` and no broader hosted action is introduced.
5. Run:
   - `npm --prefix console run test -- --run src/components/deployments/remote-action-card.test.tsx`

**Expected outcome:** The remote-action card uses shared bounded-action language, keeps the local-runtime confirmation caveat, and the focused test passes.

## Test Case 5 — Deployments page header reinforces bounded assistance only
**Goal:** Confirm the deployments landing surface reinforces the hosted trust boundary without prematurely introducing authoritative posture language.

1. Open `console/src/app/(console)/deployments/page.tsx`.
2. Confirm the page imports `getHostedContractContent()`.
3. Confirm the explanatory paragraph beneath the header is composed from shared contract wording.
4. Verify the paragraph communicates bounded operational assistance rather than broad hosted control.
5. Verify the page does **not** claim hosted certifies serving-time health, routing correctness, fallback correctness, or tenant policy enforcement.

**Expected outcome:** The deployments entry surface now reinforces the hosted boundary while staying descriptive and non-authoritative.

## Test Case 6 — Slice artifact documents the downstream acceptance contract
**Goal:** Confirm future slices have an explicit artifact to preserve.

1. Open `docs/hosted-reinforcement-boundary.md`.
2. Confirm the document contains these sections:
   - Allowed hosted reinforcement claims
   - Prohibited authority implications
   - Bounded action contract
   - Operator reading guidance
   - Acceptance rules for S02 and S03
   - Inspection and drift checks
3. Confirm the acceptance rules explicitly preserve:
   - metadata-only framing
   - not in request-serving path
   - no local runtime authority in hosted
   - local tenant policy/provider credentials remain local
   - confidence remains descriptive, not serving-time truth
   - new posture/confidence surfaces require a local-runtime caveat

**Expected outcome:** The doc is a concrete downstream contract, not a placeholder.

## Test Case 7 — Full slice frontend verification passes
**Goal:** Confirm all focused frontend contract/render checks pass together.

1. Run:
   - `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/components/deployments/remote-action-card.test.tsx`
2. Observe the result summary.

**Expected outcome:** All 4 test files pass. Failures should point to exact copy/section drift rather than broad unrelated runtime issues.

## Test Case 8 — Wording drift sweep finds the expected trust-boundary phrases
**Goal:** Confirm the key hosted reinforcement terms are present across the intended console and doc surfaces.

1. Run:
   - `rg -n "metadata-only|request-serving path|local runtime authority|serving traffic|tenant policy|provider credentials|fleet posture|confidence" console/src docs`
2. Inspect the matches.
3. Confirm the key phrases appear in:
   - `console/src/lib/hosted-contract.ts`
   - trust-boundary page/card tests or components
   - `docs/hosted-reinforcement-boundary.md`
4. Confirm the new doc artifact exists:
   - `test -f docs/hosted-reinforcement-boundary.md`

**Expected outcome:** The grep sweep returns the intended trust-boundary locations and the boundary artifact exists.

## Edge Cases

### Edge Case A — Phrase reuse across the page and card
1. Inspect the trust-boundary page and note that some shared phrases appear both in the page body and inside the embedded card.
2. Confirm this is intentional reuse of the canonical seam, not accidental copy drift.
3. Confirm tests assert presence of the shared wording rather than wrongly requiring uniqueness.

**Expected outcome:** Duplicate canonical phrases are treated as deliberate reuse of one wording source.

### Edge Case B — Hosted freshness is mistaken for runtime truth
1. Read the trust-boundary card, trust-boundary page, and remote-action card together.
2. Check whether any surface suggests that stale/offline/current hosted freshness proves present serving-time health.

**Expected outcome:** No surface makes that claim; all wording preserves local runtime authority.

### Edge Case C — Deployment-management wording implies broader remote control
1. Read the deployments page header copy and the remote-action card copy together.
2. Check whether the wording implies broader hosted operational control than audited credential rotation.

**Expected outcome:** The copy stays bounded to audited credential rotation plus status/audit visibility and does not imply broader remote management.

## Failure Signals
- `reinforcementContract` is missing from `hosted-contract.ts`
- any public surface restates hosted trust-boundary wording independently instead of consuming the shared contract
- trust-boundary surfaces imply hosted runtime authority, request-serving authority, or policy authority
- deployment-management wording suggests broader remote control than the audited credential-rotation action
- `docs/hosted-reinforcement-boundary.md` is missing or reads like a placeholder
- focused frontend tests fail on missing sections or changed canonical wording

## Notes for Tester
This slice is intentionally about language contract and boundary discipline, not fleet-posture synthesis yet. Treat any new hosted claim of runtime health, readiness, or authority as a regression even if the UI feels clearer.
