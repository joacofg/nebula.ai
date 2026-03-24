# Slice Research — M004 / S03: Confidence proof and trust walkthrough

## Summary
S03 owns the integrated proof requirements: **R037** directly and **R038** primarily, while reinforcing the already-active trust-boundary requirement **R034** and the milestone-level adoption outcome in **R014**. The implementation is **targeted research**, not deep research: S01 and S02 already established the core seams, and the codebase has a strong precedent for “composition-first integrated proof docs + focused tests + optional browser proof” from M003’s adoption slices.

The existing hosted console already has the right proof ingredients wired together:
- `console/src/app/(console)/deployments/page.tsx` is now the real hosted fleet entrypoint.
- `console/src/components/deployments/fleet-posture-summary.tsx` gives the page-level posture scan.
- `console/src/components/deployments/deployment-table.tsx` gives row-level mixed-state interpretation.
- `console/src/components/deployments/deployment-detail-drawer.tsx` composes dependency pills, the shared trust-boundary card, and the bounded remote action card into one per-deployment story.
- `console/src/components/deployments/remote-action-card.tsx` already frames the hosted action as bounded, fail-closed operational assistance.
- `console/src/lib/hosted-contract.ts` remains the canonical wording seam for all trust-boundary language.
- `console/src/app/trust-boundary/page.tsx` is the canonical public trust-boundary surface S03 can cite.

So S03 should **prove** the assembled story, not add more hosted mechanics. The missing deliverable is likely an integrated walkthrough artifact under `docs/` plus targeted verification that the assembled deployments flow and public trust-boundary page still read as descriptive, metadata-backed, and non-authoritative.

A key precedent exists in M003: the repo repeatedly uses a pattern of **one integrated walkthrough doc that assembles existing canonicals rather than redefining them** (`docs/integrated-adoption-proof.md`, `docs/embeddings-integrated-adoption-proof.md`). That pattern is the strongest structural template for S03.

## Recommendation
Build S03 around **one canonical hosted integrated proof artifact** and **verification that references existing UI seams instead of inventing new ones**.

Recommended order:
1. **Author the integrated walkthrough first** in `docs/`.
   - It should assemble the real hosted proof path: public trust boundary → deployments fleet posture summary → mixed deployment scan states → deployment detail trust boundary + dependency context → bounded remote action framing.
   - It should explicitly preserve the S01/S02 rule that local runtime enforcement remains authoritative, especially when hosted metadata is stale or offline.
2. **Add or extend focused tests second**.
   - Lock any new copy or integrated composition rules in Vitest where possible.
   - Prefer proving reuse of `getHostedContractContent()` wording and `fleet-posture.ts` derivations over snapshotting large rendered trees.
3. **Add a browser proof only if needed to close credibility gaps**.
   - There is no deployments e2e today, only `console/e2e/trust-boundary.spec.ts` for the public page.
   - If the slice needs a stronger “real walkthrough” artifact, the natural place is a new Playwright spec for the deployments surface using mocked admin API responses, mirroring the M003 observability-proof pattern.
4. **Close the loop with requirement evidence**.
   - S03 is where the milestone story becomes integrated and inspectable, so verification commands and the walkthrough should be written so S04 can tighten gaps instead of re-researching the story.

## Implementation Landscape

### Existing code and what it does
- `console/src/lib/hosted-contract.ts`
  - Canonical trust-boundary wording seam.
  - Exports `reinforcementContract`, `trustBoundaryCopy`, schema-backed exported-field list, and fail-fast phrase assertions.
  - S03 should reuse this module for any new UI or doc wording references; do not create page-local wording islands.

- `docs/hosted-reinforcement-boundary.md`
  - Human-readable acceptance contract produced by S01.
  - Already states the exact allowed claims, prohibited implications, bounded-action contract, operator-reading guidance, and acceptance rules for S02/S03.
  - This should be treated as the non-authority contract for the walkthrough.

- `console/src/components/deployments/fleet-posture.ts`
  - Shared pure derivation seam from S02.
  - Computes posture kinds (`pending_enrollment`, `linked`, `stale`, `offline`, `revoked`, `unlinked`) plus bounded action availability (`available`, `blocked`, `unavailable`).
  - This is the semantic ground truth for row-level and summary-level hosted posture claims.

- `console/src/components/deployments/fleet-posture-summary.tsx`
  - Top-of-page hosted fleet summary.
  - Uses `summarizeFleetPosture()` and shared contract wording.
  - Already contains the page-level story S03 needs to walk through: linked/current, pending enrollment, stale/offline visibility, bounded actions blocked, trust-boundary caveat, bounded-action caveat.

