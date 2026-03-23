# Phase 10: Pilot Proof and Failure-Safe Operations - Research

**Researched:** 2026-03-23
**Domain:** hosted-control-plane outage safety, stale-visibility validation, and pilot-ready hybrid deployment narrative
**Confidence:** HIGH

## User Constraints

No phase-specific `CONTEXT.md` exists for Phase 10.

Applicable constraints from `REQUIREMENTS.md`, `ROADMAP.md`, and `STATE.md`:

- Hosted control plane remains metadata-and-intent only; local enforcement stays authoritative.
- Linking remains outbound-only with short-lived enrollment bootstrap and deployment-scoped steady-state credentials.
- Remote management stays limited to one audited, non-serving-impacting allowlisted action in v2.0.
- Loss of hosted control-plane connectivity must degrade hosted visibility only and must not break the self-hosted gateway serving path.
- Pilot materials must explain hybrid onboarding, trust boundaries, remote-management safety limits, and hosted outage behavior without overstating runtime health.
- Pilot materials must make explicit that the hosted plane is metadata-and-intent only while local enforcement remains authoritative.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INVT-03 | Loss of hosted control-plane connectivity does not break the self-hosted gateway's core serving path and is surfaced as degraded or stale hosted visibility instead of runtime failure. | Reuse the existing non-fatal enrollment, heartbeat, and remote-management background-task design; add explicit outage simulation tests that prove serving continues while hosted freshness becomes stale/offline. |
| TRST-03 | Docs and demo materials explain hybrid deployment onboarding, trust boundaries, remote-management safety limits, and hosted-control-plane outage behavior for pilot conversations. | Extend the existing schema-backed trust-boundary copy and pilot docs (`self-hosting.md`, `demo-script.md`, `pilot-checklist.md`) into one consistent pilot narrative with explicit outage behavior and management limits. |
</phase_requirements>

## Summary

Phase 10 should not introduce a new runtime subsystem. The repo already has the core proof points: startup enrollment failures are non-fatal, heartbeats log and retry without backoff or queuing, remote management starts in lifespan but fails closed when enrollment or local policy is missing, and hosted freshness is already computed separately from runtime health. The remaining implementation gap is evidence: automated tests that prove hosted outages only stale visibility, and docs/demo materials that turn the existing architecture into a pilot-ready story.

The standard architecture pattern here matches established control-plane/data-plane separation: an external control plane manages metadata and intent, while the local runtime continues serving with last-known local state. Envoy’s xDS protocol explicitly documents that last known configuration persists when the management server becomes unreachable, and Istio documents external control planes as a separation of management from data-plane services. Nebula should lean into that same pattern in its tests and docs, not hand-roll a more complex resiliency layer.

**Primary recommendation:** Plan Phase 10 as two additive workstreams only: `10-01` should add outage and mixed-failure integration tests around the existing services, and `10-02` should update the pilot docs and trust-boundary narrative so every artifact repeats the same message: hosted outage affects visibility and remote intent only; local serving remains authoritative.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | `>=0.115.0,<1.0.0` | Lifespan-managed startup/shutdown for enrollment, heartbeat, and remote management | Already the app’s runtime boundary; official guidance recommends `lifespan` for shared app resources |
| httpx | `>=0.27.0,<1.0.0` | Outbound hosted calls and ASGI-transport outage simulation in tests | Already used by enrollment, heartbeat, and remote management; supports direct ASGI app transport for deterministic integration tests |
| SQLAlchemy | `>=2.0.39,<3.0.0` | Persist deployment identity, last-seen timestamps, credential state, and remote-action audit state | Existing source of truth for hosted metadata and local identity state |
| pytest + pytest-asyncio | `>=8.2.0,<9.0.0` / `>=0.23.0,<1.0.0` | Backend outage-safety and mixed-failure integration coverage | Existing async-first test harness already covers enrollment, heartbeat, and remote management |
| Pydantic | `>=2.8.0,<3.0.0` | Hosted-contract schema and regression-safe content boundary | Existing canonical contract source for trust-boundary assertions |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Next.js | `^15.2.2` | Public trust-boundary page and console-hosted copy | Use for any pilot-facing hosted narrative that should stay consistent with the schema-backed contract |
| Vitest | `^3.0.8` | Console copy/content tests | Use when trust-boundary or deployment-surface copy changes |
| Playwright | `^1.51.0` | Optional smoke validation of the pilot flow | Use only if Phase 10 wants a repeatable UI walkthrough; not required for the core outage proof |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ASGI-transport integration tests | Docker or external-host chaos tests | External tests are slower and noisier; ASGI transport already matches existing repo patterns and proves the application-level guarantee deterministically |
| Existing stale/offline freshness semantics | New “hosted outage” runtime mode | A separate mode would duplicate the meaning already captured by `degraded`, `stale`, and `offline` |
| Updating current docs and trust page | Separate slide deck or one-off pilot brief | That creates narrative drift; the repo already has canonical pilot docs and schema-backed trust-boundary content |

