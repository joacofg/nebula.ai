---
phase: 07-deployment-enrollment-and-identity
verified: 2026-03-21T23:30:00Z
status: human_needed
score: 12/12 must-haves verified
re_verification: false
human_verification:
  - test: "Navigate to http://localhost:3000/deployments"
    expected: "Empty state shows 'No deployments linked' heading with 'Create deployment slot' CTA button"
    why_human: "Visual rendering and layout cannot be verified programmatically"
  - test: "Click 'Create deployment slot', fill in display_name='test-gw-1' and environment='development', submit"
    expected: "EnrollmentTokenRevealDialog opens immediately showing a token starting with 'nbet_' in dark code slab, plus NEBULA_ENROLLMENT_TOKEN env var instruction block, disclosure warning, and a functional 'Copy token' button that changes to 'Copied' for 2 seconds"
    why_human: "Clipboard interaction, show-once UX flow, and dialog presentation require live browser"
  - test: "Close the dialog, inspect the deployments table"
    expected: "Row appears with amber 'Pending enrollment' badge, correct display name"
    why_human: "Badge rendering and table row selection require visual confirmation"
  - test: "Click the deployment row"
    expected: "Detail drawer opens on right panel showing UUID (Fira Code font), status badge, created date, and 'Linking is outbound-only...' trust boundary reminder"
    why_human: "Split-panel layout, drawer open/close behavior, and font rendering need visual check"
  - test: "Manually activate a deployment via API (POST /v1/enrollment/exchange), then view it in the console"
    expected: "Row shows sky-blue 'Active' badge; detail drawer shows 'Unlink' and 'Revoke' action buttons. Clicking 'Revoke' opens RevokeConfirmationDialog with pink-700 confirm button labeled 'Revoke deployment' and secondary 'Keep deployment' dismiss"
    why_human: "State-conditional action buttons and confirmation dialog UX require live browser"
---

# Phase 07: Deployment Enrollment and Identity Verification Report

**Phase Goal:** Implement deployment enrollment and identity management — operators can register deployments, link gateways via outbound enrollment exchange, and manage deployment lifecycle (revoke/unlink/relink).
**Verified:** 2026-03-21T23:30:00Z
**Status:** human_needed — all automated checks pass; console UI requires visual inspection
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | POST /v1/admin/deployments creates a deployment slot with pending state | VERIFIED | `create_deployment_slot` in enrollment_service.py sets `enrollment_state="pending"`; test_create_deployment_slot passes |
| 2 | POST /v1/admin/deployments/{id}/enrollment-token generates a 1-hour TTL single-use token | VERIFIED | `generate_enrollment_token` sets `expires_at = now + timedelta(hours=1)`; token starts with `nbet_`; test_generate_enrollment_token passes |
| 3 | GET /v1/admin/deployments lists all deployments including pending, active, revoked, unlinked | VERIFIED | `list_deployments` queries all rows with no state filter; test_list_includes_revoked_and_unlinked passes |
| 4 | Enrollment token is returned raw once and stored as SHA-256 hash | VERIFIED | Raw token in EnrollmentTokenResponse; only `token_hash` stored in DB; pattern confirmed in enrollment_service.py lines 64-65 |
| 5 | Gateway with NEBULA_ENROLLMENT_TOKEN set performs outbound exchange at startup | VERIFIED | main.py lifespan checks `settings.enrollment_token` and calls `attempt_enrollment`; test_startup_enrollment_exchange passes |
| 6 | Exchange consumes token atomically and returns deployment_id + steady-state credential | VERIFIED | `consume_enrollment_token` uses `.with_for_update()` pessimistic lock; test_enrollment_exchange_success passes |
| 7 | Expired or already-consumed tokens are rejected with 401 | VERIFIED | Exchange endpoint returns 401 when `consume_enrollment_token` returns None; test_enrollment_exchange_expired_token and test_enrollment_exchange_consumed_token pass |
| 8 | Exchange failure does not prevent gateway from starting | VERIFIED | main.py wraps `attempt_enrollment` in try/except; test_startup_enrollment_failure_nonfatal passes (app returns 200 /health even with unreachable hosted plane) |
| 9 | Operator can revoke a deployment and its credential is immediately invalidated | VERIFIED | `revoke_deployment` clears `credential_hash`/`credential_prefix`, sets `enrollment_state="revoked"` and `revoked_at`; test_revoke_deployment passes |
| 10 | Operator can unlink a deployment cleanly without data loss | VERIFIED | `unlink_deployment` clears credentials, sets `enrollment_state="unlinked"` and `unlinked_at`; test_unlink_deployment passes |
| 11 | Relink reuses same deployment record with new credentials, no duplicates | VERIFIED | `generate_enrollment_token` accepts `revoked`/`unlinked` state and resets to `pending`; test_relink_preserves_single_record verifies single record after full revoke+relink cycle |
| 12 | Console UI allows creating deployment slots, viewing status, and performing lifecycle actions | PARTIAL — automated checks pass; visual rendering needs human review | page.tsx, all 8 component files exist; TypeScript compiles clean; API functions wired via React Query |

