# Feature Research

**Domain:** Hosted control plane for self-hosted Nebula gateway deployments
**Researched:** 2026-03-18
**Confidence:** MEDIUM

## Feature Landscape

Scope note: this document covers only the new hosted-control-plane behavior for Nebula v2.0 validation. It assumes Nebula already ships self-hosted deployment, operator auth, tenant management, API keys, policy editing, playground, observability, and docs/demo proof.

### Table Stakes (Users Expect These)

Features users assume exist in a credible pilot. Missing these makes the hosted plane feel like a demo instead of an operational product.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Deployment registration and claim flow | Credible hybrid products use an explicit enrollment step so operators can attach a self-hosted node to a hosted account without database edits or inbound exposure. | MEDIUM | Depend on existing Nebula deployment flow, operator auth, and tenant model. Use a one-time enrollment token or install command, stable deployment ID, environment labels, and revocation/re-registration path. |
| Fleet inventory with stable identity | Operators expect a hosted list of linked deployments with name, tenant, environment, version, and last-seen metadata. | MEDIUM | Depend on existing tenant management and observability metadata. Minimum fields: deployment ID, customer-chosen label, environment, gateway version, connector version if separate, first seen, last heartbeat, last config sync result. |
| Heartbeat and scoped status model | Adjacent products consistently show connected/degraded/disconnected state plus last contact time; pilots need this before any remote action is credible. | MEDIUM | Depend on registration and observability plumbing. Status must be scoped: control-plane connectivity, not blanket runtime health. Add reason codes such as auth failure, version mismatch, clock skew, network unreachable. |
| Trust-boundary visibility in UI and docs | Buyers expect a hybrid product to state exactly what leaves the environment, what remains local, and whether the hosted plane can affect serving. | LOW | Depend on existing docs/demo package and policy/observability surfaces. Show outbound-only link, metadata classes exported, secrets handling, and that request routing/policy enforcement remain local when the hosted plane is unreachable. |
| Version and compatibility visibility | Hosted inventory is expected to show version drift and whether a deployment can safely use a hosted feature or action. | LOW | Depend on inventory. Keep this to version reporting and compatibility badges for v2.0; do not expand into full release orchestration yet. |
| Narrow remote-action queue with audit trail | A pilot hosted plane usually needs at least one remotely initiated action to prove value beyond passive inventory. | HIGH | Depend on registration, heartbeat, audit logging, and operator permissions. Keep the action set small: request support bundle upload, request config/policy bundle pull, rotate registration credential, or trigger a safe connector reconnect. No arbitrary shell, no persistent tunnel by default. |

### Differentiators (Competitive Advantage)

Features that are not required for pilot credibility, but would make Nebula’s hybrid story materially stronger.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Explicit three-lane status view: control-plane link, local policy enforcement, and remote-action eligibility | Prevents the most common hybrid-product ambiguity: “green” status that only means the agent is online, not that the gateway is healthy or safely manageable. | MEDIUM | Builds on existing observability and denied-path explainability. This is a strong fit for Nebula because operators already think in terms of route, policy, and runtime evidence. |
| Per-deployment telemetry disclosure card | Turns the trust boundary into a product feature: operators can see which metadata fields are exported and which data classes never leave the environment. | LOW | Reuse existing documentation work and expose it in-product. Strong pilot differentiator because it supports security review without adding heavy compliance scope. |
| Approval-gated remote action execution | Hosted operator requests an action, but the local deployment or local admin must approve or has preconfigured allowlists. This is safer than direct push control. | HIGH | Good follow-on if v2.0 needs stronger trust posture. Depends on the remote-action queue and existing console auth. Better fit than broad RBAC redesign because scope stays narrow. |
| Diagnostic-rich heartbeat failures | Status entries that explain why a deployment is offline or degraded reduce support load and make pilots look more mature. | MEDIUM | Add actionable failure classes: invalid token, TLS trust failure, proxy/firewall block, version skew, rejected action policy. This builds directly on the heartbeat model instead of widening product scope. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that sound attractive in a hosted plane but are the wrong move for Nebula v2.0 validation.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Arbitrary shell / terminal access from the hosted plane | It looks like the fastest way to prove “remote management.” | It blows up the trust boundary, raises procurement and security objections, and shifts Nebula toward a remote-admin product instead of an AI gateway. | Ship an allowlisted action queue with audit logs and explicit local execution semantics. |
| Push-based config mutation that applies immediately from the cloud | Teams want centralized control and faster incident response. | It weakens the self-hosted reliability story, risks surprise config drift, and makes hosted outages feel dangerous. | Use signed desired-state bundles that the deployment pulls, validates, and applies locally, ideally with dry-run or approval support. |
| Streaming prompts, responses, or full request logs to the hosted plane by default | It seems useful for fleet observability and support. | It contradicts the hybrid trust story and turns a metadata plane into a data-plane replication problem. | Keep hosted inventory at metadata level only; rely on local observability for request content and expose only aggregate or explicitly opted-in diagnostics. |
| Full SaaS account lifecycle expansion in the same milestone | Hosted products often bundle org invites, billing, self-serve signup, and rich RBAC. | Nebula’s current milestone is validating hosted control-plane value, not launching a public SaaS. This scope would drown the core signal. | Reuse existing operator auth and tenant model, keep account workflows narrow, and defer self-serve/billing/RBAC redesign. |

