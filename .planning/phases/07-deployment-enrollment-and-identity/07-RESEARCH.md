# Phase 7: Deployment Enrollment and Identity - Research

**Researched:** 2026-03-21
**Domain:** Deployment registration, credential lifecycle, enrollment state machine
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Registration initiation flow:**
- D-01: Operator creates a "deployment slot" in the hosted console UI, providing a display name and environment label.
- D-02: Hosted plane generates a single-use enrollment token with a 1-hour TTL.
- D-03: Operator copies the enrollment token into the gateway's environment config (`NEBULA_ENROLLMENT_TOKEN=...`) and restarts the gateway.
- D-04: Gateway detects the enrollment token at startup, initiates outbound enrollment exchange, receives hosted-assigned deployment ID and steady-state credential.
- D-05: Enrollment token is consumed on first successful exchange and cannot be reused.
- D-06: If the enrollment token is still present in env after successful enrollment, gateway logs a warning nudging the operator to clean it up.

**Credential lifecycle:**
- D-07: Enrollment token TTL is 1 hour. If it expires before use, operator generates a new one from the hosted UI.
- D-08: Steady-state deployment credential is stored in the gateway's local PostgreSQL governance database, alongside existing tenant/key data.
- D-09: Credential rotation is deferred to a future phase. Revoke+relink is the security escape hatch for v2.0.
- D-10: After successful credential exchange, gateway immediately sends its first heartbeat/check-in so the deployment appears in the hosted UI right away.

**Deployment identity shape:**
- D-11: Operator sets display name and environment label (production/staging/development) when creating the deployment slot.
- D-12: Gateway self-reports Nebula version and capability flags during enrollment and heartbeat. Hosted plane records what was reported — operator cannot override these fields.
- D-13: Hosted plane assigns the deployment UUID during slot creation. Gateway receives it during enrollment. Hosted plane is the identity authority.
- D-14: Deployment record tracks explicit enrollment lifecycle states: `pending` (slot created, awaiting enrollment), `active` (enrolled and communicating), `revoked` (credential killed), `unlinked` (soft disconnect by operator).

**Unlink/revoke/relink behavior:**
- D-15: Unlink is a clean operator-initiated disconnect. Gateway continues serving requests normally — it stops sending heartbeats and loses hosted features. Local credential is cleared.
- D-16: Revoke immediately invalidates the deployment's credential on the hosted side. Next gateway heartbeat/request fails auth. This is the security emergency action.
- D-17: Relinking reuses the same hosted deployment record. Operator generates a new enrollment token for the existing slot, gateway re-enrolls with fresh credentials mapped to the same record. History preserved, no duplicates.
- D-18: Revoked and unlinked deployments stay visible in the hosted fleet list with a clear status badge. Operators can filter them. No ghost records.

### Claude's Discretion

- Exact enrollment API endpoint paths and request/response shapes
- Enrollment token format and encoding
- Steady-state credential format (JWT, opaque token, etc.)
- Database schema details (column names, indexes, constraints)
- Console UI layout for deployment creation and enrollment code display
- Error handling and retry behavior during enrollment exchange
- Heartbeat interval and payload shape (detailed in Phase 8)

### Deferred Ideas (OUT OF SCOPE)

- Heartbeat interval, payload shape, and freshness calculation logic — Phase 8
- Fleet inventory UI with freshness badges and compatibility state — Phase 8
- Remote management action definition and pull-based execution — Phase 9
- Credential rotation mechanism — future phase
- Multi-deployment grouping or organizational hierarchy — future phase
- Self-serve deployment registration (without admin) — future phase (ACCT scope)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ENRL-01 | Operator can register a self-hosted Nebula deployment with the hosted control plane without manual database edits. | Console deployment slot creation UI + hosted admin API for slot creation. Operator only touches env var + restart. |
| ENRL-02 | A self-hosted gateway can complete an explicit outbound-only linking flow using short-lived enrollment credentials and durable deployment-scoped credentials for steady-state communication. | Gateway startup enrollment check in `main.py` lifespan; `EnrollmentService` handles token exchange; `DeploymentModel` stores steady-state credential using existing hash pattern. |
| ENRL-03 | Operator can revoke, unlink, or relink a deployment without leaving duplicate or ghost active records in the hosted inventory. | Hosted admin API exposes revoke/unlink actions; lifecycle state machine (pending→active→revoked/unlinked) with upsert on relink prevents duplicates; tests verify each transition leaves exactly one active record. |
</phase_requirements>

