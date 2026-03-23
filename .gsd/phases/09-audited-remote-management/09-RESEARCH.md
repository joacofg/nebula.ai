# Phase 9: Audited Remote Management - Research

**Researched:** 2026-03-22
**Domain:** deployment-scoped remote action queue, outbound polling, local authorization, and audit history
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Initial allowlisted action
- **D-01:** Phase 9 should ship exactly one remote action: `rotate_deployment_credential`.
- **D-02:** The action's value proposition is operationally real but low-blast-radius: it lets an operator recover or harden the hosted-link credential without changing serving-path behavior, tenant policy, or provider setup.
- **D-03:** The action may touch only the hosted deployment credential and the gateway's local hosted-identity record used for hosted-plane authentication.
- **D-04:** The action must not mutate tenant routing policy, provider credentials, semantic-cache settings, runtime governance, or any other serving-path control.
- **D-05:** Fleet-wide or bulk remote actions are out of scope. This is a single-deployment workflow only.

### Local authorization posture
- **D-06:** Remote action execution is pre-authorized only when the deployment is explicitly configured to allow remote management locally. No inbound approval prompt or hosted-only override exists in v2.0.
- **D-07:** Local authorization checks must require all of the following before apply: deployment is actively linked, remote management is locally enabled, the action name is on the local allowlist, and the deployment advertises the required capability for credential rotation.
- **D-08:** If any local authorization check fails, the deployment must fail closed and record a terminal failed outcome with a machine-stable reason plus operator-readable explanation.
- **D-09:** There is no interactive local approval queue in this phase. Adding approval-gated execution is explicitly deferred as a future hosted-operations capability.

### Hosted operator workflow
- **D-10:** The action should live on the hosted deployment detail surface, not as a bulk table action. Operators should target one deployment intentionally.
- **D-11:** The hosted UI should require an explicit confirmation step before queueing the action and should capture a short operator reason/note for the audit trail.
- **D-12:** The action UI should be visible only for active linked deployments. If the deployment is incompatible, stale beyond support, revoked, or unlinked, the action must fail closed in the UI with a clear reason instead of attempting the request.
- **D-13:** The hosted surface should show both the current queued/in-flight state and recent audited outcomes for this action on that deployment. For v2.0, a compact per-deployment history is enough; no fleet-wide action center is needed.

### Expiry, idempotency, and audit semantics
- **D-14:** Remote actions should have a short TTL of 15 minutes from queue time. This keeps stale management intent from lingering after operator context has changed.
- **D-15:** Expired actions remain in audit history and resolve to a terminal failed outcome with an explicit `expired` reason. They are not silently removed.
- **D-16:** Idempotency should be enforced per deployment and action type: at most one live queued rotation action may exist for a deployment at a time.
- **D-17:** If an operator tries to queue the same action while one is already queued or in progress for that deployment, the hosted plane should return the existing live action record instead of creating a duplicate.
- **D-18:** After a terminal outcome (`applied` or `failed`), a new queue request creates a new audited action record with a new idempotency window.
- **D-19:** Audit records must include queued, applied, and failed timestamps plus concise failure reason categories such as `unauthorized_local_policy`, `expired`, `unsupported_capability`, `invalid_state`, or `apply_error`.

### Claude's Discretion
- Exact remote-action polling interval, endpoint paths, and payload schema
- Exact local configuration field names for enabling remote management and allowlisting action names
- Exact credential-rotation implementation details, including whether the hosted plane returns a fresh credential during ack or through a separate apply handshake
- Exact audit-table schema and whether history lives in one table or split hosted/local records
- Exact hosted UI layout for the action card, confirmation dialog, and history list