**Installation:**
```bash
# No new package is required by the current research.
# Phase 10 should use the existing backend, console, and test stack.
```

## Architecture Patterns

### Recommended Project Structure
```text
tests/
├── test_phase10_outage_safety.py      # new: hosted outage does not break serving
└── test_remote_management_service.py  # extend: mixed hosted/local failure behavior

docs/
├── self-hosting.md                    # extend: hybrid onboarding + outage expectations
├── demo-script.md                     # extend: pilot talk track and outage-safe narrative
└── pilot-checklist.md                 # extend: explicit hosted-outage and safety-limit prep

console/src/
├── app/trust-boundary/page.tsx        # extend only if copy must surface outage semantics
└── lib/hosted-contract.ts             # keep as the single hosted narrative content source
```

### Pattern 1: Prove outage safety by breaking hosted calls, not local serving
**What:** Inject hosted-call failures into enrollment-adjacent services and keep serving requests against the same app instance.
**When to use:** `10-01` backend validation.
**Example:**
```python
# Source: repo pattern from tests/test_remote_management_service.py
transport = httpx.ASGITransport(app=app)
async with app.router.lifespan_context(app):
    app.state.container.heartbeat_service._http_transport = transport
    app.state.container.remote_management_service._http_transport = transport
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=True,
    ) as client:
        ...
```
Use the same injection seam, but point hosted URLs at an unreachable target or patch the transport to raise `httpx.ConnectError` / timeout for hosted endpoints only. Then assert:
- `/v1/chat/completions` still succeeds
- `/health/ready` remains `200` when only hosted connectivity is missing
- heartbeat/remote-management logs warn or fail closed
- hosted freshness eventually reads `stale` or `offline`

### Pattern 2: Treat hosted freshness as visibility, never as runtime authority
**What:** Keep hosted freshness derived only from `last_seen_at`, and continue using local readiness for serving health.
**When to use:** All Phase 10 test design and pilot narrative.
**Example:**
```python
# Source: src/nebula/services/heartbeat_ingest_service.py
if delta <= CONNECTED_WINDOW:
    return "connected", f"Last heartbeat {_human_delta(delta)} ago"
elif delta <= DEGRADED_WINDOW:
    return "degraded", f"No heartbeat for {_human_delta(delta)}"
elif delta <= STALE_WINDOW:
    return "stale", f"No heartbeat for {_human_delta(delta)}"
else:
    return "offline", f"No heartbeat since {last_seen_at.strftime('%b %-d %H:%M')}"
```
Phase 10 should not add cause inference like “control plane down” into freshness reasons. Keep the UI and docs explicit that freshness is hosted visibility, not a serving-path verdict.

