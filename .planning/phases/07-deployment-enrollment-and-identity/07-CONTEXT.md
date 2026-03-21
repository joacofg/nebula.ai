# Phase 7: Deployment Enrollment and Identity - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Self-hosted deployments can register with the hosted control plane through an explicit outbound-only identity flow that operators can safely manage. Covers registration without manual DB edits, outbound-only linking with credential exchange, and clean revoke/unlink/relink lifecycle. Does not add fleet inventory UI, heartbeat freshness logic, remote management, or pilot docs.

</domain>

<decisions>
## Implementation Decisions

### Registration initiation flow
- **D-01:** Operator creates a "deployment slot" in the hosted console UI, providing a display name and environment label.
- **D-02:** Hosted plane generates a single-use enrollment token with a 1-hour TTL.
- **D-03:** Operator copies the enrollment token into the gateway's environment config (`NEBULA_ENROLLMENT_TOKEN=...`) and restarts the gateway.
- **D-04:** Gateway detects the enrollment token at startup, initiates outbound enrollment exchange, receives hosted-assigned deployment ID and steady-state credential.
- **D-05:** Enrollment token is consumed on first successful exchange and cannot be reused.
- **D-06:** If the enrollment token is still present in env after successful enrollment, gateway logs a warning nudging the operator to clean it up.

### Credential lifecycle
- **D-07:** Enrollment token TTL is 1 hour. If it expires before use, operator generates a new one from the hosted UI.
- **D-08:** Steady-state deployment credential is stored in the gateway's local PostgreSQL governance database, alongside existing tenant/key data.
- **D-09:** Credential rotation is deferred to a future phase. Revoke+relink is the security escape hatch for v2.0.
- **D-10:** After successful credential exchange, gateway immediately sends its first heartbeat/check-in so the deployment appears in the hosted UI right away.

### Deployment identity shape
- **D-11:** Operator sets display name and environment label (production/staging/development) when creating the deployment slot.
- **D-12:** Gateway self-reports Nebula version and capability flags during enrollment and heartbeat. Hosted plane records what was reported — operator cannot override these fields.
- **D-13:** Hosted plane assigns the deployment UUID during slot creation. Gateway receives it during enrollment. Hosted plane is the identity authority.
- **D-14:** Deployment record tracks explicit enrollment lifecycle states: `pending` (slot created, awaiting enrollment), `active` (enrolled and communicating), `revoked` (credential killed), `unlinked` (soft disconnect by operator).

### Unlink/revoke/relink behavior
- **D-15:** Unlink is a clean operator-initiated disconnect. Gateway continues serving requests normally — it stops sending heartbeats and loses hosted features. Local credential is cleared.
- **D-16:** Revoke immediately invalidates the deployment's credential on the hosted side. Next gateway heartbeat/request fails auth. This is the security emergency action.
- **D-17:** Relinking reuses the same hosted deployment record. Operator generates a new enrollment token for the existing slot, gateway re-enrolls with fresh credentials mapped to the same record. History preserved, no duplicates.
- **D-18:** Revoked and unlinked deployments stay visible in the hosted fleet list with a clear status badge. Operators can filter them. No ghost records.

### Claude's Discretion
- Exact enrollment API endpoint paths and request/response shapes
- Enrollment token format and encoding
- Steady-state credential format (JWT, opaque token, etc.)
- Database schema details (column names, indexes, constraints)
- Console UI layout for deployment creation and enrollment code display
- Error handling and retry behavior during enrollment exchange
- Heartbeat interval and payload shape (detailed in Phase 8)

</decisions>

<specifics>
## Specific Ideas

- Registration should feel like existing bootstrap patterns — operator adds an env var, restarts, done. No new CLI tools or agents needed.
- The enrollment flow should explain the outbound-only relationship and trust boundary before generating the token (per Phase 6 disclosure decision).
- Deployment slot creation in the hosted UI should be low-ceremony: name, environment, generate token, show copy-paste instructions.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Trust boundary and hosted contract
- `src/nebula/models/hosted_contract.py` — HostedDeploymentMetadata Pydantic model with freshness states and exported field definitions
- `docs/hosted-default-export.schema.json` — Committed JSON schema artifact defining the default metadata allowlist
- `tests/test_hosted_contract.py` — Regression tests locking schema exclusions
- `console/src/lib/hosted-contract.ts` — Frontend trust-boundary content module

### Existing governance patterns
- `src/nebula/services/governance_store.py` — API key generation/revocation, hash+prefix storage, upsert patterns, bootstrap seeding
- `src/nebula/db/models.py` — ORM models for tenants, API keys, usage ledger (template for deployment model)
- `src/nebula/models/governance.py` — Pydantic models for governance records (template for deployment records)

### API and routing patterns
- `src/nebula/api/routes/admin.py` — Admin CRUD endpoints with require_admin auth (template for deployment endpoints)
- `src/nebula/core/container.py` — Service container DI pattern for registering new services
- `src/nebula/main.py` — App factory with async lifespan, health endpoints

### Console patterns
- `console/src/lib/admin-api.ts` — Type-safe admin API client with React Query integration
- `console/src/app/(console)/tenants/page.tsx` — List/search/drawer UI pattern for management pages
- `console/src/lib/query-keys.ts` — Query key organization

### Database migrations
- `migrations/versions/20260315_0001_governance_baseline.py` — Migration pattern with conditional table creation

### Phase context
- `.planning/phases/06-trust-boundary-and-hosted-contract/06-CONTEXT.md` — Phase 6 decisions constraining this phase (disclosure surfaces, status language, data export contract)
- `.planning/PROJECT.md` — Milestone goal and hybrid-model constraints
- `.planning/REQUIREMENTS.md` — ENRL-01, ENRL-02, ENRL-03 requirements

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `governance_store.py` API key lifecycle: generation, hash+prefix storage, revocation pattern directly reusable for deployment credentials
- `governance_store.py` upsert/bootstrap patterns: reusable for deployment registration and relink flows
- `db/models.py` ORM patterns: DateTime(timezone=True), metadata JSON columns, nullable revoked_at timestamps
- `admin-api.ts` fetch wrapper: extend with deployment CRUD methods
- `hosted_contract.py` HostedDeploymentMetadata: already defines the shape of what a deployment reports

### Established Patterns
- Admin-managed flows (no self-serve) — deployment enrollment follows the same operator-initiated pattern
- Hash-based credential storage — apply to deployment steady-state credentials
- Conditional migration creation — use same pattern for deployments table
- React Query + drawer-based management UI — reuse for deployment management page

### Integration Points
- New `DeploymentModel` ORM class alongside existing models in `db/models.py`
- New enrollment service registered in `container.py` alongside governance_store
- New `/deployments` admin endpoints in `routes/admin.py` or a new routes file
- Console deployment page and API client extensions
- Gateway startup sequence in `main.py` lifespan: add enrollment check after existing initialization

</code_context>

<deferred>
## Deferred Ideas

- Heartbeat interval, payload shape, and freshness calculation logic — Phase 8
- Fleet inventory UI with freshness badges and compatibility state — Phase 8
- Remote management action definition and pull-based execution — Phase 9
- Credential rotation mechanism — future phase
- Multi-deployment grouping or organizational hierarchy — future phase
- Self-serve deployment registration (without admin) — future phase (ACCT scope)

</deferred>

---

*Phase: 07-deployment-enrollment-and-identity*
*Context gathered: 2026-03-21*
