# S04 UAT — Day-1 value proof surface

## Purpose

Verify that Nebula's first successful adoption request is immediately explainable through one coherent proof path: public headers and `X-Request-ID`, admin Playground corroboration, persisted ledger evidence, and Observability dependency-health context.

## Preconditions

1. Nebula gateway is running with admin APIs available.
2. Console is running and reachable.
3. A tenant and client API key exist for the happy path.
4. Admin key is available for console/admin API access.
5. The environment can execute chat-completions requests and persist usage-ledger records.
6. Optional but recommended: local and premium providers are configured so both straightforward and fallback-oriented scenarios can be exercised.

---

## Test Case 1 — Canonical docs route the reader into one day-1 proof path

### Steps

1. Open `README.md`.
2. Confirm there is a visible link to `docs/day-1-value.md` in the documentation map.
3. Open `docs/quickstart.md` and complete the first-request confirmation section.
4. Confirm the quickstart sends the reader to `docs/day-1-value.md` for the single canonical walkthrough.
5. Open `docs/reference-migration.md`.
6. Confirm the migration guide sends the reader to `docs/day-1-value.md` after the public migration proof succeeds.
7. Open `docs/day-1-value.md`.
8. Confirm it starts from a real public `POST /v1/chat/completions` request, not Playground.
9. Confirm it explicitly references `X-Nebula-*` headers and `X-Request-ID` as the first proof surface.
10. Confirm it positions Playground and Observability as operator corroboration surfaces rather than adoption targets.

### Expected Outcomes

- There is exactly one discoverable canonical day-1 value walkthrough.
- The docs do not restate the S01 contract or S02 setup in competing ways.
- The canonical proof flow is: public request → headers / `X-Request-ID` → ledger correlation → Playground corroboration → Observability context.

---

## Test Case 2 — Public request exposes immediate route and policy evidence

### Steps

1. Send a real public `POST /v1/chat/completions` request using `X-Nebula-API-Key`.
2. Record the response body and headers.
3. Verify the response succeeds.
4. Inspect the response headers for:
   - `X-Request-ID`
   - `X-Nebula-Tenant-ID`
   - `X-Nebula-Route-Target`
   - `X-Nebula-Route-Reason`
   - `X-Nebula-Provider`
   - `X-Nebula-Cache-Hit`
   - `X-Nebula-Fallback-Used`
   - `X-Nebula-Policy-Mode`
   - `X-Nebula-Policy-Outcome`
5. Record the `X-Request-ID` value for correlation.

### Expected Outcomes

- The public request is the primary source of adoption truth.
- The immediate response reveals the route target, route reason, provider, fallback state, and policy outcome.
- `X-Request-ID` is present and usable for later correlation.

---

## Test Case 3 — Usage ledger correlates the public request to persisted operator evidence

### Steps

1. Take the `X-Request-ID` from Test Case 2.
2. Query `GET /v1/admin/usage/ledger?request_id=<captured-id>` with admin credentials.
3. Inspect the returned record.
4. Compare the returned record to the public headers from Test Case 2.
5. Confirm the ledger entry includes:
   - matching `request_id`
   - `tenant_id`
   - `final_route_target`
   - `final_provider`
   - `route_reason`
   - `fallback_used`
   - `cache_hit`
   - `policy_outcome`
   - `terminal_status`

### Expected Outcomes

- Exactly one persisted record is returned for the captured request.
- The request ID matches the public response.
- The persisted route/provider/fallback/policy data tells the same story as the immediate response.
- The request remains explainable after the original response is gone.

---

## Test Case 4 — Playground shows immediate operator-side corroboration

### Steps

1. Open the console and authenticate with the admin key.
2. Navigate to **Playground**.
3. Submit a non-streaming request for a real tenant.
4. Wait for the assistant response and metadata cards to render.
5. Inspect the **Immediate response evidence** card.
6. Confirm the card shows:
   - Request ID
   - Tenant
   - Route target
   - Route reason
   - Provider
   - Policy mode
   - Policy outcome
   - Cache hit
   - Fallback used
   - Latency

### Expected Outcomes

- Playground remains an admin-only operator surface.
- The metadata card makes the immediate route and policy decision legible without opening devtools or raw headers.
- Tenant attribution, route reason, and policy framing are visible together.

---

## Test Case 5 — Playground recorded outcome shows persisted request evidence clearly

### Steps

