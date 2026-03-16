# Phase 3: Playground & Observability - Research

**Researched:** 2026-03-16
**Domain:** Operator playground execution, request routing introspection, usage-ledger observability, and runtime dependency health
**Confidence:** MEDIUM

<user_constraints>
## User Constraints

No `03-CONTEXT.md` exists for this phase. The constraints below are inferred from the locked roadmap, state, and existing Phase 2 decisions.

### Locked Decisions
- Phase 3 stays focused on playground execution, route/cost visibility, and operator observability rather than expanding admin scope again.
- The operator console remains a separate Next.js app with a same-origin proxy boundary to the FastAPI backend.
- Admin authentication remains a pasted, memory-only admin key. Refresh clears the session.
- Nebula should visibly demonstrate routing, cache behavior, fallback behavior, and recorded request outcomes.

### Claude's Discretion
- Exact page split between playground and observability views.
- Exact admin-scoped backend shape for playground execution.
- Exact ledger correlation pattern for surfacing recorded cost and terminal outcome back into the UI.
- Exact health probe contract for premium-provider status.

### Deferred Ideas (OUT OF SCOPE)
- Broader identity or session expansion beyond the current admin-key model.
- End-user chat product features.
- Phase 4 governance/runtime alignment work beyond what Phase 3 must expose.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PLAY-01 | Operator can send a test prompt through Nebula from a playground UI | Add an admin-scoped playground backend endpoint that delegates to `ChatService`, then add a console playground page that calls it through a same-origin route handler. |
| PLAY-02 | Playground shows route target, provider, cache-hit status, fallback status, latency, and policy outcome for each request | Reuse existing `X-Nebula-*` response headers, measure latency in the client, and correlate `X-Request-ID` with ledger data for recorded outcome and cost. |
| OBS-01 | Operator can inspect usage-ledger entries by tenant, route outcome, and time window | Reuse `/v1/admin/usage/ledger`, keep filters in React Query state, and add one exact-match request correlation path for playground follow-up detail. |
| OBS-02 | Operator can see whether cache and upstream providers are healthy or degraded | Reuse `/health/dependencies` patterns, proxy it through the console, and extend backend runtime health to include premium-provider status in addition to cache and local Ollama. |
</phase_requirements>

## Summary

Phase 3 is mostly brownfield integration, not a new-stack phase. The backend already does most of the hard runtime work: `ChatService` emits route metadata headers for local, premium, cache, and fallback paths; the usage ledger already records route target, provider, fallback, cache hit, latency, policy outcome, and estimated premium cost; and the runtime health service already exposes component-level dependency status for governance, cache, and local Ollama. The Phase 2 console also already gives you the right frontend foundation: Next.js App Router, same-origin proxy route handlers, TanStack Query, Vitest, and Playwright.

The planning-critical gap is auth shape. The console only knows the admin key, while `/v1/chat/completions` requires a tenant API key. Because API keys are stored hashed and are not recoverable, the playground cannot be implemented as a pure frontend feature that reuses the public chat endpoint directly. Phase 3 therefore needs a small admin-scoped backend surface that resolves tenant context internally and delegates to the same `ChatService` logic that the public gateway uses. That is the cleanest way to satisfy `PLAY-01` without breaking the current trust model.

The second backend gap is observability completeness. `/health/dependencies` currently reports `gateway`, `governance_store`, `semantic_cache`, and `local_ollama`, but not premium-provider health, so `OBS-02` is not fully met yet. Also, the playground can immediately show route/provider/cache/fallback/policy metadata from response headers, but cost and recorded terminal outcome live in the usage ledger, not in the response. The clean Phase 3 plan is therefore: add an admin playground endpoint, add exact request correlation to the ledger path, extend dependency health to include premium provider status, and build the console pages on top of the existing Phase 2 shell and Query patterns.

**Primary recommendation:** Keep the current Next.js + TanStack Query + FastAPI stack, ship Phase 3 as non-streaming-first, and add only three backend extensions: admin-scoped playground execution, request-id ledger lookup/filtering, and premium-provider health reporting.

## Standard Stack

### Core
| Library / Surface | Version | Purpose | Why Standard |
|-------------------|---------|---------|--------------|
| FastAPI backend | `>=0.115,<1.0` | Existing API surface for admin, chat, and health endpoints | Already owns the runtime contract and should continue to be the single orchestration layer. |
| Next.js App Router | `15.2.2` | Console routes and same-origin proxy handlers | Matches the existing console app and official App Router route-handler guidance. |
| React | `19.0.0` | Client-side operator workflows | Already in the console; enough for form state, request state, and result panels. |
| TanStack Query | `5.66.9` | Server-state fetching, mutation state, invalidation, and refresh | Already used in Phase 2 and is the right fit for repeated ledger/health fetches plus playground mutations. |