---

## Summary

Phase 7 implements the enrollment identity plumbing that connects self-hosted Nebula gateways to the hosted control plane. The work spans three layers: the hosted plane (slot creation API + credential issuance), the local gateway (startup enrollment detection + credential exchange + local persistence), and the lifecycle management surface (revoke, unlink, relink).

The codebase already has all the structural patterns this phase needs. `governance_store.py` provides hash-based credential storage, upsert semantics, and revocation timestamps. `db/models.py` provides the ORM template. The migration pattern (`20260315_0001`) provides conditional table creation. Admin routes in `routes/admin.py` provide the request/response pattern. The console proxy architecture means new deployment admin API calls need no new Next.js route handlers — they flow through the existing `[...path]` catch-all.

**Primary recommendation:** Model the `DeploymentModel` and `EnrollmentService` exactly on the `ApiKeyModel`/`GovernanceStore` pattern — same hash storage for the steady-state credential, same nullable `revoked_at` field for revocation, same `upsert=True` semantics for relink. Add a `enrollment_state` string column (four states: `pending`, `active`, `revoked`, `unlinked`) instead of deriving status from nullable columns. Gateway startup adds an enrollment check after `governance_store.initialize()` in the lifespan.

---

## Standard Stack

### Core (all already in-project — no new dependencies)

| Library / Pattern | Version | Purpose | Why Standard |
|-------------------|---------|---------|--------------|
| SQLAlchemy ORM (mapped_column) | existing | `DeploymentModel` and `EnrollmentTokenModel` ORM classes | Matches every other model in `db/models.py` |
| Alembic migrations | existing | `deployments` and `enrollment_tokens` table creation | Conditional pattern already in baseline migration |
| Pydantic BaseModel | existing | `DeploymentRecord`, `EnrollmentTokenRecord`, API request/response models | Matches `governance.py` patterns |
| FastAPI APIRouter | existing | Hosted enrollment API endpoints, gateway-facing exchange endpoint | Matches `admin.py` pattern with `require_admin` |
| `secrets.token_urlsafe` | stdlib | Enrollment token generation (opaque, URL-safe, 32 bytes → 43 chars) | Already used for API key generation in `governance_store.py` |
| `hashlib.sha256` | stdlib | Token storage — hash on write, compare hash on lookup | Already used for API keys; prevents token exposure if DB is read |
| `httpx` (AsyncClient) | existing | Gateway outbound enrollment HTTP call to hosted plane | Already in project for provider HTTP calls |
| pydantic-settings | existing | `NEBULA_ENROLLMENT_TOKEN` setting in `Settings` | Config already uses this pattern |

### No New Dependencies Required

This phase adds zero new Python packages. All patterns (ORM, Alembic, Pydantic, hash storage, async HTTP) are already in the project and exercised by existing tests.

---

## Architecture Patterns

### Recommended Project Structure

New files this phase creates:

```
src/nebula/
├── db/models.py                         # +DeploymentModel, +EnrollmentTokenModel
├── models/
│   └── deployment.py                    # New: Pydantic records and request/response models
├── services/
│   └── enrollment_service.py            # New: hosted-side slot/token lifecycle
│   └── gateway_enrollment_service.py    # New: gateway-side outbound exchange
├── api/routes/
│   └── enrollment.py                    # New: hosted enrollment endpoints
migrations/versions/
└── 20260321_0002_deployments.py         # New: conditional table creation

console/src/
├── lib/admin-api.ts                     # +deployment CRUD functions and types
├── lib/query-keys.ts                    # +deployments query key
└── app/(console)/
    └── deployments/
        └── page.tsx                     # New: deployment management page
```

---

### Pattern 1: Deployment State Machine

**What:** Four explicit states stored as a string column, not derived from nullable timestamps.

```
pending  →  active      (gateway completes enrollment exchange)
active   →  revoked     (operator emergency revoke)
active   →  unlinked    (operator clean disconnect)
revoked  →  pending     (operator generates new token for relink)
unlinked →  pending     (operator generates new token for relink)
```

**When to use:** State column `enrollment_state: Mapped[str]` with CHECK constraint. Never compute state by inspecting multiple columns.

