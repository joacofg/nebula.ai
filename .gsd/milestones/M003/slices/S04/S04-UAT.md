# S04: Durable evidence correlation — UAT

## Preconditions

- Nebula gateway is running with the M003 worktree changes.
- Operator has a valid public `X-Nebula-API-Key` and admin `X-Nebula-Admin-Key`.
- Operator console is reachable and can open the Observability page.
- At least one embeddings-capable provider path is configured so `POST /v1/embeddings` can complete successfully.
- The evaluator has access to browser devtools or another way to inspect response headers.

## Test Case 1 — Public embeddings request produces correlatable durable evidence

**Purpose:** Prove the same public embeddings request can be traced from caller-visible headers to a durable usage-ledger row.

1. Send a `POST /v1/embeddings` request to Nebula with `X-Nebula-API-Key` and a valid narrow-contract body:
   ```json
   {
     "model": "nomic-embed-text",
     "input": [
       "minimal migration keeps the provider-style request body",
       "only the base URL and auth header change"
     ]
   }
   ```
   **Expected:** Response status is `200` and body uses the OpenAI-style embeddings shape (`object: "list"`, `data`, `model`, `usage`).

2. Inspect the response headers.
   **Expected:** Headers include `X-Request-ID`, `X-Nebula-Tenant-ID`, `X-Nebula-Route-Target`, `X-Nebula-Route-Reason`, `X-Nebula-Provider`, `X-Nebula-Cache-Hit`, `X-Nebula-Fallback-Used`, `X-Nebula-Policy-Mode`, and `X-Nebula-Policy-Outcome`.

3. Record the `X-Request-ID` value.
   **Expected:** The request id is non-empty and looks stable enough to use as a correlation key.

4. Query the admin usage ledger with that request id:
   ```bash
   curl "http://localhost:8000/v1/admin/usage/ledger?request_id=<captured-request-id>" \
     -H "X-Nebula-Admin-Key: <admin-key>"
   ```
   **Expected:** Exactly one row is returned.

5. Compare the returned ledger row to the public response evidence.
   **Expected:** The row matches the same request on at least `request_id`, `tenant_id`, `requested_model`, `final_route_target`, `final_provider`, `cache_hit`, `fallback_used`, `route_reason`, `policy_outcome`, and `terminal_status`.

## Test Case 2 — Observability can intentionally discover embeddings rows

**Purpose:** Prove embeddings is a first-class route-target filter in the existing Observability flow.

1. Open the Nebula console and navigate to **Observability**.
   **Expected:** The page shows the Usage ledger and Dependency health sections.

2. Open the **Route target** filter.
   **Expected:** `embeddings` appears as an available option alongside the existing route targets.

3. Select `embeddings`.
   **Expected:** The ledger refreshes using the existing listing flow and shows only rows whose route target is embeddings.

4. Confirm the row from Test Case 1 is visible in the table.
   **Expected:** The row is discoverable by its `Request ID`, tenant, route target `embeddings`, provider, and terminal status.

## Test Case 3 — Request detail explains the embeddings outcome from persisted metadata only

**Purpose:** Prove the detail surface exposes enough metadata to explain the request without exposing payload data.

1. In Observability, click the embeddings row from Test Case 2.
   **Expected:** The Request detail card opens for the selected request.

2. Inspect the visible fields.
   **Expected:** The detail card shows at least:
   - Request ID
   - Timestamp
   - Tenant
   - Route target
   - Terminal status
   - Requested model
   - Response model
   - Provider
   - Route reason
   - Policy outcome
   - Fallback used
   - Cache hit
   - Prompt tokens
   - Completion tokens
   - Total tokens

3. Verify the values align with the public headers and usage-ledger row from Test Case 1.
   **Expected:** Request id and route/outcome metadata tell a coherent story for the same request.

4. Check for sensitive or out-of-scope data.
   **Expected:** The detail card does **not** show the original input strings, raw embedding vectors, or any new payload-capture field.

## Test Case 4 — Observability stays subordinate to the public request + ledger proof path

**Purpose:** Confirm the operator UI is corroboration, not a replacement proof surface.

1. Repeat Test Case 1 and intentionally capture the `X-Request-ID` before opening the console.
   **Expected:** You can explain the request from public headers and direct ledger query alone.

2. Only after that, open Observability and filter to `embeddings`.
   **Expected:** Observability helps inspect the same row but is not required to establish the primary proof path.

3. Compare the sequence against `docs/embeddings-reference-migration.md`.
   **Expected:** The guide presents the order as public request -> headers -> ledger query -> Observability corroboration.

## Edge Case 1 — No embeddings rows match the current filters

1. In Observability, set `Route target = embeddings` and also choose a tenant or time range that excludes the known request.
   **Expected:** The ledger area shows the empty-state message indicating no rows match the filters.

2. Remove the extra restrictive filter while keeping `Route target = embeddings`.
   **Expected:** The known embeddings row becomes visible again.

## Edge Case 2 — Metadata-only boundary holds even after successful request correlation

1. Run another successful embeddings request with clearly recognizable input text.
   **Expected:** Public response succeeds and returns vectors as usual.

2. Query the ledger by `X-Request-ID` and inspect Observability for that same row.
   **Expected:** Neither surface contains the recognizable raw input text or the returned vectors.

3. Verify only metadata is persisted and rendered.
   **Expected:** Route/provider/status/policy/model/timestamp/request-id fields are present; payload content is absent.

## Edge Case 3 — Non-embeddings routes do not masquerade as embeddings evidence

1. Generate or locate a non-embeddings ledger row.
   **Expected:** It appears under its real route target (for example `local` or `premium`).

2. Filter Observability to `Route target = embeddings`.
   **Expected:** The non-embeddings row does not appear.

3. Remove the filter.
   **Expected:** The non-embeddings row returns to the broader ledger list.

## Acceptance Criteria

S04 passes UAT only if all of the following are true:

- A real `POST /v1/embeddings` request yields `X-Request-ID` and `X-Nebula-*` evidence headers.
- The same request can be retrieved from `GET /v1/admin/usage/ledger?request_id=...`.
- Observability can intentionally filter to embeddings rows through the existing route-target filter.
- The table and detail card expose enough persisted metadata to explain the request outcome coherently.
- Raw embeddings inputs and returned vectors remain absent from durable evidence surfaces.
- The overall proof sequence still reads as public request first, operator corroboration second.
