# Phase 8: Fleet Inventory and Freshness Visibility - Research

**Researched:** 2026-03-22
**Domain:** Heartbeat ingestion, freshness calculation, fleet inventory UI, capability display
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Heartbeat mechanism**
- D-01: Gateway sends heartbeats every 5 minutes to the hosted plane via outbound HTTP POST, following the same outbound-only pattern as enrollment exchange.
- D-02: Heartbeat payload is minimal: Nebula version, capability flags, and coarse dependency health summary (which local stores are healthy/degraded/unavailable). No raw usage data, no prompts, no ledger rows.
- D-03: Gateway updates its version and capability flags on every heartbeat, so a gateway upgrade reflects in the hosted plane without re-enrollment.
- D-04: Heartbeat runs as a background asyncio task in the gateway's event loop, started during lifespan, cancelled on shutdown. Matches existing enrollment startup hook pattern.
- D-05: On heartbeat failure (network issue, hosted plane down), gateway logs a warning and retries at the next scheduled interval. No backoff, no queuing, no retry storm. Hosted outage = stale visibility, not gateway disruption.
- D-06: Gateway authenticates heartbeats using the steady-state deployment credential from enrollment (same credential stored in local_hosted_identity).

**Freshness thresholds**
- D-07: Hosted plane calculates freshness from `last_seen_at` timestamp — gateway cannot self-report freshness. Single source of truth for thresholds lives on the hosted side.
- D-08: Time windows: `connected` = heard within 10 minutes. `degraded` = 10-30 minutes since last heartbeat. `stale` = 30 minutes to 1 hour. `offline` = more than 1 hour since last heartbeat.
- D-09: Reason codes are time-based only: "Last heartbeat 3 minutes ago", "No heartbeat for 45 minutes", "No heartbeat since Mar 20 14:30". No inferred causes. Matches Phase 6 "truthful uncertainty over optimism" principle.
- D-10: Stale and offline deployments remain always visible in the fleet list with dimmed row styling and a colored freshness badge. Never hidden. Timestamps show relative "last seen X ago" text.

**Fleet inventory view**
- D-11: Fleet table columns: Name, Environment, Freshness (badge), Version, Last Seen. Enrollment state column moves from the table to the detail drawer. Replaces current "Status" column with Freshness.
- D-12: Deployment detail drawer layout: freshness section at top (freshness badge, reason text, last-seen timestamp), then identity section (name, ID, environment, version, capability chips), then dependency health, then trust-boundary disclosure card (from Phase 6), then lifecycle actions (revoke, unlink, relink) at bottom.
- D-13: Dependency health displays as compact colored pills: each dependency (PostgreSQL, Qdrant, Ollama) as a green/yellow/red pill. One row, glanceable. Matches existing compact console style.
- D-14: Pending (never-enrolled) deployments show "Awaiting enrollment" instead of a freshness badge. Freshness only applies to deployments that have completed enrollment at least once.

**Capability and compatibility**
- D-15: Gateway reports fixed capability flags based on its version and enabled features (e.g., `semantic_cache`, `premium_routing`, `local_provider`). No operator override. Hosted plane records what was reported.
- D-16: Capability flags displayed as small chips/tags in the deployment detail drawer.
- D-17: When a remote action targets a deployment that lacks the required capability, the action button is disabled with a tooltip: "This deployment does not support [action] (requires [capability])". Fail closed at the UI level — no request sent.
- D-18: No fleet-wide compatibility matrix for v2.0. Per-deployment capability display in the detail drawer is sufficient for the validation milestone.

### Claude's Discretion
- Heartbeat API endpoint path and exact request/response shape
- Exact heartbeat background task implementation (asyncio.create_task, sleep loop, cancellation)
- Freshness calculation implementation (computed property vs periodic job vs on-read)
- Database schema changes for heartbeat storage (new columns on deployment table vs separate heartbeat log)
- Exact UI component structure, spacing, and color values for freshness badges and dependency pills
- Error handling edge cases (e.g., clock skew between gateway and hosted plane)
- How `last_seen_at` is updated (upsert on heartbeat receive)