- `console/src/components/deployments/deployment-table.tsx`
  - Scan surface for mixed deployments.
  - Shows status badge + freshness badge + posture label/detail + bounded-action scan text.
  - This is the strongest surface for R033/R036 evidence inside the integrated story.

- `console/src/components/deployments/deployment-detail-drawer.tsx`
  - Assembles the confidence story at per-deployment level.
  - Includes freshness, identity, dependency summary, `TrustBoundaryCard`, and `RemoteActionCard`.
  - Important for S03 because it already joins posture interpretation with the public trust-boundary seam and bounded-action explanation.

- `console/src/components/deployments/remote-action-card.tsx`
  - Uses `getBoundedActionAvailability()` from `fleet-posture.ts`.
  - Already contains the critical wording: hosted summaries are metadata-backed/descriptive only; use local runtime observability to confirm serving-time behavior; queue action remains bounded to credential rotation.
  - This is the clearest proof surface for R035/R038 in the integrated walkthrough.

- `console/src/app/(console)/deployments/page.tsx`
  - Real deployments console entrypoint.
  - Composes summary + table + drawer workflow.
  - This is likely the “real hosted console entrypoint” named by the roadmap’s DoD.

- `console/src/app/trust-boundary/page.tsx`
  - Public trust-boundary explainer.
  - Already composes the shared contract, operator guidance, prohibited claims, outage behavior, and bounded-action description.
  - Strong citation surface for “hosted is optional, metadata-only, and not in the request-serving path.”

- `console/e2e/trust-boundary.spec.ts`
  - Existing unauthenticated browser proof for the public trust-boundary page.
  - Verifies only the public page reachability and core statements.
  - No current e2e exists for the deployments walkthrough.

### Existing tests and what they lock
- `console/src/lib/hosted-contract.test.ts`
  - Locks exact reinforcement wording and phrase-presence guardrails.
  - Best place to extend only if S03 truly adds canonical wording.

- `console/src/components/deployments/fleet-posture.test.ts`
  - Locks the derivation seam and fail-closed bounded-action reasons.
  - Good precedent for keeping logic tests separate from render tests.

- `console/src/components/deployments/fleet-posture-summary.test.tsx`
  - Locks page-level posture counts and trust-boundary copy presence.
  - Useful if S03 adds more explicit integrated-story text at summary level.

- `console/src/components/deployments/deployment-table.test.tsx`
  - Locks scan-time posture interpretation and bounded-action labels.

- `console/src/components/deployments/remote-action-card.test.tsx`
  - Already locks the most important S03 behavior: bounded wording, non-authority caveat, fail-closed states, recent history rendering.

- `console/src/app/trust-boundary/page.test.tsx` and `console/src/components/hosted/trust-boundary-card.test.tsx`
  - Lock the public trust-boundary page/card wording.

- Backend tests:
  - `tests/test_hosted_contract.py` locks hosted metadata contract, freshness enum, and exclusions.
  - `tests/test_remote_management_api.py` locks remote management queue/history contract and fail-closed non-active behavior.
  - These support S03’s trust story even if S03 itself stays console/doc-heavy.

### Strong precedent from earlier milestone work
M003 established a reusable pattern that matches this slice closely:
- canonical integrated proof docs live under `docs/`
- they **assemble** existing canonicals instead of redefining them
- they explicitly state proof order and failure modes
- they point to executable tests and browser corroboration instead of copying those details inline

Key precedent file:
- `docs/integrated-adoption-proof.md`
  - This is the best structural model for S03.
  - It has sections for what the proof establishes, canonical proof order, how canonicals fit together, minimal walkthrough, what it intentionally does not duplicate, failure modes, related docs.

There is also an embeddings-specific integrated proof precedent:
- `docs/embeddings-integrated-adoption-proof.md`
  - Found by search and useful as a second example that integrated proof docs can be topic-specific and composition-first.

### Natural seams for planner tasking
1. **Documentation / proof artifact seam**
   - Candidate files: `docs/hosted-integrated-adoption-proof.md` or similar new doc; possibly small link updates in existing hosted docs if discoverability is needed.
   - Lowest coupling with code; should probably be the first task.

2. **Focused UI/test seam**
   - Candidate files: `fleet-posture-summary.test.tsx`, `remote-action-card.test.tsx`, `page.test.tsx`, maybe a new test around the deployments page if the repo has an existing render harness for full page composition.
   - Goal: lock integrated wording or evidence mapping, not redesign components.