### Deferred Ideas (OUT OF SCOPE)
- Approval-gated local execution that requires explicit local admin confirmation before apply
- Additional remote actions such as support-bundle upload, config snapshot pull, or forced heartbeat refresh
- Fleet-wide action targeting, multi-deployment orchestration, or retries across a cohort
- Generic remote execution, shell access, inbound tunnels, or direct mutation of local runtime policy/provider credentials
- Broader hosted RBAC and approval workflows beyond what this single action strictly needs
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RMGT-01 | Hosted control plane can queue at least one allowlisted, non-serving-impacting remote-management action for a linked deployment. | Reuse deployment-scoped admin routes and drawer UI, add one DB-backed queued action type limited to `rotate_deployment_credential`, and gate it to active linked deployments only. |
| RMGT-02 | A linked deployment pulls remote-management actions outbound, applies them only after local authorization checks, and records auditable queued, applied, or failed outcomes. | Reuse the existing async lifespan/background-task + deployment credential auth pattern; add polling plus local allowlist/config checks and terminal audit reasons. |
| RMGT-03 | Remote-management actions are TTL-bound, idempotent, and prevented from directly mutating local runtime policy or provider credentials from the hosted plane. | Enforce DB-level single live action per deployment/action, 15-minute expiry, and action handlers limited to hosted-link credential rotation only. |
</phase_requirements>

## Summary

Phase 9 does not need a new platform layer or extra infrastructure. The repo already has the three hard prerequisites in place: deployment identity and hosted credentials in `EnrollmentService` / `GatewayEnrollmentService`, an outbound authenticated background loop in `HeartbeatService`, and a deployment-scoped hosted UI in the fleet detail drawer. The right planning direction is to extend those paths with one DB-backed remote-action queue plus one local apply path for `rotate_deployment_credential`.

The safest architecture is to keep the queue and audit history authoritative on the hosted side, while the gateway remains authoritative for local authorization and local credential persistence. Queue creation belongs with the existing deployment admin APIs, polling belongs in the gateway lifespan/background-task path, and the action handler should reuse the same credential hashing/storage patterns already used for enrollment, revoke, and relink. Avoid introducing a generic command runner, a second scheduler, or in-memory dedupe.

**Primary recommendation:** Plan Phase 9 as three tightly scoped plans: hosted queue contract, gateway polling/apply path, and audit/TTL/idempotency surfaces, all layered onto the existing deployment/enrollment/heartbeat system.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | `>=0.115.0,<1.0.0` | Hosted admin and deployment-authenticated API routes | Already powers all current gateway/admin endpoints and uses lifespan-managed startup/shutdown. |
| SQLAlchemy | `>=2.0.39,<3.0.0` | Queue, audit, and deployment-row persistence | Already used for deployment identity, token consumption, and row-level locking via `select(...).with_for_update()`. |
| Alembic | `>=1.14.1,<2.0.0` | Schema migrations for remote-action tables/columns | Existing migration path for all governance and deployment schema changes. |
| httpx | `>=0.27.0,<1.0.0` | Outbound hosted polling/apply calls from the gateway | Already used for enrollment exchange and heartbeat sending, including ASGI transport in tests. |
| pytest + pytest-asyncio | `>=8.2.0,<9.0.0` / `>=0.23.0,<1.0.0` | Backend integration and service tests | Existing async-first test harness already covers enrollment and heartbeat flows. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Next.js | `^15.2.2` | Hosted deployment detail action surface | Reuse existing app-router control-plane UI for action trigger and history display. |
| React Query | `^5.66.9` | Queue action mutations and deployment detail refresh | Use for optimistic invalidation and polling of per-deployment action state. |
| Vitest | `^3.0.8` | Console component/client tests | Use for drawer action-card and history rendering tests. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Existing FastAPI + SQLAlchemy queue | Celery/Redis-style job system | Unnecessary operational surface for one deployment-scoped action; adds infra and splits audit state. |
| Existing heartbeat-style background task | Separate worker/service for polling | Breaks the current gateway lifecycle model and complicates local authorization state access. |
| Existing deployment credential auth | Signed webhooks or inbound callbacks | Violates the outbound-only trust boundary already established in phases 6-8. |
| One typed action handler | Generic command/action runner | Makes future scope creep too easy and weakens the trust boundary story. |

