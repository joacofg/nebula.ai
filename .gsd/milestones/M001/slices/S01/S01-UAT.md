# S01 UAT — Adoption API contract and compatibility boundary

## Purpose

Validate that S01 leaves Nebula with a clear, honest, and test-backed public adoption boundary for `POST /v1/chat/completions`, and that the admin Playground is visibly a separate operator surface.

## Preconditions

1. Work from the repository root.
2. A runnable Python test environment is available for the repo.
3. The following files exist:
   - `docs/adoption-api-contract.md`
   - `tests/test_chat_completions.py`
   - `tests/test_response_headers.py`
   - `tests/test_admin_playground_api.py`
4. Optional for runtime spot checks: a local FastAPI app test environment using the existing fixtures in `tests/support.py`.

---

## Test Case 1 — Canonical contract doc is discoverable and complete

**Goal:** Ensure adopters can find one authoritative contract doc and that it is not a placeholder.

### Steps

1. Open `docs/adoption-api-contract.md`.
2. Confirm it clearly names the public endpoint as `POST /v1/chat/completions`.
3. Confirm it documents `X-Nebula-API-Key` as the public auth header.
4. Confirm it contains sections for:
   - supported request contract
   - authentication and tenant boundary
   - model naming/routing guidance
   - response behavior
   - Nebula response-header evidence
   - admin Playground boundary
   - unsupported/deferred compatibility claims
5. Search the file for `TODO` and `TBD`.

### Expected outcome

- The file is present and readable.
- It reads as a finished contract, not draft notes.
- It explicitly distinguishes the public client path from the admin Playground.
- No placeholder markers remain.

---

## Test Case 2 — README and architecture docs point back to the canonical contract

**Goal:** Ensure the repo entry docs do not become competing versions of the API contract.

### Steps

1. Open `README.md`.
2. Confirm the selected endpoints or documentation map points to `docs/adoption-api-contract.md` for the public chat-completions path.
3. Open `docs/architecture.md`.
4. Confirm it references the public `POST /v1/chat/completions` path with `X-Nebula-API-Key` and describes the Playground as a distinct admin-only surface.

### Expected outcome

- Both docs link or defer to the canonical adoption contract.
- Neither doc claims broader compatibility than the canonical contract does.
- Playground is described as an operator surface, not public-client parity proof.

---

## Test Case 3 — Public auth contract rejects bearer-only auth

**Goal:** Verify the adoption boundary uses Nebula-specific header auth and does not imply OpenAI bearer-token parity.

### Steps

1. Run the focused auth-related contract tests in `tests/test_chat_completions.py`.
2. Inspect the bearer-auth rejection test.
3. Confirm the test sends only `Authorization: Bearer ...` to `POST /v1/chat/completions`.
4. Confirm the expected result is HTTP `401` with `{"detail": "Missing client API key."}`.

### Expected outcome

- Bearer-only auth is rejected.
- The public contract is clearly `X-Nebula-API-Key`, not `Authorization`.
- No route metadata is expected on this missing-auth path.

---

## Test Case 4 — Request validation enforces at least one user message

**Goal:** Verify the public contract is enforced at schema-validation time.

### Steps

1. Open `src/nebula/models/openai.py`.
2. Confirm `ChatCompletionRequest` has schema validation requiring at least one message with `role == "user"`.
3. Run or inspect the test that posts a request with only `system` and `assistant` messages.
4. Confirm the expected result is HTTP `422` with a single validation detail entry.
5. Confirm the test also asserts route headers such as `X-Nebula-Route-Target` are absent.

### Expected outcome

- The invariant is enforced at the request boundary.
- Failures use FastAPI's native structured 422 output.
- No route metadata is emitted for this validation failure because routing did not occur.

---

## Test Case 5 — Public streaming contract is explicit and observable

**Goal:** Verify the supported streaming path is clear and includes observable metadata.

### Steps

1. Run or inspect the streaming test in `tests/test_chat_completions.py`.
2. Confirm the request uses:
   - `POST /v1/chat/completions`
   - `X-Nebula-API-Key`
   - `stream: true`
3. Confirm the expected response includes:
   - `content-type` beginning with `text/event-stream`
   - `cache-control: no-cache`
   - `connection: keep-alive`
   - `X-Nebula-Tenant-ID`
   - `X-Nebula-Route-Target`
   - `X-Nebula-Provider`
   - `X-Nebula-Policy-Outcome`
4. Confirm the SSE body includes `chat.completion.chunk` frames and `[DONE]`.

