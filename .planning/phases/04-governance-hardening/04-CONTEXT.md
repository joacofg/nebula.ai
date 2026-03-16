# Phase 4: Governance Hardening - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Align Nebula's policy surface, runtime behavior, and operator-visible explanations so the existing governance controls are credible for real internal B2B use. This phase hardens how policy is enforced, how denied/degraded requests are explained, and how the API/UI represent those rules. It does not add broader auth scope, enterprise identity features, new governance capabilities, or a larger console surface.

</domain>

<decisions>
## Implementation Decisions

### Runtime-authoritative policy boundary
- Phase 4 should treat `routing_mode_default`, `allowed_premium_models`, `semantic_cache_enabled`, `fallback_enabled`, and `max_premium_cost_per_request` as real runtime-enforced controls.
- `max_premium_cost_per_request` should be enforced as a hard runtime block when a request exceeds the configured threshold.
- `soft_budget_usd` should remain a soft signal in Phase 4: it should annotate policy outcome and operator-visible metadata when exceeded, but it should not automatically block premium routing yet.
- `prompt_capture_enabled` and `response_capture_enabled` should not become runtime behavior in Phase 4.
- Because Phase 4's success criterion is policy/runtime alignment, prompt/response capture flags should not remain visible as normal editable policy controls in the console for this phase. If they remain in API models for forward compatibility, they should be treated as deferred/future-facing rather than operator-facing active controls.
- Downstream work should make one explicit distinction between runtime-enforced controls and non-runtime/deferred settings rather than presenting all fields as if they have equal authority.

### Error semantics and operator guidance
- Error responses should be explicit, stable, and operator-facing, but still terse.
- `401` should be reserved for missing or invalid credentials.
- `403` should be reserved for authenticated but forbidden operations, inactive-tenant cases, and disallowed routing/policy choices.
- Error messages should say exactly what failed in operator language and avoid leaking internal implementation details, stack traces, or ambiguous phrasing.
- Admin and tenant flows should feel consistent: the same category of problem should produce the same status-code semantics even if the exact message differs by entrypoint.
- Phase 4 should lock representative admin-path invalid-credential coverage in addition to tenant/chat-path invalid-credential coverage.

### Denied and degraded request explainability
- Operators should be able to explain denied and fallback-blocked requests from the same kinds of signals they use for successful requests.
- For denied requests, Nebula should preserve the attempted route target, route reason, policy mode, and policy outcome in structured metadata rather than collapsing everything into a generic denial.
- For local-provider failures where premium fallback is disabled, Nebula should explicitly say that fallback was blocked by policy rather than making it look like a generic upstream outage.
- Request-level explainability should include a stable request identifier plus enough structured metadata to connect the immediate API response with the persisted usage-ledger row.
- Successful, denied, and degraded paths should reuse one consistent metadata contract as much as possible instead of inventing separate explanation shapes for unhappy paths.

### Console policy contract and wording
- The policy screen should present a clear `runtime-enforced controls` section for the controls the gateway actually enforces at request time.
- The console should not imply that all stored policy fields affect runtime behavior.
- If a field is not enforced in Phase 4, the preferred outcome is to remove it from the visible operator policy surface rather than keep it looking active.
- The policy editor should preserve the existing explicit-save workflow and compact operator-console tone from Phase 2.
- Any explanatory copy should prioritize trust and clarity over completeness. A short, direct statement about what is enforced is preferable to long explanatory text.

### Claude's Discretion
- Exact naming of metadata fields and exact response-header/body distribution, as long as the operator can explain denied/degraded outcomes consistently.
- Exact UI phrasing and placement for the runtime-enforced explanation, as long as the boundary is unmistakable.
- Exact test organization and representative endpoint selection, as long as admin and tenant error semantics are both explicitly covered.

</decisions>

<specifics>
## Specific Ideas

- Treat Phase 4 as a credibility pass, not a feature-expansion pass.
- The best operator experience here is not "more knobs"; it is fewer ambiguous knobs and clearer consequences.
- The safest interpretation of the phase goal is: if a control is visible as active governance, it should either change runtime behavior now or be removed from that operator-facing surface.
- For unhappy-path explainability, the operator should be able to answer: what route was attempted, why was it chosen, what policy affected it, and did fallback happen or get blocked?

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase framing
- `.planning/PROJECT.md` — Product thesis, operator-first constraints, and the rule to keep the console focused rather than expanding scope.
- `.planning/REQUIREMENTS.md` — Phase 4 requirements `GOV-01`, `GOV-02`, and `ROUT-01`.
- `.planning/ROADMAP.md` — Phase 4 goal, success criteria, and plan breakdown.
- `.planning/STATE.md` — Active concern that Phase 4 should align policy surface area with enforced runtime behavior instead of broadening the console scope.