### Supporting
| Library / Surface | Version | Purpose | When to Use |
|-------------------|---------|---------|-------------|
| Vitest + RTL | `3.0.8` + current RTL stack | Component and hook tests in the console | Use for playground form/result state, ledger filters, and health cards. |
| Playwright | `1.51.0` | Browser workflow coverage | Use for operator flows across login, playground submission, ledger filters, and health states. |
| Existing usage ledger | current repo model | Source of truth for estimated cost, tokens, terminal status, route reason, and policy outcome | Use for recorded outcomes, not ad hoc frontend estimates. |
| Existing `/health/dependencies` contract | current repo route | Source of truth for dependency degradation state | Use for observability cards after extending premium-provider coverage. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Same-origin Next route handlers | Direct browser calls with CORS | Worse trust boundary and unnecessary because the proxy pattern already exists and is documented. |
| TanStack Query | Hand-rolled `useEffect` + local loading/error state | More boilerplate, weaker cache invalidation, and inconsistent with the current console. |
| Admin-scoped playground endpoint | Asking operator for a tenant API key | Conflicts with the current operator trust model and is impractical because stored keys are hashed. |
| Streaming-first playground | Non-streaming-first playground | Streaming adds SSE parsing and result-assembly complexity without being required by `PLAY-01` or `PLAY-02`. |

**Installation:**
```bash
pip install -e .[dev]
npm --prefix console install
```

No new packages are required for the baseline Phase 3 plan.

## Architecture Patterns

### Recommended Project Structure
```text
console/
├── src/app/(console)/
│   ├── playground/page.tsx       # Playground request/response workflow
│   ├── ledger/page.tsx           # Usage-ledger filters and results
│   └── health/page.tsx           # Dependency health cards
├── src/app/api/
│   ├── playground/completions/route.ts   # Same-origin proxy for admin playground calls
│   └── runtime/health/route.ts           # Same-origin proxy for dependency health
├── src/components/playground/    # Prompt form, metadata panel, response panel
├── src/components/ledger/        # Filter bar, result table, request detail panel
└── src/components/health/        # Status cards and degraded-state messaging

src/nebula/
├── api/routes/admin.py           # Extend with playground + ledger request correlation
├── services/auth_service.py      # Add admin-side tenant-context helper
├── services/runtime_health_service.py    # Add premium provider health
└── services/                     # Keep orchestration in services, not in routes
```

### Pattern 1: Admin-Scoped Playground Bridge
**What:** Add an admin-only backend endpoint that accepts `tenant_id` plus a normal chat-completions payload, resolves tenant policy internally, and delegates to `ChatService`.

**When to use:** Any operator-only execution flow where the console must exercise real routing behavior without requiring a raw tenant API key.

**Why this is the brownfield fit:** The public chat API is client-key authenticated, the console session is admin-key authenticated, and the store only retains API-key hashes. That makes a backend bridge necessary if the operator is supposed to test live routing from the console.

**Example:**
```python
# Source: local brownfield pattern in src/nebula/api/routes/admin.py,
# src/nebula/services/auth_service.py, and src/nebula/services/chat_service.py
@router.post("/playground/completions")
async def create_playground_completion(
    payload: AdminPlaygroundRequest,
    request: Request,
    container: ServiceContainer = Depends(require_admin),
) -> PlaygroundResponse:
    tenant_context = container.auth_service.resolve_playground_context(payload.tenant_id)
    envelope = await container.chat_service.create_completion_with_metadata(
        payload.request,
        tenant_context=tenant_context,
        request_id=getattr(request.state, "request_id", None),
    )
    return PlaygroundResponse(
        response=envelope.response,
        metadata=envelope.metadata,
        request_id=getattr(request.state, "request_id", None),
    )
```

### Pattern 2: Response-Header First, Ledger Second
**What:** Show immediate route metadata from the completion response, then enrich recorded outcome and cost from the ledger using `X-Request-ID`.

**When to use:** Playground request details and any UI that needs both "what just happened" and "what was recorded."

**Why:** The immediate response already exposes route target, route reason, provider, cache hit, fallback used, policy mode, policy outcome, and request ID. The ledger is the recorded source of truth for cost, token totals, terminal status, and persisted timestamps.

