# M001/S01 — Research

**Date:** 2026-03-23

## Summary

This slice is targeted research, not deep exploration. The live adoption surface already exists and is narrow: `POST /v1/chat/completions` accepts a small OpenAI-like request model, returns an OpenAI-like chat completion payload, supports SSE streaming, and adds Nebula-specific evidence through `X-Nebula-*` response headers. The core implementation lives in `src/nebula/api/routes/chat.py`, `src/nebula/models/openai.py`, and `src/nebula/services/chat_service.py`; the current tests already prove non-streaming, streaming, routing metadata, fallback, cache, and policy-denied behavior.

The main work for S01 should therefore be contract reconciliation and boundary documentation, not runtime expansion. The planner should treat this slice as “make the current contract explicit and test-backed” rather than “add broad compatibility.” The existing code also reveals important boundaries that must be stated plainly: Nebula is chat-completions-only for this milestone, request validation is strict Pydantic-driven, streaming is SSE on the public API but explicitly not supported in the admin Playground path, authentication uses Nebula headers rather than OpenAI `Authorization`, and Nebula-specific observability value appears in headers and ledger/admin surfaces rather than inside the OpenAI-shaped JSON body.

## Recommendation

Take a docs-plus-proof approach centered on the live contract. Use the existing chat endpoint and tests as the source of truth, then add any missing focused tests only where the boundary is not yet explicit enough for downstream slices. This follows the milestone decisions already loaded: D001/D003 say the inference path should be OpenAI-compatible for fast adoption, but the promise must stay tight and reliable.

Concretely, S01 should produce: (1) a supported request/response contract doc for common chat-completions usage, (2) an explicit unsupported/deferred list, and (3) compatibility notes covering auth headers, model naming/routing semantics, streaming behavior, and Nebula metadata headers. If implementation changes are needed, they should be small and in service of clarifying or stabilizing the current boundary, not broadening it.

## Implementation Landscape

### Key Files

- `src/nebula/api/routes/chat.py` — Public `POST /v1/chat/completions` entrypoint. Switches between JSON completion and SSE streaming based on `payload.stream`, and attaches the Nebula response-header contract.
- `src/nebula/models/openai.py` — Canonical public request/response schema. Current supported request fields are: `model`, `messages`, `temperature`, `top_p`, `n`, `stream`, `stop`, `max_tokens`, `presence_penalty`, `frequency_penalty`, `user`, `metadata`. Message role support is `system | user | assistant | tool`, but response shape is still assistant-text only.
- `src/nebula/services/chat_service.py` — Real compatibility boundary. Owns latest-user-message extraction, cache lookup, route selection, fallback, SSE framing, response model construction, ledger writes, and the exact `X-Nebula-*` metadata semantics for success and some failure paths.
- `src/nebula/services/auth_service.py` — Confirms public auth contract: clients must send `X-Nebula-API-Key`, and may need `X-Nebula-Tenant-ID` depending on key scope. This is a major compatibility deviation that should be called out explicitly in docs.
- `src/nebula/services/router_service.py` — Explains model naming semantics. `nebula-auto` is the default adoption model; explicit local model routes local; any other explicit model is treated as premium.
- `src/nebula/services/policy_service.py` — Defines policy-denied behaviors and the `X-Nebula-Policy-*` headers. Important for S01 because compatibility boundary includes failure/header semantics, not only happy-path JSON.
- `src/nebula/providers/openai_compatible.py` — Shows what Nebula forwards downstream to premium providers. Useful for deciding which OpenAI request fields are actually preserved vs ignored.
- `src/nebula/providers/ollama.py` — Shows local-path translation. Important boundary: Nebula normalizes the public request into provider-specific payloads; not every OpenAI nuance survives equally across providers.
- `tests/test_chat_completions.py` — Primary proof for OpenAI-like response body and SSE chunking.
- `tests/test_response_headers.py` — Best current proof of header contract across local, premium, cache, fallback, denied, and fallback-blocked paths.
- `tests/test_service_flows.py` — Additional proof for streaming fallback and cache-write behavior. Use if planner wants stronger behavioral verification without inventing new harnesses.
- `src/nebula/api/routes/admin.py` — Admin Playground path. Important negative boundary: `/v1/admin/playground/completions` rejects `stream=true` with `400`, so downstream docs must not treat Playground as the adoption contract.
- `console/src/app/api/playground/completions/route.ts` — Proxies a fixed subset of response headers from admin Playground to the console. Useful for day-1 value proof, but separate from the public client adoption path.
- `console/src/app/(console)/playground/page.tsx` and `console/src/components/playground/*` — Existing product surface showing route target, provider, cache/fallback, policy outcome, and recorded ledger result. This is the clearest current evidence of where OpenAI compatibility ends and Nebula-native value begins.
- `README.md` — Current high-level product framing already names `POST /v1/chat/completions` and Nebula metadata headers, but does not yet define the compatibility boundary precisely enough for R002/R010.
- `docs/architecture.md` — Best place for cross-linking contract semantics to routing/policy/observability behavior, but still too broad to serve as the slice’s public contract artifact by itself.

