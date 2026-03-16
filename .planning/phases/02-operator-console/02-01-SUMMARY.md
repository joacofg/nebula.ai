---
phase: 02-operator-console
plan: "01"
subsystem: console-foundation
tags: [nextjs, auth, proxy, deployment, testing]
requires: []
provides:
  - Dedicated `console/` Next.js workspace for the operator console
  - Memory-only admin session flow around the existing Nebula admin key
  - Same-origin proxy boundary from the console to `/v1/admin/*`
  - Self-hosted wiring for the console service plus baseline frontend tests
affects: [frontend, backend-api, deployment, docs]
tech-stack:
  added: [nextjs, react-query, tailwindcss, vitest, playwright]
  patterns: [memory-only admin session, same-origin admin proxy, compact control-plane shell]
key-files:
  created:
    - console/package.json
    - console/src/app/layout.tsx
    - console/src/components/auth/admin-login-form.tsx
    - console/src/lib/admin-session-provider.tsx
    - console/src/app/api/admin/[...path]/route.ts
    - console/Dockerfile
  modified:
    - src/nebula/api/routes/admin.py
    - src/nebula/models/governance.py
    - tests/test_governance_api.py
    - docker-compose.selfhosted.yml
    - README.md
    - docs/self-hosting.md
key-decisions:
  - "The operator console ships as a top-level Next.js app instead of blending UI code into the Python backend."
  - "The admin key stays in browser memory only, backed by a module-scoped in-memory session and no durable browser storage."
  - "Browser traffic stays same-origin through `/api/admin/[...path]`, and the proxy forwards `X-Nebula-Admin-Key` to FastAPI."
patterns-established:
  - "Console routes live under `console/src/app/(console)` with a shared operator shell."
  - "Component tests use Vitest plus Testing Library, while operator flows use Playwright against mocked admin routes."
requirements-completed: [CONS-01]
duration: 1 session
completed: 2026-03-16
---

# Phase 02-01 Summary

**Frontend shell, auth flow, and deployment wiring for the Nebula operator console**

## Accomplishments

- Bootstrapped a standalone `console/` workspace with Next.js App Router, Tailwind, React Query, Vitest, and Playwright.
- Added the control-plane shell with the locked navigation structure: `Tenants`, `API Keys`, and `Policy`.
- Implemented the memory-only admin-key flow, admin session probe endpoint, and same-origin proxy boundary to the FastAPI admin API.
- Wired the console into Docker Compose, Makefile helpers, README guidance, and the self-hosting runbook.

## Verification

- `./.venv/bin/pytest tests/test_governance_api.py -q`
- `npm --prefix console run lint`
- `npm --prefix console run test -- --run admin-login-form admin-session-provider`
- `npm --prefix console run e2e -- auth.spec.ts`
- `docker compose -f docker-compose.selfhosted.yml config`

## Notes

- The console foundation now supports protected in-app navigation without persisting browser secrets.
- No git commits were created during execution; the plan completed as an uncommitted working-tree change set.
