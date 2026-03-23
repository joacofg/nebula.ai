---
phase: 08-fleet-inventory-and-freshness-visibility
verified: 2026-03-22T20:34:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 8: Fleet Inventory and Freshness Visibility — Verification Report

**Phase Goal:** Fleet inventory page with heartbeat-based freshness indicators and dependency health visualization for each linked deployment.
**Verified:** 2026-03-22T20:34:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | POST /v1/heartbeat updates last_seen_at, nebula_version, and capability_flags on the deployment record | VERIFIED | `heartbeat_ingest_service.py` record_heartbeat() writes all three fields plus dependency_summary_json on session.commit() |
| 2 | GET /v1/admin/deployments returns last_seen_at, freshness_status, freshness_reason, and dependency_summary for each deployment | VERIFIED | `enrollment_service.py` _to_record() calls compute_freshness() and populates all four fields on every list/get response |
| 3 | Freshness is computed on-read from last_seen_at using connected/degraded/stale/offline thresholds | VERIFIED | compute_freshness() in heartbeat_ingest_service.py: <=10min=connected, <=30min=degraded, <=1hr=stale, >1hr=offline |
| 4 | Pending deployments return null freshness (not a false freshness state) | VERIFIED | compute_freshness(None) returns (None, None); DeploymentRecord.freshness_status is str \| None |
| 5 | Gateway sends heartbeats outbound every 5 minutes using the deployment credential | VERIFIED | HeartbeatService._loop() sleeps HEARTBEAT_INTERVAL_SECONDS=300 then calls _send_once(); started in main.py lifespan |
| 6 | Heartbeat failure logs warning and retries without disrupting gateway | VERIFIED | _send_once() wraps POST in except Exception: logger.warning(…) — never raises (D-05) |
| 7 | Fleet table shows Name, Environment, Freshness, Version, and Last Seen columns | VERIFIED | deployment-table.tsx thead contains all five headers; old Status and Enrolled headers removed |
| 8 | Deployment detail drawer shows freshness section, dependency health pills, trust-boundary card, and enrollment state | VERIFIED | deployment-detail-drawer.tsx: Freshness → Identity (with DeploymentStatusBadge) → Dependencies → TrustBoundaryCard → Lifecycle |
| 9 | Capability flags display as chips in detail drawer | VERIFIED | deployment-detail-drawer.tsx lines 104–117: capability_flags.map() renders monospace rounded chips in Identity section |

**Score:** 9/9 truths verified

---

## Required Artifacts

### Plan 08-01 Artifacts

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `src/nebula/models/heartbeat.py` | HeartbeatRequest and HeartbeatResponse Pydantic models | VERIFIED | 15 lines; HeartbeatRequest has nebula_version, capability_flags, dependency_summary; no freshness_status (D-07 compliant) |
| `src/nebula/services/heartbeat_ingest_service.py` | Heartbeat recording and freshness computation | VERIFIED | 81 lines; HeartbeatIngestService + compute_freshness with D-08 thresholds; timezone normalization for SQLite |
| `src/nebula/api/routes/heartbeat.py` | POST /v1/heartbeat with deployment credential auth | VERIFIED | 26 lines; reads X-Nebula-Deployment-Credential header, returns 401 on failure, no require_admin |
| `migrations/versions/20260322_0003_last_seen_at.py` | DB migration adding last_seen_at and dependency_summary_json | VERIFIED | Idempotent guard with inspector.get_columns(); down_revision=20260321_0002 |

### Plan 08-02 Artifacts

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `src/nebula/services/heartbeat_service.py` | Gateway-side background heartbeat sender | VERIFIED | 108 lines; start/stop/loop/_send_once; HEARTBEAT_INTERVAL_SECONDS=300; all exceptions caught |
| `tests/test_heartbeat_api.py` | Integration tests for heartbeat endpoint | VERIFIED | 7 tests covering valid/invalid/missing credential, last_seen_at update, freshness_status, capability_flags, dependency_summary |
| `tests/test_freshness.py` | Unit tests for freshness calculation | VERIFIED | 9 tests covering None, connected, degraded, stale, offline, clock skew, boundary conditions, D-09 reason format |

### Plan 08-03 Artifacts

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `console/src/lib/freshness.ts` | formatRelativeTime and getFreshnessStyle helpers | VERIFIED | Exports both functions; color map: connected=emerald, degraded=amber, stale=orange, offline=rose, null=amber |
| `console/src/components/deployments/freshness-badge.tsx` | FreshnessBadge with 5 states | VERIFIED | 20 lines; uses getFreshnessStyle; base class matches DeploymentStatusBadge exactly |
| `console/src/components/deployments/dependency-health-pills.tsx` | DependencyHealthPills compact pill row | VERIFIED | 57 lines; healthy=emerald-500, degraded=amber-500, unavailable=rose-500; null renders "No data reported" |
| `console/src/components/deployments/deployment-table.tsx` | Fleet table with freshness/version/last-seen | VERIFIED | 95 lines; FreshnessBadge + formatRelativeTime wired; opacity-75/opacity-60 for stale/offline rows |
| `console/src/components/deployments/deployment-detail-drawer.tsx` | Detail drawer with all sections | VERIFIED | 181 lines; FreshnessBadge, DependencyHealthPills, TrustBoundaryCard, DeploymentStatusBadge all imported and rendered |
| `console/src/components/deployments/freshness-badge.test.tsx` | FreshnessBadge tests | VERIFIED | 7 tests; all 4 statuses + null ("Awaiting enrollment") + color class assertions |
| `console/src/components/deployments/deployment-table.test.tsx` | DeploymentTable tests | VERIFIED | 7 tests; column headers, badge content, version string, empty state |

