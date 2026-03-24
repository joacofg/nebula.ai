# S01: Public embeddings endpoint — UAT

## Preconditions

1. The Nebula gateway for this worktree is running with the M003/S01 code.
2. A valid client API key exists for the default tenant and can be sent as `X-Nebula-API-Key`.
3. A valid admin API key exists for querying `/v1/admin/usage/ledger`.
4. The configured local embeddings backend is reachable enough for happy-path requests, or you have a known way to simulate an upstream failure for the failure case below.
5. You can inspect HTTP response headers and JSON bodies.

---

## Test Case 1 — Authenticated single-string embeddings request succeeds

**Purpose:** Prove the new public `/v1/embeddings` route works on the intended narrow happy path.

### Steps

1. Send `POST /v1/embeddings` with headers:
   - `X-Nebula-API-Key: <valid client key>`
2. Use JSON body:
   ```json
   {
     "model": "nomic-embed-text",
     "input": "hello world"
   }
   ```
3. Capture the response body and headers.

### Expected results

- HTTP status is `200`.
- Response body has OpenAI-style list shape:
  - top-level `object` is `"list"`
  - `data` contains one entry
  - `data[0].object` is `"embedding"`
  - `data[0].index` is `0`
  - `data[0].embedding` is an array of floats
  - `model` echoes the requested model or the service-returned model value for the same request
  - `usage.prompt_tokens` is present
  - `usage.total_tokens` is present
- Response headers include:
  - `X-Request-ID`
  - `X-Nebula-Tenant-ID`
  - `X-Nebula-Route-Target: embeddings`
  - `X-Nebula-Provider: ollama`
  - `X-Nebula-Route-Reason: embeddings_direct`

---

## Test Case 2 — Authenticated batch request preserves item ordering

**Purpose:** Prove the public route supports the intentionally narrow batch shape and preserves order.

### Steps

1. Send `POST /v1/embeddings` with headers:
   - `X-Nebula-API-Key: <valid client key>`
2. Use JSON body:
   ```json
   {
     "model": "nomic-embed-text",
     "input": ["first", "second"]
   }
   ```
3. Inspect the `data` array in the response.

### Expected results

- HTTP status is `200`.
- Response `data` contains two entries.
- `data[0].index == 0` and corresponds to the first input item.
- `data[1].index == 1` and corresponds to the second input item.
- Both `embedding` fields are float arrays.
- The route does not collapse the batch to a single embedding.

---

## Test Case 3 — Existing auth contract is reused unchanged

**Purpose:** Confirm embeddings does not introduce a new auth mode or different auth behavior.

### Steps

1. Send `POST /v1/embeddings` without `X-Nebula-API-Key`.
2. Send the same request again with an invalid `X-Nebula-API-Key`.

Use this body for both:
```json
{
  "model": "nomic-embed-text",
  "input": "hello"
}
```

### Expected results

- Missing-key request returns `401` with the existing missing-key behavior.
- Invalid-key request returns `401` with the existing invalid-key behavior.
- No alternate bearer-token or new auth path is required.

---

## Test Case 4 — Unsupported request shapes are rejected at the contract boundary

**Purpose:** Confirm the public contract stays intentionally narrow and does not silently accept broader OpenAI embeddings options.

### Steps

1. Send `POST /v1/embeddings` with a nested input list:
   ```json
   {
     "model": "nomic-embed-text",
     "input": [["nested"]]
   }
   ```
2. Send `POST /v1/embeddings` with an unsupported extra field:
   ```json
   {
     "model": "nomic-embed-text",
     "input": "hello",
     "encoding_format": "base64"
   }
   ```
3. Optionally send a blank input string:
   ```json
   {
     "model": "nomic-embed-text",
     "input": "   "
   }
   ```

### Expected results

- Each invalid request returns `422`.
- The route rejects nested input and unsupported extra fields instead of silently coercing or ignoring them.
- The failure reads as contract validation, not as a generic server error.

---

## Test Case 5 — Upstream embeddings failure is distinguishable from validation failure

**Purpose:** Confirm runtime failure mapping is explicit and suitable for later evidence/documentation work.

### Steps

1. Put the embeddings backend into a known failing state, or simulate an upstream failure in a controlled environment.
2. Send:
   ```json
   {
     "model": "nomic-embed-text",
     "input": "hello"
   }
   ```
3. Capture the response.

### Expected results

- HTTP status is `502`.
- Response body `detail` indicates an embeddings upstream failure, not a validation failure.
- If you later query the usage ledger by the emitted request id, the row shows terminal failure metadata rather than a completed outcome.

---

## Test Case 6 — `X-Request-ID` correlates the public request to durable usage-ledger evidence

**Purpose:** Prove the main S01 evidence story works end-to-end.

### Steps

1. Send a successful authenticated batch request to `POST /v1/embeddings`:
   ```json
   {
     "model": "nomic-embed-text",
     "input": ["first", "second"]
   }
   ```
2. Copy the `X-Request-ID` response header value.
3. As an admin, call:
   - `GET /v1/admin/usage/ledger?request_id=<copied-request-id>`
4. Inspect the returned ledger row.

### Expected results

- The ledger query returns exactly one matching row for that request id.
- The row includes metadata proving the request path:
  - `request_id` matches the response header
  - `tenant_id` matches the authenticated tenant
  - `requested_model` matches the request body
  - `final_route_target` is `"embeddings"`
  - `final_provider` is `"ollama"`
  - `terminal_status` is `"completed"` for the happy path
  - `route_reason` is `"embeddings_direct"`
  - `policy_outcome` is `"embeddings=completed"`
- The ledger row does **not** expose raw request text or returned vectors.

---

## Edge Cases to explicitly confirm

1. **Blank model value** → rejected with `422`.
2. **Empty input list** → rejected with `422`.
3. **Flat list with a blank entry** → rejected with `422`.
4. **Flat list with a non-string item** → rejected with `422`.
5. **Request headers still include `X-Request-ID` on successful calls** → yes.
6. **Embeddings route stays separate from chat orchestration** → infer by verifying embeddings-specific headers/ledger metadata rather than chat route metadata.

---

## UAT exit criteria

S01 passes UAT when:

- The public `/v1/embeddings` route succeeds for both single and flat-batch input.
- Existing API-key auth behavior is preserved.
- Unsupported shapes/options are rejected explicitly.
- Upstream failure is distinguishable from validation failure.
- A successful request can be correlated through `X-Request-ID` into a metadata-only usage-ledger row.
- No evidence suggests broader parameter parity, new auth modes, SDK/helper additions, or storage of raw embeddings payloads.
