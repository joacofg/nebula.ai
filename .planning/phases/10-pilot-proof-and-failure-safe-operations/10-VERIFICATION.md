---
phase: 10-pilot-proof-and-failure-safe-operations
verified: 2026-03-23T16:51:03Z
status: passed
score: 8/8 must-haves verified
---

# Phase 10: Pilot Proof and Failure-Safe Operations Verification Report

**Phase Goal:** Validate outage-safe behavior and ship the pilot-ready docs and demo story.
**Verified:** 2026-03-23T16:51:03Z
**Status:** passed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Hosted-control-plane transport failures do not break `POST /v1/chat/completions` for a linked deployment | ✓ VERIFIED | `tests/test_phase10_outage_safety.py` drives heartbeat and remote-management failures, then asserts `POST /v1/chat/completions` returns 200 with `X-Nebula-Route-Target=local` and `X-Nebula-Fallback-Used=false` at lines 123-153. |
| 2 | Hosted-control-plane transport failures do not turn `/health/ready` into a serving outage when only hosted visibility is degraded | ✓ VERIFIED | The same outage test asserts `/health/ready` stays 200 and status remains `ready` or `degraded` in `tests/test_phase10_outage_safety.py` lines 145-151; `src/nebula/main.py` lines 68-73 only returns 503 for `not_ready`. |
| 3 | Hosted deployment records can become stale or offline while the local gateway still serves requests successfully | ✓ VERIFIED | `tests/test_phase10_outage_safety.py` lines 157-200 mutates `last_seen_at`, verifies `freshness_status` becomes `stale` then `offline`, and confirms chat completions still return 200 after each state change. |
| 4 | Hosted heartbeat and remote-management loops fail closed with warnings instead of propagating fatal exceptions into the gateway | ✓ VERIFIED | `src/nebula/services/heartbeat_service.py` line 98 logs `Heartbeat failed:`; `src/nebula/services/remote_management_service.py` line 101 logs `Remote management poll/apply failed:`; the outage test asserts both warning substrings in `caplog` at `tests/test_phase10_outage_safety.py` lines 152-153. |
| 5 | Pilot-facing docs explain the hosted onboarding flow as outbound-only enrollment plus deployment-scoped steady-state credentials | ✓ VERIFIED | `docs/self-hosting.md` lines 121-128 defines the hosted pilot workflow, and `docs/demo-script.md` lines 91-98 plus `docs/pilot-checklist.md` lines 35-41 repeat the enrollment-token and deployment-scoped credential story. |
| 6 | Pilot-facing docs and the public trust-boundary page state that hosted outage degrades visibility only and does not break local serving | ✓ VERIFIED | `console/src/app/trust-boundary/page.tsx` lines 24-27 renders the exact outage sentence; `console/src/lib/hosted-contract.ts` lines 66-71 provides the copy; docs repeat the same claim in `docs/self-hosting.md` line 125, `docs/demo-script.md` lines 95-98, and `docs/pilot-checklist.md` line 39. |
| 7 | Pilot-facing docs state that hosted remote management is limited to one audited `rotate_deployment_credential` action and fails closed | ✓ VERIFIED | `console/src/lib/hosted-contract.ts` lines 69-71 defines the limit and fail-closed wording; `docs/self-hosting.md` line 126, `docs/demo-script.md` line 96, and `docs/pilot-checklist.md` line 40 restate it. |
| 8 | The trust-boundary page and the repo docs repeat the same metadata-only contract without drift | ✓ VERIFIED | `console/src/lib/hosted-contract.ts` remains the canonical UI source, consumed by `console/src/app/trust-boundary/page.tsx` lines 8-66; Vitest coverage passed for both `console/src/lib/hosted-contract.test.ts` and `console/src/app/trust-boundary/page.test.tsx`, and docs grep checks found the same bounded wording across all pilot docs. |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `tests/test_phase10_outage_safety.py` | Dedicated outage-safety integration coverage for serving continuity, readiness, and stale/offline hosted visibility | ✓ VERIFIED | Exists, contains both required tests plus warning assertions, and passed `.venv/bin/pytest tests/test_phase10_outage_safety.py -x`. |
| `tests/test_remote_management_service.py` | Mixed hosted/local failure regression coverage for remote-management no-op and fail-closed behavior | ✓ VERIFIED | Exists, contains both required tests and invalid-state assertion, and passed `.venv/bin/pytest tests/test_remote_management_service.py -k "hosted or outage or stale or invalid_state" -x`. |
| `console/src/lib/hosted-contract.ts` | Canonical pilot trust-boundary copy for onboarding, outage behavior, and remote-management limits | ✓ VERIFIED | Exists, exports `trustBoundaryCopy` and `getHostedContractContent`, carries exact pilot strings, and is consumed by the public page/tests. |
| `console/src/app/trust-boundary/page.tsx` | Public trust-boundary page with pilot-ready hosted narrative | ✓ VERIFIED | Exists, imports `getHostedContractContent`, renders the outage statement and the three new pilot sections, and is covered by page tests. |
| `docs/self-hosting.md` | Self-hosted onboarding and hosted-outage expectations | ✓ VERIFIED | Exists, includes `Hosted pilot workflow` with all required points and schema reference. |
| `docs/demo-script.md` | Pilot walkthrough and talk track for hosted onboarding, safety limits, and outage behavior | ✓ VERIFIED | Exists, includes `Hosted pilot proof` section with exact required statements. |
| `docs/pilot-checklist.md` | Presenter checklist for the exact hosted trust-boundary narrative | ✓ VERIFIED | Exists, includes required trust-boundary checklist items and the updated out-of-scope reminder. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `tests/test_phase10_outage_safety.py` | `src/nebula/services/heartbeat_service.py` | Mock transport failures against heartbeat path and warning assertion | ✓ VERIFIED | Test swaps `heartbeat_service._http_transport`, calls `_send_once()`, and asserts `Heartbeat failed:`; runtime warning exists in `heartbeat_service.py`. |
| `tests/test_phase10_outage_safety.py` | `src/nebula/main.py` | Assertions against `/v1/chat/completions` and `/health/ready` on the same app instance | ✓ VERIFIED | The test uses a single ASGI app/client instance for both endpoints; `main.py` exposes `/health/ready` with 200 on `ready`/`degraded`. |
| `tests/test_remote_management_service.py` | `src/nebula/services/remote_management_service.py` | `poll_and_apply_once()` remains non-fatal on hosted transport failure | ✓ VERIFIED | Test injects `httpx.MockTransport`, calls `poll_and_apply_once()`, and verifies queued action remains untouched while chat still serves; runtime warning exists in service code. |
| `console/src/app/trust-boundary/page.tsx` | `console/src/lib/hosted-contract.ts` | Schema-backed copy rendered on the public trust page | ✓ VERIFIED | Page imports `getHostedContractContent()` and renders `copy.pilotIntro`, `copy.onboardingBody`, `copy.outageBody`, and `copy.remoteLimitsBody`. |
| `docs/self-hosting.md` | `docs/hosted-default-export.schema.json` | Default-export contract reference | ✓ VERIFIED | The doc explicitly links to `docs/hosted-default-export.schema.json` and describes the metadata-only default export contract. |
| `docs/demo-script.md` | `docs/pilot-checklist.md` | Shared wording for visibility-only behavior and remote-management limits | ✓ VERIFIED | Both docs repeat `stale or offline`, `rotate_deployment_credential`, and the metadata-and-intent/local-authority language. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `INVT-03` | `10-01-PLAN.md` | Loss of hosted control-plane connectivity does not break the self-hosted gateway's core serving path and is surfaced as degraded or stale hosted visibility instead of runtime failure. | ✓ SATISFIED | Pytest verification passed for outage-safety and remote-management hosted-outage cases; tests cover serving continuity, readiness continuity, stale/offline visibility, and warning-only failures. |
| `TRST-03` | `10-02-PLAN.md` | Docs and demo materials explain hybrid deployment onboarding, trust boundaries, remote-management safety limits, and hosted-control-plane outage behavior for pilot conversations. | ✓ SATISFIED | Vitest verification passed for the public page and content module; doc grep verification found the required pilot narrative in `docs/self-hosting.md`, `docs/demo-script.md`, and `docs/pilot-checklist.md`. |

No orphaned Phase 10 requirements were found in `.planning/REQUIREMENTS.md`; the phase is mapped only to `INVT-03` and `TRST-03`, and both IDs appear in the plan frontmatter.

### Anti-Patterns Found

No blocker, warning, or info anti-pattern matches were found in the phase files when scanned for TODO/FIXME/placeholder markers, empty returns, or stub handlers.

### Human Verification Required

None. The phase goal is covered by executable regression tests plus directly inspectable documentation and UI copy, and all declared automated checks passed.

### Gaps Summary

No gaps found. The outage-safe runtime contract is proven by tests against the actual app instance, and the pilot-facing trust-boundary narrative is present in the shipped page and repo docs with consistent wording.

---

_Verified: 2026-03-23T16:51:03Z_
_Verifier: Claude (gsd-verifier)_