---

## Key Link Verification

### Plan 08-01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `heartbeat.py` (route) | `heartbeat_ingest_service.py` | container.heartbeat_ingest_service.record_heartbeat() | WIRED | Line 14: `container.heartbeat_ingest_service.record_heartbeat(…)` |
| `enrollment_service.py` | `heartbeat_ingest_service.py` | _to_record() calls compute_freshness() | WIRED | Line 18 import + line 192 call confirmed |
| `heartbeat_ingest_service.py` | `db/models.py` | DeploymentModel.last_seen_at update | WIRED | Lines 74–78: deployment.last_seen_at, nebula_version, capability_flags_json, dependency_summary_json all written |

### Plan 08-02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `heartbeat_service.py` | `heartbeat.py` (route) | outbound POST /v1/heartbeat | WIRED | _send_once() POSTs to `{hosted_plane_url}/v1/heartbeat` with X-Nebula-Deployment-Credential header |
| `main.py` | `heartbeat_service.py` | lifespan start/stop | WIRED | Line 38: container.heartbeat_service.start(); container shutdown calls await self.heartbeat_service.stop() |

### Plan 08-03 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `deployment-table.tsx` | `freshness-badge.tsx` | import and render FreshnessBadge | WIRED | Line 2 import; line 77: `<FreshnessBadge status={deployment.freshness_status} />` |
| `deployment-detail-drawer.tsx` | `dependency-health-pills.tsx` | import and render DependencyHealthPills | WIRED | Line 8 import; line 140: `<DependencyHealthPills summary={deployment.dependency_summary} />` |
| `deployment-detail-drawer.tsx` | `trust-boundary-card.tsx` | import and render TrustBoundaryCard | WIRED | Line 9 import; line 145: `<TrustBoundaryCard />` |

---

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| INVT-01 | 08-01, 08-02, 08-03 | Display deployment identity, environment, Nebula version, registration time, and last-seen time | SATISFIED | deployment-table.tsx shows Name/Environment/Version/Last Seen; GET /v1/admin/deployments returns all fields including last_seen_at; 7 API integration tests prove updates land in GET response |
| INVT-02 | 08-01, 08-02, 08-03 | Show freshness with connected/degraded/stale/offline semantics and reason codes that do not overstate health | SATISFIED | compute_freshness() implements exact D-08 thresholds; reason codes are time-based only (D-09 compliant — no "healthy/running/stable"); FreshnessBadge renders all four statuses plus "Awaiting enrollment" for null |
| INVT-04 | 08-01, 08-02, 08-03 | Deployment reports capability and version metadata | SATISFIED | HeartbeatRequest carries nebula_version and capability_flags; record_heartbeat() persists both to DB; capability_flags rendered as monospace chips in detail drawer; test_heartbeat_updates_capability_flags confirms round-trip |

No orphaned requirements: REQUIREMENTS.md traceability table assigns INVT-01, INVT-02, INVT-04 to Phase 8, and all three are claimed by plans 08-01/02/03. INVT-03 is assigned to Phase 10 — not a Phase 8 obligation.

---

## Anti-Patterns Found

None detected across all phase-modified files.

Scanned:
- `src/nebula/models/heartbeat.py` — no stubs
- `src/nebula/services/heartbeat_ingest_service.py` — no stubs
- `src/nebula/api/routes/heartbeat.py` — no stubs
- `src/nebula/services/heartbeat_service.py` — no stubs
- `console/src/lib/freshness.ts` — no stubs
- `console/src/components/deployments/freshness-badge.tsx` — no stubs
- `console/src/components/deployments/dependency-health-pills.tsx` — no stubs
- `console/src/components/deployments/deployment-table.tsx` — no stubs
- `console/src/components/deployments/deployment-detail-drawer.tsx` — no stubs

---

## Test Suite Status

| Suite | Result |
|-------|--------|
| `pytest tests/test_freshness.py tests/test_heartbeat_api.py` | 16 passed |
| `pytest` (full backend) | 91 passed, 0 failed |
| `npm --prefix console run test -- --run` (full console) | 65 passed (24 test files) |

---

## Human Verification Required

### 1. Visual fleet inventory inspection

**Test:** Start `make console-dev` + `make run`. Navigate to `/deployments`.
**Expected:** Fleet table shows 5 columns (Name, Environment, Freshness, Version, Last Seen). Click a row to open drawer. Verify drawer order: Freshness section, Identity (with enrollment state badge and capability chips), Dependencies, Trust Boundary card, Lifecycle actions.
**Why human:** Row opacity dimming (stale=opacity-75, offline=opacity-60) and color correctness of FreshnessBadge (emerald/amber/orange/rose) require visual inspection against active deployment data. Automated tests cover rendering but not visual fidelity.

---

## Gaps Summary

No gaps. All automated checks passed, all truths verified, all artifacts substantive and wired, all requirements satisfied, test suites green.

---

_Verified: 2026-03-22T20:34:00Z_
_Verifier: Claude (gsd-verifier)_
