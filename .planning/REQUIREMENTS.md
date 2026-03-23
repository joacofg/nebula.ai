# Requirements: Nebula.ai

**Defined:** 2026-03-18
**Core Value:** Reduce cost per successful LLM request while preserving reliability, control, and operator visibility.

## v2.0 Requirements

### Enrollment

- [x] **ENRL-01**: Operator can register a self-hosted Nebula deployment with the hosted control plane without manual database edits.
- [x] **ENRL-02**: A self-hosted gateway can complete an explicit outbound-only linking flow using short-lived enrollment credentials and durable deployment-scoped credentials for steady-state communication.
- [x] **ENRL-03**: Operator can revoke, unlink, or relink a deployment without leaving duplicate or ghost active records in the hosted inventory.

### Fleet Inventory and Status

- [x] **INVT-01**: Hosted control plane can display deployment identity, environment label, Nebula version, registration time, and last-seen time for each linked deployment.
- [x] **INVT-02**: Hosted control plane shows deployment freshness using explicit connected, degraded, stale, or offline semantics with reason codes that do not overstate runtime health.
- [ ] **INVT-03**: Loss of hosted control-plane connectivity does not break the self-hosted gateway's core serving path and is surfaced as degraded or stale hosted visibility instead of runtime failure.
- [x] **INVT-04**: Deployment reports capability and version metadata so the hosted plane can show compatibility state and fail unsupported actions closed.

### Remote Management

- [x] **RMGT-01**: Hosted control plane can queue at least one allowlisted, non-serving-impacting remote-management action for a linked deployment.
- [x] **RMGT-02**: A linked deployment pulls remote-management actions outbound, applies them only after local authorization checks, and records auditable queued, applied, or failed outcomes.
- [x] **RMGT-03**: Remote-management actions are TTL-bound, idempotent, and prevented from directly mutating local runtime policy or provider credentials from the hosted plane.

### Trust Boundary and Pilot Proof

- [x] **TRST-01**: Hosted control plane clearly distinguishes hosted metadata from self-hosted runtime-enforced state in the product UI and architecture narrative.
- [x] **TRST-02**: Security model states exactly what data leaves the self-hosted environment by default and excludes raw prompts, responses, provider credentials, and authoritative runtime policy state.
- [ ] **TRST-03**: Docs and demo materials explain hybrid deployment onboarding, trust boundaries, remote-management safety limits, and hosted-control-plane outage behavior for pilot conversations.

## Future Requirements

### Hosted Operations

- **HOPS-01**: Hosted control plane supports approval-gated remote actions beyond the initial allowlist.
- **HOPS-02**: Hosted control plane provides richer diagnostic and remediation guidance for heartbeat and compatibility failures.
- **HOPS-03**: Hosted control plane supports broader release orchestration or multi-deployment fleet actions.

### Account Model

- **ACCT-01**: Hosted control plane supports richer hosted user, organization, and RBAC workflows beyond the minimum needed for v2.0 validation.
- **ACCT-02**: Hosted control plane supports public self-serve signup and billing.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Public self-serve SaaS launch | This milestone is validating a hybrid control-plane direction, not launching a public hosted product. |
| Self-serve signup and billing | Commercial lifecycle work would overwhelm the control-plane validation signal. |
| Broad RBAC redesign | Identity and permissions should expand only where strictly required for the hosted-control-plane flow. |
| Arbitrary shell access, inbound tunnels, or generic remote execution | These break the self-hosted trust boundary and create avoidable security objections. |
| Default export of prompts, responses, request logs, or provider secrets to the hosted plane | Nebula's hosted layer is validating metadata-and-intent workflows, not centralizing customer runtime data. |
| Broad provider/commercial expansion in parallel | The milestone should isolate whether hybrid control-plane value is real before widening product scope again. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENRL-01 | Phase 7 | Complete |
| ENRL-02 | Phase 7 | Complete |
| ENRL-03 | Phase 7 | Complete |
| INVT-01 | Phase 8 | Complete |
| INVT-02 | Phase 8 | Complete |
| INVT-03 | Phase 10 | Pending |
| INVT-04 | Phase 8 | Complete |
| RMGT-01 | Phase 9 | Complete |
| RMGT-02 | Phase 9 | Complete |
| RMGT-03 | Phase 9 | Complete |
| TRST-01 | Phase 6 | Complete |
| TRST-02 | Phase 6 | Complete |
| TRST-03 | Phase 10 | Pending |

**Coverage:**
- v2.0 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-18 after v2.0 research synthesis*