### Pattern 3: Reuse the existing fail-closed remote-management posture
**What:** Hosted outages and stale state should prevent further hosted actions without impacting local serving.
**When to use:** Mixed-failure validation and pilot messaging.
**Example:**
```python
# Source: src/nebula/services/remote_management_service.py
if (
    credential is None
    or not self.settings.hosted_plane_url
    or not getattr(self.settings, "remote_management_enabled", False)
):
    return
```
The plan should verify the current principle in three cases:
- hosted plane unreachable: no serving failure, no remote apply
- local policy disallows remote action: hosted action fails closed, serving unaffected
- stale or offline hosted freshness: action UI remains blocked and narrative explains why

### Pattern 4: Keep pilot narrative schema-backed and repo-native
**What:** Derive pilot trust-boundary messaging from `docs/hosted-default-export.schema.json` and the existing hosted content module instead of inventing new copy silos.
**When to use:** `10-02` docs and demo materials.
**Example:**
```typescript
// Source: console/src/lib/hosted-contract.ts
export const trustBoundaryCopy = {
  heading: "What this deployment shares",
  metadataOnly: "Metadata-only by default",
  freshnessWarning: "Hosted freshness is not local runtime authority.",
  notInPath: "Nebula's hosted control plane is not in the request-serving path.",
  excludedHeading: "Excluded by default",
  footnote: "Richer diagnostics must be operator-initiated exceptions to this default contract.",
} as const;
```
Phase 10 docs should add pilot-specific wording around onboarding and outage behavior, but they should still point back to the same canonical contract and excluded-data list.

### Anti-Patterns to Avoid
- **Hosted outage as app failure:** Do not make `/health/ready` or serving requests depend on heartbeat success, poll success, or hosted freshness.
- **Narrative drift across docs:** Do not put different trust-boundary or outage wording in `self-hosting.md`, `demo-script.md`, and the trust-boundary page.
- **New retry/queue machinery:** Do not add backoff schedulers, heartbeat queues, or local replay buffers for this phase.
- **Previewing future hosted scope:** Do not imply shell access, generic remote execution, or hosted authority over local runtime policy.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hosted outage simulation | Ad hoc sleep-based network flake tests | Existing `configured_app()` + `httpx.ASGITransport` + injectable transport seams | Deterministic, fast, and already proven in repo tests |
| Runtime/hosted health synthesis | New “global status” layer | Existing local readiness endpoints plus hosted freshness semantics | Keeps truth separate: local runtime authority vs hosted visibility |
| Pilot narrative source of truth | Standalone slides or duplicated copy blocks | Existing docs plus schema-backed hosted contract module | Prevents trust-boundary drift |
| Remote safety controls | New approval or execution framework | Existing allowlist, stale/offline gating, and fail-closed reasons | v2.0 scope is deliberately narrow |

**Key insight:** The expensive mistake in this phase is not missing another retry mechanism. It is muddying the trust boundary by making hosted visibility look like runtime authority or by letting pilot docs imply more hosted power than the code actually has.

## Common Pitfalls

### Pitfall 1: Testing hosted outage without proving serving continuity
**What goes wrong:** The test suite proves heartbeat failure, but never asserts that chat serving still works during the outage.
**Why it happens:** It is easier to test the hosted subsystem in isolation than to keep a serving-path assertion in the same scenario.
**How to avoid:** Every INVT-03 outage test should pair one hosted failure assertion with one successful serving-path assertion.
**Warning signs:** Tests only inspect logs or freshness fields and never hit `/v1/chat/completions`.

### Pitfall 2: Treating stale visibility as proof of runtime failure
**What goes wrong:** Docs or UI copy imply that `stale` or `offline` means the gateway is down.
**Why it happens:** Hosted freshness feels like health, but Phase 8 deliberately scoped it as hosted visibility only.
**How to avoid:** Repeat the wording “hosted freshness is not local runtime authority” and keep reason codes time-based only.
**Warning signs:** Copy uses phrases like “gateway unhealthy” or “deployment unavailable” based only on hosted freshness.