**Example (ORM):**

```python
# Source: modeled on db/models.py ApiKeyModel pattern
class DeploymentModel(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)       # UUID from hosted plane
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(64), nullable=False)  # production/staging/development
    enrollment_state: Mapped[str] = mapped_column(String(32), nullable=False)  # pending/active/revoked/unlinked
    nebula_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capability_flags_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    credential_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    credential_prefix: Mapped[str | None] = mapped_column(String(32), nullable=True)
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unlinked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

---

### Pattern 2: Enrollment Token Model (Hosted Side)

**What:** Short-lived single-use tokens stored hashed; consumed on first exchange.

```python
# Source: modeled on ApiKeyModel in db/models.py
class EnrollmentTokenModel(Base):
    __tablename__ = "enrollment_tokens"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)          # UUID
    deployment_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    token_prefix: Mapped[str] = mapped_column(String(16), nullable=False)   # for log display
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

**Key constraint:** `consumed_at IS NULL AND expires_at > NOW()` is the only valid-token predicate.

---

### Pattern 3: Enrollment Token Format and Encoding

**What:** Opaque URL-safe token with a recognizable prefix, generated with `secrets.token_urlsafe`.

**Recommended format:** `nbet_<43 chars urlsafe base64>` (prefix `nbet_` = Nebula Bootstrap Enrollment Token, similar to `nbk_` for API keys).

**Why:** Matches `nbk_` prefix pattern already in `governance_store.py`; prefix makes tokens identifiable in logs and config files; full token is never stored — only SHA-256 hash.

```python
# Source: governance_store.py create_api_key pattern
token = f"nbet_{secrets.token_urlsafe(32)}"   # 5 + 43 = 48 chars
token_hash = hashlib.sha256(token.encode()).hexdigest()
token_prefix = token[:12]  # "nbet_xxxxxxx" — enough to identify in logs
```

---

### Pattern 4: Steady-State Credential Format

**What:** Opaque deployment-scoped secret issued by hosted plane after successful enrollment exchange. Gateway includes it in all subsequent outbound calls (heartbeats, Phase 8+).

**Recommended format:** `nbdc_<43 chars urlsafe base64>` (prefix `nbdc_` = Nebula Deployment Credential).

**Storage:** Hash stored in `deployments.credential_hash` using same SHA-256 pattern. Raw credential returned once at enrollment exchange time and stored in local PostgreSQL governance DB (`D-08`). Operator never sees it after exchange.

---

### Pattern 5: Gateway Startup Enrollment Check

**What:** After `governance_store.initialize()` in `main.py` lifespan, check for `NEBULA_ENROLLMENT_TOKEN` setting. If present and no local credential exists, perform outbound enrollment exchange.

```python
# Source: modeled on main.py lifespan pattern
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    container = ServiceContainer(settings=settings)
    await container.initialize()
    # Phase 7: enrollment check after governance init
    if settings.enrollment_token:
        await container.gateway_enrollment_service.attempt_enrollment(settings.enrollment_token)
    app.state.container = container
    try:
        yield {"settings": settings}
    finally:
        await container.shutdown()
```

**Key behaviors:**
- If local credential already exists (already enrolled), skip exchange and log at INFO.
- If token is expired or consumed, log ERROR with operator instructions (generate new token).
- If exchange succeeds, immediately send first heartbeat (`D-10`).
- If token is still in env after enrollment, log WARNING per `D-06`.
- Exchange failure must not prevent gateway from starting — log ERROR and continue without hosted features.

---

### Pattern 6: Hosted Enrollment API Endpoints

New endpoints mounted alongside existing `/v1/admin/...` routes. Since the console proxy catch-all routes all `/api/admin/**` to `/v1/admin/**`, these are automatically reachable from the console.

**Hosted plane (operator-facing):**
```
POST   /v1/admin/deployments                    # Create deployment slot (D-01)
GET    /v1/admin/deployments                    # List all deployments
GET    /v1/admin/deployments/{id}               # Get single deployment
POST   /v1/admin/deployments/{id}/enrollment-token   # Generate/reissue enrollment token (D-02, D-17)
POST   /v1/admin/deployments/{id}/revoke        # Revoke credential (D-16)
POST   /v1/admin/deployments/{id}/unlink        # Unlink (D-15)
```

