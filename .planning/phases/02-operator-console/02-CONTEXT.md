# Phase 2: Operator Console - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a focused web console so operators can authenticate into a Nebula deployment and manage tenants, API keys, and tenant routing policy without relying on raw admin API calls. This phase is limited to the operator console surface for those governance workflows. Playground execution, usage analytics, dependency observability, SSO, broader user management, and hosted/self-serve onboarding remain outside this phase.

</domain>

<decisions>
## Implementation Decisions

### Admin sign-in model
- The console should open on a login screen where the operator pastes the deployment admin key for that session.
- The admin key should be kept in memory only; refreshing the page or closing the tab clears the session.
- Successful sign-in should land directly on the tenants view.
- If the admin key is invalid or the in-memory session is lost, the app should return to the login screen and show a clear inline error.

### Console shell and visual direction
- The app should use a left sidebar with three focused sections: `Tenants`, `API Keys`, and `Policy`.
- The visual tone should feel technical and precise, like an infrastructure control plane rather than a marketing-style SaaS app.
- Screen layouts should be compact and data-dense, with efficient tables and tight cards instead of airy presentation-first spacing.
- Each main screen should use a slim page header with the page title, a short explanatory description, and the primary action for that view.
- Downstream UI work should follow the `ui-ux-pro-max` design direction rather than defaulting to a generic admin template.

### Tenant management workflow
- Tenant management should be list-first.
- The main tenants screen should show the tenant list and allow editing the selected tenant in a side panel or adjacent detail pane.
- Active and inactive tenants should appear in the same list, with strong status badges and filters so operators can narrow the view without losing visibility.

### API key workflow
- API key creation should reveal the raw secret once immediately after creation.
- That one-time reveal should include an obvious copy action and a warning that the secret will not be shown again.
- Revoked keys should remain in the list with a clear revoked status and visually muted styling rather than disappearing.

### Policy editing workflow
- Tenant policy should be edited through a structured form with grouped controls and plain-language labels.
- The default view should foreground core routing controls.
- More advanced controls, especially budget and prompt/response capture settings, should live in advanced sections rather than the primary surface.
- Allowed premium models should be edited through a multi-select of known options, with manual entry available when needed.
- Policy changes should use an explicit `Save` action with unsaved-change cues rather than auto-saving field-by-field.

### Claude's Discretion
- Exact frontend framework and packaging choice for the new console, as long as it preserves the focused operator-console scope.
- Exact component styling, spacing scale, and icon set, as long as the result remains compact, precise, and accessible.
- Exact empty-state copy, filter interaction details, and success/error toast language.
- Exact grouping and order of policy form sections, as long as core routing controls remain primary and advanced settings remain secondary.

</decisions>

<specifics>
## Specific Ideas

- The console should feel like a real control plane for AI gateway operations, not a polished-but-generic startup dashboard.
- `ui-ux-pro-max` guidance should anchor the visual system: light slate/navy palette, strong text contrast, compact information density, and precise typography.
- The design should favor trust and operational clarity over novelty.
- The user explicitly wants the design work for this phase informed by the installed `ui-ux-pro-max` skill.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase framing
- `.planning/PROJECT.md` — Product thesis, self-hosted constraints, operator-console scope, and the confirmed decision to add a separate frontend surface.
- `.planning/REQUIREMENTS.md` — Phase 2 requirements `CONS-01` through `CONS-04`.
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria, and plan breakdown for auth, tenant/API key workflows, and policy workflows.
- `.planning/STATE.md` — Current project focus, active phase, and the warning to keep Operator Console scope narrow.
- `.planning/phases/01-self-hosted-foundation/01-CONTEXT.md` — Prior decisions that carry forward into this phase, especially self-hosted deployment constraints and the focused operator-product positioning.

### Existing codebase context
- `.planning/codebase/STACK.md` — Current backend stack and the fact that no frontend stack is established in-repo yet.
- `.planning/codebase/STRUCTURE.md` — Repository structure, backend integration points, and where new application code currently lives.
- `.planning/codebase/CONVENTIONS.md` — Existing code quality and style conventions to preserve when extending the codebase.
- `README.md` — Current operator-facing API surface, local development instructions, and documented admin endpoints.
- `docs/self-hosting.md` — Supported self-hosted deployment topology the console will operate against.

### Backend APIs and models for the console
- `src/nebula/api/routes/admin.py` — Admin endpoints for tenants, API keys, tenant policy, and usage ledger.
- `src/nebula/api/dependencies.py` — Current admin dependency enforcement and container access pattern.
- `src/nebula/services/auth_service.py` — Current admin authentication model based on `X-Nebula-Admin-Key`.
- `src/nebula/models/governance.py` — Tenant, API key, and policy data shapes the console will read and edit.
- `src/nebula/services/governance_store.py` — Current persistence behavior and CRUD flows backing the admin endpoints.
- `tests/test_governance_api.py` — Existing behavioral coverage for tenant, key, and policy workflows.

### UI direction
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.codex/skills/ui-ux-pro-max/SKILL.md` — Required design-system workflow and UI/UX guidance the user explicitly asked to apply to this phase.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/nebula/api/routes/admin.py`: already exposes the CRUD-style backend surface for tenants, API keys, and tenant policy, so the console can be built directly against existing APIs.
- `src/nebula/models/governance.py`: defines the current request/response models for tenant records, API key records, and tenant policy fields.
- `src/nebula/services/auth_service.py`: already establishes the admin trust model as a single deployment-wide admin key.
- `tests/test_governance_api.py`: provides concrete examples of the intended tenant, key, and policy flows and can anchor frontend expectations during planning.

### Established Patterns
- Admin access is currently authenticated only through `X-Nebula-Admin-Key`; Phase 2 should wrap that model in a console UX rather than inventing broader identity scope.
- The backend API is already shaped around list, create, patch, get, put, and revoke workflows; frontend planning should preserve that operational model.
- Governance policy is a structured typed object with a small set of routing and capture controls, which supports a grouped form UX instead of a generic freeform editor.
- There is no existing frontend scaffold or JS toolchain in this repository yet, so Phase 2 must introduce the initial console app structure deliberately.

### Integration Points
- Console authentication will integrate with the admin endpoints by attaching the pasted admin key to requests.
- Tenant management flows will integrate with `GET/POST/PATCH /v1/admin/tenants`.
- API key management flows will integrate with `GET/POST /v1/admin/api-keys` and `POST /v1/admin/api-keys/{api_key_id}/revoke`.
- Policy editing will integrate with `GET/PUT /v1/admin/tenants/{tenant_id}/policy`.
- The new frontend will need a clear local-development relationship with the existing FastAPI app and self-hosted deployment shape defined in Phase 1.

</code_context>

<deferred>
## Deferred Ideas

- Usage-ledger analytics and richer operator observability views — Phase 3.
- Playground request execution and route/cost inspection UX — Phase 3.
- SSO, multi-user roles, and broader identity management — future phases.
- Hosted/self-serve onboarding flows — future phases.

</deferred>

---

*Phase: 02-operator-console*
*Context gathered: 2026-03-16*
