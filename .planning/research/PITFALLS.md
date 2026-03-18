# Pitfalls Research

**Domain:** Hybrid hosted control plane for a self-hosted AI gateway
**Researched:** 2026-03-18
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Blurring the trust boundary between hosted metadata and local enforcement

**What goes wrong:**
The hosted plane starts acting like part of the request-serving path or like the source of truth for runtime policy enforcement. Pilot buyers then hear "self-hosted" in marketing but discover that real control lives in Nebula Cloud.

**Why it happens:**
Teams add hosted inventory, health, and remote actions incrementally and never freeze a hard contract for what is metadata, what is advisory control, and what remains locally enforced.

**How to avoid:**
Write an explicit boundary before implementation: hosted plane may store deployment identity, last-seen state, version, capability metadata, and queued management intents; the local gateway remains the enforcement point for request routing, provider credentials, policy decisions, and serving continuity. Document "control plane down" behavior as a product requirement, not an implementation detail.

**Warning signs:**
- Hosted connectivity is required for the gateway to start or to evaluate request policy
- UI copy says "managed" without stating what is still enforced locally
- Engineers need to ask whether a given setting is authoritative in cloud or on-box

**Phase to address:**
Phase 1: Trust boundary and protocol contract

---

### Pitfall 2: Using weak deployment registration and long-lived shared secrets

**What goes wrong:**
A copied registration token, reused bootstrap secret, or environment-wide API key can enroll the wrong gateway, impersonate an existing deployment, or keep talking to the hosted plane after ownership should have changed.

**Why it happens:**
Bootstrap is treated as a convenience flow instead of an identity problem. Teams use one token for both first-linking and long-term communication, or they never separate enrollment credentials from rotating operational credentials.

**How to avoid:**
Use a one-time or short-lived bootstrap flow to link a deployment, then issue separate rotating credentials for steady-state communication. Prefer outbound mutual authentication with per-deployment identity. If cloud metadata can attest the instance, use it; otherwise require explicit operator confirmation. Support revoke, re-link, and ownership transfer as first-class lifecycle flows.

**Warning signs:**
- The same secret appears in docs for bootstrap and ongoing heartbeats
- Multiple deployments can be linked by the same token without approval
- There is no credible answer for "how do we revoke a stolen registration token?"

**Phase to address:**
Phase 2: Secure enrollment and identity lifecycle

---

### Pitfall 3: Making the hosted plane part of the serving reliability path

**What goes wrong:**
Self-hosted gateways lose serving capability, degrade policy correctness, or block startup when the hosted plane is slow or unavailable. The product stops being credibly self-hosted the first time a control-plane outage happens.

**Why it happens:**
Status sync, config fetch, or remote command polling is implemented inline with request handling or startup readiness. Engineers optimize for "single source of truth" instead of local survivability.

**How to avoid:**
Keep registration, heartbeats, and remote-management polling asynchronous and outside the request path. Cache the last valid local config. Make hosted-originated changes explicit, versioned, and applied locally only after validation. Define a degraded mode where the gateway keeps serving and the hosted UI shows "stale/unknown" rather than "down."

**Warning signs:**
- Request latency rises when hosted APIs are slow
- Gateway startup fails if Nebula Cloud is unreachable
- Operators cannot explain what happens during a hosted outage

**Phase to address:**
Phase 1: Trust boundary and protocol contract, then Phase 5: Pilot resilience drills

---

### Pitfall 4: Treating heartbeats as truth instead of as a lease with staleness semantics

**What goes wrong:**
The hosted console shows deployments as healthy when they are partitioned, shows them as dead during temporary network loss, or hides uncertainty behind a single green badge. Operators make decisions from stale status.

**Why it happens:**
Teams implement "last ping wins" status with no lease duration, no stale state, no distinction between app heartbeat and runtime health, and no server-side interpretation rules.

**How to avoid:**
Model heartbeats as leases with explicit expiry windows and separate fields for `last_seen`, `reported_at`, `expires_at`, and local health summary. Distinguish `healthy`, `degraded`, `stale`, `offline`, and `unknown`. Tie status visibility to monotonic sequence numbers or timestamps and include version/capability metadata so status is interpretable.

