# Phase 9: Audited Remote Management - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove one narrow remote-management workflow that is initiated from the hosted plane, pulled outbound by a linked deployment, authorized locally, and recorded with audit history. This phase is limited to one allowlisted non-serving-impacting action plus the queue, polling, apply, TTL, idempotency, and audit semantics needed to make that workflow credible. It does not add arbitrary remote execution, multi-action orchestration, local runtime-policy mutation, provider-credential mutation, or broader approval/RBAC systems.

</domain>

<decisions>
## Implementation Decisions

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

</decisions>

<specifics>
## Specific Ideas

- The first remote action should prove that the hosted plane can safely initiate a meaningful operational workflow without becoming a remote shell.
- Credential rotation is stronger than a "refresh now" ping because it demonstrates real management value, but it still stays outside the request-serving path.
- The operator note captured at queue time should read like change intent, not freeform chat. Short and auditable beats verbose.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Trust boundary and prior hosted-phase decisions
- `.planning/phases/06-trust-boundary-and-hosted-contract/06-CONTEXT.md` — Hosted plane is metadata-and-intent only, local runtime remains authoritative, and remote management must stay narrow.
- `.planning/phases/07-deployment-enrollment-and-identity/07-CONTEXT.md` — Deployment identity lifecycle, steady-state credential model, revoke/unlink/relink behavior, and outbound-only linking pattern.
- `.planning/phases/08-fleet-inventory-and-freshness-visibility/08-CONTEXT.md` — Freshness semantics, deployment capability display, and fail-closed compatibility expectations for remote actions.
- `.planning/PROJECT.md` — Milestone goal and constraint that hosted outages or features must not break self-hosted serving.
- `.planning/REQUIREMENTS.md` — RMGT-01, RMGT-02, RMGT-03 and the explicit out-of-scope ban on arbitrary remote execution.
- `.planning/ROADMAP.md` — Phase 9 goal, success criteria, and plan split across queue contract, polling/apply flow, and audit semantics.

### Existing backend contract and identity sources
- `src/nebula/models/hosted_contract.py` — Canonical hosted metadata contract, including `remote_action_summary`.
- `docs/hosted-default-export.schema.json` — Schema artifact downstream UI/docs already rely on for hosted-visible fields.
- `src/nebula/models/deployment.py` — Deployment record and enrollment exchange models that Phase 9 will extend.
- `src/nebula/db/models.py` — Deployment and local hosted-identity ORM patterns, plus the likely insertion points for remote-action persistence.
- `src/nebula/services/enrollment_service.py` — Hosted-side deployment credential lifecycle and deployment-state transitions.
- `src/nebula/services/gateway_enrollment_service.py` — Gateway-side local identity storage and current hosted credential usage.

### Existing outbound and hosted-surface patterns
- `src/nebula/api/routes/heartbeat.py` — Current deployment-authenticated hosted ingest pattern.
- `src/nebula/services/heartbeat_service.py` — Existing outbound background-service pattern for deployment-to-hosted polling/sending behavior.
- `src/nebula/services/heartbeat_ingest_service.py` — Existing hosted-side freshness/update path and deployment-authenticated service pattern.
- `console/src/components/deployments/deployment-detail-drawer.tsx` — Existing per-deployment hosted surface where the action should live.
- `console/src/components/deployments/deployment-table.tsx` — Existing fleet view that should remain list-first without becoming a bulk-actions surface.
- `console/src/lib/admin-api.ts` — Hosted admin client pattern for deployment detail actions and result polling.

### Existing regression coverage and research
- `tests/test_hosted_contract.py` — Locks the hosted metadata contract and `remote_action_summary` shape.
- `.planning/research/FEATURES.md` — Phase-level rationale for one narrow audited remote action and explicit rejection of shell/tunnel style management.
- `.planning/research/ARCHITECTURE.md` — Early architecture sketch for remote-management service boundaries and apply/audit wiring.
- `.planning/research/PITFALLS.md` — Security and scope risks around remote-management breadth, auditability, and local authorization.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/nebula/services/enrollment_service.py`: already owns hosted-side deployment credential issuance, revoke, and relink flows, making it the natural base for a safe credential-rotation action.
- `src/nebula/services/gateway_enrollment_service.py`: already persists the local hosted identity and exposes the raw deployment credential used for hosted auth, so Phase 9 can rotate this specific linkage without touching tenant or provider state.
- `src/nebula/api/routes/heartbeat.py`: already authenticates deployment-scoped outbound traffic with `X-Nebula-Deployment-Credential`, which is a close fit for a deployment polling/apply channel.
- `src/nebula/models/hosted_contract.py`: already reserves `remote_action_summary` in the hosted metadata contract, so audit rollups have a defined hosted-visible destination.
- `console/src/components/deployments/deployment-detail-drawer.tsx`: already concentrates deployment-specific lifecycle controls in one place, which matches the single-deployment action decision.

### Established Patterns
- Hosted communication remains outbound-only from the gateway. Phase 9 should reuse that model for action polling rather than inventing inbound control channels.
- Deployment credentials are already scoped to hosted-plane communication and stored separately from tenant/provider credentials. That separation is what makes credential rotation safe here.
- Phase 8 established capability-based fail-closed UI behavior for unsupported remote actions; Phase 9 should honor that instead of optimistic enablement.
- Prior phases consistently favored explicit operator visibility and auditability over hidden automation, which supports mandatory queued/applied/failed history and explicit reason fields.

### Integration Points
- Hosted-side queue creation and audit history will likely extend deployment-oriented services and admin routes alongside the existing enrollment/fleet APIs.
- Gateway-side polling should integrate with the current lifecycle/background-task wiring rather than creating a second unrelated scheduler path.
- Local authorization should read from runtime settings plus local hosted identity state before any apply step runs.
- Hosted deployment detail UI should add one action card, one confirmation flow, and a compact action-history section without changing the fleet table into a command center.

</code_context>

<deferred>
## Deferred Ideas

- Approval-gated local execution that requires explicit local admin confirmation before apply
- Additional remote actions such as support-bundle upload, config snapshot pull, or forced heartbeat refresh
- Fleet-wide action targeting, multi-deployment orchestration, or retries across a cohort
- Generic remote execution, shell access, inbound tunnels, or direct mutation of local runtime policy/provider credentials
- Broader hosted RBAC and approval workflows beyond what this single action strictly needs

</deferred>

---

*Phase: 09-audited-remote-management*
*Context gathered: 2026-03-22*
