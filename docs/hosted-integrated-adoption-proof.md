# Hosted integrated adoption proof

This document is Nebula's canonical integrated hosted walkthrough for the M004/S03 confidence proof.

It assembles the existing hosted trust-boundary and deployments-console canonicals into one joined evaluator path without redefining the hosted product contract. Keep these sources in their canonical roles:

- [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) — acceptance contract for hosted reinforcement language and bounded-action scope
- `console/src/lib/hosted-contract.ts` — canonical wording seam for metadata-only hosted claims, operator guidance, and bounded action phrasing
- `console/src/app/trust-boundary/page.tsx` — public hosted trust-boundary entrypoint
- `console/src/app/(console)/deployments/page.tsx` — authenticated deployments proof entrypoint
- `console/src/components/deployments/fleet-posture-summary.tsx` — hosted fleet posture summary surface
- `console/src/components/deployments/deployment-table.tsx` — mixed-state deployment scan surface
- `console/src/components/deployments/deployment-detail-drawer.tsx` — detail-level trust and dependency composition surface
- `console/src/components/deployments/remote-action-card.tsx` — bounded operational assistance surface

Use this walkthrough when an evaluator needs one discoverable hosted story that proves Nebula's hosted console improves onboarding clarity and multi-deployment understanding while remaining explicitly non-authoritative for local runtime enforcement.

## What this integrated proof establishes

The hosted integrated proof is complete only when an evaluator can start from the public hosted trust boundary, move into the real deployments console, inspect fleet posture across mixed deployment states, open one deployment detail view, and still end with the same conclusion:

1. hosted summaries are metadata-backed and descriptive only
2. hosted fleet posture reflects what deployments most recently reported, not what the local runtime is enforcing right now
3. bounded hosted actions are limited to audited deployment credential rotation and related status visibility
4. the hosted plane is not in the request-serving path and does not have local runtime authority
5. stale or offline hosted signals do not change local routing, fallback, policy, provider selection, or serving-time authority

If any step in the walkthrough weakens those claims, the proof has drifted away from the canonical hosted contract.

## Canonical hosted proof order

Follow this sequence in order.

### 1. Start on the public hosted trust-boundary page

Begin at `console/src/app/trust-boundary/page.tsx`.

This page is the evaluator's public framing surface. It should establish, before authentication or console context, that hosted onboarding gives deployment identity and fleet visibility without moving request serving or runtime policy into the hosted plane. The page already does this by reusing `getHostedContractContent()` from `console/src/lib/hosted-contract.ts` instead of inventing page-local phrasing.

When reviewing this step, confirm the page keeps all three seams visible:

- the allowed descriptive claim that hosted onboarding establishes deployment identity and operator visibility without moving request-serving or policy authority into the hosted plane
- the allowed descriptive claim that hosted fleet posture describes what deployments most recently reported, not what the local runtime is enforcing right now
- the outage framing that if the hosted control plane is unreachable, Nebula keeps serving with local policy and local provider access while hosted freshness simply ages toward stale or offline

This is the first proof seam because it tells the evaluator, in public, that hosted visibility is informative but not authoritative.

### 2. Treat the trust-boundary card as the canonical hosted contract disclosure

On the same page, the embedded trust-boundary card remains the canonical disclosure surface for what the deployment shares by default.

The evaluator should use that card to confirm that the hosted plane stays metadata-only by default and excludes raw prompts, raw responses, provider credentials, tenant secrets, and authoritative runtime policy state. The surrounding page copy should then reinforce how to read hosted freshness and fleet posture without promoting them into serving-time truth.

This matters because the hosted integrated proof is not supposed to create a second contract. It is supposed to point back to the shared contract seam and show where that seam is reused.

### 3. Move into the authenticated deployments console

From there, continue into `console/src/app/(console)/deployments/page.tsx`.

This is the real hosted fleet posture entrypoint. Its job is not to restate the full trust boundary from scratch. Instead, it composes existing surfaces around one operator reading rule: treat hosted remote-action availability as bounded operational assistance, not broad remote control, while still keeping the hosted action scope limited to audited deployment credential rotation.

The page should be read as the first authenticated confirmation that the hosted plane can summarize multiple deployments without becoming the runtime authority for any of them.

### 4. Read the fleet posture summary before scanning individual deployments

Next, inspect `console/src/components/deployments/fleet-posture-summary.tsx`.

This summary is the canonical page-level posture framing. It should be the evaluator's first authenticated proof that Nebula can summarize a mixed fleet while preserving the trust boundary:

- the heading explicitly presents a metadata-backed hosted fleet posture
- the summary text reuses the canonical claims that hosted summaries are metadata-backed and descriptive only and that hosted fleet posture describes what deployments most recently reported
- the trust-boundary callout tells operators to use freshness and dependency summaries to prioritize investigation, then confirm serving-time behavior from the local runtime and its observability surfaces
- the bounded-actions callout keeps the deployment-bound hosted action scope limited to audited credential rotation and related status visibility

This is where an evaluator should understand the fleet as a descriptive operator summary, not as an authoritative health dashboard for request serving.

### 5. Use the deployment table as the mixed-fleet interpretation surface

After reading the summary, inspect `console/src/components/deployments/deployment-table.tsx`.

The table is the scan surface that makes mixed deployment posture legible. It lets an evaluator compare linked, pending, stale, and offline states in one place while preserving the distinction between reported metadata and local runtime truth.

What to verify here:

- posture labels and detail text are used to describe what has been reported, not to claim current request-serving health
- stale and offline rows remain visibly degraded so a mixed fleet reads as uncertain or out-of-date where appropriate
- the action summary stays narrow: rotation available, blocked, or unavailable
- the table does not imply that hosted freshness, dependency summaries, or posture labels can override local runtime routing or fallback behavior