**Warning signs:**
- "Online" means only "we received an HTTP POST recently"
- There is no `stale` or `unknown` state in the UI
- Heartbeats come from a sidecar that can live while the actual gateway is unhealthy

**Phase to address:**
Phase 3: Heartbeats, status model, and hosted UX honesty

---

### Pitfall 5: Shipping broad remote management before proving a narrow safe command set

**What goes wrong:**
Remote management expands from "safe pilot value" into shell-like control, arbitrary config mutation, or destructive operations that customers will not trust. One bad remote action can damage the entire hybrid story.

**Why it happens:**
Once a command channel exists, every missing operational feature looks easy to add. Product pressure pushes the system from narrow management intents into generic remote execution.

**How to avoid:**
Start with a tiny allowlist of idempotent, low-blast-radius actions such as "request config reload," "rotate hosted-plane credentials," or "run connectivity self-check." Require explicit action type, issuer, TTL, idempotency key, audit trail, result code, and local authorization policy. Reject arbitrary shell execution and hidden config patching.

**Warning signs:**
- Remote management is described as "we can just send commands"
- There is no per-action approval, TTL, or replay protection
- Engineers propose SSH-like fallbacks for operational convenience

**Phase to address:**
Phase 4: Narrow remote management with audit and rollback

---

### Pitfall 6: Exfiltrating too much tenant data to make hosted visibility feel useful

**What goes wrong:**
Prompts, responses, provider secrets, customer identifiers, or detailed local topology leak into the hosted plane because the team uses request payloads to power status pages and support workflows. Trust erodes immediately, especially for self-hosted buyers.

**Why it happens:**
Hosted UX is easier to build when raw payloads are centralized. Teams blur diagnostic metadata with customer content and fail to enforce data minimization at the protocol level.

**How to avoid:**
Define a strict hosted metadata schema: deployment identity, software version, heartbeat state, coarse health, and explicit remote-action audit data only. Make any request or content telemetry opt-in and separately governed. Redact secrets before serialization, and state in docs exactly what leaves the environment by default.

**Warning signs:**
- Hosted APIs accept arbitrary JSON "status blobs"
- Support/debug workflows depend on shipping prompts or raw provider errors by default
- Docs cannot answer "what data leaves the box?" in one paragraph

**Phase to address:**
Phase 1: Trust boundary and protocol contract, reinforced in Phase 5: Pilot docs and demo narrative

---

### Pitfall 7: Ignoring revocation, unlink, and ghost deployment cleanup

**What goes wrong:**
A deployment is cloned, rebuilt, renamed, or retired, but the hosted plane still shows it as active, still accepts old credentials, or cannot cleanly transfer ownership. Inventory becomes untrustworthy and support workflows get messy fast.

**Why it happens:**
Teams design the happy-path enroll flow only. They skip tombstones, explicit unlink states, key rotation, and duplicate-identity handling because the first demo only needs "register once."

**How to avoid:**
Design the full lifecycle: enroll, rotate, unlink, revoke, retire, and reclaim. Store immutable deployment IDs separate from human-readable names. Detect duplicate identities, show conflicts in the UI, and make stale records expire or archive automatically.

**Warning signs:**
- Deleting a deployment in cloud does not invalidate its communication credentials
- Reinstalling the same deployment creates multiple indistinguishable records
- There is no operator flow for "this machine is gone, remove its trust"

**Phase to address:**
Phase 2: Secure enrollment and identity lifecycle

---

### Pitfall 8: Skipping version and capability negotiation

**What goes wrong:**
The hosted plane assumes every gateway supports the same heartbeat fields, action types, and config semantics. Older deployments then misreport health, reject actions, or apply incompatible changes.

**Why it happens:**
Teams control both sides early on and hard-code payload shapes instead of designing a versioned protocol with capability discovery.

**How to avoid:**
Version the registration, heartbeat, and action schemas from the start. Require deployments to report software version and capabilities. Gate remote actions on capability checks. Maintain a compatibility matrix and fail closed when the hosted plane wants an unsupported action.

**Warning signs:**
- Heartbeat or command payloads have no schema version
- Hosted code dispatches actions by assumed product version instead of negotiated capability
- Upgrade guidance says "deploy latest everywhere" because mixed versions break

**Phase to address:**
Phase 1: Trust boundary and protocol contract, then Phase 5: Pilot upgrade and rollback validation