### Deferred Ideas (OUT OF SCOPE)
- Remote management actions, pull-based execution, and audit history — Phase 9
- Heartbeat history timeline or log in the detail drawer — future enhancement
- Fleet-wide compatibility matrix view — future enhancement for larger fleets
- Operator annotations or custom labels on deployments — future enhancement
- Diagnostic bundle upload or richer error reporting — future (requires explicit operator initiation per Phase 6 contract)
- Outage-safe serving validation and pilot docs — Phase 10
- Credential rotation mechanism — future phase
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INVT-01 | Hosted control plane can display deployment identity, environment label, Nebula version, registration time, and last-seen time for each linked deployment. | `DeploymentModel` already stores identity/env/version; `last_seen_at` needs a new column; `DeploymentRecord` needs extension; fleet table UI needs new columns. |
| INVT-02 | Hosted control plane shows deployment freshness using explicit connected, degraded, stale, or offline semantics with reason codes that do not overstate runtime health. | `FreshnessStatus` Literal type already exists in `hosted_contract.py`; thresholds locked in D-08; reason code format locked in D-09; freshness calculation is on-read (no periodic job needed). |
| INVT-04 | Deployment reports capability and version metadata so the hosted plane can show compatibility state and fail unsupported actions closed. | `capability_flags_json` already stored on `DeploymentModel`, updated on enrollment exchange; heartbeat updates it on each send (D-03); UI capability chips already exist in detail drawer; fail-closed tooltip pattern needed for Phase 9 actions. |
</phase_requirements>

---

## Summary

Phase 8 adds three interconnected capabilities: a heartbeat sender on the gateway side, a heartbeat ingest endpoint and `last_seen_at` update on the hosted side, and fleet inventory UI that surfaces the freshness and capability state the heartbeats populate.

The codebase is exceptionally well-prepared. `HostedDeploymentMetadata` in `hosted_contract.py` already defines `last_seen_at`, `freshness_status`, `freshness_reason`, `dependency_summary`, and `capability_flags`. The `DeploymentModel` ORM already stores `nebula_version` and `capability_flags_json`. The `GatewayEnrollmentService` already has the outbound httpx pattern the heartbeat sender will copy. The enrollment lifespan hook in `main.py` already shows the exact startup pattern for a background asyncio task. A first-heartbeat stub at line 94-97 of `gateway_enrollment_service.py` is explicitly waiting for this phase.

The three plans map cleanly: Plan 08-01 is backend-only (gateway heartbeat sender + hosted ingest endpoint + DB schema), Plan 08-02 is frontend-only (fleet table columns + detail drawer layout), Plan 08-03 is the integration layer (freshness calculation on-read + reason codes + capability fail-closed behavior that connects the backend data to UI semantics).

**Primary recommendation:** Add `last_seen_at` as a new column on `DeploymentModel` (not a separate heartbeat log), compute freshness on-read from `datetime.now(UTC) - last_seen_at`, return it in `DeploymentRecord` API responses, and extend existing console components rather than replacing them.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | already in project | Outbound heartbeat HTTP POST from gateway | Same client used for enrollment exchange; injectable transport for ASGI tests |
| SQLAlchemy | already in project | Add `last_seen_at` column to `DeploymentModel` | Already used for all ORM models |
| Alembic | already in project | Schema migration for `last_seen_at` column | All prior schema changes use Alembic migrations |
| asyncio | stdlib | Background heartbeat task loop | D-04 locks this; `asyncio.create_task` + sleep loop + cancellation on shutdown |
| Pydantic | already in project (v2) | Heartbeat request/response models | All API models use Pydantic |
| React Query (@tanstack/react-query) | already in console | Fleet data fetching + polling | All console data fetching uses this pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime (stdlib, UTC-aware) | stdlib | Freshness threshold calculation | D-07: hosted side computes freshness from `last_seen_at`; always `datetime.now(UTC)` |
| lucide-react | already in console | Icons for freshness states | Existing console icon library |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Single column `last_seen_at` on deployments | Separate heartbeat_log table | Log table enables heartbeat history but is out of scope (deferred); single column is sufficient for v2.0 and avoids JOIN overhead |
| On-read freshness calculation | Periodic background job | On-read is simpler, no state to manage, freshness is already computed at query time; periodic job would need its own failure handling |
| asyncio sleep loop | APScheduler / Celery | Sleep loop matches the existing gateway pattern and has zero new dependencies; scheduler frameworks are overkill for a single 5-minute task |

