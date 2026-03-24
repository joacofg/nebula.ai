# UAT — S03: Confidence proof and trust walkthrough

## Preconditions

1. Worktree is `M004` with S03 changes present.
2. Console dependencies are installed.
3. Python test environment exists at `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv`.
4. No stale browser build output is present if re-running browser proof after TypeScript fixes; if needed, remove `console/.next` first.
5. Hosted trust-boundary and deployments proof files exist:
   - `docs/hosted-integrated-adoption-proof.md`
   - `console/e2e/deployments-proof.spec.ts`
   - `console/e2e/trust-boundary.spec.ts`

---

## Test Case 1 — Canonical hosted proof artifact exists and reads as non-authoritative

### Steps
1. Open `docs/hosted-integrated-adoption-proof.md`.
2. Confirm the walkthrough starts from the public trust-boundary surface and then moves into deployments.
3. Confirm the document explicitly states that hosted summaries are metadata-backed and descriptive only.
4. Confirm the document explicitly states that hosted is not in the request-serving path.
5. Confirm the document explicitly states that local runtime authority remains authoritative when hosted is stale or offline.
6. Confirm the document limits hosted actions to audited credential rotation.

### Expected Outcomes
- The document exists and is non-empty.
- The proof order is public trust boundary → deployments → fleet posture → drawer → bounded remote action.
- The doc never claims hosted controls routing, fallback, policy enforcement, provider authority, or serving-time truth.
- The doc reads as an integrated walkthrough, not a second canonical contract.

---

## Test Case 2 — Public trust-boundary page is reachable before authentication

### Steps
1. Run `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts`.
2. Observe the browser test that opens the public trust-boundary page without authentication.
3. Confirm the page shows trust-boundary framing and hosted caveats.

### Expected Outcomes
- The test passes.
- The trust-boundary page is reachable without signing in.
- The page communicates that hosted is not in the request-serving path.
- The page communicates that hosted freshness is not local runtime authority.

---

## Test Case 3 — Login page provides the trust-boundary entrypoint before auth

### Steps
1. Run `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts`.
2. Observe the browser test that starts from the login page.
3. Confirm the login page links to the trust-boundary page before authentication.

### Expected Outcomes
- The test passes.
- An evaluator can discover the trust-boundary explanation before entering the console.
- The hosted trust story is accessible as part of onboarding, not hidden behind auth.

---

## Test Case 4 — Deployments walkthrough proves mixed fleet posture stays descriptive

### Steps
1. If browser proof previously failed after a code fix, clear `console/.next`.
2. Run `npm --prefix console run e2e -- e2e/deployments-proof.spec.ts`.
3. Observe the browser walkthrough from trust-boundary entry into the authenticated deployments console.
4. Confirm the mocked fleet includes mixed states (current, pending, stale, offline).
5. Confirm the deployments page shows fleet posture counts and row-level cues.
6. Open a deployment detail drawer from the table.
7. Confirm the drawer shows trust-boundary guidance and bounded remote-action framing.

### Expected Outcomes
- The test passes.
- The deployments page clearly distinguishes mixed fleet posture states.
- Stale and offline states are shown as visibility/interpretation cues, not runtime authority.
- The drawer explicitly redirects serving-time verification back to local runtime observability.
- The remote-action framing remains bounded to credential rotation.

---

## Test Case 5 — Focused trust/deployments composition tests lock shared wording and semantics

### Steps
1. Run:
   `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'`
2. Inspect the passing test list.
3. Confirm the suite covers:
   - hosted contract wording,
   - trust-boundary page composition,
   - fleet posture summary wording,
   - deployment-table mixed posture semantics,
   - remote-action fail-closed behavior,
   - deployments-page entrypoint composition.

### Expected Outcomes
- The entire focused Vitest suite passes.
- A regression in hosted wording or posture semantics would fail a focused test rather than hiding inside a broad snapshot.
- The deployments walkthrough is locked to shared contract and helper seams instead of duplicated prose.

---

## Test Case 6 — Backend contract still enforces metadata-only hosted scope and fail-closed remote actions

### Steps
1. Run:
   `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`
2. Inspect the test result count.

### Expected Outcomes
- All tests pass.
- Hosted contract semantics remain aligned with the console proof.
- Remote management remains bounded and fail-closed.
- No backend drift undermines the UI confidence story.

---

## Test Case 7 — Source and docs contain the required trust and posture phrases

### Steps
1. Run:
   `rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src docs && test -f docs/hosted-integrated-adoption-proof.md`
2. Inspect matches in `console/src/lib/hosted-contract.ts`, trust-boundary surfaces, deployments surfaces, and hosted docs.

### Expected Outcomes
- The grep command succeeds.
- Required trust-boundary phrases are present in the shared contract and the integrated proof doc.
- Hosted wording remains clearly descriptive, metadata-backed, and bounded.

---

## Test Case 8 — Drawer-level remote action stays bounded and fail-closed

### Steps
1. Open `console/src/components/deployments/remote-action-card.tsx` and its test file.
2. Review the UI copy and test assertions for unavailable/blocked states.
3. Confirm there is no wording implying broader hosted control.
4. Confirm tests cover stale, offline, revoked, unlinked, and unsupported cases.

### Expected Outcomes
- The UI frames the action as hosted-link credential rotation only.
- Blocked/unavailable reasoning is explicit and fail-closed.
- The card tells operators to use local runtime observability for serving-time confirmation.

---

## Edge Cases To Check Manually

### Edge Case A — Hosted stale state
- Confirm stale is interpreted as last-reported metadata older than the heartbeat window.
- Expected: operator caution increases, but runtime authority does not move to hosted.

### Edge Case B — Hosted offline state
- Confirm offline is interpreted as missing current control-plane connectivity.
- Expected: hosted visibility degrades, but local runtime continues to serve based on local policy/provider access.

### Edge Case C — Pending enrollment deployment
- Confirm pending enrollment appears as a setup/posture state, not as a runtime failure.
- Expected: hosted explains adoption progress without implying health or authority.

### Edge Case D — Unsupported bounded action
- Confirm unsupported deployments show credential rotation as unavailable rather than pretending hosted can act.
- Expected: clear limitation, no authority inflation.

### Edge Case E — Browser proof after TS fix
- If Playwright still reports a compile error on an already-fixed line, clear `console/.next` and rerun.
- Expected: stale build output is removed and proof reflects current source.

---

## Acceptance Decision

Mark S03 accepted only if all of the following are true:

- canonical hosted proof doc exists and is accurate,
- focused Vitest suite passes,
- hosted browser walkthrough passes,
- backend hosted-contract and remote-management tests pass,
- hosted wording still reads as metadata-backed and descriptive only,
- stale/offline hosted states do not imply serving-time authority,
- bounded hosted action remains audited credential rotation only.