**Example:**
```typescript
// Source: current response-header contract in src/nebula/api/routes/chat.py
// plus TanStack Query mutation/invalidation guidance
const mutation = useMutation({
  mutationFn: async (payload: PlaygroundInput) => {
    const startedAt = performance.now();
    const response = await fetch("/api/playground/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Nebula-Admin-Key": adminKey },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    const body = await response.json();
    return {
      body,
      requestId: response.headers.get("X-Request-ID") ?? "",
      latencyMs: Math.round(performance.now() - startedAt),
      routeTarget: response.headers.get("X-Nebula-Route-Target") ?? "unknown",
      provider: response.headers.get("X-Nebula-Provider") ?? "unknown",
      cacheHit: response.headers.get("X-Nebula-Cache-Hit") === "true",
      fallbackUsed: response.headers.get("X-Nebula-Fallback-Used") === "true",
      policyOutcome: response.headers.get("X-Nebula-Policy-Outcome") ?? "unknown",
    };
  },
  onSuccess: async (result) => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.ledger(result.body.tenant_id) });
    await queryClient.prefetchQuery({
      queryKey: queryKeys.ledgerRequest(result.requestId),
      queryFn: () => getLedgerEntry(adminKey, result.requestId),
    });
  },
});
```

### Pattern 3: Centralized Runtime Health Aggregation
**What:** Keep dependency health aggregation in `RuntimeHealthService`, not in the console.

**When to use:** Cache status, local-provider status, premium-provider status, and any future dependency state presented in the operator UI.

**Why:** The frontend should render a single backend-owned contract. It should not learn how to probe Qdrant, Ollama, or premium providers itself.

**Example:**
```python
# Source: local RuntimeHealthService pattern in src/nebula/services/runtime_health_service.py
async def dependencies(self) -> dict[str, dict[str, object]]:
    return {
        "gateway": {"status": "ready", "required": True, "detail": "FastAPI application is running."},
        "governance_store": self.governance_store.health_status(),
        "semantic_cache": await self.semantic_cache.health_status(),
        "local_ollama": await self.embeddings_service.health_status(),
        "premium_provider": await self.provider_health_service.health_status(),
    }
```

### Anti-Patterns to Avoid
- **Operator playground via public chat auth:** Do not ask the operator for a tenant API key or try to recover a stored one from the database.
- **Frontend-owned dependency pings:** Do not probe Qdrant or providers directly from the browser.
- **Streaming-first implementation:** Do not make SSE parsing the baseline if the requirement only needs successful prompt execution plus metadata display.
- **Duplicate cost estimation in the UI:** Do not estimate premium cost in the console when the ledger already records it.
- **Overbuilt dashboarding:** Do not add charts or Prometheus visualization libraries for Phase 3. Tables and status cards are sufficient.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Browser/backend auth bridge | Ad hoc CORS workarounds | Next.js route handlers as the same-origin proxy layer | This is already the console architecture and keeps the browser trust boundary narrow. |
| Server-state lifecycle | Custom loading/error/cache plumbing | TanStack Query queries and mutations | Existing console code already uses this pattern and official docs support invalidation after mutations. |
| Recorded request accounting | UI-side token/cost math | Usage ledger lookup by request ID | The backend already records estimated cost, tokens, and terminal status. |
| Dependency aggregation | Separate UI fetches to each dependency | `RuntimeHealthService` | One contract, one policy for ready/degraded/not-ready, less duplication. |
| Playground streaming baseline | Custom SSE parser and incremental state machine | Non-streaming request/response first | Lower risk, satisfies the requirements, and avoids touching fragile streaming behavior unless needed. |

**Key insight:** Phase 3 should add only the backend surface area that current contracts are missing. Everything else should compose around existing headers, ledger records, health payloads, and Query patterns.

## Common Pitfalls

### Pitfall 1: Admin Auth Is Not Client Auth
**What goes wrong:** A planner assumes the console can call `/v1/chat/completions` directly because both sides already exist.
**Why it happens:** The operator console uses `X-Nebula-Admin-Key`, while the public chat path requires `X-Nebula-API-Key` plus tenant resolution. Those are different trust models.
**How to avoid:** Add one admin-scoped backend playground endpoint that creates a tenant context internally and reuses `ChatService`.
**Warning signs:** Playground design asks for raw tenant keys, or the plan mentions direct browser calls to `/v1/chat/completions`.

### Pitfall 2: Premium Health Is Missing from the Current Runtime Contract
**What goes wrong:** The UI ships a "dependency health" page that only shows cache and local Ollama, leaving premium-provider status invisible.
**Why it happens:** `RuntimeHealthService` currently reports `gateway`, `governance_store`, `semantic_cache`, and `local_ollama` only.
**How to avoid:** Extend backend health aggregation first, then build the UI against that contract.
**Warning signs:** `OBS-02` is marked complete without any backend change under `runtime_health_service.py`.