**Installation:** No new packages required. All dependencies are already present in the project.

---

## Architecture Patterns

### Recommended Project Structure for Phase 8

New files:
```
src/nebula/
├── services/
│   └── heartbeat_service.py      # Gateway-side: background task + outbound POST
│   └── heartbeat_ingest_service.py  # Hosted-side: record_heartbeat(), compute_freshness()
├── models/
│   └── heartbeat.py              # HeartbeatRequest / HeartbeatResponse Pydantic models
├── api/routes/
│   └── heartbeat.py              # POST /v1/heartbeat endpoint (deployment-credential auth)
migrations/versions/
└── 20260322_0003_last_seen_at.py # Add last_seen_at to deployments

console/src/
├── components/deployments/
│   └── freshness-badge.tsx           # FreshnessBadge component (new variant)
│   └── dependency-health-pills.tsx   # Dependency health row component
│   └── deployment-table.tsx          # Extended (columns: Name, Env, Freshness, Version, Last Seen)
│   └── deployment-detail-drawer.tsx  # Extended (freshness section, deps, trust-boundary card)
└── lib/
    └── admin-api.ts              # Extended with FreshnessStatus, last_seen_at types
    └── freshness.ts              # formatRelativeTime(), getFreshnessBadgeStyle() helpers
```

### Pattern 1: Gateway Heartbeat Background Task

**What:** asyncio task started in lifespan, runs a sleep loop, sends POST every 5 minutes, logs warning on failure, exits cleanly on cancellation.

**When to use:** D-04 locks this pattern. Match the enrollment startup hook structure in `main.py`.

**Example:**
```python
# src/nebula/services/heartbeat_service.py
import asyncio
import logging
from datetime import UTC, datetime

import httpx

from nebula.core.config import Settings
from nebula.db.models import LocalHostedIdentityModel
from nebula.models.heartbeat import HeartbeatRequest

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_SECONDS = 300  # 5 minutes (D-01)


class HeartbeatService:
    def __init__(
        self,
        settings: Settings,
        gateway_enrollment_service,  # provides get_local_identity()
        runtime_health_service,       # provides dependencies() for dep summary
        http_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._enrollment = gateway_enrollment_service
        self._health = runtime_health_service
        self._http_transport = http_transport
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            await self._send_once()

    async def _send_once(self) -> None:
        identity = self._enrollment.get_local_identity()
        if identity is None or self.settings.hosted_plane_url is None:
            return  # not enrolled — skip silently
        try:
            dep_summary = await self._health.dependencies()
            payload = HeartbeatRequest(
                nebula_version=_nebula_version(),
                capability_flags=["semantic_cache", "premium_routing"],
                dependency_summary=_summarize_deps(dep_summary),
            )
            client_kwargs: dict = {"timeout": 10.0}
            if self._http_transport is not None:
                client_kwargs["transport"] = self._http_transport
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.post(
                    f"{self.settings.hosted_plane_url}/v1/heartbeat",
                    json=payload.model_dump(),
                    headers={"X-Nebula-Deployment-Credential": identity.deployment_id},
                    # Note: actual auth header name TBD by implementer (Claude's discretion)
                )
                response.raise_for_status()
        except Exception as exc:
            logger.warning("Heartbeat failed: %s. Will retry at next interval.", exc)
            # D-05: no backoff, no queuing
```

### Pattern 2: Hosted Heartbeat Ingest Endpoint

**What:** `POST /v1/heartbeat` authenticated by deployment credential (hash comparison, same pattern as admin key auth). Updates `last_seen_at`, `nebula_version`, `capability_flags_json` on `DeploymentModel`.

**When to use:** Gateway-facing endpoint — no admin auth, deployment credential IS the authentication. Pattern mirrors `exchange_router` (no `require_admin`).