**Installation:**
```bash
# No new package is required by the current research.
# Phase 9 should use the stack already declared in pyproject.toml and console/package.json.
```

## Architecture Patterns

### Recommended Project Structure
```text
src/nebula/
├── models/
│   └── deployment.py                # extend with remote-action request/record models
├── db/
│   └── models.py                    # add remote-action queue/audit ORM models
├── services/
│   ├── enrollment_service.py        # hosted queue creation + credential rotation issuance
│   ├── gateway_enrollment_service.py# local credential persistence/rotation application
│   ├── heartbeat_service.py         # shared background-task pattern to mirror for polling
│   └── remote_management_service.py # new local auth + apply/ack orchestration
├── api/routes/
│   ├── enrollment.py                # hosted admin/deployment routes for queueing/history
│   └── remote_management.py         # deployment-authenticated poll/ack routes if split
└── main.py                          # lifespan startup/shutdown wiring

console/src/
├── lib/admin-api.ts                 # queue action + history client methods
└── components/deployments/
    └── deployment-detail-drawer.tsx # action card + history section
```

### Pattern 1: DB-backed deployment action queue
**What:** Persist queue state in the hosted DB and use row state, TTL, and timestamps as the source of truth for queued/in-progress/applied/failed outcomes.
**When to use:** Always. This phase needs durable idempotency and audit history, not in-memory scheduling.
**Example:**
```python
# Source: src/nebula/services/enrollment_service.py
token_row = session.scalars(
    select(EnrollmentTokenModel)
    .where(
        EnrollmentTokenModel.token_hash == token_hash,
        EnrollmentTokenModel.consumed_at.is_(None),
        EnrollmentTokenModel.expires_at > now,
    )
    .with_for_update()
).first()
```
Use the same locking pattern for "find existing live remote action or create one" so duplicate queue requests race safely.

