---
phase: 07-deployment-enrollment-and-identity
plan: "03"
subsystem: api, console
tags: [fastapi, sqlalchemy, enrollment, lifecycle, nextjs, react-query, typescript]

# Dependency graph
requires:
  - phase: 07-01
    provides: EnrollmentService, DeploymentModel, enrollment admin routes
  - phase: 07-02
    provides: consume_enrollment_token, exchange endpoint, LocalHostedIdentityModel

provides:
  - revoke_deployment and unlink_deployment methods on EnrollmentService
  - POST /v1/admin/deployments/{id}/revoke and /{id}/unlink endpoints
  - TypeScript deployment CRUD types and API functions in admin-api.ts
  - deployments/deployment query keys
  - Full console deployment management page at /deployments
  - DeploymentTable, DeploymentStatusBadge, CreateDeploymentSlotDrawer
  - EnrollmentTokenRevealDialog (show-once UX)
  - DeploymentDetailDrawer with state-based actions
  - RevokeConfirmationDialog, UnlinkConfirmationDialog

affects:
  - Completes ENRL-03 — all lifecycle transitions testable
  - Console navigation: /deployments page now functional

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Lifecycle methods raise ValueError (caught as 409) for state guard violations
    - Console follows tenants split-panel pattern with components/ directory
    - createMutation chains generateEnrollmentToken on success for seamless token reveal flow
    - Token reveal dialog uses setTimeout(2s) for clipboard copy feedback

key-files:
  created:
    - console/src/app/(console)/deployments/page.tsx
    - console/src/components/deployments/create-deployment-slot-drawer.tsx
    - console/src/components/deployments/deployment-detail-drawer.tsx
    - console/src/components/deployments/deployment-status-badge.tsx
    - console/src/components/deployments/deployment-table.tsx
    - console/src/components/deployments/enrollment-token-reveal-dialog.tsx
    - console/src/components/deployments/revoke-confirmation-dialog.tsx
    - console/src/components/deployments/unlink-confirmation-dialog.tsx
  modified:
    - src/nebula/services/enrollment_service.py (revoke_deployment, unlink_deployment added)
    - src/nebula/api/routes/enrollment.py (revoke and unlink endpoints added)
    - tests/test_enrollment_api.py (6 new lifecycle tests)
    - console/src/lib/admin-api.ts (deployment types and API functions added)
    - console/src/lib/query-keys.ts (deployments/deployment keys added)

key-decisions:
  - "Components split into console/src/components/deployments/ directory following the tenants pattern"
  - "createMutation chains generateEnrollmentToken immediately after slot creation so the token reveal dialog fires without a second user action"
  - "Color classes (bg-amber-50, bg-rose-50, etc.) live in DeploymentStatusBadge component, not inlined in page.tsx — follows tenants component separation pattern"

patterns-established:
  - "Lifecycle state guards: raise ValueError in service, caught as 409 in route handler"
  - "Show-once token dialog: rendered at page level, triggered by mutation side-effect"

requirements-completed:
  - ENRL-03

# Metrics
duration: 6min
completed: 2026-03-21
---

# Phase 07 Plan 03: Deployment Lifecycle and Console UI Summary

**Revoke/unlink lifecycle endpoints with full credential invalidation, relink via same deployment record, and a complete console deployment management page following the split-panel UI-SPEC pattern**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-03-21T23:11:36Z
- **Completed:** 2026-03-21T23:17:25Z
- **Tasks:** 2 completed (Task 3 is human-verify checkpoint, not yet approved)
- **Files modified/created:** 13

## Accomplishments

- `revoke_deployment` and `unlink_deployment` added to `EnrollmentService`: state guard enforced (ValueError → 409), credential_hash/prefix cleared on transition, timestamps set
- `POST /{id}/revoke` and `POST /{id}/unlink` endpoints added to admin router with auth guard
- Relink flow verified end-to-end: revoke + new token generation + exchange reuses the same deployment_id with fresh credential, no duplicate records
- 6 new ENRL-03 lifecycle integration tests; full 75-test suite green
- TypeScript deployment types and API functions added to `admin-api.ts`
- `deployments`/`deployment` query keys added to `query-keys.ts`
- Full deployment management page at `/deployments` with:
  - Split-panel layout matching tenants pattern
  - DeploymentTable with empty state, loading, error, and row selection
  - DeploymentStatusBadge: semantic colors per UI-SPEC (amber/sky/rose/slate)
  - CreateDeploymentSlotDrawer with trust boundary reminder
  - EnrollmentTokenRevealDialog: show-once, dark slab, copy-to-clipboard with 2s "Copied" feedback
  - DeploymentDetailDrawer with state-based actions
  - RevokeConfirmationDialog (pink-700 destructive button + "Keep deployment" dismiss)
  - UnlinkConfirmationDialog (secondary-button confirm + "Keep linked" dismiss)
- TypeScript compiles clean (1 pre-existing e2e error, none in project files)
- All 51 console tests pass with no regressions

## Task Commits

1. **TDD RED: Failing lifecycle tests** — `e008b62` (test)
2. **Task 1: Revoke and unlink lifecycle endpoints** — `0b18c17` (feat)
3. **Task 2: Console deployment management page** — `7ae1bc0` (feat)

## Files Created/Modified

- `src/nebula/services/enrollment_service.py` — Added `revoke_deployment`, `unlink_deployment`
- `src/nebula/api/routes/enrollment.py` — Added `POST /{id}/revoke` and `POST /{id}/unlink`
- `tests/test_enrollment_api.py` — 6 lifecycle tests (07-03-01 through 07-03-04 + two 409 guard tests)
- `console/src/lib/admin-api.ts` — Deployment types (DeploymentRecord, EnrollmentState, etc.) and 5 API functions
- `console/src/lib/query-keys.ts` — `deployments` and `deployment` query keys
- `console/src/app/(console)/deployments/page.tsx` — Main page with React Query integration
- `console/src/components/deployments/*` — 7 component files

## Decisions Made

- Components split into `console/src/components/deployments/` directory following the tenants pattern, rather than inlining everything in page.tsx. The split produces cleaner, more testable components.
- `createMutation` chains `generateEnrollmentToken` automatically on success, so the operator sees the token reveal dialog immediately after slot creation without a separate click.
- Color utility classes live in `DeploymentStatusBadge` component (not inlined in page.tsx), consistent with tenants pattern where badge rendering is in the table component.

## Deviations from Plan

None — plan executed exactly as written. Component placement follows the explicit guidance: "If the tenants page keeps components in a separate directory, do the same for deployments."

## Known Stubs

None — all components are wired to real React Query mutations and queries against live API functions.

## Self-Check: PASSED
