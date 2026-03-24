# UAT — M004 / S02: Fleet posture UX

## Scope
Validate that the hosted deployments console now reads as a real, non-authoritative fleet-posture surface for multi-deployment operators. These checks are tailored to the S02 work: shared posture derivation, page-level fleet summary, scan-time row cues, and bounded-action alignment.

## Preconditions
1. Start the console and gateway in a state where the deployments page can load existing deployment records.
2. Use a dataset or fixture set that includes at least:
   - 1 linked/current deployment (`active` + current freshness)
   - 1 pending enrollment deployment
   - 1 active stale deployment
   - 1 active offline deployment
   - 1 revoked deployment
   - 1 unlinked deployment
   - 1 active deployment that does not advertise `remote_credential_rotation`
3. Ensure the operator can open the hosted deployments page with a valid admin session.
4. Confirm the deployment detail drawer and remote action history UI are available.

## Test Case 1 — Deployments entrypoint shows a real fleet posture summary
1. Open the hosted deployments page.
2. Observe the content above the inventory table.
3. **Expected:** A dedicated fleet-posture summary section is present before the table, not just the page header.
4. **Expected:** The section heading communicates hosted posture as metadata-backed, not runtime-authoritative.
5. **Expected:** Summary cards include all of these groupings:
   - Linked and current
   - Pending enrollment
   - Stale or offline visibility
   - Bounded actions blocked
6. **Expected:** The fleet scan area shows a total deployment count.
7. **Expected:** Supporting text explains that hosted posture is descriptive/metadata-backed and that local runtime behavior still requires local confirmation.

## Test Case 2 — Mixed fleet counts are believable and grouped correctly
1. With the mixed-state dataset loaded, inspect the counts shown in the four fleet summary cards.
2. Compare them against the visible deployments in the table.
3. **Expected:** Linked/current count includes only active deployments with current metadata visibility.
4. **Expected:** Pending enrollment count includes only pending deployments, not stale/offline ones.
5. **Expected:** Stale or offline visibility count groups stale and offline active deployments together in the summary.
6. **Expected:** Bounded actions blocked count includes deployments where rotation is blocked or unavailable, including pending, stale, offline, revoked, unlinked, and unsupported active deployments.
7. **Expected:** No card wording implies hosted is certifying serving-time health.

## Test Case 3 — Empty-state summary remains coherent
1. Use an environment or fixture where no deployments exist.
2. Open the deployments page.
3. **Expected:** The page still renders coherently without broken cards or contradictory copy.
4. **Expected:** The summary guidance explains that a deployment slot must be created to populate hosted fleet posture.
5. **Expected:** The table area shows the existing “No deployments linked” empty state.

## Test Case 4 — Table makes row posture legible without opening drawers
1. Return to the mixed-state dataset.
2. Scan the Posture column for each deployment row without opening the detail drawer.
3. **Expected:** Each row shows enrollment-state information and posture interpretation directly in the table.
4. **Expected:** The linked/current deployment shows an active/link-related posture plus a positive bounded-action cue.
5. **Expected:** The pending deployment shows pending enrollment wording and no active freshness cue.
6. **Expected:** The stale deployment shows stale visibility wording and a blocked bounded-action cue.
7. **Expected:** The offline deployment shows offline visibility wording and a blocked bounded-action cue.
8. **Expected:** The revoked deployment shows revoked wording and an unavailable bounded-action cue.
9. **Expected:** The unlinked deployment shows unlinked wording and an unavailable bounded-action cue.
10. **Expected:** The unsupported active deployment shows a bounded-action unavailable cue rather than blocked-for-freshness wording.

## Test Case 5 — Freshness and enrollment are not conflated
1. Identify the pending enrollment deployment.
2. Inspect its row in the table.
3. **Expected:** It is described as pending enrollment, not stale or offline.
4. **Expected:** It does not display an active-deployment freshness badge.
5. Open the stale deployment row.
6. **Expected:** It still shows as linked/active inventory, but the posture language explicitly frames the issue as stale visibility.
7. Open the offline deployment row.
8. **Expected:** It still shows as linked/active inventory, but the posture language explicitly frames the issue as offline visibility.

