# S02 Research — Runtime outage behavior proof

## Summary
Targeted research. S02 is mostly backend outage-proof work using already-established S01 resilience fields. The codebase already has the typed contract (`dependency_class`, `lifecycle_state`, `serving_effect`, `reason_code`, `recovering`, recovery timestamps) and one existing outage-proof file, `tests/test_phase10_outage_safety.py`, but that file currently proves only metadata-only hosted-plane outages. The highest-value missing proof is runtime request behavior plus matching `/health/ready` and `/health/dependencies` truth for one serving-critical outage (PostgreSQL governance) and one serving-optional outage (Qdrant semantic cache or premium provider).

Active requirements supported here: R086, R087, R088. R086/R087 are the direct owners: exercise real outage classes end to end and prove safe serving vs fail-closed behavior. R088 is only partially touched here: S02 should verify the backend evidence surfaces are truthful, but broader operator presentation belongs to S03.

## Recommendation
Make S02 backend-first and keep UI work out unless needed for a narrow proof fixture. Reuse the `configured_app()` / `httpx.ASGITransport` test style and extend `tests/test_phase10_outage_safety.py` rather than inventing a new harness. First proof should be a serving-critical governance outage because it is the strongest fail-closed invariant and will expose whether request-path exceptions, response status, and readiness truth stay aligned. Second proof should be a serving-optional outage using semantic cache/Qdrant because the service already degrades to cache-disabled behavior and still serves locally/premium.

Per the installed `observability` and `write-docs` style guidance: keep proof pointer-first on existing runtime surfaces, and avoid widening into dashboard logic or new incident-state products. This slice should produce executable outage evidence, not new abstractions.

## Implementation Landscape

### Existing outage-proof harness
- `tests/test_phase10_outage_safety.py`
  - Already contains a realistic app+lifecycle harness via `configured_outage_client()`.
  - Uses `configured_app(...)`, starts real lifespan, installs request-serving stubs, and injects failure transports.
  - Current assertions prove hosted heartbeat / remote-management outage does **not** break `/v1/chat/completions` or readiness. This is a metadata-only pattern, useful as the template for S02 structure.
- `tests/support.py`
  - `configured_app()` creates an isolated DB, runs Alembic, and builds the real app.
  - `FakeCacheService` and `StubProvider` are ready-made seams for controlled serving-path tests.

### Serving-critical seam: governance / PostgreSQL
- `src/nebula/services/governance_store.py`
  - `health_status()` already maps DB query/schema failures to `dependency_class="serving_critical"`, `lifecycle_state="not_ready"`, `serving_effect="fail_closed"`.
  - This is the canonical health truth for the critical outage scenario.
- `src/nebula/services/chat_service.py`
  - Request flow depends on `policy_service.resolve(...)`, tenant auth/context, and usage persistence through `governance_store.record_usage(...)`.
  - A governance outage can fail in multiple phases: auth/policy read before routing, or usage persistence after provider completion.
  - Planner should pick one deterministic failure point first. The least ambiguous first proof is a pre-serving governance failure that blocks request honesty and should fail closed.
- `src/nebula/main.py`
  - `/health/ready` returns `503` when runtime status is `not_ready`; `/health/dependencies` returns the same readiness report body.
- `src/nebula/services/runtime_health_service.py`
  - Overall readiness already becomes `not_ready` if any dependency has `dependency_class == "serving_critical"` or `serving_effect == "fail_closed"` and is not ready.

### Serving-optional seam: semantic cache / Qdrant
- `src/nebula/services/semantic_cache_service.py`
  - `initialize()` marks `enabled=False` and stores `degraded_reason` if Qdrant setup fails.
  - `lookup()` and `store()` already fail soft: lookup miss/exception returns `None`; store exception only logs a warning.
  - `health_status()` maps Qdrant failures to `dependency_class="serving_optional"`, `lifecycle_state="degraded"`, `serving_effect="continuity_limited"`.
  - This is the cleanest optional-outage proof because the serving continuity behavior already exists and is explicit.
- `src/nebula/services/embeddings_service.py`
  - Also serving-optional, but impacts semantic-cache capability and can blur the proof with embedding availability. Qdrant-only outage is cleaner than Ollama outage for S02.
- `src/nebula/services/premium_provider_health_service.py`
  - Premium probe failures already degrade health truth, but request-path proof is less direct because premium serving can still succeed/fail independently of `/models` health probing. Better as a later extension, not the first optional proof.

### Existing operator/runtime consumer surfaces
- `console/src/app/api/runtime/health/route.ts` simply proxies `/health/dependencies` after admin session validation.
- `console/src/components/health/runtime-health-cards.tsx` renders generic cards and only has a special banner for optional degraded dependencies.
- `console/src/app/(console)/observability/page.tsx` already frames dependency health as supporting runtime context, not primary proof.
- `console/e2e/observability.spec.ts` already mocks degraded optional dependency state. This is useful evidence that S03 can consume S02 payloads without needing schema invention here.