## Feature Dependencies

```text
Deployment registration and claim flow
    └──requires──> Existing self-hosted deployment path
    └──requires──> Existing operator auth + tenant management

Fleet inventory with stable identity
    └──requires──> Deployment registration and claim flow

Heartbeat and scoped status model
    └──requires──> Fleet inventory with stable identity
    └──requires──> Connector-to-hosted authenticated channel

Trust-boundary visibility in UI and docs
    └──requires──> Heartbeat/status field definitions
    └──requires──> Existing docs/demo narrative

Version and compatibility visibility
    └──requires──> Fleet inventory with stable identity

Narrow remote-action queue with audit trail
    └──requires──> Deployment registration and claim flow
    └──requires──> Heartbeat and scoped status model
    └──requires──> Existing auth/audit surfaces

Approval-gated remote action execution
    └──enhances──> Narrow remote-action queue with audit trail

Streaming request data to hosted plane
    └──conflicts──> Trust-boundary visibility in UI and docs
```

### Dependency Notes

- **Fleet inventory requires deployment registration:** the hosted plane cannot show stable deployment records until each self-hosted gateway has a durable identity and claim flow.
- **Heartbeat/status requires an authenticated outbound channel:** without a connector identity and signed heartbeat payloads, “last seen” is weak and remote actions are unsafe.
- **Trust-boundary visibility requires precise field definitions:** Nebula cannot honestly claim what the hosted plane sees until registration, heartbeat, and inventory payloads are concretely defined.
- **Narrow remote actions require auditability first:** once the hosted plane can initiate actions, audit logs and permission checks stop being optional.
- **Streaming request data conflicts with the hybrid story:** it turns the hosted plane into a shadow observability backend and undermines the explicit local-enforcement boundary.

## MVP Definition

### Launch With (v2.0 validation)

Minimum feature set needed to validate whether the hosted-control-plane direction is worthwhile.

- [ ] Deployment registration and claim flow — proves operators can attach self-hosted Nebula deployments without manual database work.
- [ ] Fleet inventory with identity, last seen, version, and environment labels — gives the hosted plane a useful operator surface on day one.
- [ ] Scoped heartbeat/status model — validates whether hosted visibility is trustworthy instead of vague.
- [ ] Trust-boundary visibility in UI/docs — necessary for pilot credibility and security conversations.
- [ ] One narrow remote action with audit trail — enough to prove the hosted plane adds operational value beyond passive inventory.

### Add After Validation (v2.x)

Features worth adding once pilots confirm the hybrid model is desirable.

- [ ] Approval-gated remote action execution — add when pilot users ask for tighter local control over hosted-initiated actions.
- [ ] Diagnostic-rich heartbeat failures — add when support friction shows that “offline” is too coarse.
- [ ] Compatibility and version drift guidance — add when more than one supported connector/gateway version is active in the field.