### Build Order

1. **Prove the live contract from code/tests first.** The riskiest mistake is documenting a broader surface than the implementation actually supports. The planner should begin by extracting the exact supported request/response and header semantics from `openai.py`, `chat.py`, `chat_service.py`, and current tests.
2. **Define the explicit boundary second.** After the live surface is pinned down, write the supported/unsupported contract documentation. This unblocks S02 and S03 because they need a stable migration target, not exploratory parity promises.
3. **Add focused tests only if a boundary is undocumented or under-specified.** Examples: explicit auth-header expectations, unsupported Playground streaming, or strict failure/header behavior if those are needed to keep docs honest.
4. **Then align repo entry docs.** Update `README.md` and/or a dedicated adoption-contract doc so downstream slices can reference one stable place.

### Verification Approach

- Run `make test` if the slice touches broad backend behavior.
- At minimum run targeted contract tests:
  - `pytest tests/test_chat_completions.py`
  - `pytest tests/test_response_headers.py`
  - `pytest tests/test_admin_playground_api.py -k playground`
- If docs point to operator evidence, verify that the console Playground code still matches the described header fields (`console/src/app/api/playground/completions/route.ts`, `console/src/components/playground/playground-metadata.tsx`, `console/src/components/playground/playground-recorded-outcome.tsx`).
- Observable behaviors that should remain true:
  - `POST /v1/chat/completions` returns `chat.completion` JSON for non-streaming requests.
  - `stream=true` returns `text/event-stream` SSE chunks with `chat.completion.chunk` payloads and terminal `[DONE]`.
  - Response headers include `X-Nebula-Tenant-ID`, `X-Nebula-Route-Target`, `X-Nebula-Route-Reason`, `X-Nebula-Provider`, `X-Nebula-Cache-Hit`, `X-Nebula-Fallback-Used`, `X-Nebula-Policy-Mode`, `X-Nebula-Policy-Outcome`.
  - Denied/fallback-blocked paths still expose Nebula metadata headers.
  - Admin Playground remains non-streaming only.

## Constraints

- The slice owns active requirements `R001`, `R002`, and `R010`; all research findings should be framed against fast adoption path, explicit compatibility boundary, and explicit unsupported features.
- The compatibility contract is intentionally narrow by milestone decision `D003`; planner should avoid turning S01 into broad OpenAI parity work.
- Public authentication is not OpenAI-native: `X-Nebula-API-Key` is required, and `X-Nebula-Tenant-ID` may be required. Any migration doc must state this upfront.
- `ChatService._extract_latest_user_prompt()` requires at least one user message; requests without a user role fail with HTTP 422. That is a meaningful boundary for docs/tests.
- The response body is OpenAI-like but not full parity: only assistant text responses are modeled, no tool-call result payloads are emitted despite `tool` being an allowed input role and `tool_calls` being present only as a finish-reason enum.
- The admin Playground contract is different from the public adoption path: it requires `X-Nebula-Admin-Key`, a tenant id in body, and rejects streaming.
- Embeddings already have a service file (`src/nebula/services/embeddings_service.py`) but are out of scope for this milestone and already deferred by `R011`; S01 docs should avoid implying embeddings support.

## Common Pitfalls

- **Documenting provider passthrough instead of Nebula’s stable contract** — The planner should treat `src/nebula/models/openai.py` plus route/service tests as the contract, not whatever downstream OpenAI-compatible providers happen to accept.
- **Confusing public API with Playground API** — Public adoption is `/v1/chat/completions`; Playground is admin-only proof tooling and is intentionally non-streaming.
- **Overstating OpenAI compatibility from field names alone** — Some familiar fields exist (`n`, `stop`, penalties, `user`), but cross-provider behavior is only trustworthy where current tests or code paths prove it.
- **Burying Nebula-native value in docs** — Day-1 differentiation is already exposed via headers and ledger/console surfaces; the contract doc should mark this as “Nebula-specific evidence layered on top of the compatibility path.”

## Open Risks

- Some request fields are modeled but not deeply behavior-tested across both local and premium providers, so the planner may need a small task to classify them as supported happy-path inputs versus accepted-but-not-strongly-guaranteed.
- There is no obvious dedicated contract doc yet; if the planner chooses to create one, it should keep a single canonical source to avoid README/docs drift.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Next.js 15 / React 19 console | installed: `react-best-practices` | available |
| FastAPI backend | `wshobson/agents@fastapi-templates` | available via `npx skills add wshobson/agents@fastapi-templates` |
| Next.js App Router | `wshobson/agents@nextjs-app-router-patterns` | available via `npx skills add wshobson/agents@nextjs-app-router-patterns` |
| OpenAI-compatible API conventions | `jezweb/claude-skills@openai-api` | available via `npx skills add jezweb/claude-skills@openai-api` |