### Expected outcome

- Streaming is a supported public behavior.
- The streaming path keeps the same explainability story as non-streaming through Nebula headers.
- The contract does not imply broader streaming support outside this path.

---

## Test Case 6 — Routed failures still expose Nebula metadata

**Goal:** Verify adoption-time failures remain explainable.

### Steps

1. Run or inspect the denied/fallback-blocked tests in `tests/test_response_headers.py`.
2. Confirm there is coverage for:
   - policy-denied explicit premium request (`403`)
   - explicit local denial (`403`)
   - fallback-blocked local provider failure (`502`)
3. Confirm the expected assertions include route and policy metadata headers such as:
   - `X-Nebula-Route-Target`
   - `X-Nebula-Route-Reason`
   - `X-Nebula-Policy-Outcome`
4. Confirm the policy-outcome assertion requires presence/non-empty value rather than a stale hard-coded string unless the runtime explicitly guarantees one.

### Expected outcome

- Routed failures remain observable and explainable.
- The tests preserve the distinction between routed failures and pre-routing validation failures.
- A developer can tell what Nebula tried to do and why it failed.

---

## Test Case 7 — Admin Playground is a non-equivalent operator contract

**Goal:** Verify the admin Playground does not get mistaken for the public adoption surface.

### Steps

1. Run or inspect `tests/test_admin_playground_api.py`.
2. Confirm there is coverage showing public client auth does not work on `/v1/admin/playground/completions`.
3. Confirm there is coverage showing `stream: true` is rejected with HTTP `400`.
4. Confirm successful Playground responses include `X-Request-ID`.
5. Confirm the tests correlate that request id through `GET /v1/admin/usage/ledger`.
6. Confirm the success-path expectations match the actual tested runtime route/provider behavior for `gpt-4o-mini`.

### Expected outcome

- Playground is clearly admin-only.
- Playground is clearly non-streaming for this milestone.
- Playground is useful as an operator inspection surface, but not as public API parity proof.

---

## Test Case 8 — Unsupported/deferred claims are explicit

**Goal:** Verify Nebula makes honest omissions instead of implying broad OpenAI parity.

### Steps

1. Open the `## Unsupported or deferred compatibility claims` section in `docs/adoption-api-contract.md`.
2. Confirm it explicitly excludes or defers claims for:
   - bearer-token public auth
   - admin Playground equivalence
   - Playground streaming
   - broad untested request fields/features such as tools, multimodal inputs, response formats, or parallel tool execution
   - unsupported endpoints outside the document
3. Confirm the prose tells readers to treat unlisted, untested behavior as outside the current contract.

### Expected outcome

- The compatibility boundary is narrow and honest.
- Future slices can extend the surface deliberately, rather than inheriting accidental promises.

---

## Edge Cases to watch

1. **Docs drift:** README or architecture docs restate contract details that later diverge from `docs/adoption-api-contract.md`.
2. **Validation drift:** Runtime stops enforcing the required-user-message rule at schema level, causing service-layer behavior to differ from docs/tests.
3. **Observability drift:** `422` validation failures begin emitting route headers, blurring the distinction between request-shape failure and routed failure.
4. **Playground drift:** Admin Playground gains behavior that resembles public compatibility without docs/tests being updated to preserve the boundary.
5. **Policy-header drift:** Tests hard-code a specific `X-Nebula-Policy-Outcome` string where runtime only guarantees meaningful presence.

---

## Suggested execution commands

If a runnable test environment is available, use:

```bash
pytest tests/test_chat_completions.py tests/test_response_headers.py tests/test_admin_playground_api.py -q
pytest tests/test_chat_completions.py -k "stream or user or auth" -q
pytest tests/test_response_headers.py -k "denied or fallback_blocked or validation_failures" -q
test -f docs/adoption-api-contract.md && grep -c "^## " docs/adoption-api-contract.md | awk '{exit !($1 >= 6)}' && ! rg -n "TBD|TODO" docs/adoption-api-contract.md
rg -n "adoption-api-contract|POST /v1/chat/completions|X-Nebula-API-Key|unsupported|deferred" README.md docs/architecture.md docs/adoption-api-contract.md
```

## UAT verdict rule

Mark S01 acceptable when all of the following are true:

- the public adoption contract is discoverable from repo entry docs
- the contract is narrow, explicit, and test-backed
- public auth, validation, streaming, and failure-observability behavior are all covered
- admin Playground is clearly proven to be a different contract
- unsupported/deferred claims are named explicitly rather than implied