### Prior decisions that constrain Phase 4
- `.planning/phases/01-self-hosted-foundation/01-CONTEXT.md` — Self-hosted trust and degraded-mode principles that still apply to policy/runtime hardening.
- `.planning/phases/02-operator-console/02-CONTEXT.md` — Admin trust model, compact operator-console direction, explicit-save policy editing flow, and prior decision to keep advanced settings secondary.

### Existing governance/runtime sources of truth
- `.planning/phases/04-governance-hardening/04-RESEARCH.md` — Brownfield findings, open questions, and validation architecture for this phase.
- `src/nebula/services/auth_service.py` — Admin and tenant auth semantics plus current exact error details.
- `src/nebula/services/policy_service.py` — Current policy resolution and enforcement behavior.
- `src/nebula/services/chat_service.py` — Runtime route/fallback behavior and usage-ledger recording paths.
- `src/nebula/api/routes/admin.py` — Current admin policy surface and admin-playground entrypoint.
- `src/nebula/api/routes/chat.py` — Current response metadata contract for chat requests.
- `src/nebula/models/governance.py` — Tenant policy and usage-ledger model definitions.
- `tests/test_governance_api.py` — Current governance and auth-path behavioral coverage.
- `tests/test_response_headers.py` — Current response metadata coverage.
- `tests/test_admin_playground_api.py` — Admin-playground behavior and request-correlation coverage.

### Console policy surface
- `console/src/components/policy/policy-form.tsx` — Main operator policy-editing workflow.
- `console/src/components/policy/policy-advanced-section.tsx` — Current advanced-settings wording and field exposure that Phase 4 must clarify.
- `console/e2e/policy.spec.ts` — Current browser-level policy-editing expectations.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/nebula/services/policy_service.py`: already enforces routing-mode, allowlist, cache, fallback, and spend-guardrail behavior, so Phase 4 should harden and clarify this path rather than invent a new governance layer.
- `src/nebula/services/auth_service.py`: already centralizes the admin and tenant credential semantics needed for a stable GOV-02 contract.
- `src/nebula/services/chat_service.py`: already records routing and fallback behavior, making it the natural place to preserve unhappy-path explanations instead of creating side channels.
- `src/nebula/api/routes/chat.py`: already exposes a structured `X-Nebula-*` metadata pattern that should be reused for denied/degraded cases where feasible.
- `console/src/components/policy/policy-advanced-section.tsx`: already isolates advanced policy controls, which gives Phase 4 a natural place either to tighten wording or remove misleading controls from the visible operator surface.

### Established Patterns
- Auth and policy failures are already expressed through `HTTPException`; Phase 4 should standardize details and coverage rather than replace that pattern.
- The operator console uses an explicit-save policy workflow and should keep that interaction model.
- Previous phases already established that the console should feel like a precise control plane, which argues against showing speculative or non-authoritative controls as if they are active.
- The product already distinguishes immediate runtime metadata from persisted ledger data; Phase 4 should preserve that distinction while making unhappy-path explanations complete.

### Integration Points
- Runtime-authoritative policy decisions connect `TenantPolicy` models, `PolicyService.resolve()`, `ChatService` request execution, and the admin policy options/UI contract.
- Error semantics connect `AuthService`, FastAPI dependency enforcement, admin endpoints, tenant chat endpoints, and the test suite.
- Denied/degraded explainability connects response headers, response detail strings, request IDs, and usage-ledger persistence.
- Console alignment connects the backend policy-options contract with the policy form and advanced-section wording.

</code_context>

<deferred>
## Deferred Ideas

- Turning `prompt_capture_enabled` or `response_capture_enabled` into real runtime capture behavior — future governance/privacy phase.
- Any broader identity/access-control work beyond the existing admin-key model — future phase.
- New governance features beyond clarifying and hardening the currently scoped controls — separate future phase.

</deferred>

---

*Phase: 04-governance-hardening*
*Context gathered: 2026-03-16*
