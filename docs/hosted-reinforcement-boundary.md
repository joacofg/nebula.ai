# Hosted reinforcement boundary

This slice artifact defines the acceptance contract for hosted reinforcement language introduced in M004/S01. Downstream slices may improve clarity and proof surfaces, but they must preserve the same trust boundary.

## Allowed hosted reinforcement claims

Hosted surfaces may say that:

- Hosted summaries are metadata-backed and descriptive only.
- Hosted fleet posture describes what deployments most recently reported, not what the local runtime is enforcing right now.
- Hosted freshness indicates report recency, not serving-time health or request success.
- Hosted onboarding establishes deployment identity and operator visibility without moving request-serving or policy authority into the hosted plane.
- Hosted remote actions stay bounded to audited deployment-credential rotation and related audit visibility.

## Prohibited authority implications

Hosted surfaces must not imply that:

- the hosted plane serves traffic or sits in the request-serving path
- the hosted plane has local runtime authority
- the hosted plane enforces tenant policy, routing, fallback, or provider selection
- the hosted plane holds provider credentials, raw prompts, raw responses, or tenant secrets by default
- hosted freshness or fleet posture is authoritative health for serving traffic
- deployment-management UI grants broader remote control beyond the existing audited action

## Bounded action contract

The only hosted deployment action described in this slice is audited credential rotation.

Accepted wording must keep all of these points true:

- the action is limited to deployment credential rotation
- the action is accompanied by audit visibility or status visibility
- the action does not change tenant policy
- the action does not change routing or fallback behavior
- the action does not grant provider-credential authority
- the action does not imply broader operational authority over the local runtime

## Operator reading guidance

When hosted surfaces summarize deployment state, they should tell operators to:

- read hosted fleet posture as an operator summary derived from deployment metadata exports
- use freshness and dependency summaries to prioritize investigation
- confirm serving-time behavior from the local runtime and its observability surfaces
- treat hosted remote-action availability as bounded operational assistance, not broad remote control

## Acceptance rules for S02 and S03

S02 and S03 may add fleet posture synthesis, confidence framing, and integrated proof surfaces only if they preserve the boundary below:

1. Keep the metadata-only contract explicit on user-visible hosted surfaces.
2. Preserve the statement that Nebula's hosted control plane is not in the request-serving path.
3. Preserve the statement that hosted does not have local runtime authority.
4. Keep tenant policy and provider credentials local unless a future milestone explicitly changes the product contract.
5. Treat confidence as descriptive evidence about reported state, never as authoritative serving-time truth.
6. Do not expose raw prompts, raw responses, provider credentials, tenant secrets, or authoritative runtime policy state in new proof artifacts.
7. If new hosted summaries mention fleet posture or confidence, pair them with a local-runtime confirmation caveat.
8. If deployment-management copy changes, keep it bounded to the existing audited credential-rotation action unless the backend capability and milestone plan both expand.

## Inspection and drift checks

To inspect this boundary later:

- read `console/src/lib/hosted-contract.ts` for the canonical wording source
- run `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/components/deployments/remote-action-card.test.tsx`
- run `pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`
- run `rg -n "metadata-only|request-serving path|local runtime authority|serving traffic|tenant policy|provider credentials|fleet posture|confidence" console/src docs`

If any of those checks fail, treat the result as wording drift or a boundary regression until proven otherwise.
