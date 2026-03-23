# Requirements

## Active

No active milestone requirements.

## Validated

### ENRL-01 — Operator can register a self-hosted Nebula deployment with the hosted control plane without manual database edits.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Operator can register a self-hosted Nebula deployment with the hosted control plane without manual database edits.

### ENRL-02 — A self-hosted gateway can complete an explicit outbound-only linking flow using short-lived enrollment credentials and durable deployment-scoped credentials for steady-state communication.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

A self-hosted gateway can complete an explicit outbound-only linking flow using short-lived enrollment credentials and durable deployment-scoped credentials for steady-state communication.

### ENRL-03 — Operator can revoke, unlink, or relink a deployment without leaving duplicate or ghost active records in the hosted inventory.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Operator can revoke, unlink, or relink a deployment without leaving duplicate or ghost active records in the hosted inventory.

### INVT-01 — Hosted control plane can display deployment identity, environment label, Nebula version, registration time, and last-seen time for each linked deployment.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Hosted control plane can display deployment identity, environment label, Nebula version, registration time, and last-seen time for each linked deployment.

### INVT-02 — Hosted control plane shows deployment freshness using explicit connected, degraded, stale, or offline semantics with reason codes that do not overstate runtime health.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Hosted control plane shows deployment freshness using explicit connected, degraded, stale, or offline semantics with reason codes that do not overstate runtime health.

### INVT-03 — Loss of hosted control-plane connectivity does not break the self-hosted gateway's core serving path and is surfaced as degraded or stale hosted visibility instead of runtime failure.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Loss of hosted control-plane connectivity does not break the self-hosted gateway's core serving path and is surfaced as degraded or stale hosted visibility instead of runtime failure.

### INVT-04 — Deployment reports capability and version metadata so the hosted plane can show compatibility state and fail unsupported actions closed.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Deployment reports capability and version metadata so the hosted plane can show compatibility state and fail unsupported actions closed.

### RMGT-01 — Hosted control plane can queue at least one allowlisted, non-serving-impacting remote-management action for a linked deployment.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Hosted control plane can queue at least one allowlisted, non-serving-impacting remote-management action for a linked deployment.

### RMGT-02 — A linked deployment pulls remote-management actions outbound, applies them only after local authorization checks, and records auditable queued, applied, or failed outcomes.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

A linked deployment pulls remote-management actions outbound, applies them only after local authorization checks, and records auditable queued, applied, or failed outcomes.

### RMGT-03 — Remote-management actions are TTL-bound, idempotent, and prevented from directly mutating local runtime policy or provider credentials from the hosted plane.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Remote-management actions are TTL-bound, idempotent, and prevented from directly mutating local runtime policy or provider credentials from the hosted plane.

### TRST-01 — Hosted control plane clearly distinguishes hosted metadata from self-hosted runtime-enforced state in the product UI and architecture narrative.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Hosted control plane clearly distinguishes hosted metadata from self-hosted runtime-enforced state in the product UI and architecture narrative.

### TRST-02 — Security model states exactly what data leaves the self-hosted environment by default and excludes raw prompts, responses, provider credentials, and authoritative runtime policy state.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Security model states exactly what data leaves the self-hosted environment by default and excludes raw prompts, responses, provider credentials, and authoritative runtime policy state.

### TRST-03 — Docs and demo materials explain hybrid deployment onboarding, trust boundaries, remote-management safety limits, and hosted-control-plane outage behavior for pilot conversations.

- Status: validated
- Class: core-capability
- Source: archived v2.0 milestone

Docs and demo materials explain hybrid deployment onboarding, trust boundaries, remote-management safety limits, and hosted-control-plane outage behavior for pilot conversations.

## Deferred

No deferred requirements recorded.

## Out of Scope

- Public self-serve signup and billing before the hybrid pilot story is validated.
- Broad RBAC redesign beyond what the hosted-control-plane workflow strictly needs.
- Deep enterprise procurement or compliance packaging before the product boundary is proven.
- Expanding provider and commercialization features in parallel with the control-plane validation work.
