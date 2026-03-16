# Phase 2 Research: Operator Console

**Phase:** 2
**Researched:** 2026-03-16
**Confidence:** HIGH

## Executive Summary

Phase 2 should introduce a separate operator console application rather than trying to stretch the FastAPI backend into a templated UI. The current backend already exposes most of the required governance surface through `/v1/admin/*`; the missing pieces are a real browser-facing control plane, an operator-friendly authentication flow around the existing admin key model, and deployment wiring so the console can run alongside the self-hosted API.

The cleanest brownfield fit is a top-level `console/` Next.js App Router app that proxies browser requests to the existing FastAPI admin API. That keeps the pasted admin key in browser memory, avoids opening broad CORS surface area on the backend, and lets Phase 2 ship a credible control-plane experience without expanding identity scope beyond the current single-admin-key trust model.

## Current Baseline

### Backend Surface Already Exists

- `src/nebula/api/routes/admin.py` already supports:
  - tenant list/create/get/update
  - tenant policy get/update
  - API key list/create/revoke
  - usage ledger listing
- `src/nebula/models/governance.py` already defines the tenant, API key, and policy payload shapes the UI needs.
- `tests/test_governance_api.py` already covers the core admin CRUD flows and can protect API regressions while the console is added.

### UI and Deployment Gaps

- There is no frontend project, JS toolchain, or browser test harness in the repo.
- `docker-compose.selfhosted.yml` currently ships only `nebula`, `postgres`, and `qdrant`; there is no console service in the supported self-hosted path.
- `src/nebula/main.py` does not add CORS middleware, so a separate browser origin would need either explicit CORS work or a proxy boundary.

### Auth and Product Constraints

- Admin auth is currently header-based through `X-Nebula-Admin-Key` in `src/nebula/services/auth_service.py`.
- Phase context locks the operator experience to:
  - pasted admin key at login
  - memory-only browser session
  - direct landing on tenants after success
  - clear return to login on invalid/expired session
- Product framing in `.planning/PROJECT.md` still requires a focused operator console, not a broader customer-facing app.

## Recommended Implementation Direction

### 1. Add a Separate `console/` Next.js App Router Workspace

Use a new top-level `console/` application rather than mixing frontend assets into the Python package.

Recommended shape:

- `console/package.json` for the Node workspace
- `console/src/app/` for App Router routes
- `console/src/components/` for shell, tables, dialogs, and forms
- `console/src/lib/` for session state, API clients, and query utilities
- `console/e2e/` for Playwright flows

Why this fits:

- It respects the existing decision to keep FastAPI as the backend core and add a separate frontend surface.
- It isolates the first JS toolchain from the Python app cleanly.
- It preserves room for Phase 3 playground and observability work without redesigning the app shell later.

### 2. Use a Same-Origin Proxy Boundary Instead of Backend CORS

Do not start Phase 2 by adding permissive CORS rules to the FastAPI backend. Use Next.js route handlers under `console/src/app/api/admin/[...path]/route.ts` to proxy console requests to the FastAPI admin API instead.

Recommended environment contract:

- `NEBULA_API_BASE_URL=http://127.0.0.1:8000` for local console development
- `NEBULA_API_BASE_URL=http://nebula:8000` inside the self-hosted Compose stack

Why this is the better Phase 2 move:

- The browser only talks to the console origin, so the admin key never needs cross-origin browser access.
- The proxy can forward `X-Nebula-Admin-Key` exactly as entered without inventing a server-side session store.
- Self-hosted deployment stays simpler because the console and API only need an internal network contract.

### 3. Add a Minimal Admin Session Probe Endpoint

The backend should expose a lightweight authenticated probe such as `GET /v1/admin/session` that simply confirms the admin key is valid.

Why this is worth adding:

- Login should not need to misuse `GET /v1/admin/tenants` as an auth check.
- The console can validate the pasted key cleanly before routing into the shell.
- Backend coverage for auth success/failure remains straightforward in `tests/test_governance_api.py`.

### 4. Keep Session State in Browser Memory Only

The console should use an in-memory React session provider for the admin key and derived auth status.

Implications:

- Refresh and tab close naturally clear the session, which matches the locked phase context.
- Protected console routes should redirect back to login if the provider has no key.
- A session-expired API response should clear the in-memory key and show an inline “enter the admin key again” message rather than silently failing.

### 5. Use a Compact Control-Plane UI System, Not a Generic Dashboard

The `ui-ux-pro-max` guidance and the phase context point to a technical, data-dense control plane.

Recommended design system decisions:

- Light slate background and strong text contrast
- Navy/slate palette with blue action color
- `Fira Sans` body typography and `Fira Code` accents/headings
- Dense tables, tight cards, and visible row hover states
- Left sidebar with `Tenants`, `API Keys`, and `Policy`
- Slim page headers with title, description, and primary action
- Lucide or equivalent SVG icons only
- `overflow-x-auto` wrappers for tables on small screens

UX rules to preserve from the skill:

