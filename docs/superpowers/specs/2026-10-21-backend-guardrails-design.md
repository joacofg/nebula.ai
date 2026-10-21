# Backend guardrails and robustness — design

Date: 2026-10-21. First of three PRs before the defense (backend → semantic cache → console).
Decisions come from the 2026-10-21 grill (option B). IDs (B1…) refer to the audit inventory.

## Goal

Make the gateway's governance promises hold on every path the audit found broken, without
changing routing behavior on the happy path or any thesis number.

## Behavior changes

### Premium fallback obeys the tenant (B1, B6, shared helper from B8)

When the local provider fails, the gateway may only fall back to premium if a premium request
would have been allowed for this tenant. The fallback is blocked when any of these holds:

| Condition | 502 detail |
|---|---|
| `fallback_enabled` is false | `Local provider failed and tenant policy disabled premium fallback.` (unchanged) |
| `routing_mode_default == "local_only"` | `Local provider failed and tenant policy restricts routing to local only.` |
| hard budget exceeded (any enforcement) | `Local provider failed and the tenant hard budget is exhausted.` |
| fallback model not in a non-empty `allowed_premium_models` | `Local provider failed and premium model '<model>' is not allowed for this tenant.` |
| projected fallback cost > `max_premium_cost_per_request` | `Local provider failed and the premium fallback exceeds the tenant per-request cost limit.` |

A blocked fallback records one ledger row (`route_target=local`,
`route_reason=local_provider_error_fallback_blocked`, `terminal_status=provider_error`) and the
502 carries the `X-Nebula-*` headers. The fallback model is always explicit: the economy model
when configured and allowed, else `settings.premium_model`. The local model id is never sent to
the premium provider.

Streaming and non-streaming share one failure helper, so a streaming 502 records the same
route reason and `fallback_used` as the non-streaming one, and every 502 carries `X-Nebula-*`
headers.

### Ledger completeness (B5, B7)

- A stream the client abandons records one ledger row with `terminal_status="client_disconnected"`,
  usage estimated from the content already streamed, and its premium cost. The console labels it
  "cortado por el cliente".
- A premium response with `content: null` is treated as an empty answer: 200 with `""`, usage
  recorded, nothing cached.
- Provider errors keep the upstream status and the first 300 characters of the upstream body
  (e.g. OpenRouter's "insufficient credits") in the 502 detail.

### Restart safety (B2, B3)

- Startup creates the bootstrap tenant and its policy only when missing; an existing bootstrap
  tenant keeps its name, `active` flag and policy.
- Startup finds the bootstrap key by hash whether or not it is revoked; a revoked bootstrap key
  stays revoked and never blocks startup.
- Operator-only flows (recommendations, policy simulation, playground) use one
  `GovernanceStore.operator_api_key()` that never inserts a duplicate.

### Admin API errors (B4)

| Case | Status | Detail |
|---|---|---|
| Create tenant with an existing id | 409 | `Tenant 'x' already exists.` |
| Create API key with a raw key whose hash exists (revoked or not) | 409 | `An API key with this secret already exists.` |
| Create API key for an unknown tenant | 404 | `Unknown tenant: x` |

`list_api_keys(tenant_id=x)` also returns keys whose `allowed_tenant_ids` include `x`.
`scripts/seed_demo_data.py` ignores revoked keys when checking for the demo key.

### Rate limiting (B12)

- A request whose body fails schema validation gets its 422 without spending a token.
- Buckets idle for 60 s or more are dropped (a bucket idle that long is full, so dropping it is
  behavior-neutral).
- Raising a tenant's limit grants the extra tokens immediately; lowering still clamps.
- `X-RateLimit-*` headers appear on every response of a rate-limited tenant, including 403 and
  502.

### OpenAI-compatible error shape (B15)

Errors on `/v1/chat/completions` and `/v1/embeddings` return
`{"error": {"message", "type", "code"}, "detail": message}`. `detail` stays for existing
clients (the console reads it). `type` by status: 400/422 `invalid_request_error`,
401 `authentication_error`, 403 `permission_error`, 404 `not_found_error`, 409 `conflict_error`,
429 `rate_limit_error`, 5xx `api_error`. `code` is the `X-Nebula-Route-Reason` header when present,
else `null`. Admin routes keep FastAPI's `{"detail": …}`.

### Dead signal removed (B11)

`budget_penalty` and `budget_proximity` leave the score breakdown, the persisted signals and the
console's ledger detail. Budgets keep being enforced by the hard-budget downgrade/deny and the
per-request cap. `X-Nebula-Route-Score` keeps its value (the removed term was always 0).

### Security hygiene (B13, B14)

- `docker-compose.selfhosted.yml` binds Postgres and Qdrant to `127.0.0.1` only.
- The admin key is compared in constant time.
- Client strings are bounded before they reach `String(255)` columns: `model` (max 255, 422
  otherwise), tenant id on create (max 255), `X-Request-ID` (truncated to 128).

### Cleanup (B21, B22, B23, B9)

- Remove dead code: `PolicyService._enforce_explicit_model_constraints`,
  `RouterService.choose_target` / `resolve_model` / `uses_embeddings`, `GovernanceStore._lock`,
  unused `Calibration*Reason` aliases, `RecommendationService`'s unused simulation dependency,
  `ChatService.create_completion` / `stream_completion` (tests move to the `_with_metadata`
  methods), stale "Phase 3" / "M009" comments.
- `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT`.
- CI builds the console (`next build`) and runs the Playwright e2e suite (all calls mocked).
- `docs/self-hosting.md`: `runtime_profile` only gates startup validation; the hard budget sums
  ledger rows inside the evidence retention window, so it behaves as a rolling budget over that
  window (B9).
- `TODOS.md`: drop the 409 and `budget_penalty` items.

## Out of scope

Semantic cache changes (PR 2), console UX (PR 3), B16–B20 (OpenAI contract details, async DB,
outcome-evidence summary, simulation N+1, logging/metrics labels), merging
`PolicyEvaluation`/`PolicyResolution`, `prompt_capture_enabled` enforcement.

## Deploy

One gateway release plus the console build from the same commit. No migration (the new terminal
status fits the existing `String(64)` column).