## Test Case 6 — Bounded-action semantics stay aligned between table and detail drawer
1. From the table, select the stale deployment.
2. Note the table’s bounded-action cue.
3. Open the detail drawer and inspect the Remote action card.
4. **Expected:** The Remote action card explains the same blocked reason implied by the table state.
5. Repeat for:
   - offline deployment
   - pending deployment
   - revoked deployment
   - unlinked deployment
   - unsupported active deployment
6. **Expected:** The available / blocked / unavailable state remains semantically consistent between scan table and Remote action card for each case.
7. **Expected:** The Remote action card still describes the action as bounded hosted assistance only, not broad remote control.

## Test Case 7 — Linked/current deployment allows the one bounded hosted action
1. Select a linked/current deployment that advertises `remote_credential_rotation`.
2. Inspect the row’s posture cue.
3. **Expected:** The table says rotation is available.
4. Open the detail drawer and inspect the Remote action card.
5. **Expected:** The note textarea and queue button are enabled.
6. Enter a valid short note.
7. **Expected:** The form accepts input normally and does not show a blocked/unavailable error before submission.
8. Do not submit if the environment should remain unchanged; this step is only to confirm availability framing.

## Test Case 8 — Hosted trust-boundary wording remains explicit on the deployments page
1. Read the summary text and the bounded-actions/trust-boundary callouts above the table.
2. **Expected:** The wording explicitly signals that hosted summaries are metadata-backed/descriptive.
3. **Expected:** The wording tells the operator to confirm serving-time behavior from the local runtime / local observability surfaces.
4. **Expected:** Bounded hosted actions are described as audited credential rotation only (or equivalent narrow phrasing), not as general deployment control.
5. **Expected:** No wording claims hosted enforces tenant policy, routing, fallback, or provider selection.

## Test Case 9 — Table interaction behavior is preserved
1. Click a deployment row in the table.
2. **Expected:** The selected row is visually highlighted.
3. **Expected:** The corresponding detail drawer opens on the right.
4. Click a different row.
5. **Expected:** Selection moves correctly and the drawer updates to the new deployment.
6. **Expected:** The added posture cues do not break the existing click-to-select workflow.

## Edge Cases

### Edge Case A — All deployments pending enrollment
1. Use a dataset where every deployment is pending.
2. Open the deployments page.
3. **Expected:** The summary shows zero linked/current deployments and a non-zero pending enrollment count.
4. **Expected:** Stale/offline counts stay at zero.
5. **Expected:** Bounded-action-blocked count reflects that pending deployments are unavailable for rotation.
6. **Expected:** The page still reads as an onboarding/fleet-posture surface, not an error state.

### Edge Case B — Revoked and unlinked records remain visible for interpretation
1. Use a dataset containing revoked and unlinked records.
2. Open the deployments page and inspect both summary and table.
3. **Expected:** These records remain visible enough to understand fleet posture and audit context.
4. **Expected:** Their posture wording makes clear they are no longer linked.
5. **Expected:** Their action state is unavailable, not merely stale/offline.

### Edge Case C — Unsupported but current active deployment
1. Use an active deployment with current freshness but without `remote_credential_rotation` capability.
2. Inspect its table row and Remote action card.
3. **Expected:** Hosted posture can still read as linked/current.
4. **Expected:** Bounded action is unavailable because the deployment lacks support, not because hosted assumes the runtime is unhealthy.

## Failure signals
- The deployments page still opens directly into table-only inventory with no summary layer.
- Pending deployments are mislabeled as stale or offline.
- Stale/offline rows require opening the drawer before their meaning becomes legible.
- Table cues and Remote action card reasons disagree for the same deployment.
- Hosted wording implies runtime authority, health certification, or broader remote control.
- Revoked/unlinked records disappear from fleet interpretation instead of staying visible with descriptive audit context.

## Notes for tester
- This slice is about truthful synthesis, not new hosted mechanics. If the UI feels clearer but starts sounding authoritative about serving-time runtime truth, treat that as a failure.
- Prefer datasets with multiple deployments visible at once; S02 is optimized for the multi-deployment evaluator/operator case.