**Key implementation:**
```python
# src/nebula/api/routes/heartbeat.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from nebula.models.heartbeat import HeartbeatRequest, HeartbeatResponse

heartbeat_router = APIRouter(prefix="/heartbeat", tags=["heartbeat"])

@heartbeat_router.post("", response_model=HeartbeatResponse)
async def receive_heartbeat(
    request: Request,
    body: HeartbeatRequest,
) -> HeartbeatResponse:
    container = request.app.state.container
    # Authenticate via deployment credential in header
    credential = request.headers.get("X-Nebula-Deployment-Credential")
    result = container.heartbeat_ingest_service.record_heartbeat(
        raw_credential=credential,
        nebula_version=body.nebula_version,
        capability_flags=body.capability_flags,
        dependency_summary=body.dependency_summary,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or unknown deployment credential.")
    return HeartbeatResponse(acknowledged=True)
```

### Pattern 3: Freshness Calculation (On-Read)

**What:** Compute `freshness_status` and `freshness_reason` at read time from `last_seen_at`. No periodic background job.

**When to use:** Every call to `list_deployments()` and `get_deployment()` enriches the record before returning.

**Implementation:**
```python
# In enrollment_service.py _to_record() or a new helper
from datetime import UTC, datetime, timedelta
from nebula.models.hosted_contract import FreshnessStatus

CONNECTED_WINDOW = timedelta(minutes=10)    # D-08
DEGRADED_WINDOW  = timedelta(minutes=30)
STALE_WINDOW     = timedelta(hours=1)

def compute_freshness(last_seen_at: datetime | None) -> tuple[FreshnessStatus | None, str | None]:
    """Returns (status, reason). Returns (None, None) for never-enrolled deployments (D-14)."""
    if last_seen_at is None:
        return None, None  # pending, never sent heartbeat
    now = datetime.now(UTC)
    delta = now - last_seen_at
    if delta <= CONNECTED_WINDOW:
        return "connected", f"Last heartbeat {_human_delta(delta)} ago"
    elif delta <= DEGRADED_WINDOW:
        return "degraded", f"No heartbeat for {_human_delta(delta)}"
    elif delta <= STALE_WINDOW:
        return "stale", f"No heartbeat for {_human_delta(delta)}"
    else:
        return "offline", f"No heartbeat since {last_seen_at.strftime('%b %-d %H:%M')}"
```

### Pattern 4: DB Schema — Column on deployments Table

**What:** Add `last_seen_at` (nullable DateTime) directly on `DeploymentModel`. No separate heartbeat log table.

**When to use:** Sufficient for v2.0; avoids JOIN complexity; matches D-07 (single source of truth).

```python
# migrations/versions/20260322_0003_last_seen_at.py
def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("deployments")}
    if "last_seen_at" not in cols:
        op.add_column(
            "deployments",
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        )
```

### Pattern 5: Frontend Freshness Badge

**What:** New `FreshnessBadge` component extending the `DeploymentStatusBadge` pattern. Separate component because it has different semantics and styling (4 states vs enrollment states).

**Color semantics:**
| Status | Badge style | Row style |
|--------|------------|-----------|
| connected | `bg-emerald-50 text-emerald-700 border-emerald-200` | normal |
| degraded | `bg-amber-50 text-amber-700 border-amber-200` | normal |
| stale | `bg-orange-50 text-orange-700 border-orange-200` | dimmed (`opacity-75`) |
| offline | `bg-rose-50 text-rose-700 border-rose-200` | dimmed (`opacity-60`) |
| null (pending) | show "Awaiting enrollment" amber badge | normal |

**Pattern matches** existing `DeploymentStatusBadge` exactly:
```tsx
// console/src/components/deployments/freshness-badge.tsx
const FRESHNESS_STYLES: Record<FreshnessStatus, { className: string; label: string }> = {
  connected: { className: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "Connected" },
  degraded:  { className: "bg-amber-50 text-amber-700 border-amber-200",  label: "Degraded"  },
  stale:     { className: "bg-orange-50 text-orange-700 border-orange-200", label: "Stale"    },
  offline:   { className: "bg-rose-50 text-rose-700 border-rose-200",    label: "Offline"   },
};
```

