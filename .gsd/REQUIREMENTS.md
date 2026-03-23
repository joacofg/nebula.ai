# Requirements

## Active

### ENRL-01 — Operator can register a self-hosted Nebula deployment with the hosted control plane without manual database edits.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Operator can register a self-hosted Nebula deployment with the hosted control plane without manual database edits.

### ENRL-02 — A self-hosted gateway can complete an explicit outbound-only linking flow using short-lived enrollment credentials and durable deployment-scoped credentials for steady-state communication.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

A self-hosted gateway can complete an explicit outbound-only linking flow using short-lived enrollment credentials and durable deployment-scoped credentials for steady-state communication.

### ENRL-03 — Operator can revoke, unlink, or relink a deployment without leaving duplicate or ghost active records in the hosted inventory.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Operator can revoke, unlink, or relink a deployment without leaving duplicate or ghost active records in the hosted inventory.

### INVT-01 — Hosted control plane can display deployment identity, environment label, Nebula version, registration time, and last-seen time for each linked deployment.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Hosted control plane can display deployment identity, environment label, Nebula version, registration time, and last-seen time for each linked deployment.

### INVT-02 — Hosted control plane shows deployment freshness using explicit connected, degraded, stale, or offline semantics with reason codes that do not overstate runtime health.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Hosted control plane shows deployment freshness using explicit connected, degraded, stale, or offline semantics with reason codes that do not overstate runtime health.

### INVT-03 — Loss of hosted control-plane connectivity does not break the self-hosted gateway's core serving path and is surfaced as degraded or stale hosted visibility instead of runtime failure.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Loss of hosted control-plane connectivity does not break the self-hosted gateway's core serving path and is surfaced as degraded or stale hosted visibility instead of runtime failure.

### INVT-04 — Deployment reports capability and version metadata so the hosted plane can show compatibility state and fail unsupported actions closed.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Deployment reports capability and version metadata so the hosted plane can show compatibility state and fail unsupported actions closed.

### RMGT-01 — Hosted control plane can queue at least one allowlisted, non-serving-impacting remote-management action for a linked deployment.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Hosted control plane can queue at least one allowlisted, non-serving-impacting remote-management action for a linked deployment.

### RMGT-02 — A linked deployment pulls remote-management actions outbound, applies them only after local authorization checks, and records auditable queued, applied, or failed outcomes.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

A linked deployment pulls remote-management actions outbound, applies them only after local authorization checks, and records auditable queued, applied, or failed outcomes.

### RMGT-03 — Remote-management actions are TTL-bound, idempotent, and prevented from directly mutating local runtime policy or provider credentials from the hosted plane.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Remote-management actions are TTL-bound, idempotent, and prevented from directly mutating local runtime policy or provider credentials from the hosted plane.

### TRST-01 — Hosted control plane clearly distinguishes hosted metadata from self-hosted runtime-enforced state in the product UI and architecture narrative.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Hosted control plane clearly distinguishes hosted metadata from self-hosted runtime-enforced state in the product UI and architecture narrative.

### TRST-02 — Security model states exactly what data leaves the self-hosted environment by default and excludes raw prompts, responses, provider credentials, and authoritative runtime policy state.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Security model states exactly what data leaves the self-hosted environment by default and excludes raw prompts, responses, provider credentials, and authoritative runtime policy state.

### TRST-03 — Docs and demo materials explain hybrid deployment onboarding, trust boundaries, remote-management safety limits, and hosted-control-plane outage behavior for pilot conversations.

- Status: active
- Class: core-capability
- Source: inferred
- Primary Slice: none yet

Docs and demo materials explain hybrid deployment onboarding, trust boundaries, remote-management safety limits, and hosted-control-plane outage behavior for pilot conversations.

## Validated

## Deferred

## Out of Scope