### Pitfall 3: Forgetting lifespan management in async hosted-call tests
**What goes wrong:** Background tasks or startup hooks never initialize in tests, so outage simulations give false confidence.
**Why it happens:** HTTPX documents that ASGI lifespan events are not triggered automatically by `AsyncClient`.
**How to avoid:** Wrap async integration tests in `app.router.lifespan_context(app)` or equivalent.
**Warning signs:** Tests patch service transports directly but never enter the lifespan context.

### Pitfall 4: Mixed-failure cases remain untested
**What goes wrong:** Hosted outage and local policy failure are each tested alone, but not together.
**Why it happens:** Single-failure tests are simpler, but pilot objections usually ask about compound conditions.
**How to avoid:** Add at least one scenario where hosted visibility is stale or unreachable while local runtime still serves and remote actions remain blocked or no-op.
**Warning signs:** The plan covers only heartbeat failure or only remote-action auth failure, not both in one narrative.

### Pitfall 5: Pilot docs claim more than the shipped repo proves
**What goes wrong:** The demo story promises hosted onboarding flow, outage dashboard behavior, or remediation UX that does not exist.
**Why it happens:** Pilot docs tend to slide into roadmap messaging.
**How to avoid:** Keep every pilot claim grounded in current docs, tests, and existing console surfaces.
**Warning signs:** Phrases like “the hosted plane will automatically recover and reconcile” without a tested implementation path.

## Code Examples

Verified patterns from repo and official sources:

### Lifespan-managed startup and cleanup
```python
# Source: https://fastapi.tiangolo.com/advanced/events/
@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize shared resources
    yield
    # clean up shared resources

app = FastAPI(lifespan=lifespan)
```

### ASGI transport for in-process integration tests
```python
# Source: https://www.python-httpx.org/advanced/transports/
transport = httpx.ASGITransport(app=app)
async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
    response = await client.get("/")
```

### Heartbeat failure stays non-fatal
```python
# Source: src/nebula/services/heartbeat_service.py
try:
    response = await client.post(
        f"{self.settings.hosted_plane_url}/v1/heartbeat",
        json=payload.model_dump(),
        headers={"X-Nebula-Deployment-Credential": credential},
    )
    response.raise_for_status()
except Exception as exc:
    logger.warning("Heartbeat failed: %s. Will retry at next interval.", exc)
```

### Enrollment failure stays non-fatal at startup
```python
# Source: src/nebula/main.py
if settings.enrollment_token:
    try:
        await container.gateway_enrollment_service.attempt_enrollment(
            settings.enrollment_token
        )
    except Exception as exc:
        logging.getLogger(__name__).error(
            "Enrollment startup hook failed unexpectedly: %s. "
            "Gateway will start without hosted features.",
            exc,
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Control plane directly gates runtime behavior | Control plane manages metadata/intention; local runtime remains authoritative | Current Nebula v2.0 direction, aligned with current Istio external-control-plane guidance | Hosted outages become visibility/management issues, not request-path outages |
| Runtime health and hosted connectivity conflated | Local readiness and hosted freshness are separate signals | Phase 8 introduced explicit freshness states | Pilot messaging can be precise about stale visibility vs serving health |
| Docs describe hosted model abstractly | Docs should show onboarding, safety limits, and outage behavior concretely | Phase 10 | Pilot conversations become credible because objections are answered with tested behavior |

**Deprecated/outdated:**
- Using `startup`/`shutdown` events as the primary app lifecycle pattern is outdated for this repo; FastAPI currently recommends the `lifespan` parameter instead.
- Treating hosted freshness as an inferred root-cause detector is outdated relative to Phase 8’s time-based reason-code model.

## Open Questions

1. **Should Phase 10 add any new product UI for hosted-outage explanation, or keep it doc-only?**
   - What we know: The current product already has freshness badges, trust-boundary copy, and remote-action fail-closed messaging.
   - What's unclear: Whether pilot conversations need one explicit hosted-outage callout in the deployment drawer or trust page.
   - Recommendation: Default to doc/demo updates only unless a real pilot script gap remains after `10-02`.

2. **How much outage simulation is enough for INVT-03?**
   - What we know: The code already handles enrollment, heartbeat, and remote-management failures non-fatally.
   - What's unclear: Whether one integration test per subsystem is enough, or whether the plan should include a compound scenario.
   - Recommendation: Include one compound test: hosted calls fail, serving still works, and hosted freshness later becomes stale/offline.

3. **Should Playwright be part of Phase 10 validation?**
   - What we know: The repo already has Playwright configured, but current trust-boundary coverage is mostly Vitest and backend tests.
   - What's unclear: Whether the phase needs a browser-level regression proof for the demo flow.
   - Recommendation: Keep Playwright optional. Use it only if the updated pilot flow introduces UI behavior that unit/component tests cannot cover well.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` `>=8.2.0,<9.0.0`, `pytest-asyncio` `>=0.23.0,<1.0.0`, `vitest` `^3.0.8` |