### Pattern 6: Dependency Health Pills

**What:** Compact colored dot + name inline row for PostgreSQL, Qdrant, Ollama. One row in detail drawer.

**Pattern:**
```tsx
// console/src/components/deployments/dependency-health-pills.tsx
const STATUS_DOT: Record<string, string> = {
  healthy:     "bg-emerald-500",
  degraded:    "bg-amber-500",
  unavailable: "bg-rose-500",
};
// Renders: [• PostgreSQL] [• Qdrant] [• Ollama]  — color per status
```

### Anti-Patterns to Avoid

- **Freshness in gateway payload:** Gateway MUST NOT send a `freshness_status` field in the heartbeat. D-07 is absolute: hosted plane calculates freshness, gateway sends raw timestamps/data only.
- **Hiding stale/offline rows:** D-10 is explicit — they stay visible, just dimmed. Never filter them from the list.
- **Using `datetime.now()` without UTC:** All timestamps in this codebase use `datetime.now(UTC)`. Mixing naive datetimes will cause incorrect freshness calculations.
- **Replacing existing components:** `deployment-table.tsx` and `deployment-detail-drawer.tsx` are to be extended with new props/sections, not replaced. Existing enrollment functionality must remain intact.
- **Making heartbeat failure fatal:** D-05 explicitly: log warning + continue. Never `raise`, never block gateway startup.
- **Sending enrollment credential as plain text in heartbeat header:** Credential is verified by hash comparison on hosted side (same pattern as `credential_hash` on `DeploymentModel`). The credential IS sent over HTTPS for verification, same as the enrollment credential was used.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relative time formatting ("3 minutes ago") | Custom formatter | Simple Python `timedelta` formatting or JS `Intl.RelativeTimeFormat` | Already-available stdlib; no edge cases at 5-min heartbeat granularity |
| Dependency health aggregation | New health probe | Re-use `runtime_health_service.dependencies()` output | Already returns `{status: ready/degraded/unavailable}` per dependency; map to `HostedDependencySummary` |
| Credential authentication for heartbeat endpoint | New auth system | Hash comparison against `DeploymentModel.credential_hash` (same as enrollment) | Pattern already proven in `consume_enrollment_token`; SHA-256 of raw credential == stored hash |
| Background task retry logic | Exponential backoff queue | None — log and skip | D-05 explicitly prohibits queuing; stale visibility is the designed degradation mode |

**Key insight:** The dependency health system (`RuntimeHealthService`) already produces exactly the data shape `HostedDependencySummary` needs. Map `ready` → `healthy`, `degraded` → `degraded`, `not_ready` → `unavailable` when building the heartbeat payload.

---

## Common Pitfalls

### Pitfall 1: Clock Skew Between Gateway and Hosted Plane

**What goes wrong:** Gateway clock is ahead of hosted plane clock; `last_seen_at` is in the future; freshness calculation returns negative delta; `connected` is incorrectly returned for a stale deployment.

**Why it happens:** Servers in different environments, Docker containers with skewed clocks, test environments.

**How to avoid:** In `compute_freshness`, clamp `delta = max(delta, timedelta(0))` before threshold comparison. Log a warning if `last_seen_at > now`.

**Warning signs:** Freshness = "connected" for a deployment that hasn't sent a heartbeat in hours.

### Pitfall 2: DeploymentRecord Missing last_seen_at Before Schema Migration Runs

**What goes wrong:** `DeploymentModel` column added in Python ORM but migration hasn't run; SQLAlchemy maps `None` for all rows; freshness always appears as "Awaiting enrollment" for active deployments.

**Why it happens:** Test setup runs `configured_app()` which calls `_run_migrations()` — if the new migration file is missing, the column won't exist.

**How to avoid:** Create the migration file in the same plan as the ORM change. `configured_app()` in tests calls `alembic upgrade head` which will pick it up automatically.

**Warning signs:** All active deployments show `last_seen_at: None` even after a heartbeat is sent.

### Pitfall 3: `_to_record()` Returns `DeploymentRecord` Without freshness Fields