**Gateway-facing exchange endpoint (called outbound by gateway, not by console):**
```
POST   /v1/enrollment/exchange                  # Consume token, return deployment_id + credential
```

The exchange endpoint uses the enrollment token for auth (not `X-Nebula-Admin-Key`), is unauthenticated in the traditional sense, and rate-limits by token. This endpoint is the only surface that accepts enrollment tokens.

---

### Pattern 7: Enrollment Exchange Request/Response

**Request (gateway → hosted plane):**
```python
class EnrollmentExchangeRequest(BaseModel):
    enrollment_token: str            # raw "nbet_..." token
    nebula_version: str              # from importlib.metadata or package constant
    capability_flags: list[str]      # e.g. ["semantic_cache", "premium_routing"]
```

**Response (hosted plane → gateway):**
```python
class EnrollmentExchangeResponse(BaseModel):
    deployment_id: str               # hosted-assigned UUID (D-13)
    deployment_credential: str       # raw "nbdc_..." — return once, never again
    display_name: str                # for local logging / confirmation
    environment: str
```

---

### Pattern 8: Local Credential Storage in Gateway DB

After successful exchange, gateway stores the deployment identity and credential in its local PostgreSQL governance DB. This is a new `local_deployments` table (or `hosted_identity`) in the local DB — not the same `deployments` table that lives in the hosted plane's DB.