### Pattern 2: Outbound polling in FastAPI lifespan-managed tasks
**What:** Start a long-lived asyncio task from the app lifespan, let it sleep/poll, and stop it during shutdown.
**When to use:** For deployment-side polling of queued remote actions.
**Example:**
```python
# Source: src/nebula/main.py and src/nebula/services/heartbeat_service.py
container.heartbeat_service.start()

async def _loop(self) -> None:
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
        await self._send_once()
```
FastAPI’s current guidance is to use the `lifespan` parameter and an async context manager for startup/shutdown work, which matches the existing repo pattern. Source: [FastAPI lifespan docs](https://fastapi.tiangolo.com/advanced/events/).

### Pattern 3: Deployment-credential authenticated hosted calls
**What:** Authenticate deployment-originated traffic with the steady-state deployment credential, hashed and looked up server-side.
**When to use:** Poll and ack/apply endpoints for remote management.
**Example:**
```python
# Source: src/nebula/api/routes/heartbeat.py and src/nebula/services/heartbeat_ingest_service.py
credential = request.headers.get("X-Nebula-Deployment-Credential")
success = container.heartbeat_ingest_service.record_heartbeat(
    raw_credential=credential,
    ...
)
```
Do not invent a second auth mechanism for Phase 9. Reuse the deployment credential channel already used by heartbeat.

### Pattern 4: Credential lifecycle stays inside enrollment services
**What:** Keep hosted credential issuance and local credential storage in the services that already own them.
**When to use:** The `rotate_deployment_credential` action handler should ask hosted services for a new credential and ask gateway enrollment/local-identity code to persist it.
**Example:**
```python
# Source: src/nebula/services/gateway_enrollment_service.py
cred_hash = hashlib.sha256(exchange.deployment_credential.encode("utf-8")).hexdigest()
cred_prefix = exchange.deployment_credential[:12]
identity = LocalHostedIdentityModel(
    deployment_id=exchange.deployment_id,
    credential_hash=cred_hash,
    credential_prefix=cred_prefix,
    credential_raw=exchange.deployment_credential,
    ...
)
```

### Anti-Patterns to Avoid
- **Generic remote executor:** Phase 9 should not accept arbitrary action names or payloads beyond one fixed allowlisted type.
- **In-memory dedupe:** Duplicate queue suppression must survive process restarts and concurrent requests.
- **Credential swap before terminal audit:** If the gateway changes credentials before the action is durably marked applied, later ack/history can fail or become ambiguous.
- **Hosted-side local auth decisions:** The hosted plane can queue intent, but only the gateway can decide if local config/capability currently permits execution.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Remote action scheduling | A new worker/cron subsystem | Existing lifespan-managed async task pattern | One action does not justify a second execution framework. |
| Idempotency | Python-side dedupe cache | SQL row uniqueness + `with_for_update()` guarded lookup | Restart-safe and concurrency-safe; matches current enrollment token consumption pattern. |
| Deployment auth | New signed callback or webhook secret flow | Existing deployment credential header + hash lookup | Trust boundary already proven by phases 7-8; reuse it. |
| Credential storage | New secret store abstraction | Existing `LocalHostedIdentityModel` and enrollment credential hashing/prefix rules | Keeps remote action limited to hosted-link identity only. |
| Audit rollups | Manually maintained counters in multiple places | Derive rollups from an action history table and project summary into deployment responses | Prevents counter drift and supports explicit timestamps/reason codes. |

**Key insight:** The dangerous hand-rolled part in this phase is not the action logic. It is ad hoc state management around queue dedupe, TTL expiry, and credential transition. Keep those rules DB-backed and explicit.

## Common Pitfalls

### Pitfall 1: Rotating the credential too early
**What goes wrong:** The gateway updates local auth state before the hosted side records the terminal applied outcome, and the final ack path no longer authenticates cleanly.
**Why it happens:** Credential rotation changes the very secret the poll/apply/ack channel uses.
**How to avoid:** Plan an ordered handshake where the action stays tied to the old credential until the apply result is durably written, then switch both ends in a controlled sequence.
**Warning signs:** Actions appear applied locally but remain queued/failed remotely with auth errors afterward.

### Pitfall 2: Duplicate live actions for one deployment
**What goes wrong:** Two operators queue the same action close together and the gateway rotates twice or produces ambiguous history.
**Why it happens:** Idempotency enforced only in application code or only in the UI.
**How to avoid:** Use a DB-enforced "one live queued/in-progress action per deployment/action type" rule plus locked lookup-before-insert.
**Warning signs:** Multiple queued rows with the same deployment and action type before any terminal outcome.

### Pitfall 3: Expiry as silent deletion
**What goes wrong:** Expired actions disappear instead of becoming terminal audited failures.
**Why it happens:** TTL treated as garbage collection instead of business state.
**How to avoid:** Store `expires_at`, transition expired rows to a failed outcome with `expired`, and keep them visible in history.
**Warning signs:** Operators see missing history or cannot tell whether the deployment ignored an action.

### Pitfall 4: UI affordance on unsupported deployment states
**What goes wrong:** The hosted UI offers the action for pending, revoked, unlinked, or incompatible deployments, creating avoidable failed requests.
**Why it happens:** State/capability checks only happen on the server.
**How to avoid:** Reuse the Phase 8 fail-closed capability/state gating pattern in the drawer and still validate server-side.
**Warning signs:** High rate of `invalid_state` or `unsupported_capability` failures from normal UI usage.

### Pitfall 5: Letting remote management leak into runtime governance
**What goes wrong:** The remote action path grows into a generic configuration mutation channel.
**Why it happens:** Shared payload models or handlers touch broader settings than hosted-link identity.
**How to avoid:** Keep the action type and handler narrow: only deployment credential rotation, no policy or provider state writes.
**Warning signs:** Plan tasks reference tenant policy tables, provider config, or routing settings from the remote-action path.

## Code Examples

Verified patterns from repo and official sources:

### Locked lookup before state transition
```python
# Source: src/nebula/services/enrollment_service.py
token_row = session.scalars(
    select(EnrollmentTokenModel)
    .where(
        EnrollmentTokenModel.token_hash == token_hash,
        EnrollmentTokenModel.consumed_at.is_(None),
        EnrollmentTokenModel.expires_at > now,
    )
    .with_for_update()
).first()
```
SQLAlchemy 2.0 documents `Select.with_for_update()` as the supported way to emit `FOR UPDATE` locking on supporting backends. Source: [SQLAlchemy 2.0 selectable docs](https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.GenerativeSelect.with_for_update).

### Lifespan-managed startup/shutdown
```python
# Source: src/nebula/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    container = ServiceContainer(settings=settings)
    await container.initialize()
    app.state.container = container
    container.heartbeat_service.start()
    try:
        yield {"settings": settings}
    finally:
        await container.shutdown()
```

### Deployment-authenticated outbound call
```python
# Source: src/nebula/services/heartbeat_service.py
async with httpx.AsyncClient(**client_kwargs) as client:
    response = await client.post(
        f"{self.settings.hosted_plane_url}/v1/heartbeat",
        json=payload.model_dump(),
        headers={"X-Nebula-Deployment-Credential": credential},
    )
    response.raise_for_status()
```

### Existing integration-test harness for hosted flows
```python
# Source: tests/test_gateway_enrollment.py
transport = httpx.ASGITransport(app=app)
svc = GatewayEnrollmentService(
    settings=settings,
    session_factory=session_factory,
    http_transport=transport,
)
result = asyncio.get_event_loop().run_until_complete(
    svc.attempt_enrollment(raw_token)
)
```
This is the right pattern for testing poll/apply flows without a real external hosted server.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FastAPI startup/shutdown event handlers | `lifespan` async context manager | Current FastAPI guidance as of the 2026 docs | Phase 9 should keep new polling loops inside the existing lifespan pattern, not add deprecated event hooks. |
| Ad hoc concurrency handling | SQLAlchemy 2.x typed `select(...).with_for_update()` flows | Current SQLAlchemy 2.x series | Queue dedupe and live-action locking should be expressed in SQLAlchemy 2.x patterns already used in the repo. |

**Deprecated/outdated:**
- Separate `startup` / `shutdown` event handlers for new lifecycle work: FastAPI documents `lifespan` as the recommended path and notes that providing `lifespan` means those event handlers are no longer called. Source: [FastAPI lifespan docs](https://fastapi.tiangolo.com/advanced/events/).

## Open Questions

1. **Where should the action history summary be projected into deployment responses?**
   - What we know: `HostedDeploymentMetadata` already includes `remote_action_summary`.
   - What's unclear: whether `DeploymentRecord` should also carry a summary and recent history list directly, or whether history should be fetched from a separate endpoint.
   - Recommendation: keep the summary on `DeploymentRecord` for drawer display and expose detailed history through a deployment-scoped endpoint to avoid bloating list responses.

2. **How should the credential-rotation handshake avoid self-invalidating the apply channel?**
   - What we know: the same deployment credential is used for hosted auth today.
   - What's unclear: whether the hosted side should return the new credential on poll, on explicit apply, or on ack.
   - Recommendation: planner should force one explicit ordered handshake task with acceptance criteria around old/new credential behavior and terminal audit state.

3. **What capability flag name should gate the UI and local auth path?**
   - What we know: Phase 8 already displays `capability_flags` and fail-closes unsupported actions.
   - What's unclear: the exact new flag naming and how it is derived from settings.
   - Recommendation: add one explicit capability flag for remote credential rotation and derive it from local remote-management config rather than hardcoding it always-on.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest>=8.2.0,<9.0.0` + `pytest-asyncio>=0.23.0,<1.0.0`; `vitest^3.0.8` for console |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options] asyncio_mode = "auto"`), `console/vitest.config.ts` |
| Quick run command | `pytest tests/test_remote_management_api.py tests/test_remote_management_service.py tests/test_remote_management_audit.py -x` |
| Full suite command | `make test && make console-test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RMGT-01 | Admin queues `rotate_deployment_credential` only for active compatible deployments and receives the live queued record on duplicate requests | integration/API | `pytest tests/test_remote_management_api.py -k 'queue or duplicate or invalid_state' -x` | ❌ Wave 0 |
| RMGT-02 | Gateway polls outbound, enforces local config/allowlist/capability checks, applies the action, and records `queued`/`applied`/`failed` outcomes | integration/service | `pytest tests/test_remote_management_service.py -x` | ❌ Wave 0 |
| RMGT-03 | TTL expiry, idempotency, and no policy/provider mutation are enforced; expired rows remain audited with stable reasons | unit + integration | `pytest tests/test_remote_management_audit.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_remote_management_api.py tests/test_remote_management_service.py -x`
- **Per wave merge:** `pytest tests/test_remote_management_api.py tests/test_remote_management_service.py tests/test_remote_management_audit.py -x && npm --prefix console run test -- --run src/components/deployments`
- **Phase gate:** `make test && make console-test`

### Wave 0 Gaps
- [ ] `tests/test_remote_management_api.py` — queue/create/list/history endpoint coverage for RMGT-01
- [ ] `tests/test_remote_management_service.py` — gateway polling, local auth, and apply/ack flow coverage for RMGT-02
- [ ] `tests/test_remote_management_audit.py` — TTL expiry, duplicate queue suppression, and failure-reason coverage for RMGT-03
- [ ] `console/src/components/deployments/remote-action-card.test.tsx` — action card gating and confirmation UX
- [ ] `console/src/lib/admin-api.remote-actions.test.ts` — client methods for queueing/history and duplicate-return behavior

## Sources

### Primary (HIGH confidence)
- Local repo sources:
  - `src/nebula/services/enrollment_service.py` — current hosted credential lifecycle, token locking pattern, and deployment state transitions
  - `src/nebula/services/gateway_enrollment_service.py` — local hosted identity persistence and credential hashing/prefix storage
  - `src/nebula/services/heartbeat_service.py` — background polling/sending pattern
  - `src/nebula/services/heartbeat_ingest_service.py` — deployment credential auth and deployment-row updates
  - `src/nebula/db/models.py` — current deployment/local identity ORM patterns
  - `src/nebula/main.py` — lifespan-managed service startup/shutdown
  - `src/nebula/api/routes/heartbeat.py` — deployment-authenticated hosted ingress pattern
  - `console/src/lib/admin-api.ts` and `console/src/components/deployments/deployment-detail-drawer.tsx` — hosted deployment UI/client extension points
  - `tests/test_gateway_enrollment.py`, `tests/test_heartbeat_api.py`, `tests/support.py` — existing integration-test harness and hosted-flow coverage patterns
- [FastAPI lifespan docs](https://fastapi.tiangolo.com/advanced/events/) — current startup/shutdown guidance for lifespan-managed tasks
- [SQLAlchemy 2.0 `with_for_update()` docs](https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.GenerativeSelect.with_for_update) — current row-locking API and semantics

### Secondary (MEDIUM confidence)
- `pyproject.toml` and `console/package.json` — in-repo version constraints for planning against the current stack
- `.planning/research/FEATURES.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md` — earlier milestone-level research that aligns with the locked Phase 9 direction

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versions and libraries are declared in-repo and match the existing implemented phases
- Architecture: HIGH - recommendations extend existing enrollment, heartbeat, and deployment UI paths rather than speculating about new subsystems
- Pitfalls: HIGH - all identified failure modes come directly from the current credential/auth/polling architecture and locked Phase 9 constraints

**Research date:** 2026-03-22
**Valid until:** 2026-04-21