**What goes wrong:** `enrollment_service.py`'s `_to_record()` is called in every deployment API response. If `last_seen_at` and freshness fields aren't added to `DeploymentRecord` Pydantic model AND `_to_record()` doesn't populate them, the list/detail endpoints return records without freshness data.

**Why it happens:** Schema change and ORM change are done but the Pydantic model and `_to_record()` conversion are overlooked.

**How to avoid:** Update `DeploymentRecord` (in `models/deployment.py`) and `_to_record()` in the same task as the ORM change. The planner should treat these as a single atomic change.

### Pitfall 4: Frontend DeploymentRecord Type Out of Sync with Backend

**What goes wrong:** `console/src/lib/admin-api.ts` `DeploymentRecord` type is missing `last_seen_at`, `freshness_status`, `freshness_reason`, `dependency_summary` fields. Components crash or silently show no freshness data.

**Why it happens:** TypeScript type is hand-maintained (not generated from OpenAPI). It must be extended manually in sync with the backend model.

**How to avoid:** Update `admin-api.ts` types at the same time as backend `DeploymentRecord` Pydantic model. Both are in-scope for Plan 08-01 backend work.

### Pitfall 5: Heartbeat Task Starts Before Enrollment Completes

**What goes wrong:** Heartbeat task starts in lifespan but `get_local_identity()` returns `None` because enrollment hasn't run yet; heartbeat silently skips every interval.

**Why it happens:** Task is started before `attempt_enrollment()` runs, or enrollment fails, leaving no local identity.

**How to avoid:** Heartbeat task already handles `None` identity gracefully (D-05 pattern). BUT the task start order in `lifespan` matters: heartbeat task should be started AFTER the enrollment check, not before. Alternatively, the heartbeat `_send_once()` simply returns early if identity is `None` — which is the correct behavior anyway.

### Pitfall 6: test_hosted_contract.py Regression After Schema Artifact Drift

**What goes wrong:** If `HostedDeploymentMetadata` model is changed without regenerating `docs/hosted-default-export.schema.json`, the test `test_committed_schema_artifact_matches_model` fails.

**Why it happens:** The JSON artifact is committed to `docs/` and acts as a regression guard. Any model change that alters the schema (adding/removing fields) requires regenerating the artifact.

**How to avoid:** This phase does NOT modify `HostedDeploymentMetadata` — the model already has all required fields (`last_seen_at`, `freshness_status`, etc.). No schema artifact regeneration needed. Confirm no fields are added to `HostedDeploymentMetadata` in this phase.

---

## Code Examples

Verified patterns from existing code:

### Existing httpx outbound pattern (reuse for heartbeat sender)
```python
# Source: src/nebula/services/gateway_enrollment_service.py lines 68-76
client_kwargs: dict = {"timeout": 30.0}
if self._http_transport is not None:
    client_kwargs["transport"] = self._http_transport
async with httpx.AsyncClient(**client_kwargs) as client:
    response = await client.post(
        f"{self.settings.hosted_plane_url}/v1/enrollment/exchange",
        json=request_body.model_dump(),
    )
    response.raise_for_status()
```

### Existing lifespan startup hook pattern
```python
# Source: src/nebula/main.py lines 23-34
if settings.enrollment_token:
    try:
        await container.gateway_enrollment_service.attempt_enrollment(
            settings.enrollment_token
        )
    except Exception as exc:
        logging.getLogger(__name__).error(
            "Enrollment startup hook failed unexpectedly: %s. "
            "Gateway will start without hosted features.",
            exc,
        )
```

### Existing credential hash verification (reuse for heartbeat auth)
```python
# Source: src/nebula/services/enrollment_service.py lines 112-125
raw_credential = f"nbdc_{secrets.token_urlsafe(32)}"
cred_hash = hashlib.sha256(raw_credential.encode("utf-8")).hexdigest()
# ... stored as deployment.credential_hash
# Verification: hashlib.sha256(incoming.encode()).hexdigest() == deployment.credential_hash
```