**Local identity table:**
```python
class LocalHostedIdentityModel(Base):
    __tablename__ = "local_hosted_identity"

    deployment_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(64), nullable=False)
    credential_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    credential_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unlinked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

Single-row table (at most one hosted identity per gateway). Use `upsert=True` semantics for relink.

---

### Pattern 9: Relink Flow — No Ghost Records

**What:** Relink must update the existing hosted `DeploymentModel` row, not insert a new one.

**How:**
1. Operator generates a new token for an existing slot (POST `/v1/admin/deployments/{id}/enrollment-token`) — this works for `revoked` or `unlinked` states.
2. Gateway re-runs enrollment exchange with new token.
3. Exchange handler looks up the token, finds the linked `deployment_id`, resets `enrollment_state` to `active`, issues new credential, consumes old token.
4. Result: same deployment row, new credential, no duplicate records.

**Anti-pattern:** Creating a new deployment slot when the intent is to relink. The planner should document that "create slot" is only for first-time registrations.

---

### Anti-Patterns to Avoid

- **Deriving enrollment_state from nullable columns:** Computing state as "is `revoked_at` null and `credential_hash` not null?" creates ambiguous state during transition. Use an explicit `enrollment_state` string column.
- **Inlining enrollment logic in lifespan:** Gateway startup enrollment belongs in `GatewayEnrollmentService`, not in `main.py`. Lifespan calls the service; service handles exchange, storage, and first heartbeat.
- **Storing raw enrollment token in env after enrollment:** Token must only be read at startup. After exchange, gateway should check whether the token is still present and log a warning per D-06. It does not clear it automatically (that's operator responsibility), but does warn.
- **Blocking gateway startup on enrollment failure:** If enrollment exchange fails (expired token, network error), gateway must log the error and start normally without hosted features. Enrollment failure is not fatal.
- **Using the same table for hosted and local deployments:** The hosted plane's `deployments` table is the authority. The gateway's local DB has a separate `local_hosted_identity` table for the one record it needs locally.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Secure token generation | Custom entropy collection | `secrets.token_urlsafe(32)` | Already used in `governance_store.py`; cryptographically secure |
| Token storage security | Plaintext token in DB | SHA-256 hash via `hashlib.sha256` | Same pattern as API keys; prevents exposure if DB is read |
| Outbound HTTP call | Raw socket / requests | `httpx.AsyncClient` | Already in project; async-safe; proper timeout handling |
| Settings parsing | Custom env parsing | `pydantic_settings.BaseSettings` + `Field(alias=...)` | `Settings` class already handles env var binding |
| Migration | Raw SQL scripts | Alembic conditional migration | Existing pattern in `20260315_0001` handles multiple environments |
| Console API proxy | New Next.js route handler | Existing `[...path]` catch-all | Already proxies all `/api/admin/**` to `/v1/admin/**` |

**Key insight:** Every primitive this phase needs is already used in the codebase. The task is composing them correctly, not building new utilities.

---

## Common Pitfalls

### Pitfall 1: Token Reuse Window

**What goes wrong:** Between token generation and first use, there's a 1-hour window. If the operator's token file is compromised, an attacker could enroll with it.
**Why it happens:** Single-use tokens with TTL are stateless until consumption.
**How to avoid:** Store `consumed_at` timestamp atomically with credential issuance in a single DB transaction. Check `consumed_at IS NULL` and `expires_at > NOW()` in the same query. Wrap exchange handler in a transaction so concurrent requests cannot both consume the same token.
**Warning signs:** If enrollment_state shows `active` but two credential records exist — the transaction wasn't atomic.

### Pitfall 2: Enrollment Blocking Gateway Start

**What goes wrong:** Developer puts enrollment exchange in the synchronous initialization path and the hosted plane is unreachable (network partition, misconfigured URL). Gateway refuses to start.
**Why it happens:** Treating enrollment as a hard dependency like the PostgreSQL connection.
**How to avoid:** Enrollment exchange is best-effort. Wrap in `try/except`, log the failure at ERROR, set hosted_features_enabled=False, continue startup. Only the governance DB is a hard startup dependency.
**Warning signs:** Test suite breaks when `NEBULA_ENROLLMENT_TOKEN` is set but no hosted plane is running.

### Pitfall 3: Relink Creates Duplicate Active Records

**What goes wrong:** `POST /v1/admin/deployments` is called instead of `POST /v1/admin/deployments/{id}/enrollment-token`, creating a second slot for the same physical gateway.
**Why it happens:** UI doesn't prevent creating a new slot for an already-enrolled gateway.
**How to avoid:** The exchange endpoint must use `upsert` semantics keyed on `deployment_id`. The hosted fleet list query that checks for active deployments should filter on `enrollment_state='active'`. Add a test: enroll, unlink, relink — assert row count in `deployments` is still 1 for that `deployment_id`.
**Warning signs:** `deployment_id` changes between relinks — it shouldn't (D-13, D-17).

### Pitfall 4: Credential Hash Collision Risk

**What goes wrong:** `credential_hash` column has `unique=True`. SHA-256 of two different credentials could theoretically collide (astronomically unlikely but should be designed for).
**Why it happens:** Same constraint as `api_keys.key_hash`.
**How to avoid:** Exactly the same as `api_keys` — SHA-256 with `unique=True` is standard. The real risk is a key-generation loop that issues the same raw key twice; prevent by using `secrets.token_urlsafe(32)` which provides 256 bits of entropy.
**Warning signs:** `IntegrityError` on `credential_hash` unique constraint during enrollment.

### Pitfall 5: Enrollment Token Accepted After Consumption

**What goes wrong:** Token exchange endpoint doesn't check `consumed_at` and allows re-use.
**Why it happens:** Query only checks `expires_at > NOW()` but forgets `consumed_at IS NULL`.
**How to avoid:** The token validation predicate must be: `token_hash = $hash AND consumed_at IS NULL AND expires_at > NOW()`. Test: call exchange endpoint twice with the same token; second call must return 401.
**Warning signs:** Same token enrolls the same gateway twice.

### Pitfall 6: Settings Cache Not Cleared in Tests

**What goes wrong:** Tests that set `NEBULA_ENROLLMENT_TOKEN` via env override don't call `get_settings.cache_clear()` and pick up cached settings without the token.
**Why it happens:** `get_settings` is decorated with `@lru_cache` in `config.py`.
**How to avoid:** Follow the existing `configured_app` pattern in `tests/support.py` which already calls `get_settings.cache_clear()` before and after each test. Add `NEBULA_ENROLLMENT_TOKEN` to the `default_overrides` when testing enrollment flows, or pass it as a kwarg to `configured_app`.
**Warning signs:** Test passes in isolation but fails when run alongside other tests.

---

## Code Examples

### Example 1: Migration for Deployments Tables

```python
# Source: modeled on migrations/versions/20260315_0001_governance_baseline.py
def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "deployments" not in tables:
        op.create_table(
            "deployments",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("display_name", sa.String(255), nullable=False),
            sa.Column("environment", sa.String(64), nullable=False),
            sa.Column("enrollment_state", sa.String(32), nullable=False, server_default="pending"),
            sa.Column("nebula_version", sa.String(64), nullable=True),
            sa.Column("capability_flags_json", sa.JSON(), nullable=False, server_default="'[]'"),
            sa.Column("credential_hash", sa.String(64), nullable=True, unique=True),
            sa.Column("credential_prefix", sa.String(32), nullable=True),
            sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("unlinked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    if "enrollment_tokens" not in tables:
        op.create_table(
            "enrollment_tokens",
            sa.Column("id", sa.String(255), primary_key=True),
            sa.Column("deployment_id", sa.String(255),
                      sa.ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
            sa.Column("token_prefix", sa.String(16), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
```

---

### Example 2: Enrollment Service — Token Generation

```python
# Source: modeled on governance_store.py create_api_key
import secrets
import hashlib
from datetime import UTC, datetime, timedelta

def _generate_enrollment_token(self) -> tuple[str, str, str, datetime]:
    """Returns (raw_token, token_hash, token_prefix, expires_at)."""
    raw = f"nbet_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    prefix = raw[:12]
    expires_at = datetime.now(UTC) + timedelta(hours=1)
    return raw, token_hash, prefix, expires_at
```

---

### Example 3: Enrollment Exchange Handler (Atomic Consumption)

```python
# Source: pattern derived from governance_store.py revoke_api_key + create_api_key
def consume_enrollment_token(self, raw_token: str, ...) -> tuple[str, str] | None:
    """Returns (deployment_id, raw_credential) or None if token invalid."""
    token_hash = self._hash_key(raw_token)
    now = self._now()
    with self._session() as session:
        token_row = session.scalar(
            select(EnrollmentTokenModel).where(
                EnrollmentTokenModel.token_hash == token_hash,
                EnrollmentTokenModel.consumed_at.is_(None),
                EnrollmentTokenModel.expires_at > now,
            ).with_for_update()   # pessimistic lock prevents double-consume
        )
        if token_row is None:
            return None
        # Issue credential
        raw_credential = f"nbdc_{secrets.token_urlsafe(32)}"
        cred_hash = self._hash_key(raw_credential)
        # Update deployment to active, set credential
        deployment = session.get(DeploymentModel, token_row.deployment_id)
        deployment.enrollment_state = "active"
        deployment.credential_hash = cred_hash
        deployment.credential_prefix = raw_credential[:12]
        deployment.enrolled_at = now
        deployment.updated_at = now
        # Mark token consumed
        token_row.consumed_at = now
        session.commit()
        return deployment.id, raw_credential
```

---

### Example 4: Settings Extension for Enrollment Token

```python
# Source: modeled on config.py Settings class
enrollment_token: str | None = Field(default=None, alias="NEBULA_ENROLLMENT_TOKEN")
hosted_plane_url: str | None = Field(default=None, alias="NEBULA_HOSTED_PLANE_URL")
```

Both fields are optional — gateway functions normally without them.

---

### Example 5: Console Admin API Extension

```typescript
// Source: modeled on console/src/lib/admin-api.ts

export type DeploymentEnvironment = "production" | "staging" | "development";
export type EnrollmentState = "pending" | "active" | "revoked" | "unlinked";

export type DeploymentRecord = {
  id: string;
  display_name: string;
  environment: DeploymentEnvironment;
  enrollment_state: EnrollmentState;
  nebula_version: string | null;
  capability_flags: string[];
  enrolled_at: string | null;
  revoked_at: string | null;
  unlinked_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DeploymentCreateInput = {
  display_name: string;
  environment: DeploymentEnvironment;
};

export type EnrollmentTokenResponse = {
  token: string;              // raw token shown ONCE to operator
  expires_at: string;
  deployment_id: string;
};

export const ADMIN_DEPLOYMENTS_ENDPOINT = "/api/admin/deployments";

export function listDeployments(adminKey: string) {
  return adminRequest<DeploymentRecord[]>(ADMIN_DEPLOYMENTS_ENDPOINT, { adminKey });
}

export function createDeployment(adminKey: string, payload: DeploymentCreateInput) {
  return adminRequest<DeploymentRecord>(ADMIN_DEPLOYMENTS_ENDPOINT, {
    adminKey, method: "POST", body: payload,
  });
}

export function generateEnrollmentToken(adminKey: string, deploymentId: string) {
  return adminRequest<EnrollmentTokenResponse>(
    `${ADMIN_DEPLOYMENTS_ENDPOINT}/${deploymentId}/enrollment-token`,
    { adminKey, method: "POST" },
  );
}

export function revokeDeployment(adminKey: string, deploymentId: string) {
  return adminRequest<DeploymentRecord>(
    `${ADMIN_DEPLOYMENTS_ENDPOINT}/${deploymentId}/revoke`,
    { adminKey, method: "POST" },
  );
}

export function unlinkDeployment(adminKey: string, deploymentId: string) {
  return adminRequest<DeploymentRecord>(
    `${ADMIN_DEPLOYMENTS_ENDPOINT}/${deploymentId}/unlink`,
    { adminKey, method: "POST" },
  );
}
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Static long-lived shared secrets for gateway auth | Short-lived enrollment token + deployment-scoped steady-state credential | Enrollment tokens expire; compromise window is 1 hour |
| Manual DB records for registered agents | Operator UI slot creation + env var bootstrap | No manual DB edits (ENRL-01) |
| Inbound registration calls from control plane | Outbound-only enrollment from gateway | Maintains trust boundary — hosted plane never opens inbound connections |

**Key architecture choice verified against CONTEXT.md:** The enrollment flow is deliberately similar to "adding a cloud service account": operator creates slot in UI, copies a short-lived bootstrap secret, drops it in env, restarts. This is the recognized pattern for self-hosted software that needs to register with a SaaS control plane (e.g., Terraform Cloud agents, GitHub Actions self-hosted runners, Datadog agents). All of those use the same envelope: create registration token in UI → paste in env → restart → exchange for durable credential.

---

## Open Questions

1. **Hosted plane URL for gateway enrollment exchange**
   - What we know: Gateway needs `NEBULA_HOSTED_PLANE_URL` to know where to POST the exchange request. During local dev, there is no hosted plane running.
   - What's unclear: Should the enrollment check be skipped entirely when `NEBULA_HOSTED_PLANE_URL` is not set, or should it fail loudly?
   - Recommendation: Skip silently with an INFO log if `NEBULA_HOSTED_PLANE_URL` is not configured. This makes local dev workflows unaffected.

2. **Enrollment exchange endpoint authentication**
   - What we know: The exchange endpoint accepts the raw enrollment token. It does not use `X-Nebula-Admin-Key`.
   - What's unclear: Should this be a separate FastAPI router with different auth middleware, or use the same `require_admin` dependency?
   - Recommendation: Separate router (e.g., `/v1/enrollment/`) with its own token-validation dependency. This keeps admin-key auth strictly separated from token-based exchange auth.

3. **Console enrollment token display — show-once UX**
   - What we know: The raw enrollment token must be shown to the operator exactly once (D-05 — consumed on use). After generation, it cannot be retrieved again.
   - What's unclear: Should the token response from `POST .../enrollment-token` include the raw token in the HTTP response body (standard), or does the console need a separate "copy" flow?
   - Recommendation: Return raw token in POST response body only. Console displays a copy-paste block with a "I've copied it" confirmation. After the operator dismisses the modal, the token is gone from the UI. This is the standard GitHub personal access token UX.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (auto mode) |
| Config file | `pyproject.toml` (or `pytest.ini`) |
| Quick run command | `pytest tests/test_enrollment_api.py -x` |
| Full suite command | `make test` |
| Console tests | `make console-test` (vitest) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENRL-01 | POST /admin/deployments creates slot, token generated, no DB edit required | integration | `pytest tests/test_enrollment_api.py::test_create_deployment_slot -x` | Wave 0 |
| ENRL-01 | GET /admin/deployments lists all states including pending | integration | `pytest tests/test_enrollment_api.py::test_list_deployments_includes_all_states -x` | Wave 0 |
| ENRL-02 | POST /enrollment/exchange with valid token → returns deployment_id + credential, sets state=active | integration | `pytest tests/test_enrollment_api.py::test_enrollment_exchange_success -x` | Wave 0 |
| ENRL-02 | Exchange with expired token → 401 | integration | `pytest tests/test_enrollment_api.py::test_enrollment_exchange_expired_token -x` | Wave 0 |
| ENRL-02 | Exchange with already-consumed token → 401 | integration | `pytest tests/test_enrollment_api.py::test_enrollment_exchange_consumed_token -x` | Wave 0 |
| ENRL-02 | Gateway startup with NEBULA_ENROLLMENT_TOKEN set triggers exchange | integration | `pytest tests/test_gateway_enrollment.py::test_startup_enrollment_exchange -x` | Wave 0 |
| ENRL-02 | Gateway startup without NEBULA_ENROLLMENT_TOKEN skips enrollment, starts normally | integration | `pytest tests/test_gateway_enrollment.py::test_startup_no_token_skips_enrollment -x` | Wave 0 |
| ENRL-02 | Gateway startup with unreachable hosted plane logs error, starts normally | integration | `pytest tests/test_gateway_enrollment.py::test_startup_enrollment_failure_nonfatal -x` | Wave 0 |
| ENRL-03 | Revoke sets state=revoked, subsequent credential lookup fails | integration | `pytest tests/test_enrollment_api.py::test_revoke_deployment -x` | Wave 0 |
| ENRL-03 | Unlink sets state=unlinked, clears local credential | integration | `pytest tests/test_enrollment_api.py::test_unlink_deployment -x` | Wave 0 |
| ENRL-03 | Relink (generate new token for existing slot) → exchange → same deployment_id, single active row | integration | `pytest tests/test_enrollment_api.py::test_relink_preserves_single_record -x` | Wave 0 |
| ENRL-03 | Fleet list shows revoked + unlinked records, not hidden | integration | `pytest tests/test_enrollment_api.py::test_list_includes_revoked_and_unlinked -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_enrollment_api.py tests/test_gateway_enrollment.py -x`
- **Per wave merge:** `make test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_enrollment_api.py` — covers ENRL-01 (slot creation, token generation, list) and ENRL-02 (exchange success/failure), ENRL-03 (revoke/unlink/relink)
- [ ] `tests/test_gateway_enrollment.py` — covers ENRL-02 gateway-side startup enrollment behavior (token detection, outbound exchange, non-fatal failure)
- [ ] Migration: `migrations/versions/20260321_0002_deployments.py` — `deployments` + `enrollment_tokens` tables (Wave 0 / Plan 1)

*(Existing `configured_app` in `tests/support.py` already handles test DB setup and migration runs — new tests use it without modification.)*

---

## Sources

### Primary (HIGH confidence)

- Direct code read: `src/nebula/services/governance_store.py` — credential generation, hash storage, revocation, upsert patterns
- Direct code read: `src/nebula/db/models.py` — ORM column types, nullable patterns, DateTime(timezone=True), JSON columns
- Direct code read: `migrations/versions/20260315_0001_governance_baseline.py` — conditional table creation pattern
- Direct code read: `src/nebula/api/routes/admin.py` — FastAPI CRUD endpoint structure, `require_admin` dependency
- Direct code read: `src/nebula/core/container.py` — DI service registration pattern
- Direct code read: `src/nebula/main.py` — async lifespan pattern, initialization order
- Direct code read: `console/src/lib/admin-api.ts` — TypeScript type patterns, `adminRequest` wrapper
- Direct code read: `console/src/app/api/admin/[...path]/route.ts` — proxy catch-all (new endpoints need no new Next.js handlers)
- Direct code read: `src/nebula/models/hosted_contract.py` — `HostedDeploymentMetadata` fields (deployment_id, display_name, environment, nebula_version, capability_flags)
- Direct code read: `tests/support.py` — `configured_app`, `get_settings.cache_clear()`, `admin_headers()` patterns

### Secondary (MEDIUM confidence)

- Pattern cross-reference: GitHub Actions self-hosted runner enrollment (create token in UI → paste in env → restart → durable credential) confirms this is standard industry practice for hybrid control plane registration.
- Pattern cross-reference: Terraform Cloud agent token flow and Datadog Agent API key bootstrap follow the same envelope.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all patterns verified by direct code read
- Architecture patterns: HIGH — directly derived from existing `governance_store.py` and `db/models.py` patterns
- Pitfalls: HIGH — derived from known concurrency issues (double-consume), observed test harness patterns (`lru_cache` clearing), and explicit decisions in CONTEXT.md
- Console patterns: HIGH — existing `[...path]` proxy makes new admin endpoints automatically reachable; types pattern verified from `admin-api.ts`

**Research date:** 2026-03-21
**Valid until:** 2026-04-20 (stable internal codebase; no external dependency changes)