| Config file | `pyproject.toml`, `console/vitest.config.ts`, `console/playwright.config.ts` |
| Quick run command | `pytest tests/test_phase10_outage_safety.py -x` |
| Full suite command | `make test` and `make console-test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INVT-03 | Hosted outage does not break serving; hosted visibility becomes stale/offline instead of runtime failure | integration | `pytest tests/test_phase10_outage_safety.py -x` | ❌ Wave 0 |
| TRST-03 | Trust-boundary and hybrid pilot copy stays aligned with canonical hosted contract and public trust page | unit + manual docs review | `npm --prefix console run test -- --run src/app/trust-boundary/page.test.tsx` | ✅ |

### Sampling Rate
- **Per task commit:** `pytest tests/test_phase10_outage_safety.py -x`
- **Per wave merge:** `make test` and `make console-test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_phase10_outage_safety.py` — covers INVT-03 with hosted outage plus successful serving assertions
- [ ] Extend `tests/test_remote_management_service.py` with a mixed hosted/local failure case that keeps serving unaffected
- [ ] Manual pilot-doc review checklist for `docs/self-hosting.md`, `docs/demo-script.md`, and `docs/pilot-checklist.md` — existing automated tests do not validate the full narrative

## Sources

### Primary (HIGH confidence)
- Repo code and docs:
  - `src/nebula/main.py`
  - `src/nebula/services/gateway_enrollment_service.py`
  - `src/nebula/services/heartbeat_service.py`
  - `src/nebula/services/heartbeat_ingest_service.py`
  - `src/nebula/services/remote_management_service.py`
  - `docs/architecture.md`
  - `docs/self-hosting.md`
  - `docs/demo-script.md`
  - `docs/pilot-checklist.md`
  - `console/src/lib/hosted-contract.ts`
  - `tests/test_gateway_enrollment.py`
  - `tests/test_heartbeat_api.py`
  - `tests/test_remote_management_service.py`
  - `tests/test_hosted_contract.py`
- FastAPI lifespan docs: https://fastapi.tiangolo.com/advanced/events/
- HTTPX transports docs: https://www.python-httpx.org/advanced/transports/
- Envoy xDS protocol docs: https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol.html
- Istio deployment models docs: https://istio.io/latest/docs/ops/deployment/deployment-models/

### Secondary (MEDIUM confidence)
- None needed.

### Tertiary (LOW confidence)
- None needed.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all recommended libraries and patterns are already present in the repo and verified in project files or official docs.
- Architecture: HIGH - repo behavior matches official lifecycle and control-plane/data-plane separation guidance.
- Pitfalls: HIGH - pitfalls are directly grounded in existing implementation seams, prior phase decisions, and official HTTPX/FastAPI testing behavior.

**Research date:** 2026-03-23
**Valid until:** 2026-04-22