### Existing DeploymentModel column pattern (for last_seen_at addition)
```python
# Source: src/nebula/db/models.py lines 63-78
class DeploymentModel(Base):
    __tablename__ = "deployments"
    # ... existing columns ...
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Add analogously:
    # last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

### Existing alembic migration guard pattern
```python
# Source: migrations/versions/20260321_0002_deployments.py lines 21-22
bind = op.get_bind()
inspector = sa.inspect(bind)
# cols = {c["name"] for c in inspector.get_columns("deployments")}
# if "last_seen_at" not in cols:
#     op.add_column(...)
```

### Existing enrollment state badge pattern (freshness badge should match)
```tsx
// Source: console/src/components/deployments/deployment-status-badge.tsx
const STATE_STYLES: Record<EnrollmentState, { className: string; label: string }> = {
  pending:  { className: "bg-amber-50 text-amber-700 border-amber-200", label: "Pending enrollment" },
  active:   { className: "bg-sky-50 text-sky-700 border-sky-200",       label: "Active" },
  revoked:  { className: "bg-rose-50 text-rose-700 border-rose-200",    label: "Revoked" },
  unlinked: { className: "bg-slate-100 text-slate-600 border-slate-200", label: "Unlinked" },
};
export function DeploymentStatusBadge({ state }: DeploymentStatusBadgeProps) {
  const { className, label } = STATE_STYLES[state] ?? STATE_STYLES.pending;
  return (
    <span className={["inline-flex items-center rounded-full border px-2 py-1 text-xs font-semibold", className].join(" ")}>
      {label}
    </span>
  );
}
```

### Existing React Query deployment fetch pattern
```tsx
// Source: console/src/app/(console)/deployments/page.tsx lines 47-51
const deploymentsQuery = useQuery({
  queryKey: queryKeys.deployments,
  queryFn: () => listDeployments(adminKey ?? ""),
  enabled: Boolean(adminKey),
});
```

### TrustBoundaryCard already exists and is importable
```tsx
// Source: console/src/components/hosted/trust-boundary-card.tsx
// Import directly in deployment-detail-drawer.tsx — no rebuild needed
import { TrustBoundaryCard } from "@/components/hosted/trust-boundary-card";
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Status column showing enrollment state | Freshness column showing connectivity freshness | Phase 8 | Fleet table becomes operational monitoring dashboard, not administrative form |
| No heartbeat stub | First heartbeat stub at gateway_enrollment_service.py:94-97 | Phase 7 | Phase 8 replaces stub with real implementation |
| `HostedDeploymentMetadata` without runtime data | All freshness/dependency fields pre-defined | Phase 6 | No model changes needed in Phase 8 |

**Deprecated/outdated:**
- First heartbeat stub in `gateway_enrollment_service.py` lines 94-97: replaced by actual `HeartbeatService.start()` call in lifespan.

---

## Open Questions

1. **Exact header name for deployment credential in heartbeat request**
   - What we know: credential is stored as SHA-256 hash on `DeploymentModel.credential_hash`; gateway has the raw credential in `LocalHostedIdentityModel.credential_hash` (hash only) and... wait — the gateway stores only the HASH, not the raw credential. The raw credential was returned once in the enrollment exchange response and must be stored somewhere retrievable.
   - What's unclear: `LocalHostedIdentityModel` stores `credential_hash` and `credential_prefix`, NOT the raw credential. The raw credential was returned by `EnrollmentExchangeResponse.deployment_credential` but never persisted. The gateway needs the raw credential to send in heartbeat requests for hosted-side verification.
   - Recommendation: During Plan 08-01, add a `credential_raw` (or encrypted store) to `LocalHostedIdentityModel`, or adopt a HMAC-based approach where the gateway signs a nonce rather than sending the raw credential. Alternatively, store the raw credential encrypted at rest. This is the most critical design gap to resolve before implementation.

2. **Capability flags on heartbeat: hardcoded vs. dynamic**
   - What we know: D-15 says "fixed capability flags based on its version and enabled features". The current enrollment sends `["semantic_cache", "premium_routing"]` hardcoded.
   - What's unclear: Should heartbeat re-derive capability flags from `Settings` (e.g., check if Qdrant is reachable) or always send the same hardcoded list?
   - Recommendation: Derive from `Settings` at send time — check `settings.premium_provider != "mock"` for `premium_routing`, always include `semantic_cache` and `local_provider`. Keeps it honest without complexity.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest with pytest-asyncio (auto mode) |
