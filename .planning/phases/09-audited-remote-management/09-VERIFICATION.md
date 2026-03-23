---
phase: 09-audited-remote-management
verified: 2026-03-23T00:30:09Z
status: human_needed
score: 11/11 must-haves verified
human_verification:
  - test: "Hosted drawer queue flow in a running console"
    expected: "An active, connected deployment with `remote_credential_rotation` support shows the rotate card, requires a note, confirms intent, queues one action, and renders the new history row."
    why_human: "Automated tests cover component logic and API wiring, but not full browser UX, styling, or operator clarity in the live console."
  - test: "End-to-end hosted-to-gateway credential rotation against a live linked deployment"
    expected: "The hosted plane queues one rotation, the gateway polls outbound, applies only the hosted-link credential change, old deployment credential stops authenticating, and the new credential succeeds."
    why_human: "This crosses real process boundaries and validates the trust-boundary behavior in a live environment rather than in-process test transports."
---

# Phase 9: Audited Remote Management Verification Report

**Phase Goal:** The hosted plane proves limited management value through one safe remote action that is pulled outbound and enforced locally.
**Verified:** 2026-03-23T00:30:09Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Hosted admin API can queue exactly one allowlisted remote action named `rotate_deployment_credential` for an active linked deployment | ✓ VERIFIED | `queue_rotate_deployment_credential()` validates active state and action type in `src/nebula/services/enrollment_service.py`; admin route exposed in `src/nebula/api/routes/admin.py`; covered by `tests/test_remote_management_api.py::test_queue_rotate_credential_returns_201_for_active_deployment`. |
| 2 | Queueing a duplicate live rotation action returns the existing queued or `in_progress` record instead of creating a second one | ✓ VERIFIED | Existing live row is selected `FOR UPDATE` and returned in `src/nebula/services/enrollment_service.py`; guarded by partial unique index `uq_remote_actions_live`; covered by `tests/test_remote_management_api.py::test_queue_rotate_credential_returns_existing_live_action`. |
| 3 | Each queued action persists operator note, requested_at, expires_at, and status for durable audit history | ✓ VERIFIED | Persisted in `DeploymentRemoteActionModel` and migration `migrations/versions/20260322_0005_remote_actions.py`; serialized by `RemoteActionRecord`; exercised by queue/history tests in `tests/test_remote_management_api.py`. |
| 4 | A linked deployment polls outbound for queued remote actions using its existing deployment credential | ✓ VERIFIED | Poll endpoint authenticates `X-Nebula-Deployment-Credential` in `src/nebula/api/routes/remote_management.py`; gateway polls `/v1/remote-actions/poll` in `src/nebula/services/remote_management_service.py`; covered by `tests/test_remote_management_service.py::test_poll_valid_credential_returns_next_queued_action_and_marks_in_progress`. |
| 5 | Local configuration and allowlist checks decide whether a queued action is applied or failed closed | ✓ VERIFIED | `_authorize()` checks local identity and `remote_management_allowed_actions` in `src/nebula/services/remote_management_service.py`; unauthorized actions complete as failed; covered by `tests/test_remote_management_service.py::test_allowlist_failure_completes_action_as_failed_with_unauthorized_local_policy`. |
| 6 | Applying `rotate_deployment_credential` updates the local hosted-link credential and the hosted-side deployment credential without touching serving-path policy or provider state | ✓ VERIFIED | `complete_remote_action()` rotates only deployment credential hash/prefix in `src/nebula/services/enrollment_service.py`; `replace_deployment_credential()` updates local hosted identity in `src/nebula/services/gateway_enrollment_service.py`; no policy/provider services are mutated on this path; covered by `tests/test_remote_management_service.py::test_successful_rotation_returns_new_credential_and_follow_up_poll_accepts_it`. |
| 7 | Queued actions record terminal `applied` or `failed` outcomes with stable failure reasons | ✓ VERIFIED | Completion flow writes `applied`, `failed`, `invalid_state`, `apply_error`, and `unauthorized_local_policy` outcomes in `src/nebula/services/enrollment_service.py` and `src/nebula/services/remote_management_service.py`; covered by service tests for failed and successful completion. |
| 8 | Expired queued or `in_progress` actions become failed with reason `expired` and remain visible in audit history | ✓ VERIFIED | `_expire_remote_actions()` marks live expired rows failed with `failure_reason=\"expired\"` in `src/nebula/services/enrollment_service.py`; covered by `tests/test_remote_management_audit.py::test_expired_queued_and_in_progress_actions_fail_with_expired_reason`. |
| 9 | Deployment records expose queued/applied/failed summary counts plus `last_action_at` for hosted visibility | ✓ VERIFIED | `_build_remote_action_summary()` projects `HostedRemoteActionSummary` into `DeploymentRecord.remote_action_summary` in `src/nebula/services/enrollment_service.py`; schema present in `src/nebula/models/hosted_contract.py`; covered by `tests/test_remote_management_audit.py::test_list_and_get_deployment_project_remote_action_summary_counts`. |
| 10 | The deployment detail drawer shows a single rotate-credential action surface with required note entry and recent history | ✓ VERIFIED | `RemoteActionCard` renders the rotate workflow and history in `console/src/components/deployments/remote-action-card.tsx`; drawer integration in `console/src/components/deployments/deployment-detail-drawer.tsx`; covered by `console/src/components/deployments/remote-action-card.test.tsx`. |
| 11 | The hosted UI fails closed for revoked, unlinked, unsupported, stale, or offline deployments | ✓ VERIFIED | `getDisabledReason()` enforces fail-closed gating in `console/src/components/deployments/remote-action-card.tsx`; covered by `console/src/components/deployments/remote-action-card.test.tsx::it(\"fails closed...\")`. |