## Natural seams for planning
1. **Critical outage proof task**
   - Extend outage tests to force a deterministic governance failure.
   - Verify request fails closed with bounded response semantics.
   - Verify `/health/ready` returns `503` and `/health/dependencies` shows governance as serving-critical/not_ready/fail_closed.
2. **Optional outage proof task**
   - Extend outage tests to force semantic-cache/Qdrant unavailability while local serving still works.
   - Verify chat completion still returns `200` with truthful route/fallback headers.
   - Verify readiness remains `200` with overall `ready` or `degraded` and dependency payload marks semantic cache degraded.
3. **Shared outage fixtures/support task**
   - Add helper fixtures/mutators in `tests/test_phase10_outage_safety.py` or `tests/support.py` only if needed to inject failure points cleanly.
   - Keep helpers local unless multiple future slices will reuse them.

## First proof
Serving-critical governance outage first. It is the biggest unblocker because:
- it proves S01’s fail-closed semantics actually bind request behavior, not just health payloads;
- it is the scenario most likely to reveal drift between request errors and readiness truth;
- it reduces ambiguity for later recovery/runbook work in S04.

Recommended first deterministic cut: simulate governance-store failure before request completion, then assert all three layers in one test:
- request response is non-200 and bounded/truthful;
- `/health/ready` is `503` with `status: not_ready`;
- `/health/dependencies` includes governance `dependency_class: serving_critical`, `serving_effect: fail_closed`, matching reason/detail.

## Constraints and watch-outs
- Avoid inventing a new resilience API or admin endpoint; roadmap/context explicitly forbid new dashboard/product sprawl.
- Prefer one outage class per test over broad chaos bundles; deterministic proof matters more than breadth.
- Be precise about where governance failure occurs. A post-provider `record_usage()` failure could create a tricky honesty question (did Nebula serve but fail evidence persistence?). That may be valuable later, but it is not the cleanest first proof for S02.
- Optional outage should not accidentally rely on cache being hit. The proof is continuity under disabled/degraded cache, so use a prompt path where a normal cache miss still serves correctly.
- S03 owns operator-visible wording and console depth. S02 should only lock the backend truth surfaces those UIs already consume.

## Files and purpose
- `tests/test_phase10_outage_safety.py` — primary slice target; add end-to-end outage proofs here.
- `tests/support.py` — optional test helper extensions if outage injection needs reusable fakes.
- `src/nebula/services/governance_store.py` — existing serving-critical health truth; likely read-only unless tests expose a missing reason/detail edge.
- `src/nebula/services/semantic_cache_service.py` — existing optional-degradation health truth and fail-soft serving seam.
- `src/nebula/services/runtime_health_service.py` — readiness aggregation already implements S01 semantics; modify only if outage tests expose drift.
- `src/nebula/services/chat_service.py` — request-path fail-closed / degraded continuity behavior; likely only touched if tests reveal untruthful handling.
- `src/nebula/main.py` — confirms readiness/dependencies endpoint contract; likely read-only.
- `console/src/app/api/runtime/health/route.ts`, `console/src/components/health/runtime-health-cards.tsx`, `console/src/app/(console)/observability/page.tsx` — downstream consumer references; likely no S02 change.

## Verification
Primary backend proof command:
- `.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q`

If request-path behavior changes touch broader routing/fallback semantics, add:
- `.venv/bin/pytest tests/test_service_flows.py -q`
- `.venv/bin/pytest tests/test_chat_completions.py -q`

If any console contract shape changes leak in unexpectedly, narrow verification:
- `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx`
- `npm --prefix console run test -- --run e2e/observability.spec.ts` (only if payload shape changes)

## Skill discovery notes
Directly relevant installed skills already exist:
- `observability` — useful to keep runtime truth operator-friendly without widening scope.
- `write-docs` — useful later for S04/S05 proof packaging, less so for implementation.
- `api-design` — optional if endpoint contract drift appears, but current slice should stay additive.

Promising non-installed skills discovered; do not install automatically:
- FastAPI: `npx skills add wshobson/agents@fastapi-templates` (17.8K installs)
- FastAPI: `npx skills add mindrally/skills@fastapi-python` (9.1K installs)
- Qdrant: `npx skills add giuseppe-trisciuoglio/developer-kit@qdrant` (961 installs)
- Qdrant: `npx skills add qdrant/skills@qdrant-clients-sdk` (803 installs)

These are only worth adding if the executor uncovers framework-specific issues not already obvious from local code patterns.