## Technical Debt Patterns

Shortcuts that look acceptable in a pilot but become expensive quickly.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Reusing one static registration secret for enroll plus runtime heartbeats | Very fast first demo | Impersonation risk, no clean rotation, weak ownership transfer | Never |
| Treating hosted status as a free-form JSON blob from the gateway | Fast UI iteration | Unstable schema, impossible compatibility guarantees, accidental data leakage | Only for throwaway prototypes, not v2.0 validation |
| Building remote management as arbitrary config patch delivery | Flexible feature velocity | Hidden blast radius, hard rollback, no trustable audit story | Never |
| Inferring deployment identity from hostname alone | Easy onboarding | Clones collide, rebuilds fork inventory, ghost records accumulate | Never |
| Polling hosted config on every request to keep state "fresh" | Simplifies consistency reasoning | Breaks self-hosted reliability and increases latency | Never |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Hosted registration API | Accepting blind enrollments from any bearer of a token | Use one-time bootstrap plus per-deployment operational credentials and explicit operator confirmation |
| Gateway heartbeat pipeline | Reporting from a process that is not the actual request-serving runtime | Report both agent connectivity and local gateway health, and show them separately |
| Local persistence | Storing hosted-issued config only in memory | Persist the last accepted local state and require explicit revalidation on updates |
| Hosted UI | Presenting a single "healthy" badge for all conditions | Separate connectivity freshness, local runtime health, and remote-action status |
| Remote command queue | Allowing actions to execute after long offline periods without TTL or dedupe | Require TTL, idempotency keys, action status transitions, and local replay rejection |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| High-frequency heartbeats with verbose payloads | Control-plane write amplification, noisy dashboards, expensive retention | Send small lease updates on a sane interval and separate detailed diagnostics from heartbeat cadence | Usually breaks first at multi-deployment pilot scale, not massive scale |
| Fan-out polling from every deployment on a short interval | Spiky hosted load and thundering herd behavior | Jitter polling, back off on failures, and avoid tight loops for command retrieval | Breaks as soon as dozens of deployments reconnect after an outage |
| Status recomputation from raw event history on every page load | Slow fleet inventory pages and misleading stale summaries | Materialize latest deployment state and append audit events separately | Breaks once operators manage more than a handful of deployments |
| Shipping full diagnostic payloads for every heartbeat | Storage cost and privacy risk increase together | Keep heartbeats tiny and move detailed diagnostics behind explicit local export flows | Breaks during real pilot traffic and support usage |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Using shared or non-expiring enrollment credentials | Deployment impersonation and unauthorized fleet joins | One-time bootstrap, short TTL, rotate to per-deployment credentials after linking |
| Allowing hosted-originated actions without local authorization checks | Cloud compromise becomes gateway compromise | Enforce allowlisted actions and local policy checks before execution |
| Sending plaintext secrets in remote action payloads or audit logs | Credential leakage through hosted logs and support tooling | Use local secret references or encrypted parameter stores, never plaintext action arguments |
| Treating "outbound-only" as sufficient security by itself | False confidence; stolen credentials still grant control-plane access | Combine outbound transport with strong identity, revocation, scoping, and auditability |
| Failing to scope identity claims narrowly enough | Token replay across environments or tenants | Bind credentials to deployment ID, tenant/account, environment, and capability set |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Saying "self-hosted" without a concrete hosted-data disclosure | Buyers assume hidden SaaS dependence and lose trust | Put the trust boundary and default data egress in the first screen and first doc page |
| Showing "online" with no freshness window | Operators over-trust stale data | Show last seen, freshness state, and which signals are locally reported versus cloud-observed |
| Hiding remote actions inside generic settings saves | Operators cannot tell what was requested remotely versus changed locally | Surface remote actions as discrete audited events with actor, time, target, and outcome |
| Making unlink/revoke a support-only operation | Operators fear lock-in and shadow records | Provide visible self-service unlink and credential rotation flows |

## "Looks Done But Isn't" Checklist