1. After completing Test Case 4, wait for the recorded outcome section to load.
2. Inspect the **Recorded outcome** card.
3. Confirm it shows:
   - Terminal status
   - Route target
   - Provider
   - Route reason
   - Policy outcome
   - Fallback used
   - Cache hit
   - Prompt tokens
   - Completion tokens
   - Total tokens
   - Estimated cost
4. Compare the recorded route/provider/fallback/policy values to the immediate Playground metadata.

### Expected Outcomes

- The recorded outcome card makes persisted ledger evidence obvious next to usage and cost.
- The operator can distinguish live response metadata from persisted final outcome.
- Immediate and recorded evidence align for the same request.

---

## Test Case 6 — Observability acts as the persisted explanation surface

### Steps

1. Navigate to **Observability** in the console.
2. Confirm the page heading and introduction describe persisted request explanation, not only generic monitoring.
3. Filter the ledger by tenant or route target.
4. Select a request row.
5. Inspect the request detail panel.
6. Confirm the detail panel shows:
   - Tenant
   - Route target
   - Provider
   - Route reason
   - Policy outcome
   - Fallback used
   - Cache hit
   - Terminal status
   - Token counts

### Expected Outcomes

- Observability clearly functions as the persisted explanation surface for request outcomes.
- Operators can explain what happened to a request using the persisted details alone.
- Route/fallback/policy evidence remains available after request completion.

---

## Test Case 7 — Dependency health stays visible alongside request explanation

### Steps

1. Stay on the Observability page.
2. Scroll to the dependency health section.
3. Confirm dependency cards render current dependency states.
4. If possible, reproduce or simulate an optional dependency degradation state.
5. Confirm the UI messaging explains that degraded optional dependencies remain visible without implying total gateway failure.

### Expected Outcomes

- Dependency health is visible in the same operator workflow as persisted request explanation.
- Required failures read as immediate blockers.
- Optional degradation remains inspectable as reduced capability, not as total outage.

---

## Test Case 8 — Canonical happy-path correlation remains understandable end to end

### Steps

1. Perform one public request as in Test Case 2.
2. Record `X-Request-ID` and route/policy headers.
3. Look up the request in the usage ledger as in Test Case 3.
4. Open Playground and run a separate operator request.
5. Review its immediate response evidence and recorded outcome.
6. Open Observability and locate the public request or operator request in the ledger list.
7. Explain, in one sentence each, where you would look for:
   - immediate response proof
   - persisted request proof
   - dependency-health context

### Expected Outcomes

- A tester can explain the canonical proof path without guessing.
- The answer should be:
   - immediate response proof = public headers or Playground immediate metadata
   - persisted request proof = usage ledger / recorded outcome / Observability detail
   - dependency-health context = Observability dependency health section

---

## Edge Cases

### Edge Case A — Ambiguous multi-tenant key requires explicit tenant selection

#### Steps
1. Use an API key authorized for multiple tenants with no default tenant.
2. Send a public chat-completions request without `X-Nebula-Tenant-ID`.
3. Retry with `X-Nebula-Tenant-ID` set explicitly.

#### Expected Outcomes
- The first request fails with the expected tenant-header requirement.
- The failed request does not masquerade as a successful routed request.
- The second request succeeds and becomes correlatable through `X-Request-ID` and the usage ledger.

### Edge Case B — Policy denial remains explainable

#### Steps
1. Use a tenant policy that blocks a premium request or blocks fallback.
2. Send a matching public request.
3. Inspect the response detail and `X-Nebula-Policy-Outcome` header.
4. Look up the request in the usage ledger.

#### Expected Outcomes
- The denial remains explainable through both the immediate response and the persisted ledger row.
- `route_reason`, `final_route_target`, and `policy_outcome` remain meaningful in the persisted record.

### Edge Case C — Optional dependency degraded while requests remain inspectable

#### Steps
1. Put an optional dependency into a degraded state if possible.
2. Open Observability.
3. Inspect dependency health and a request detail row together.

#### Expected Outcomes
- The UI communicates degraded optional capability without implying the ledger trail is lost.
- Request explanation remains available even when part of the runtime is degraded.

---

## UAT Pass Criteria

S04 passes UAT when all of the following are true:

- The docs route users into one canonical day-1 proof path.
- A public request exposes route/fallback/policy evidence and `X-Request-ID`.
- The usage ledger can be correlated back to that request.
- Playground makes immediate operator-side evidence obvious.
- Recorded outcome makes persisted route/provider/fallback/policy evidence obvious.
- Observability clearly acts as the persisted explanation surface.
- Dependency health remains visible in the same explanatory workflow.
- The tester can articulate the difference between public adoption proof and admin-side corroboration.
