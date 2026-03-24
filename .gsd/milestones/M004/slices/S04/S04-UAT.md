# UAT — S04: Targeted reinforcement refinements

## Preconditions
- Worktree is `/Users/joaquinfernandezdegamboa/Proj/nebula/.gsd/worktrees/M004`
- Console dependencies are installed
- Python venv exists at `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv`
- Playwright browsers are installed for `console/`
- No other process is already bound to `127.0.0.1:3001`

## Test Case 1 — Public trust-boundary page stays reachable and non-authoritative

### Steps
1. Run `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts`
2. Open the public `/trust-boundary` route in the Playwright run.
3. Confirm the page shows the heading **Hosted trust boundary**.
4. Confirm the page shows **Hosted freshness is not local runtime authority.**
5. Confirm the page shows **Nebula's hosted control plane is not in the request-serving path.**
6. Confirm the page still presents the metadata-only and excluded-by-default sections.

### Expected Results
- The page loads without authentication.
- The copy makes hosted limitations explicit.
- No wording implies hosted serves traffic, enforces policy, or becomes runtime authority.

## Test Case 2 — Login entrypoint links into the same hosted trust story

### Steps
1. Start the same Playwright run or open `/`.
2. Confirm the login page shows **Review hosted trust boundary**.
3. Click the link.
4. Confirm navigation to `/trust-boundary`.
5. Re-check the two key guardrail statements:
   - **Hosted freshness is not local runtime authority.**
   - **Nebula's hosted control plane is not in the request-serving path.**

### Expected Results
- The pre-auth entrypoint exposes the trust boundary before console access.
- The trust story is consistent before and after navigation.

## Test Case 3 — Deployments page presents metadata-backed fleet posture across mixed states

### Steps
1. Run `npm --prefix console run e2e -- e2e/deployments-proof.spec.ts`.
2. In the mocked login flow, enter the admin key and enter the console.
3. Navigate to **Deployments**.
4. Confirm the page shows **Metadata-backed hosted fleet posture**.
5. Confirm the summary shows both canonical descriptive claims:
   - hosted summaries are metadata-backed and descriptive only
   - hosted fleet posture reflects what deployments most recently reported
6. Confirm the summary shows mixed-fleet counts:
   - `4 deployments`
   - `Linked and current = 1`
   - `Pending enrollment = 1`
   - `Stale or offline visibility = 2`
   - `Bounded actions blocked = 3`
7. Confirm the page also shows the shared guidance about using local runtime confirmation and bounded action scope.

### Expected Results
- The fleet summary is understandable without opening each row.
- The page reads as a metadata-backed operator summary, not runtime truth.
- Mixed-state interpretation is legible in one scan.

## Test Case 4 — Mixed stale/offline rows remain descriptive-only

### Steps
1. On the deployments page, inspect the **Edge Gateway** row.
2. Confirm it shows **Stale visibility** and **Rotation blocked**.
3. Confirm it explains that hosted posture is stale because the deployment report is older than the expected heartbeat window.
4. Inspect the **DR Gateway** row.
5. Confirm it shows **Offline visibility** and **Rotation blocked**.
6. Verify neither row says hosted is serving traffic, healthy, or authoritative.

### Expected Results
- Stale and offline rows clearly change operator urgency, not authority semantics.
- The table distinguishes visibility degradation from serving-time truth.

## Test Case 5 — Deployment drawer treats freshness and dependencies as supporting evidence only

### Steps
1. Click **Production Gateway** from the deployments table.
2. Confirm the drawer opens with **Deployment detail** and the deployment name.
3. Confirm the drawer shows:
   - freshness reason
   - dependency section
   - **What this deployment shares** trust-boundary card
4. Confirm the drawer includes shared guidance that drawer-level freshness/dependency details are supporting evidence for fleet posture, not hosted authority.
5. Confirm the drawer also includes shared guidance that operators should confirm serving-time behavior from the local runtime and its observability surfaces.

### Expected Results
- Drawer detail deepens the fleet story without changing authority.
- Evidence framing stays subordinate to local runtime truth.

## Test Case 6 — Remote action framing stays bounded to audited credential rotation

### Steps
1. In the open deployment drawer, inspect the remote action card.
2. Confirm it shows the bounded-action label for credential rotation only.
3. Confirm it explains that deployment-bound hosted actions are limited to audited credential rotation and related status visibility.
4. Confirm the card repeats descriptive-only/shared guidance instead of introducing page-local authority wording.
5. Confirm **Queue rotation** is enabled only for the connected active deployment in the proof fixture.

### Expected Results
- Hosted operational help reads as bounded operational assistance, not broad remote control.
- Action scope remains narrow and explicit.

## Test Case 7 — Integrated walkthrough never drifts into hosted authority claims

### Steps
1. During the same browser walkthrough, scan the trust-boundary page, deployments summary, drawer, and remote-action card.
2. Confirm the flow never claims that hosted:
   - serves traffic
   - sits in the request-serving path
   - has local runtime authority
   - controls routing, fallback, or tenant policy
   - holds provider credentials by default
3. Confirm the walkthrough always routes serving-time verification back to the local runtime.

### Expected Results
- The full end-to-end story is reinforcement-only.
- No single surface contradicts the hosted trust boundary.

## Edge Case 1 — Standalone production server path works for Playwright verification

### Steps
1. Run `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts`.
2. Observe that the Playwright web server starts successfully.
3. Confirm there is no failure caused by using `next start` with `output: standalone`.
4. Confirm the browser tests complete successfully against the production-style server.

### Expected Results
- The console starts via the standalone server path.
- Browser proof is no longer blocked by server-start mismatch.

## Edge Case 2 — Shared wording reuse is allowed across composed surfaces

### Steps
1. Run the focused Vitest suite for hosted reinforcement.
2. Inspect passing assertions in:
   - `src/app/(console)/deployments/page.test.tsx`
   - `src/components/hosted/trust-boundary-card.test.tsx`
   - `src/components/deployments/remote-action-card.test.tsx`
3. Confirm tests tolerate repeated shared phrases where the page and embedded card both intentionally reuse canonical contract wording.

### Expected Results
- Tests guard against wording drift without forcing artificial copy divergence.
- Shared-contract reuse is preserved as a deliberate pattern.

## Edge Case 3 — Backend guardrails still align with the hosted proof

### Steps
1. Run `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`
2. Confirm hosted contract tests pass.
3. Confirm remote-management API guardrail tests pass.

### Expected Results
- UI proof remains aligned with backend trust-boundary and bounded-action rules.
- S04 did not fix the story by drifting away from backend guardrails.

## Acceptance Checklist
- [ ] Public trust-boundary route remains reachable without auth
- [ ] Login entrypoint links into the trust-boundary flow
- [ ] Deployments summary clearly shows mixed fleet posture counts
- [ ] Stale/offline rows remain descriptive-only
- [ ] Drawer evidence reads as supporting evidence, not authority
- [ ] Remote action scope remains credential rotation only
- [ ] No hosted-authority drift appears in the integrated walkthrough
- [ ] Playwright proof passes against the standalone production server path
- [ ] Focused Vitest suite passes
- [ ] Backend hosted guardrail tests pass