- [ ] **Registration:** Often missing ownership transfer and duplicate identity handling — verify reinstallation, cloning, and revoke/re-link flows
- [ ] **Heartbeats:** Often missing `stale` and `unknown` semantics — verify the UI becomes honest during packet loss and hosted outages
- [ ] **Hosted visibility:** Often missing a strict metadata contract — verify docs state exactly what leaves the environment by default
- [ ] **Remote management:** Often missing TTL, idempotency, and replay protection — verify queued actions cannot execute twice or days later
- [ ] **Hybrid reliability:** Often missing outage drills — verify the self-hosted serving path continues during total hosted-plane loss
- [ ] **Versioning:** Often missing capability negotiation — verify older gateways are shown accurately and unsupported actions fail closed

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Blurred trust boundary shipped to pilots | HIGH | Freeze new hosted features, publish a hard boundary doc, move any runtime-critical logic back on-box, and rerun outage drills |
| Weak registration secrets leaked or reused | HIGH | Revoke bootstrap tokens, rotate all operational credentials, force re-link where identity cannot be proven, and audit past enrollments |
| Misleading heartbeat semantics | MEDIUM | Introduce stale/offline states, backfill lease expiry fields, and annotate prior status records as unreliable if needed |
| Unsafe remote management action shipped | HIGH | Disable the action type server-side, invalidate queued actions, publish audit guidance, and reduce the command surface to an allowlist |
| Ghost deployments and duplicate identities | MEDIUM | Add tombstones and conflict detection, merge or archive records, and require fresh attestations for ambiguous deployments |
| Version skew breaking hosted actions | MEDIUM | Gate actions by capability, hotfix schema negotiation, and document a minimum supported version for pilots |

## Pitfall-to-Phase Mapping

Suggested phase structure for this milestone:
- Phase 1: Trust boundary and protocol contract
- Phase 2: Secure enrollment and identity lifecycle
- Phase 3: Heartbeats, status model, and hosted UX honesty
- Phase 4: Narrow remote management with audit and rollback
- Phase 5: Pilot docs, resilience drills, and upgrade validation

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Blurred hosted/local trust boundary | Phase 1 | Hosted outage drill proves serving still works and docs clearly state local enforcement boundaries |
| Weak registration identity | Phase 2 | Bootstrap token reuse, stolen token, revoke, and ownership transfer scenarios all fail safely |
| Hosted plane on serving path | Phase 1, then Phase 5 | Gateway continues serving with cloud disconnected and status degrades honestly to stale/unknown |
| Misleading heartbeat semantics | Phase 3 | UI and API expose freshness windows and differentiate local runtime health from connectivity |
| Over-broad remote management | Phase 4 | Every remote action is allowlisted, idempotent, TTL-bound, audited, and locally authorized |
| Excessive data egress to hosted plane | Phase 1, then Phase 5 | Data disclosure doc matches observed network payloads in test captures |
| Missing revoke/unlink lifecycle | Phase 2 | Reinstall, retire, unlink, and clone scenarios do not create ghost or privileged stale records |
| Version/capability mismatch | Phase 1, then Phase 5 | Mixed-version pilot test shows unsupported actions fail closed without corrupting status |

## Sources

- [Kubernetes Leases](https://kubernetes.io/docs/concepts/architecture/leases/) - official lease-based heartbeat pattern; HIGH confidence
- [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/) - outbound-only, redundant connector pattern; HIGH confidence
- [Cloudflare control/data plane separation pattern](https://developers.cloudflare.com/reference-architecture/diagrams/storage/durable-object-control-data-plane-pattern/) - separation rationale; MEDIUM confidence for Nebula adaptation
- [Tailscale KB: What happens when the coordination server is down?](https://tailscale.com/kb/1023/troubleshooting#what-happens-when-the-coordination-server-is-down) - self-hosted connectivity should survive control-plane loss; HIGH confidence
- [SPIFFE/SPIRE configuring node attestation](https://spiffe.io/docs/latest/deploying/configuring/) - attested workload/node identity patterns; HIGH confidence
- [Elastic Agent command reference](https://www.elastic.co/docs/reference/fleet/agent-command-reference) - enrollment workflow, tags, and privilege constraints in managed-agent systems; MEDIUM confidence
- [AWS Systems Manager Run Command](https://docs.aws.amazon.com/systems-manager/latest/userguide/running-commands.html) - remote command logging and secret-handling constraints; HIGH confidence

---
*Pitfalls research for: Hybrid hosted control plane for a self-hosted AI gateway*
*Researched: 2026-03-18*