**Score:** 12/12 truths verified (1 requires human for visual confirmation)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/nebula/db/models.py` | DeploymentModel and EnrollmentTokenModel ORM classes | VERIFIED | `class DeploymentModel(Base)` at line 63, `class EnrollmentTokenModel(Base)` at line 81, `class LocalHostedIdentityModel(Base)` at line 95 |
| `src/nebula/models/deployment.py` | Pydantic request/response models | VERIFIED | DeploymentRecord, DeploymentCreateRequest, EnrollmentTokenResponse, EnrollmentExchangeRequest, EnrollmentExchangeResponse all present |
| `src/nebula/services/enrollment_service.py` | Hosted-side enrollment lifecycle | VERIFIED | EnrollmentService with create_deployment_slot, generate_enrollment_token, consume_enrollment_token, revoke_deployment, unlink_deployment, list_deployments, get_deployment |
| `src/nebula/api/routes/enrollment.py` | Admin deployment endpoints + exchange endpoint | VERIFIED | `router = APIRouter(prefix="/admin/deployments")` and `exchange_router = APIRouter(prefix="/enrollment")`; all 7 endpoints present |
| `src/nebula/services/gateway_enrollment_service.py` | Gateway-side outbound enrollment | VERIFIED | GatewayEnrollmentService with attempt_enrollment, get_local_identity, clear_local_identity; injectable http_transport for testing |
| `migrations/versions/20260321_0002_deployments.py` | deployments, enrollment_tokens, local_hosted_identity tables | VERIFIED | All 3 tables created with conditional pattern; `down_revision = "20260315_0001"` |
| `tests/test_enrollment_api.py` | Integration tests for deployment CRUD and lifecycle | VERIFIED | 13 tests covering ENRL-01, ENRL-02, ENRL-03; all pass |
| `tests/test_gateway_enrollment.py` | Gateway startup enrollment tests | VERIFIED | 4 tests covering startup exchange, no-token skip, failure non-fatal, already-enrolled skip; all pass |
| `console/src/lib/admin-api.ts` | TypeScript deployment CRUD types and API functions | VERIFIED | DeploymentRecord type, EnrollmentState type, listDeployments, createDeployment, generateEnrollmentToken, revokeDeployment, unlinkDeployment, ADMIN_DEPLOYMENTS_ENDPOINT constant |
| `console/src/lib/query-keys.ts` | deployments/deployment query keys | VERIFIED | `deployments: ["deployments"] as const` and `deployment: (id: string) => ["deployment", id] as const` |
| `console/src/app/(console)/deployments/page.tsx` | Deployment management page with React Query | VERIFIED | Imports and wires listDeployments, createDeployment, revokeDeployment via React Query; renders DeploymentTable |
| `console/src/components/deployments/` | 7 component files | VERIFIED | create-deployment-slot-drawer.tsx, deployment-detail-drawer.tsx, deployment-status-badge.tsx, deployment-table.tsx, enrollment-token-reveal-dialog.tsx, revoke-confirmation-dialog.tsx, unlink-confirmation-dialog.tsx |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/nebula/api/routes/enrollment.py` | `src/nebula/services/enrollment_service.py` | `container.enrollment_service` | WIRED | Routes call `container.enrollment_service.*` for all CRUD and lifecycle operations |
| `src/nebula/services/enrollment_service.py` | `src/nebula/db/models.py` | SQLAlchemy session queries | WIRED | DeploymentModel and EnrollmentTokenModel queried throughout; `.with_for_update()` on EnrollmentTokenModel for atomic consumption |
| `src/nebula/core/container.py` | `src/nebula/services/enrollment_service.py` | DI registration | WIRED | `self.enrollment_service = EnrollmentService(settings=settings, session_factory=create_session_factory(settings))` at line 32 |
| `src/nebula/core/container.py` | `src/nebula/services/gateway_enrollment_service.py` | DI registration | WIRED | `self.gateway_enrollment_service = GatewayEnrollmentService(...)` at line 36 |
| `src/nebula/main.py` | `src/nebula/services/gateway_enrollment_service.py` | lifespan enrollment check | WIRED | `if settings.enrollment_token:` block calls `container.gateway_enrollment_service.attempt_enrollment(settings.enrollment_token)` at lines 23-28 |
| `src/nebula/services/gateway_enrollment_service.py` | `POST /v1/enrollment/exchange` | httpx outbound POST | WIRED | `client.post(f"{self.settings.hosted_plane_url}/v1/enrollment/exchange", ...)` with injectable transport |
| `console/src/app/(console)/deployments/page.tsx` | `console/src/lib/admin-api.ts` | React Query + API functions | WIRED | listDeployments, createDeployment, revokeDeployment all imported and called in useQuery/useMutation hooks |
| `console/src/lib/admin-api.ts` | `/api/admin/deployments` | ADMIN_DEPLOYMENTS_ENDPOINT constant | WIRED | All deployment API functions use `ADMIN_DEPLOYMENTS_ENDPOINT` (= `/api/admin/deployments`) |
| `src/nebula/api/routes/enrollment.py` → `src/nebula/services/enrollment_service.py` | revoke/unlink | `enrollment_service.revoke_deployment` / `enrollment_service.unlink_deployment` | WIRED | Route handlers catch ValueError as 409, return None as 404 |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ENRL-01 | 07-01-PLAN.md | Operator can register a self-hosted Nebula deployment with the hosted control plane without manual database edits | SATISFIED | POST /v1/admin/deployments creates deployment slot via API; 4 integration tests cover slot creation, listing, token generation, and 409 guard; all pass |
| ENRL-02 | 07-02-PLAN.md | A self-hosted gateway can complete an explicit outbound-only linking flow using short-lived enrollment credentials and durable deployment-scoped credentials for steady-state communication | SATISFIED | Gateway startup hook detects NEBULA_ENROLLMENT_TOKEN, makes outbound POST to exchange endpoint, receives `nbdc_`-prefixed steady-state credential, stores in local_hosted_identity; 4 gateway tests cover exchange, no-token skip, failure non-fatal, already-enrolled skip; all pass |
| ENRL-03 | 07-03-PLAN.md | Operator can revoke, unlink, or relink a deployment without leaving duplicate or ghost active records in the hosted inventory | SATISFIED | revoke_deployment clears credentials immediately; unlink_deployment disconnects cleanly; relink via generate_enrollment_token resets state to pending and reuses same deployment_id; test_relink_preserves_single_record verifies no duplicate records; 6 lifecycle tests pass |