This is the key multi-deployment step in the proof. An evaluator should be able to see a fleet posture story across several deployments while still understanding that the request-serving path remains local.

### 6. Open a deployment detail drawer to inspect context, not authority

Then open one deployment in `console/src/components/deployments/deployment-detail-drawer.tsx`.

The detail drawer is where the proof becomes more contextual without widening authority. It should combine:

- freshness state and freshness reason
- deployment identity and enrollment state
- dependency summary pills
- the embedded trust-boundary card
- the bounded remote-action card

This composition matters because it shows how Nebula gives operators enough metadata to interpret a deployment's posture without claiming that the hosted plane is enforcing routing, fallback, tenant policy, or provider selection.

In other words, the drawer should deepen the evaluator's understanding of one deployment while still redirecting serving-time trust back to the local runtime.

### 7. Read dependency and freshness signals as investigative cues only

Inside the drawer, freshness state and dependency summary are the main inspection signals for follow-up.

They tell the operator what to investigate first. They do not tell the operator that the hosted plane has current serving-time truth. This distinction is critical when one deployment is stale, one is offline, and another is current.

Hosted freshness indicates report recency, not serving-time health or request success. Dependency summary is coarse context for triage, not authoritative proof that requests are succeeding or failing right now.

That means stale or offline hosted signals should change operator urgency, not runtime behavior. They do not reroute traffic. They do not change fallback behavior. They do not rewrite local tenant policy. They do not change which provider credentials the local runtime holds or uses.

### 8. Interpret the remote action card as bounded operational assistance

Finally, inspect `console/src/components/deployments/remote-action-card.tsx`.

This card is the canonical bounded-action surface for the hosted console. It should preserve all of the following truths at once:

- the action is limited to audited credential rotation and related status visibility
- the action history is operational audit context, not evidence of broader remote control
- hosted summaries here are still metadata-backed and descriptive only
- operators must use local runtime observability to confirm serving-time behavior before treating a deployment as healthy
- blocked or unavailable action states are fail-closed constraints, not invitations to widen hosted authority

This is where the phrase bounded operational assistance matters most. The evaluator should leave this surface understanding that the hosted plane can help with narrowly scoped credential rotation, but it still cannot change tenant policy, routing, fallback, provider authority, or the request-serving path.

## How to read stale and offline states in the integrated proof

The hosted integrated walkthrough is especially important when a fleet is mixed.

If one deployment is current, another is stale, and a third is offline, the evaluator should read that result like this:

- hosted fleet posture is still useful as a metadata-backed operator summary
- stale or offline visibility means the hosted plane is showing last-reported or missing connectivity state, not local serving-time truth
- local runtime observability remains the authoritative place to confirm whether traffic is still being served, what routing path is active, whether fallback is engaged, and which policy outcome applies
- the hosted plane remains outside the request-serving path even when its own freshness signals degrade

That is the core trust proof for S03. The hosted console may become less current, but Nebula's local runtime authority does not move.

## Minimal evaluator walkthrough

Use this concise path when you need the full hosted proof in one pass:

1. Open the public hosted trust-boundary page.
2. Confirm the page says hosted onboarding provides deployment identity and operator visibility without moving request-serving or policy authority into the hosted plane.
3. Confirm the trust-boundary card keeps the shared contract metadata-only and excludes sensitive or authoritative local data classes.
4. Open the authenticated deployments page.
5. Read the fleet posture summary as a metadata-backed hosted fleet posture, not as authoritative runtime health.
6. Scan the deployment table for mixed posture, including stale or offline states.
7. Open one deployment drawer to inspect freshness, dependency summary, trust-boundary disclosure, and bounded action scope together.
8. Read the remote action card as audited credential rotation only.
9. Confirm the walkthrough never says hosted can change routing, fallback, tenant policy, provider selection, or the local request-serving path.
10. If any hosted signal is stale or offline, confirm the walkthrough still directs serving-time verification back to the local runtime and its observability surfaces.

That is Nebula's canonical hosted integrated adoption proof for M004/S03.

## What this walkthrough intentionally does not duplicate

This document should not become a second hosted contract.

It intentionally does not restate:

- the complete hosted reinforcement boundary from [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md)
- the full shared wording and schema-backed content definitions from `console/src/lib/hosted-contract.ts`
- the full UI implementation details of the trust-boundary page or deployments console
- any new authority model for hosted freshness, fleet posture, or remote actions

If those details change, update the canonical source rather than copying replacement wording here.

## Failure modes this integrated proof makes obvious

This walkthrough has failed if any of these become true:

- the trust boundary is no longer the public first step in the hosted proof path
- the deployments page stops reading as a composition of the shared hosted contract and instead invents its own authority language
- fleet posture is described as request-serving truth instead of a metadata-backed summary
- stale or offline hosted signals are described as changing local routing, fallback, policy, or provider selection
- the drawer stops redirecting serving-time interpretation back to the local runtime
- the remote action surface implies broad remote control instead of audited credential rotation only
- proof artifacts expose prompts, responses, provider credentials, tenant secrets, or authoritative local policy state

## Related docs and seams

- [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) — canonical hosted reinforcement boundary and acceptance rules
- `console/src/lib/hosted-contract.ts` — canonical hosted wording seam used by the UI
- `console/src/app/trust-boundary/page.tsx` — public trust-boundary entrypoint
- `console/src/app/(console)/deployments/page.tsx` — hosted deployments proof entrypoint
- `console/src/components/deployments/fleet-posture-summary.tsx` — hosted fleet summary surface
- `console/src/components/deployments/deployment-table.tsx` — mixed-fleet scan surface
- `console/src/components/deployments/deployment-detail-drawer.tsx` — detail composition surface
- `console/src/components/deployments/remote-action-card.tsx` — bounded action surface