| Config file | `pytest.ini` / `pyproject.toml` |
| Quick run command | `pytest tests/test_heartbeat_api.py -x` |
| Full suite command | `make test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INVT-01 | `GET /v1/admin/deployments` returns `last_seen_at` and version after heartbeat | integration | `pytest tests/test_heartbeat_api.py::test_heartbeat_updates_last_seen_at -x` | Wave 0 |
| INVT-01 | Fleet table renders Name, Environment, Version, Last Seen columns | unit (vitest) | `npm --prefix console run test -- --run src/components/deployments/deployment-table.test.tsx` | Wave 0 |
| INVT-02 | Freshness transitions: connected/degraded/stale/offline at correct time windows | unit | `pytest tests/test_freshness.py -x` | Wave 0 |
| INVT-02 | Freshness reason codes are time-based only (no inferred causes) | unit | `pytest tests/test_freshness.py::test_freshness_reason_format -x` | Wave 0 |
| INVT-02 | `FreshnessBadge` renders correct color per status | unit (vitest) | `npm --prefix console run test -- --run src/components/deployments/freshness-badge.test.tsx` | Wave 0 |
| INVT-04 | Capability flags updated on heartbeat; reflected in GET deployment response | integration | `pytest tests/test_heartbeat_api.py::test_heartbeat_updates_capability_flags -x` | Wave 0 |
| INVT-04 | Pending deployment (never enrolled) shows "Awaiting enrollment" not freshness badge | unit (vitest) | `npm --prefix console run test -- --run src/components/deployments/freshness-badge.test.tsx` | Wave 0 |

**Console quick run:** `npm --prefix console run test -- --run`
**Console full suite:** `make console-test`

### Sampling Rate
- **Per task commit:** `pytest tests/test_heartbeat_api.py tests/test_freshness.py -x`
- **Per wave merge:** `make test && make console-test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_heartbeat_api.py` — covers INVT-01, INVT-04 backend integration
- [ ] `tests/test_freshness.py` — covers INVT-02 freshness calculation unit tests
- [ ] `console/src/components/deployments/freshness-badge.test.tsx` — covers INVT-02 UI
- [ ] `console/src/components/deployments/deployment-table.test.tsx` — extend existing for new columns

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `src/nebula/models/hosted_contract.py` — all freshness/dependency model types confirmed
- Direct code inspection: `src/nebula/services/gateway_enrollment_service.py` — httpx outbound pattern, first heartbeat stub at line 94
- Direct code inspection: `src/nebula/services/enrollment_service.py` — `_to_record()`, `list_deployments()`, credential hash pattern
- Direct code inspection: `src/nebula/db/models.py` — `DeploymentModel` column set, `LocalHostedIdentityModel` fields
- Direct code inspection: `src/nebula/main.py` — lifespan startup pattern
- Direct code inspection: `src/nebula/api/routes/enrollment.py` — no-auth exchange router pattern
- Direct code inspection: `console/src/components/deployments/` — all four deployment UI components
- Direct code inspection: `console/src/lib/admin-api.ts` — `DeploymentRecord` type, all API functions
- Direct code inspection: `console/src/lib/hosted-contract.ts` — `TrustBoundaryCard` content, freshness state labels
- Direct code inspection: `migrations/versions/20260321_0002_deployments.py` — idempotent migration pattern
- Direct code inspection: `.planning/phases/08-fleet-inventory-and-freshness-visibility/08-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)
- Reasoning from `LocalHostedIdentityModel` field set: raw credential is NOT stored, only hash + prefix. The open question about credential retrieval is verified by direct ORM inspection.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project, no new dependencies
- Architecture: HIGH — all patterns verified from existing code; new code follows exact established patterns
- Pitfalls: HIGH — derived from direct inspection of existing code and data models; clock skew and migration ordering are standard engineering concerns, not speculation
- Open Questions: MEDIUM — credential storage gap identified from direct ORM inspection; resolution approach is recommendation, not locked

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable codebase; no fast-moving dependencies)