### Future Consideration (v3+)

Features to defer until the product boundary is proven and the trust model is accepted.

- [ ] Broader fleet actions across many deployments — defer until targeting, rollback, and blast-radius controls are justified.
- [ ] Rich hosted policy orchestration and release channels — defer until Nebula decides the hosted plane should own more lifecycle state.
- [ ] Self-serve SaaS onboarding, billing, and broad RBAC redesign — defer until hybrid adoption is validated commercially.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Deployment registration and claim flow | HIGH | MEDIUM | P1 |
| Fleet inventory with stable identity | HIGH | MEDIUM | P1 |
| Heartbeat and scoped status model | HIGH | MEDIUM | P1 |
| Trust-boundary visibility in UI and docs | HIGH | LOW | P1 |
| Narrow remote-action queue with audit trail | HIGH | HIGH | P1 |
| Version and compatibility visibility | MEDIUM | LOW | P2 |
| Diagnostic-rich heartbeat failures | MEDIUM | MEDIUM | P2 |
| Approval-gated remote action execution | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for v2.0 validation
- P2: Valuable follow-on once the hosted pattern is proven
- P3: Defer unless pilot feedback specifically demands it

## Competitor Feature Analysis

| Feature | AWS Systems Manager / Azure Arc | Portainer Edge / Cloudflare Tunnel / Replicated | Our Approach |
|---------|----------------------------------|-------------------------------------------------|--------------|
| Registration | Uses explicit activation/onboarding flows with managed-node identity and account linkage. | Uses agent or tunnel enrollment tied to a hosted account or customer instance. | One-time Nebula deployment claim flow with stable deployment ID and revocation path. |
| Inventory | Shows node metadata such as identity, tags, agent version, and connection state. | Shows edge endpoints, instances, or tunnels with state and labels. | Hosted deployment list with environment, tenant, versions, and last-seen data only. |
| Heartbeat | Uses agent check-in / connection status but does not imply every workload is healthy. | Uses connector status with clear online/down/degraded semantics. | Explicitly scope status to control-plane connectivity and separate it from local serving health. |
| Remote management | Offers powerful fleet command/extension features. | Often offers support-oriented or edge-focused remote actions, sometimes including tunnels. | Ship only one allowlisted action path for v2.0; avoid shell access and broad mutation. |
| Trust boundary | Enterprise tools document metadata and agent behavior, but the boundary is often buried in docs. | Tunnel/control-plane docs often clarify that connector health is not origin-service health. | Make the boundary visible in product UI and demo narrative, not just documentation footnotes. |

## Sources

- Nebula project context: `/Users/joaquinfernandezdegamboa/Documents/Playground/.planning/PROJECT.md`
- Cloudflare Tunnel monitoring docs: https://developers.cloudflare.com/tunnel/monitoring/ (HIGH for status-scope pattern)
- AWS Systems Manager Run Command docs: https://docs.aws.amazon.com/systems-manager/latest/userguide/send-commands-multiple.html (HIGH for remote-action breadth and fleet-targeting pattern)
- Azure Arc overview and connected machine guidance: https://learn.microsoft.com/azure/azure-arc/overview and related connected machine docs (MEDIUM for managed-node inventory and hybrid identity pattern)
- Portainer Edge Agent documentation: https://docs.portainer.io/admin/environments/add/docker/edge-agent (MEDIUM for outbound registration and edge inventory pattern)
- Replicated Vendor Platform docs: https://docs.replicated.com/ (MEDIUM for hosted metadata/instance visibility pattern)

## Recommendation

For Nebula v2.0, treat the hosted plane as a metadata-and-intent layer, not a remote-control surface. The table stakes are enrollment, inventory, scoped heartbeat semantics, explicit trust-boundary disclosure, and one narrow audited remote action. That is enough to test whether customers value hosted visibility and safe operational assistance without undermining the self-hosted reliability story Nebula already established in v1.0.

---
*Feature research for: Hosted control plane for self-hosted Nebula deployments*
*Researched: 2026-03-18*
