# Phase 8: Fleet Inventory and Freshness Visibility - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Show honest deployment inventory, freshness, and compatibility state in the hosted plane. Covers heartbeat ingestion from linked gateways, freshness calculation with explicit semantics, fleet inventory UI with deployment detail, and capability/compatibility display with fail-closed behavior. Does not add remote management actions, pilot docs, or outage-safe serving validation.

</domain>

<decisions>
## Implementation Decisions

### Heartbeat mechanism
- **D-01:** Gateway sends heartbeats every 5 minutes to the hosted plane via outbound HTTP POST, following the same outbound-only pattern as enrollment exchange.
- **D-02:** Heartbeat payload is minimal: Nebula version, capability flags, and coarse dependency health summary (which local stores are healthy/degraded/unavailable). No raw usage data, no prompts, no ledger rows.
- **D-03:** Gateway updates its version and capability flags on every heartbeat, so a gateway upgrade reflects in the hosted plane without re-enrollment.
- **D-04:** Heartbeat runs as a background asyncio task in the gateway's event loop, started during lifespan, cancelled on shutdown. Matches existing enrollment startup hook pattern.
- **D-05:** On heartbeat failure (network issue, hosted plane down), gateway logs a warning and retries at the next scheduled interval. No backoff, no queuing, no retry storm. Hosted outage = stale visibility, not gateway disruption.
- **D-06:** Gateway authenticates heartbeats using the steady-state deployment credential from enrollment (same credential stored in local_hosted_identity).

### Freshness thresholds
- **D-07:** Hosted plane calculates freshness from `last_seen_at` timestamp — gateway cannot self-report freshness. Single source of truth for thresholds lives on the hosted side.
- **D-08:** Time windows: `connected` = heard within 10 minutes. `degraded` = 10-30 minutes since last heartbeat. `stale` = 30 minutes to 1 hour. `offline` = more than 1 hour since last heartbeat.
- **D-09:** Reason codes are time-based only: "Last heartbeat 3 minutes ago", "No heartbeat for 45 minutes", "No heartbeat since Mar 20 14:30". No inferred causes. Matches Phase 6 "truthful uncertainty over optimism" principle.
- **D-10:** Stale and offline deployments remain always visible in the fleet list with dimmed row styling and a colored freshness badge. Never hidden. Timestamps show relative "last seen X ago" text.

### Fleet inventory view
- **D-11:** Fleet table columns: Name, Environment, Freshness (badge), Version, Last Seen. Enrollment state column moves from the table to the detail drawer. Replaces current "Status" column with Freshness.
- **D-12:** Deployment detail drawer layout: freshness section at top (freshness badge, reason text, last-seen timestamp), then identity section (name, ID, environment, version, capability chips), then dependency health, then trust-boundary disclosure card (from Phase 6), then lifecycle actions (revoke, unlink, relink) at bottom.
- **D-13:** Dependency health displays as compact colored pills: each dependency (PostgreSQL, Qdrant, Ollama) as a green/yellow/red pill. One row, glanceable. Matches existing compact console style.
- **D-14:** Pending (never-enrolled) deployments show "Awaiting enrollment" instead of a freshness badge. Freshness only applies to deployments that have completed enrollment at least once.

### Capability and compatibility
- **D-15:** Gateway reports fixed capability flags based on its version and enabled features (e.g., `semantic_cache`, `premium_routing`, `local_provider`). No operator override. Hosted plane records what was reported.
- **D-16:** Capability flags displayed as small chips/tags in the deployment detail drawer.
- **D-17:** When a remote action targets a deployment that lacks the required capability, the action button is disabled with a tooltip: "This deployment does not support [action] (requires [capability])". Fail closed at the UI level — no request sent.
- **D-18:** No fleet-wide compatibility matrix for v2.0. Per-deployment capability display in the detail drawer is sufficient for the validation milestone.

### Claude's Discretion
- Heartbeat API endpoint path and exact request/response shape
- Exact heartbeat background task implementation (asyncio.create_task, sleep loop, cancellation)
- Freshness calculation implementation (computed property vs periodic job vs on-read)
- Database schema changes for heartbeat storage (new columns on deployment table vs separate heartbeat log)
- Exact UI component structure, spacing, and color values for freshness badges and dependency pills
- Error handling edge cases (e.g., clock skew between gateway and hosted plane)
- How `last_seen_at` is updated (upsert on heartbeat receive)

</decisions>

<specifics>
## Specific Ideas

- Freshness should read as "what the control plane last heard" rather than "the deployment is definitely healthy now" — carry Phase 6 language into every freshness surface.
- The fleet table should feel like a monitoring dashboard, not a management form. Lead with operational state (freshness), not administrative state (enrollment).
- Dependency health pills should be the same compact style as the existing console — dense, informative, no wasted space.
- The trust-boundary disclosure card in the detail drawer reinforces that the hosted plane only knows what the deployment reports, not what's actually happening at runtime.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Trust boundary and hosted contract
- `src/nebula/models/hosted_contract.py` — HostedDeploymentMetadata Pydantic model with FreshnessStatus, HostedDependencySummary, HostedRemoteActionSummary, and HOSTED_EXCLUDED_DATA_CLASSES
- `docs/hosted-default-export.schema.json` — Committed JSON schema artifact defining the default metadata allowlist
- `tests/test_hosted_contract.py` — Regression tests locking schema exclusions
- `console/src/lib/hosted-contract.ts` — Frontend trust-boundary content module