### Pitfall 3: Playground Result Enrichment Becomes Racey
**What goes wrong:** The UI tries to find the just-recorded ledger entry by fetching the latest rows and guessing which one belongs to the last request.
**Why it happens:** The ledger list API filters by tenant, route outcome, and time window, but not by exact `request_id`.
**How to avoid:** Add `request_id` filtering or a single-record lookup path to the ledger API and use `X-Request-ID` for correlation.
**Warning signs:** The plan mentions "grab the newest ledger row" after a playground completion.

### Pitfall 4: Cost and Latency Get Sourced from the Wrong Place
**What goes wrong:** The UI mixes client-side latency, response headers, and estimated cost without a clear contract.
**Why it happens:** Immediate request metadata and recorded ledger data live in different places.
**How to avoid:** Use client timing for latency-to-response, response headers for routing metadata, and the ledger for recorded cost/tokens/terminal outcome.
**Warning signs:** The design expects `estimated_cost` or `latency_ms` to already be in current chat headers.

### Pitfall 5: Phase 3 Accidentally Turns into a Streaming Rewrite
**What goes wrong:** The plan tries to support token streaming, partial-result UI, and request cancellation in the first pass.
**Why it happens:** The backend already supports streaming, so it is tempting to expose it immediately.
**How to avoid:** Treat streaming as optional follow-up work. Phase 3 requirements do not require it.
**Warning signs:** Planned tasks include SSE parsing, incremental transcript assembly, or stream cancellation before the basic non-streaming flow is covered.

## Code Examples

Verified patterns from official and brownfield sources:

### Same-Origin Proxy Route
```typescript
// Source: Next.js route handlers docs and current console/src/app/api/admin/[...path]/route.ts
export async function POST(request: NextRequest) {
  const upstream = new URL("/v1/admin/playground/completions", process.env.NEBULA_API_BASE_URL);
  const response = await fetch(upstream, {
    method: "POST",
    headers: request.headers,
    body: await request.text(),
    cache: "no-store",
  });

  return new Response(await response.arrayBuffer(), {
    status: response.status,
    headers: response.headers,
  });
}
```

### Query Invalidation After Playground Execution
```typescript
// Source: TanStack Query mutation invalidation guidance
const mutation = useMutation({
  mutationFn: submitPlaygroundRequest,
  onSuccess: async (result) => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.ledger(result.tenantId) });
    await queryClient.invalidateQueries({ queryKey: queryKeys.health });
  },
});
```