3. **Optional browser verification seam**
   - Candidate file: new `console/e2e/deployments.spec.ts` or similarly named spec.
   - Should use mocked deployments / remote-action responses the way M003’s observability proof mocked admin surfaces.
   - This is the riskiest/separate task because it introduces more moving parts and likely needs auth/session fixture patterns from other console e2e tests.

## What to Build or Prove First
1. **Prove the intended integrated story in a doc first.**
   The slice requirement is about confidence proof and trust walkthrough, not more UI state. The planner should prioritize a doc artifact that makes the assembled story inspectable and keeps the trust boundary explicit.

2. **Anchor the walkthrough to the real UI sequence already shipped.**
   The doc should walk through:
   - public trust-boundary page for contract framing
   - deployments page summary for fleet scan
   - table mixed-state interpretation for linked/pending/stale/offline/revoked/unlinked
   - detail drawer for trust-boundary card + dependency summary
   - remote action card for bounded hosted assistance and fail-closed reasons

3. **Make stale/offline/local-runtime authority explicit in the walkthrough.**
   This is the slice’s core risk. The roadmap and S01 artifact both emphasize that hosted data may age or go offline without changing local serving correctness. The walkthrough must keep that explicit.

4. **Only then decide whether a browser proof is necessary.**
   If the integrated doc plus focused tests make the story credible enough, S03 can stay narrow. If not, add a deployments e2e that demonstrates the mixed-fleet walkthrough with mocked data.

## Verification
Recommended verification set for S03, based on existing seams:

### Focused frontend checks
- `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx`

Why:
- covers canonical wording seam
- covers public trust boundary
- covers derivation seam
- covers scan-time posture and bounded-action framing

### Backend contract checks
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`

Why:
- proves hosted metadata contract and remote-action fail-closed behavior still align with the walkthrough
- use repo venv path directly; prior summaries already noted plain `pytest` may be unavailable in closer shells

### Content/source grep checks
- `rg -n "metadata-backed and descriptive only|fleet posture|local runtime|request-serving path|bounded operational assistance|credential rotation|stale|offline" console/src docs`

Why:
- quick drift check across the UI/doc surfaces S03 will likely touch

### Optional browser proof
If S03 adds a deployments e2e walkthrough:
- `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/<new-deployments-proof>.spec.ts`

If only the public page remains browser-verified:
- at minimum rerun `console/e2e/trust-boundary.spec.ts`

## Constraints and Guardrails
- Do **not** add new hosted mechanics, new hosted authority, or new backend state just to make the walkthrough easier.
- Do **not** fork logic already centralized in `fleet-posture.ts`.
- Do **not** create a second wording seam outside `console/src/lib/hosted-contract.ts`.
- Keep docs composition-first, following the pattern in `docs/integrated-adoption-proof.md`.
- Preserve the S01 rule: any mention of confidence must be descriptive evidence about reported state, not authoritative runtime truth.
- Preserve the S02 rule: bounded action availability is derived from `getBoundedActionAvailability()` and remains fail-closed.

## Skill Discovery
Installed skills directly relevant to this slice:
- `react-best-practices`
  - Relevant guidance used: avoid duplicated state/logic, prefer composition over local condition trees, keep proof surfaces thin and derived from existing seams.
- `agent-browser`
  - Relevant if planner chooses browser verification for the deployments walkthrough.

Promising external skill candidates discovered but **not installed**:
- Playwright: `currents-dev/playwright-best-practices-skill@playwright-best-practices`
  - Install command: `npx skills add currents-dev/playwright-best-practices-skill@playwright-best-practices`
  - Best candidate by install count for e2e proof work.
- FastAPI: `wshobson/agents@fastapi-templates`
  - Install command: `npx skills add wshobson/agents@fastapi-templates`
  - Potentially useful only if the slice unexpectedly expands backend proof surfaces; likely not necessary for current scope.

## Forward Intelligence for Planner
- The codebase is already set up for this slice; the gap is **proof assembly**, not missing product seams.
- The strongest implementation path is to mirror M003’s integrated-proof doc pattern rather than invent a new artifact shape.
- A new doc under `docs/` is the most likely required deliverable.
- A new deployments e2e proof is optional, not obviously mandatory from current evidence. Decide based on whether the integrated walkthrough needs live UI corroboration beyond existing Vitest coverage.
- If browser proof is added, keep it narrow: mocked mixed deployments, row selection, detail drawer open, assert trust-boundary and bounded-action text. Do not turn it into a broad dashboard or backend integration test.
- If requirement updates happen later, R037/R038 validation should cite the integrated walkthrough plus the focused verification commands together, following the M003 close-out pattern.