**Orphaned requirements:** None — all ENRL-01, ENRL-02, ENRL-03 are claimed in plan frontmatter and implemented.

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `tests/test_gateway_enrollment.py:60` | `asyncio.get_event_loop().run_until_complete(...)` | INFO — DeprecationWarning | Test-only; deprecated in Python 3.10+; does not affect runtime behavior. No functional impact. |
| `src/nebula/services/gateway_enrollment_service.py:96` | `logger.info("Sending first heartbeat (stub — Phase 8 delivers actual heartbeat implementation)")` | INFO — intentional stub | Documented in SUMMARY.md as known; Phase 8 delivers actual heartbeat. Gateway serving and enrollment are fully functional. |

No blockers. No placeholders in business logic paths. All stubs are either test utilities or explicitly deferred to Phase 8.

---

### Human Verification Required

The following items require human testing in a running console.

#### 1. Console Deployment Page — Empty State

**Test:** Start gateway (`make run`) and console (`make console-dev`), navigate to http://localhost:3000/deployments
**Expected:** Empty state shows "No deployments linked" heading with a "Create deployment slot" CTA button
**Why human:** Visual layout, empty state copy, and button placement require browser rendering

#### 2. Create Slot + Token Reveal Dialog

**Test:** Click "Create deployment slot", fill in display_name="test-gw-1" and environment="development", submit
**Expected:** EnrollmentTokenRevealDialog opens immediately (no second click required) showing: token starting with `nbet_` in a dark code slab, NEBULA_ENROLLMENT_TOKEN env var instruction block, "This token will not be shown again" disclosure, and a "Copy token" button that toggles to "Copied" for 2 seconds after clicking
**Why human:** Show-once UX, clipboard API, and dialog presentation require live browser

#### 3. Deployment Table + Pending Status Badge

**Test:** Close the dialog, observe the table
**Expected:** Row appears with an amber "Pending enrollment" badge, correct display name
**Why human:** Badge color rendering and table row structure require visual confirmation

#### 4. Detail Drawer + Trust Boundary Reminder

**Test:** Click the deployment row
**Expected:** Detail drawer opens on the right panel showing UUID in Fira Code font, status badge, created date, and the trust boundary reminder "Linking is outbound-only. The hosted plane receives metadata only..."
**Why human:** Split-panel layout, drawer animation, font rendering need live browser

#### 5. Active State Actions + Revoke Dialog

**Test:** Manually activate a deployment via `POST /v1/enrollment/exchange` with a valid token, refresh the console
**Expected:** Row shows sky-blue "Active" badge; detail drawer shows "Unlink" (secondary) and "Revoke" (pink-700) action buttons. Clicking "Revoke" opens RevokeConfirmationDialog with "Revoke deployment" in pink-700 and "Keep deployment" dismiss button
**Why human:** State-conditional UI logic and confirmation dialog UX require live browser

---

### Gaps Summary

No gaps. All 12 must-haves are verified at the artifact, substantive, and wiring levels. All 17 automated tests pass. TypeScript compiles clean. The phase goal is achieved: operators can register deployments, gateways can link via outbound enrollment exchange, and the full lifecycle (revoke/unlink/relink) is implemented with no duplicate records.

The only outstanding items are human visual verification of the console UI, which requires a running browser — not indicators of missing implementation.

---

_Verified: 2026-03-21T23:30:00Z_
_Verifier: Claude (gsd-verifier)_