**Score:** 11/11 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/nebula/models/deployment.py` | Remote-action contracts and deployment summary fields | ✓ VERIFIED | Defines `RemoteActionType`, `RemoteActionStatus`, queue/poll/completion models, and `DeploymentRecord.remote_action_summary`. |
| `src/nebula/db/models.py` | Hosted queue/audit ORM model | ✓ VERIFIED | `DeploymentRemoteActionModel` exists with required columns and partial unique live-action index metadata. |
| `migrations/versions/20260322_0005_remote_actions.py` | Durable queue table and uniqueness guard | ✓ VERIFIED | Creates `deployment_remote_actions` and idempotent `uq_remote_actions_live` index. |
| `tests/test_remote_management_api.py` | Hosted queue/history contract coverage | ✓ VERIFIED | 7 tests passed. |
| `src/nebula/services/enrollment_service.py` | Hosted queue, claim, complete, expiry, and summary logic | ✓ VERIFIED | Contains queue, poll claim, completion, expiry, and projection methods used by API routes. |
| `src/nebula/api/routes/admin.py` | Hosted admin queue/history endpoints | ✓ VERIFIED | Queue and history routes call `EnrollmentService`. |
| `src/nebula/services/remote_management_service.py` | Gateway poll/apply/local-authorization orchestration | ✓ VERIFIED | Polls outbound, authorizes locally, completes hosted actions, rotates local credential. |
| `src/nebula/api/routes/remote_management.py` | Deployment-authenticated poll/complete endpoints | ✓ VERIFIED | Endpoints exist and validate deployment credential. |
| `src/nebula/core/config.py` | Remote-management settings | ✓ VERIFIED | Exposes enablement, allowlist, and poll interval settings. |
| `tests/test_remote_management_service.py` | Poll/apply/fail-closed integration coverage | ✓ VERIFIED | 5 tests passed. |
| `tests/test_remote_management_audit.py` | Expiry and summary regression coverage | ✓ VERIFIED | 3 tests passed. |
| `console/src/lib/admin-api.ts` | Remote-action client types and admin methods | ✓ VERIFIED | Exposes `RemoteActionRecord`, `RemoteActionSummary`, `queueRotateDeploymentCredential()`, and `listRemoteActions()`. |
| `console/src/components/deployments/remote-action-card.tsx` | Hosted action/history UI | ✓ VERIFIED | Renders required note, confirmation CTA, and recent history with fail-closed gating. |
| `console/src/components/deployments/deployment-detail-drawer.tsx` | Drawer integration for remote action surface | ✓ VERIFIED | Renders `RemoteActionCard` above lifecycle actions. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/nebula/api/routes/admin.py` | `src/nebula/services/enrollment_service.py` | `queue_rotate_deployment_credential` and `list_remote_actions` | WIRED | Admin endpoints directly invoke service methods and map expected 404/409/422 errors. |
| `src/nebula/services/enrollment_service.py` | `src/nebula/db/models.py` | `DeploymentRemoteActionModel` row creation and live-action lookup | WIRED | Queue, claim, completion, expiry, and summaries all query/update `DeploymentRemoteActionModel`. |
| `migrations/versions/20260322_0005_remote_actions.py` | `src/nebula/db/models.py` | `deployment_remote_actions` table and `uq_remote_actions_live` index | WIRED | Migration schema matches ORM table/index names and live-action predicate. |
| `src/nebula/services/remote_management_service.py` | `src/nebula/api/routes/remote_management.py` | Poll and completion HTTP calls with `X-Nebula-Deployment-Credential` | WIRED | Service calls `/remote-actions/poll` and `/{action_id}/complete`; routes authenticate same header. |
| `src/nebula/services/remote_management_service.py` | `src/nebula/services/gateway_enrollment_service.py` | `replace_deployment_credential` after applied completion | WIRED | Successful completion triggers local credential replacement only after hosted acknowledgement. |
| `src/nebula/main.py` | `src/nebula/services/remote_management_service.py` | Lifespan start and stop | WIRED | `container.remote_management_service.start()` is called in lifespan and stopped via container shutdown. |
| `src/nebula/services/enrollment_service.py` | `src/nebula/models/hosted_contract.py` | `remote_action_summary` projection | WIRED | `_build_remote_action_summary()` returns `HostedRemoteActionSummary`, then `_to_record()` serializes it into deployment responses. |
| `console/src/components/deployments/deployment-detail-drawer.tsx` | `console/src/components/deployments/remote-action-card.tsx` | Drawer renders `RemoteActionCard` | WIRED | Direct import and render confirmed. |
| `console/src/components/deployments/remote-action-card.tsx` | `console/src/lib/admin-api.ts` | `queueRotateDeploymentCredential` and `listRemoteActions` | WIRED | Card loads history on mount and queues rotation through admin API client methods. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| RMGT-01 | `09-01-PLAN.md`, `09-03-PLAN.md` | Hosted control plane can queue at least one allowlisted, non-serving-impacting remote-management action for a linked deployment. | ✓ SATISFIED | Hosted queue endpoint and durable action history exist; UI exposes only the single rotate-credential action with note capture and fail-closed gating; backend and console tests passed. |
| RMGT-02 | `09-02-PLAN.md` | A linked deployment pulls remote-management actions outbound, applies them only after local authorization checks, and records auditable queued, applied, or failed outcomes. | ✓ SATISFIED | Poll/complete endpoints, gateway poller, local allowlist enforcement, completion outcomes, and rotation handshake are implemented and covered by `tests/test_remote_management_service.py`. |
| RMGT-03 | `09-01-PLAN.md`, `09-02-PLAN.md`, `09-03-PLAN.md` | Remote-management actions are TTL-bound, idempotent, and prevented from directly mutating local runtime policy or provider credentials from the hosted plane. | ✓ SATISFIED | TTL expiry, duplicate-live-action suppression, partial unique index, and a rotation flow limited to deployment hosted-link credentials are implemented and covered by API/service/audit tests. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| None | - | No blocking TODO/placeholder/stub patterns found in phase-touched files. | - | No blocker identified from static anti-pattern scan. |

### Human Verification Required

### 1. Hosted Drawer Queue Flow

**Test:** Open a linked deployment in the running hosted console and use the rotate-credential card.
**Expected:** The card appears only for supported deployments, requires a 1-280 character note, asks for confirmation, queues one rotation, and shows the action in recent history.
**Why human:** Browser rendering, copy clarity, and operator trust-boundary comprehension are not fully verifiable from component tests alone.

### 2. Live Hosted-to-Gateway Rotation

**Test:** Against a real linked gateway, queue one rotation from the hosted plane and observe the gateway poll/apply path.
**Expected:** The gateway pulls the action outbound, rotates only the hosted-link deployment credential, the old credential stops authenticating, and the new credential works for subsequent polls/heartbeats.
**Why human:** In-process tests validate logic, but not a live multi-process deployment boundary or operational timing.

### Gaps Summary

No implementation gaps were found in the codebase for the declared Phase 9 must-haves. All automated backend and console checks passed, and all requirement IDs declared in Phase 9 plans are accounted for in `REQUIREMENTS.md`. Remaining work is human-only verification of live UI behavior and end-to-end operator flow.

---

_Verified: 2026-03-23T00:30:09Z_
_Verifier: Claude (gsd-verifier)_