### Enrollment and deployment identity (Phase 7 output)
- `src/nebula/services/enrollment_service.py` — Hosted-side enrollment service: slot creation, token generation, credential exchange, revoke/unlink lifecycle
- `src/nebula/services/gateway_enrollment_service.py` — Gateway-side outbound enrollment exchange, local identity storage, first heartbeat stub (line 94-97)
- `src/nebula/models/deployment.py` — DeploymentRecord, EnrollmentExchangeRequest/Response, DeploymentEnvironment, EnrollmentState types
- `src/nebula/db/models.py` — DeploymentModel ORM, EnrollmentTokenModel, LocalHostedIdentityModel

### API and routing patterns
- `src/nebula/api/routes/admin.py` — Admin CRUD endpoints with require_admin auth (template for heartbeat ingest endpoint)
- `src/nebula/core/container.py` — Service container DI pattern for registering new services
- `src/nebula/main.py` — App factory with async lifespan (heartbeat background task starts here)

### Console patterns
- `console/src/components/deployments/deployment-table.tsx` — Existing fleet table (name, env, enrollment state, enrolled_at) — needs freshness/version/last-seen columns
- `console/src/components/deployments/deployment-detail-drawer.tsx` — Existing detail drawer with lifecycle actions — needs freshness/dependency/trust-boundary sections
- `console/src/components/deployments/deployment-status-badge.tsx` — Existing enrollment state badge — needs freshness badge variant
- `console/src/lib/admin-api.ts` — Type-safe admin API client (extend with heartbeat/freshness types)

### Phase context
- `.planning/phases/06-trust-boundary-and-hosted-contract/06-CONTEXT.md` — Status language decisions (connected/degraded/stale/offline), disclosure surface requirements, "truthful uncertainty over optimism"
- `.planning/phases/07-deployment-enrollment-and-identity/07-CONTEXT.md` — Enrollment lifecycle, credential shape, outbound-only linking pattern
- `.planning/PROJECT.md` — Milestone goal and hybrid-model constraints
- `.planning/REQUIREMENTS.md` — INVT-01, INVT-02, INVT-04 requirements

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `gateway_enrollment_service.py` outbound HTTP pattern: httpx client with injectable transport for ASGI testing — reuse for heartbeat sender
- `enrollment_service.py` deployment CRUD: `list_deployments`, `get_deployment` already return `DeploymentRecord` — extend with last_seen_at and freshness fields
- `hosted_contract.py` `HostedDeploymentMetadata`: already defines freshness_status, freshness_reason, dependency_summary, last_seen_at — heartbeat should populate these fields
- `deployment-table.tsx` / `deployment-detail-drawer.tsx`: existing UI components to extend, not replace
- `deployment-status-badge.tsx`: existing badge component — add freshness-aware variant alongside enrollment state variant

### Established Patterns
- Outbound-only HTTP calls from gateway to hosted plane (enrollment exchange) — heartbeat follows same pattern
- Background task in asyncio event loop — match lifespan startup/shutdown pattern in `main.py`
- Hash-based credential auth — heartbeat authenticates with same deployment credential
- Compact, dense UI with colored badges — freshness badges and dependency pills follow same style
- React Query for data fetching — fleet inventory uses same query key and polling patterns

### Integration Points
- `main.py` lifespan: add heartbeat background task startup after enrollment check
- `enrollment_service.py` or new heartbeat service: add `record_heartbeat()` method to update last_seen_at and metadata
- `DeploymentModel` ORM: add `last_seen_at` column (or extend existing schema)
- `DeploymentRecord` Pydantic model: add `last_seen_at`, computed freshness fields for API responses
- New heartbeat ingest endpoint: `POST /v1/heartbeat` authenticated by deployment credential
- Console deployment table: replace enrollment status column with freshness column, add version and last-seen columns
- Console detail drawer: add freshness section, dependency health pills, trust-boundary card, capability chips

</code_context>

<deferred>
## Deferred Ideas

- Remote management actions, pull-based execution, and audit history — Phase 9
- Heartbeat history timeline or log in the detail drawer — future enhancement
- Fleet-wide compatibility matrix view — future enhancement for larger fleets
- Operator annotations or custom labels on deployments — future enhancement
- Diagnostic bundle upload or richer error reporting — future (requires explicit operator initiation per Phase 6 contract)
- Outage-safe serving validation and pilot docs — Phase 10
- Credential rotation mechanism — future phase

</deferred>

---

*Phase: 08-fleet-inventory-and-freshness-visibility*
*Context gathered: 2026-03-22*
