# Phase 4: Governance Hardening - Research

**Researched:** 2026-03-16
**Domain:** FastAPI governance, routing, and runtime observability hardening
**Confidence:** HIGH

<user_constraints>
## User Constraints

Inferred from `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, and the current codebase because no `04-CONTEXT.md` exists.

### Locked Decisions
- Keep the existing Python/FastAPI gateway core. Do not replatform.
- Treat this as a governance/runtime hardening phase, not a new frontend design phase.
- Preserve the operator trust model: admin-managed onboarding, admin-authenticated console, and server-side tenant resolution for the playground.
- Keep the focused operator console/playground shape rather than broadening product scope.
- Keep immediate response metadata and persisted ledger usage visibly separate; both matter and should not be conflated.
- Phase 4 must close the governance/runtime gaps for `GOV-01`, `GOV-02`, and `ROUT-01`.

### Claude's Discretion
- Decide which current policy fields are true runtime controls versus stored-only metadata and make that boundary explicit.
- Decide how denied and degraded paths should be represented in headers, ledger records, and tests so operators can explain outcomes consistently.
- Decide whether to harden existing endpoints mostly through backend consistency and tests, or whether a small console adjustment is required to keep UI/API truth aligned.

### Deferred Ideas
- Public self-serve onboarding
- Hosted control plane work
- Broad enterprise auth/compliance scope
- Benchmarking/documentation work from Phase 5
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GOV-01 | Tenant policy changes affect runtime behavior for routing mode, fallback enablement, semantic-cache enablement, and premium-model allowlists | Existing enforcement lives in `PolicyService.resolve()` and `ChatService`; plan should harden missing routing-mode verification and resolve extra exposed policy fields. |
| GOV-02 | Admin and tenant operations return clear error states for invalid credentials, inactive tenants, and disallowed routing choices | Existing auth and policy errors already use `HTTPException`; plan should standardize message coverage and add missing inactive/disallowed-path tests. |
| ROUT-01 | Nebula records enough metadata per request to explain why a route was chosen and whether a fallback occurred | Success paths already emit response headers and ledger fields; plan should close denied/provider-error metadata gaps and verify request-level traceability end to end. |
</phase_requirements>

## Summary

Phase 4 is a brownfield hardening phase, not a greenfield governance build. The core enforcement path already exists: request auth resolves tenant context, `PolicyService` derives a `PolicyResolution`, `ChatService` applies cache/provider/fallback behavior from that resolution, and successful requests already emit `X-Nebula-*` headers plus usage-ledger records with `route_reason` and `policy_outcome`.

The planning risk is not missing infrastructure. The risk is contract drift. The `TenantPolicy` schema and console expose more fields than the runtime clearly enforces, denied paths do not preserve as much explanatory metadata as successful paths, and current tests only prove part of the requirement matrix. The plan should therefore center on contract alignment, denied-path observability, and verification completeness.

**Primary recommendation:** Keep enforcement centralized in `PolicyService` and `ChatService`, then harden Phase 4 by making policy/runtime truth explicit, enriching denied-path metadata, and filling the missing requirement-level tests before adding any new governance surface.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | `>=0.115.0,<1.0.0` | HTTP API, dependency injection, error responses | Already owns request auth, admin routing, and exception handling across Nebula. |
| Pydantic | `>=2.8.0,<3.0.0` | Request/response and policy models | Already defines the governance contract, including numeric guardrails and typed policy fields. |
| SQLAlchemy | `>=2.0.39,<3.0.0` | Governance persistence | Already backs tenants, policies, API keys, and usage ledger state. |
| Alembic | `>=1.14.1,<2.0.0` | Schema evolution | Required for any governance/ledger schema hardening. |
| pytest | `>=8.2.0,<9.0.0` | Backend integration and service-flow verification | Existing governance/runtime coverage is already in pytest. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-asyncio | `>=0.23.0,<1.0.0` | Async service-flow tests | For `ChatService` and other coroutine-level governance tests. |
| Next.js | `^15.2.2` | Operator console proxy/UI shell | Only when Phase 4 changes the policy contract exposed to operators. |
| Vitest | `^3.0.8` | Console component tests | For policy editor copy/contract adjustments. |
| Playwright | `^1.51.0` | Console workflow verification | For end-to-end policy editor behavior if Phase 4 changes visible semantics. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Existing FastAPI `HTTPException` error flow | Custom error framework | Unnecessary scope; FastAPI already provides consistent JSON error responses and works with the current dependency/service structure. |
| Existing `PolicyService` + `ChatService` governance path | Per-route or per-provider policy checks | Would duplicate rules and create drift between non-streaming, streaming, admin playground, and tenant traffic. |
| Existing SQLAlchemy/Alembic governance store | Ad hoc JSON/file-based policy state | Would weaken auditability and break the current usage-ledger/reporting flow. |

**Installation:**
```bash
pip install -e '.[dev]'
npm --prefix console install
```

## Architecture Patterns

### Recommended Project Structure
```text
src/nebula/api/            # FastAPI routes and dependency gates
src/nebula/services/       # Auth, policy, routing, chat, governance store
src/nebula/models/         # Pydantic contracts for policy and ledger data
tests/                     # Backend integration and service-flow verification
console/src/               # Operator contract/UI only when policy semantics change
```

### Pattern 1: Resolve Policy Before Any Cache or Provider Work
**What:** Every request should produce one authoritative `PolicyResolution` before cache lookup, route execution, or fallback decisions.
**When to use:** All chat and playground requests, streaming and non-streaming.
**Example:**
```python
# Source: /Users/joaquinfernandezdegamboa/Documents/Playground/src/nebula/services/policy_service.py
route_decision = await router_service.choose_target_with_reason(
    prompt,
    request,
    routing_mode=policy.routing_mode_default,
)
self._enforce_explicit_model_constraints(request, route_decision, policy.routing_mode_default)
```

### Pattern 2: Emit Metadata Once, Then Reuse It for Headers and Ledger
**What:** Build one metadata object per terminal path and reuse it for response headers and ledger persistence.
**When to use:** Completed, cache-hit, fallback, provider-error, and denied paths.
**Example:**
```python
# Source: /Users/joaquinfernandezdegamboa/Documents/Playground/src/nebula/api/routes/chat.py
response.headers.update(_nebula_headers(completion_envelope.metadata))
```

### Pattern 3: Keep Auth and Admin Gating in Dependencies, Not Route Bodies
**What:** Use FastAPI dependencies to resolve tenant context and require admin access before handlers run.
**When to use:** All `/v1/chat/*` and `/v1/admin/*` routes.
**Example:**
```python
# Source: /Users/joaquinfernandezdegamboa/Documents/Playground/src/nebula/api/dependencies.py
def require_admin(request: Request, admin_api_key: str | None = Header(default=None, alias=ADMIN_API_KEY_HEADER)):
    container = get_container(request)
    container.auth_service.authenticate_admin(admin_api_key)
    return container
```

### Anti-Patterns to Avoid
- **Policy checks in routes or providers:** Keep policy enforcement in `PolicyService` and runtime recording in `ChatService`.
- **UI-defined governance semantics:** The console should reflect backend truth, not invent stored-only behavior that the runtime cannot explain.
- **Stringly-typed denied metadata assembled ad hoc in multiple places:** Centralize denied-path metadata just like success metadata.
- **Treating fallback-disabled failures as generic upstream noise:** Preserve the policy context so operators can tell why premium recovery did not happen.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API error envelopes | Custom response/error framework | FastAPI `HTTPException` + route/dependency flow | Already integrated and officially supported. |
| Request and policy validation | Manual parsing or route-level guard code | Pydantic models and `Field(...)` constraints | Numeric guardrails and typed policy fields already live here. |
| Governance persistence | Manual SQL strings or sidecar JSON | `GovernanceStore` + SQLAlchemy + Alembic | Existing ledger and policy state depend on it. |
| Request correlation | New tracing ID system | Existing request middleware and `X-Request-ID` propagation | Already wired into API, playground, and ledger filtering. |

**Key insight:** Phase 4 should remove ambiguity from the existing governance path, not introduce parallel mechanisms.

## Common Pitfalls

### Pitfall 1: Exposing Policy Fields That Are Not Runtime-Authoritative
**What goes wrong:** `TenantPolicy` exposes `max_premium_cost_per_request`, `soft_budget_usd`, and capture flags, while the console explicitly says some advanced settings are "not yet enforced at runtime."
**Why it happens:** The API/UI schema grew ahead of requirement-level enforcement and verification.
**How to avoid:** For Phase 4, classify every exposed policy field as either enforced, advisory, or out of scope, then make API/UI/test behavior match that classification.
**Warning signs:** Operators can save a field but cannot observe a runtime consequence or recorded explanation for it.

### Pitfall 2: Denied Requests Lose Route Explanation
**What goes wrong:** Successful requests persist `route_reason`, but `policy_denied` records currently store `route_reason=None`.
**Why it happens:** `_resolve_policy()` catches `HTTPException` and writes a minimal denied ledger record instead of a structured denied metadata object.
**How to avoid:** Introduce a first-class denied metadata path that captures attempted target, policy gate, and denial reason.
**Warning signs:** Ledger entries explain that a request was denied but not what route was being attempted or which rule blocked it.

### Pitfall 3: Fallback-Disabled Failures Are Hard to Interpret
**What goes wrong:** If local execution fails and fallback is disabled, the client gets a `502` provider error, even though policy materially affected the outcome.
**Why it happens:** The runtime treats this as a provider failure path, not a policy-denied path.
**How to avoid:** Keep the transport status if desired, but preserve policy context in the response/ledger so the operator can distinguish "provider failed" from "policy prevented recovery."
**Warning signs:** A `502` contains only provider text and no clear explanation that fallback was disabled by tenant policy.

### Pitfall 4: The Requirement Matrix Is Only Partially Verified
**What goes wrong:** Some paths are covered well, but `routing_mode_default` enforcement, inactive-tenant cases, and denied-path metadata consistency are not proven end to end.
**Why it happens:** Phase 2 and Phase 3 added behavior incrementally, with tests focused on the features added in those phases.
**How to avoid:** Add requirement-oriented tests that cover successful, denied, degraded, and admin-playground variants of the same governance rules.
**Warning signs:** Tests prove fields can be edited, but not that the same fields change runtime behavior in every entrypoint.

## Code Examples

Verified patterns from current project sources:

### Central Policy Enforcement
```python
# Source: /Users/joaquinfernandezdegamboa/Documents/Playground/src/nebula/services/policy_service.py
if policy.allowed_premium_models and premium_model not in policy.allowed_premium_models:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Premium model '{premium_model}' is not allowed for this tenant.",
    )
```

### Header-Level Runtime Explanation
```python
# Source: /Users/joaquinfernandezdegamboa/Documents/Playground/src/nebula/api/routes/chat.py
return {
    "X-Nebula-Tenant-ID": metadata.tenant_id,
    "X-Nebula-Route-Target": metadata.route_target,
    "X-Nebula-Route-Reason": metadata.route_reason,
    "X-Nebula-Provider": metadata.provider,
    "X-Nebula-Cache-Hit": str(metadata.cache_hit).lower(),
    "X-Nebula-Fallback-Used": str(metadata.fallback_used).lower(),
    "X-Nebula-Policy-Mode": metadata.policy_mode,
    "X-Nebula-Policy-Outcome": metadata.policy_outcome,
}
```

### Denied-Path Ledger Recording
```python
# Source: /Users/joaquinfernandezdegamboa/Documents/Playground/src/nebula/services/chat_service.py
if exc.status_code == status.HTTP_403_FORBIDDEN:
    self.governance_store.record_usage(
        UsageLedgerRecord(
            request_id=request_id or f"req-{uuid4().hex}",
            tenant_id=tenant_context.tenant.id,
            requested_model=request.model,
            final_route_target="denied",
            terminal_status="policy_denied",
            route_reason=None,
            policy_outcome=exc.detail,
        )
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Policy as stored admin data only | Policy resolves into `PolicyResolution` before runtime execution | Phase 2-3, 2026-03-16 | Governance now already affects cache, allowlist, and fallback behavior. |
| Route visibility only in logs or internal code | `X-Nebula-*` response headers plus usage-ledger `route_reason` and `policy_outcome` | Phase 3, 2026-03-16 | Operators can explain successful routing and fallback decisions directly from API/UI surfaces. |
| UI can expose fields without runtime proof | Phase 4 must align the exposed policy surface with enforced behavior | Current phase | Prevents governance drift and makes the product defensible for internal B2B use. |

**Deprecated/outdated:**
- Assuming every field in `TenantPolicy` is equally enforced at runtime. That is not true in the current codebase.
- Treating denied requests as "explained enough" with only a freeform `detail` string. That falls short of `ROUT-01` quality.

## Open Questions

1. **What should happen to stored-only advanced fields during Phase 4?**
   - What we know: The API model exposes them and the console labels them as not enforced.
   - What's unclear: Whether the plan should enforce them now, relabel them as advisory-only, or remove them from the editable runtime contract.
   - Recommendation: Decide explicitly in Wave 0. Do not leave them ambiguous.

2. **Should denied requests expose response metadata, ledger metadata, or both?**
   - What we know: Success paths have rich headers and ledger entries; denied paths currently only persist a minimal ledger row.
   - What's unclear: Whether `GOV-02`/`ROUT-01` require the client response itself to expose route/policy denial metadata.
   - Recommendation: At minimum, make denied ledger records structured. If feasible, add denial headers too for symmetry.

3. **Should fallback-disabled local failures remain `502`?**
   - What we know: Current behavior is tested as `502`.
   - What's unclear: Whether product semantics are clearer if the response detail explicitly states that policy disabled fallback recovery.
   - Recommendation: Keep transport semantics only if the explanatory payload and ledger metadata become unambiguous.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` 8.x + `pytest-asyncio` 0.23.x; `vitest` 3.x; `@playwright/test` 1.51.x |
| Config file | [pyproject.toml](/Users/joaquinfernandezdegamboa/Documents/Playground/pyproject.toml), [console/package.json](/Users/joaquinfernandezdegamboa/Documents/Playground/console/package.json) |
| Quick run command | `.venv/bin/pytest tests/test_governance_api.py tests/test_response_headers.py tests/test_admin_playground_api.py tests/test_service_flows.py -q` |
| Full suite command | `.venv/bin/pytest && npm --prefix console run test -- --run` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GOV-01 | Policy toggles change cache, fallback, routing, and premium-model behavior | integration | `.venv/bin/pytest tests/test_governance_api.py -q` | ✅ |
| GOV-02 | Invalid credentials, inactive tenants, and disallowed routing choices return clear states | integration | `.venv/bin/pytest tests/test_governance_api.py tests/test_admin_playground_api.py -q` | ✅ |
| ROUT-01 | Response headers and ledger records explain route choice and fallback outcome | integration | `.venv/bin/pytest tests/test_response_headers.py tests/test_governance_api.py tests/test_admin_playground_api.py -q` | ✅ |

### Sampling Rate
- **Per task commit:** `.venv/bin/pytest tests/test_governance_api.py tests/test_response_headers.py tests/test_admin_playground_api.py tests/test_service_flows.py -q`
- **Per wave merge:** `.venv/bin/pytest && npm --prefix console run test -- --run`
- **Phase gate:** Full backend suite green, console tests green if contract/UI text changes, and one targeted Playwright policy flow if console semantics change.

### Wave 0 Gaps
- [ ] `tests/test_governance_runtime_hardening.py` — add an end-to-end routing-mode matrix for `auto`, `local_only`, and `premium_only`, including explicit-model conflicts.
- [ ] `tests/test_governance_api.py` — add inactive-tenant request cases and assert exact `detail` messages, not just status codes.
- [ ] `tests/test_response_headers.py` or a new denied-path test file — verify what metadata is exposed for `policy_denied` and fallback-disabled failures.
- [ ] `tests/test_admin_playground_api.py` — add inactive-tenant playground coverage.
- [ ] `console/e2e/policy.spec.ts` and related component tests — update only if Phase 4 changes the stored-only advanced-settings contract or visible copy.

## Sources

### Primary (HIGH confidence)
- [STATE.md](/Users/joaquinfernandezdegamboa/Documents/Playground/.planning/STATE.md) - phase focus, locked product decisions, current blockers
- [REQUIREMENTS.md](/Users/joaquinfernandezdegamboa/Documents/Playground/.planning/REQUIREMENTS.md) - `GOV-01`, `GOV-02`, `ROUT-01`
- [ROADMAP.md](/Users/joaquinfernandezdegamboa/Documents/Playground/.planning/ROADMAP.md) - Phase 4 goal, success criteria, plan split
- [policy_service.py](/Users/joaquinfernandezdegamboa/Documents/Playground/src/nebula/services/policy_service.py) - current policy enforcement behavior
- [chat_service.py](/Users/joaquinfernandezdegamboa/Documents/Playground/src/nebula/services/chat_service.py) - metadata emission, fallback logic, denied-path recording
- [auth_service.py](/Users/joaquinfernandezdegamboa/Documents/Playground/src/nebula/services/auth_service.py) - current admin/tenant error states
- [governance.py](/Users/joaquinfernandezdegamboa/Documents/Playground/src/nebula/models/governance.py) - runtime policy and ledger contracts
- [test_governance_api.py](/Users/joaquinfernandezdegamboa/Documents/Playground/tests/test_governance_api.py) - existing governance integration coverage
- [test_response_headers.py](/Users/joaquinfernandezdegamboa/Documents/Playground/tests/test_response_headers.py) - existing runtime metadata coverage
- [test_admin_playground_api.py](/Users/joaquinfernandezdegamboa/Documents/Playground/tests/test_admin_playground_api.py) - playground traceability coverage
- [policy-advanced-section.tsx](/Users/joaquinfernandezdegamboa/Documents/Playground/console/src/components/policy/policy-advanced-section.tsx) - current stored-only UI contract

### Secondary (MEDIUM confidence)
- https://fastapi.tiangolo.com/tutorial/handling-errors/ - verified FastAPI `HTTPException` guidance for consistent error handling
- https://docs.pydantic.dev/latest/api/fields/ - verified `Field(..., ge=0)` style used by policy numeric guardrails
- https://pytest-asyncio.readthedocs.io/en/stable/reference/configuration.html - verified `asyncio_mode=auto` matches current pytest config

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versions are pinned in the repo and no new libraries are needed for Phase 4.
- Architecture: HIGH - enforcement and metadata flow already exist in project source.
- Pitfalls: MEDIUM - gaps are strongly supported by code and tests, but some product-semantics choices still need explicit Phase 4 decisions.

**Research date:** 2026-03-16
**Valid until:** 2026-04-15