- Every input has a visible label
- Blur-time validation is preferable to submit-only validation
- Submit actions need loading and success/error feedback
- Required fields must be clearly marked

### 6. Use TanStack Query for CRUD State and Explicit Form Saves

The operator console will issue repeated list/mutation flows against the same admin API surface. Use TanStack Query for server state and cache invalidation.

Why:

- Tenant, API key, and policy screens all need list refresh after mutation.
- Query keys map cleanly to the backend resources (`tenants`, `api-keys`, `tenant-policy`, `policy-options`).
- Explicit mutation status supports the requested inline error/success feedback.

For form handling, standard controlled React forms are sufficient if they enforce inline validation and explicit save semantics. Server Actions are less attractive here because the admin key is intentionally kept in client memory rather than a server-side session.

### 7. Treat Policy Capture Flags as Stored-Only Advanced Controls

`prompt_capture_enabled` and `response_capture_enabled` are already in the policy model, but `.planning/codebase/CONCERNS.md` notes that runtime behavior does not consume them yet.

Recommendation:

- Keep these fields in the advanced section of the policy page to honor the locked Phase 2 context.
- Label them clearly as stored policy settings that are not yet enforced at runtime.
- Avoid presenting them as production-ready observability controls until Phase 4 closes the runtime gap.

### 8. Expand the Self-Hosted Story to Include the Console

Phase 2 is not complete if the console only runs in a local development shell. The self-hosted stack should gain a `console` service and documented operator entrypoint.

Concrete direction:

- Add `console/Dockerfile`
- Add a `console` service to `docker-compose.selfhosted.yml`
- Expose the console on `3000:3000`
- Keep the API on `8000:8000`
- Document the console URL and the operator login flow in `README.md` and `docs/self-hosting.md`

## Plan Split Recommendation

### Plan 01

Stand up the frontend shell and admin authentication model:

- bootstrap the `console/` app
- add the control-plane shell and design system
- implement login with memory-only admin-key session
- add admin session probe + proxy layer
- wire self-hosted deployment and baseline frontend test harness

### Plan 02

Implement tenant and API key workflows:

- tenant list, search, status filters, create/edit detail pane
- API key table, tenant filtering, create flow, reveal-once secret modal
- revoke confirmation and revoked-state presentation
- workflow-specific component and e2e tests

### Plan 03

Implement tenant policy management workflows:

- policy options metadata endpoint
- tenant selector + grouped policy editor
- model allowlist multi-select with manual entry
- explicit save/reset and unsaved-change cues
- capture-flag helper text and advanced-section handling

## Validation Architecture

Phase 2 needs mixed backend and frontend validation.

- Backend regression command: `./.venv/bin/pytest tests/test_governance_api.py -q`
- Frontend quick command target: `npm --prefix console run test -- --run`
- Frontend full command target: `npm --prefix console run lint && npm --prefix console run test -- --run && npm --prefix console run e2e`

Wave 0 must create the frontend testing spine because none exists today:

- `console/package.json` scripts for `lint`, `test`, and `e2e`
- `console/vitest.config.ts`
- `console/playwright.config.ts`
- test setup utilities for rendering authenticated console routes and stubbing proxy responses

## Risks to Avoid

- Do not store the admin key in `localStorage` or `sessionStorage`; the phase context explicitly rejects that.
- Do not expose broad backend CORS rules as a shortcut when a console-side proxy keeps the trust boundary narrower.
- Do not present prompt/response capture flags as enforced runtime behavior.
- Do not build an airy marketing dashboard; the product needs a compact operations surface.
- Do not leave self-hosted deployment docs API-only after introducing the console.

## Research Inputs

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/02-operator-console/02-CONTEXT.md`
- `.planning/phases/01-self-hosted-foundation/01-CONTEXT.md`
- `.planning/codebase/STACK.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONCERNS.md`
- `.planning/research/STACK.md`
- `.planning/research/SUMMARY.md`
- `README.md`
- `docs/self-hosting.md`
- `docker-compose.selfhosted.yml`
- `Makefile`
- `src/nebula/main.py`
- `src/nebula/api/routes/admin.py`
- `src/nebula/api/dependencies.py`
- `src/nebula/services/auth_service.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/models/governance.py`
- `tests/test_governance_api.py`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.codex/skills/ui-ux-pro-max/SKILL.md`

## Sources

- [Next.js Link component docs](https://nextjs.org/docs/app/api-reference/components/link) — navigation guidance for App Router admin shells
- [Next.js Route Handlers docs](https://nextjs.org/docs/app/building-your-application/routing/route-handlers) — proxy boundary for console-to-API forwarding
- [TanStack Query React overview](https://tanstack.com/query/latest/docs/framework/react/overview) — server-state and mutation orchestration for admin CRUD
- [Playwright introduction](https://playwright.dev/docs/intro) — browser automation fit for operator workflow regression tests

---
*Phase research completed: 2026-03-16*
*Ready for planning: yes*