### Dependency Health Card Poll
```typescript
// Source: current console Query pattern + existing /health/dependencies payload contract
const healthQuery = useQuery({
  queryKey: queryKeys.health,
  queryFn: getDependencyHealth,
  refetchInterval: 15_000,
});
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Cross-origin SPA calls with browser-held backend secrets | Same-origin route handlers in Next.js App Router | Current console baseline; aligned with current Next.js docs | New Phase 3 console calls should stay behind `/api/*` proxies, not expand backend CORS. |
| Manual fetch state per page | TanStack Query v5 for queries, mutations, and invalidation | Current console baseline | Playground, ledger, and health pages should follow the same query-key pattern as existing tenants/policy pages. |
| Treating request responses as the full source of truth | Correlating immediate headers with recorded ledger entries | Already implied by current backend contracts | Phase 3 should not duplicate accounting fields into ad hoc UI-only state. |

**Deprecated/outdated:**
- Persistent browser storage for admin auth: rejected by the current console contract.
- Direct operator use of tenant API keys in the console: does not fit the current admin workflow and is not supported by the hashed-key store.

## Open Questions

1. **Should Phase 3 support streaming in the playground?**
   - What we know: The backend supports streaming, but the requirements only require prompt execution plus metadata display.
   - What's unclear: Whether demo value justifies the extra SSE complexity now.
   - Recommendation: Plan Phase 3 as non-streaming-first. Add streaming only if the planner explicitly decides it is needed for the demo story.

2. **What exact premium-provider probe should back `OBS-02`?**
   - What we know: There is no premium-provider health contract today, and the provider protocol has no `health_status()` method.
   - What's unclear: Whether the team wants a generic transport probe or provider-specific probes.
   - Recommendation: Add a dedicated provider-health service or protocol extension and keep the output contract backend-owned. Treat the exact probe implementation as MEDIUM confidence until chosen in planning.

3. **Should cost appear in the playground result immediately or after ledger enrichment?**
   - What we know: Recorded cost exists in the usage ledger, not current chat headers.
   - What's unclear: Whether the UI needs a brief "awaiting recorded outcome" state after a completion returns.
   - Recommendation: Use request-id correlation and show a small follow-up loading state for recorded outcome/cost rather than duplicating cost logic into the chat response path.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Pytest `8.x` + Vitest `3.0.8` + Playwright `1.51.0` |
| Config file | `pyproject.toml`; `console/vitest.config.ts`; `console/playwright.config.ts` |
| Quick run command | `./.venv/bin/pytest tests/test_governance_api.py tests/test_response_headers.py tests/test_health.py -q` |
| Full suite command | `make test && npm --prefix console run test -- --run && npm --prefix console run e2e` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLAY-01 | Operator submits a playground prompt and gets a completion through Nebula | backend integration + browser e2e | `./.venv/bin/pytest tests/test_admin_playground_api.py -q && npm --prefix console run e2e -- playground.spec.ts` | ❌ Wave 0 |
| PLAY-02 | Playground surfaces route/provider/cache/fallback/latency/policy metadata and recorded outcome | backend integration + component test | `./.venv/bin/pytest tests/test_admin_playground_api.py -q && npm --prefix console run test -- --run playground` | ❌ Wave 0 |
| OBS-01 | Operator filters ledger by tenant, route outcome, and time window | backend integration + browser e2e | `./.venv/bin/pytest tests/test_governance_api.py -q && npm --prefix console run e2e -- observability.spec.ts` | ❌ Wave 0 |
| OBS-02 | Operator sees degraded cache or upstream-provider status in the console | backend integration + component/e2e | `./.venv/bin/pytest tests/test_health.py -q && npm --prefix console run test -- --run health` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `./.venv/bin/pytest tests/test_governance_api.py tests/test_response_headers.py tests/test_health.py -q`
- **Per wave merge:** `make test && npm --prefix console run test -- --run`
- **Phase gate:** Full suite green plus console e2e green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_admin_playground_api.py` - covers admin playground execution, request-id lookup/filtering, and header/ledger correlation
- [ ] `tests/test_health.py` extension or `tests/test_runtime_health.py` - covers premium-provider health status and degraded-state payloads
- [ ] `console/src/components/playground/*.test.tsx` - covers request form, result metadata panel, and recorded-outcome follow-up state
- [ ] `console/src/components/ledger/*.test.tsx` - covers tenant/status/time filters and empty/error states
- [ ] `console/src/components/health/*.test.tsx` - covers ready/degraded/not-ready card rendering
- [ ] `console/e2e/playground.spec.ts` - covers playground submit flow
- [ ] `console/e2e/observability.spec.ts` - covers ledger filters and dependency health display

## Sources

### Primary (HIGH confidence)
- Local repo: `src/nebula/api/routes/chat.py`, `src/nebula/services/chat_service.py`, `src/nebula/api/routes/admin.py`, `src/nebula/services/auth_service.py`, `src/nebula/services/governance_store.py`, `src/nebula/services/runtime_health_service.py`, `src/nebula/services/semantic_cache_service.py`, `src/nebula/services/embeddings_service.py`
- Local repo: `console/src/app/api/admin/[...path]/route.ts`, `console/src/lib/admin-api.ts`, `console/src/app/(console)/*.tsx`, `console/src/lib/query-provider.tsx`, `console/src/lib/query-keys.ts`
- https://nextjs.org/docs/app/building-your-application/routing/route-handlers - verified App Router route-handler usage and current caching notes
- https://nextjs.org/docs/app/guides/testing/vitest - verified current Next.js guidance for Vitest in App Router apps
- https://nextjs.org/docs/app/guides/testing/playwright - verified current Next.js guidance for Playwright E2E testing
- https://tanstack.com/query/latest/docs/framework/react/overview - verified React Query v5 role for async server state
- https://tanstack.com/query/latest/docs/framework/react/guides/invalidations-from-mutations - verified mutation invalidation pattern
- https://playwright.dev/docs/test-webserver - verified current Playwright `webServer` pattern for app-backed E2E runs

### Secondary (MEDIUM confidence)
- None

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - The repo already pins the main versions and the official docs support the existing patterns.
- Architecture: MEDIUM - The admin playground bridge and premium-provider health extension are strongly implied by the brownfield gaps, but the exact endpoint and probe shapes are not locked yet.
- Pitfalls: HIGH - They are directly evidenced by the current auth, ledger, and health implementations.

**Research date:** 2026-03-16
**Valid until:** 2026-04-15
