# Research — M010 S01: Dependency failure contract

## Summary
- The current backend already has a coarse runtime dependency contract centered on `status`, `required`, and `detail`, exposed through `RuntimeHealthService.readiness()` and surfaced at both `/health/ready` and `/health/dependencies` (`src/nebula/services/runtime_health_service.py`, `src/nebula/main.py`). This is the natural anchor for S01.
- Today the contract is not yet typed around the milestone’s resilience classes. It distinguishes only required-vs-optional plus `ready` / `degraded` / `not_ready`; there is no shared vocabulary for **serving-critical**, **serving-optional**, or **metadata-only** dependency classes, no explicit recovery state, and no failure classification beyond free-text `detail`.
- Existing implementations already hint at the target split: `governance_store` is effectively serving-critical (`required=True`, `not_ready` on query/schema failure), while `semantic_cache`, `premium_provider`, `local_ollama`, and `retention_lifecycle` are currently modeled as optional and often degrade without blocking readiness (`src/nebula/services/governance_store.py`, `src/nebula/services/semantic_cache_service.py`, `src/nebula/services/premium_provider_health_service.py`, `src/nebula/services/embeddings_service.py`, `src/nebula/services/retention_lifecycle_service.py`).
- Request-path failure semantics are partially present in `ChatService`: local provider failure can fail closed with `502` when fallback is blocked, or degrade into premium fallback when allowed; cache lookup/store failures are swallowed into continuity behavior; policy-denied requests already persist explicit terminal status (`src/nebula/services/chat_service.py`, `tests/test_response_headers.py`). S01 should unify these already-existing request behaviors under one typed resilience contract instead of inventing a parallel mechanism.
- Operator/UI surfaces already follow the milestone’s “existing surfaces remain primary” rule. Observability explicitly states dependency health is supporting runtime context, not authority, and the hosted plane already carries only a coarse `dependency_summary` allowlist (`console/src/app/(console)/observability/page.tsx`, `src/nebula/models/hosted_contract.py`). That reduces scope: S01 can establish backend truth first without adding a new dashboard.

## Active requirements this slice supports
- **R086** — trustworthy behavior under dependency outage and recovery: S01 owns the typed contract that later outage proofs will exercise.
- **R087** — explicit safe degradation without false success: S01 needs to define which dependencies are fail-closed vs continuity-preserving.
- **R088** — operators can see degradation, last failure state, and recovery status: S01 must produce the vocabulary consumed later by health/admin/observability.
- **R089** — verified operator recovery paths: S01 should include recovery-state slots now so later slices do not bolt them on incompatibly.

## Memory / prior-art findings
- `MEM047` is directly relevant: prior work kept runtime diagnostics coarse and exposed them through existing health/dependency surfaces rather than widening into a new operational product. S01 should preserve that pattern.
- `MEM049` and `MEM051` reinforce the trust model: one shared backend contract first, operator surfaces second; request-level evidence remains authoritative and higher-level context remains supporting only. That matches the milestone context exactly.
- `MEM055` shows an established local pattern: keep compatibility field names where needed, but evolve the state vocabulary underneath via one serializable contract. S01 can likely follow the same migration style rather than forcing broad endpoint/UI churn.

## Recommendation
- Add a **shared resilience contract module** in backend models/types first, then migrate `RuntimeHealthService` and the per-dependency health producers onto it before touching broader request-path behavior.
- The first contract should be additive and compatibility-friendly. Keep top-level `status` / `required` / `detail` for existing callers, but add typed fields such as:
  - dependency class: `serving_critical | serving_optional | metadata_only`
  - lifecycle state: `ready | degraded | not_ready | recovering`
  - effect on serving: `fail_closed | continuity_limited | unaffected`
  - machine-readable reason / code
  - optional last failure / last recovery timestamps
- Do **not** start S01 by changing console copy or hosted payload shape. The highest risk is backend truth-model drift, not presentation.
- Use the existing `RuntimeHealthService` seam as the single aggregator. Individual services should report typed local facts; aggregation decides overall readiness and later slices can reuse the same payload everywhere.

## Implementation landscape

### 1. Current runtime truth seam
- `src/nebula/services/runtime_health_service.py`
  - Aggregates `gateway`, `governance_store`, `semantic_cache`, `local_ollama`, `premium_provider`, and `retention_lifecycle`.
  - Computes overall readiness by:
    - `not_ready` if any `required=True` dependency is not `ready`
    - `degraded` if any dependency is `degraded`
    - else `ready`
- `src/nebula/main.py`
  - `/health/ready` returns `200` for `ready` or `degraded`, `503` otherwise.
  - `/health/dependencies` currently returns the same readiness payload.
- Natural S01 seam: introduce new contract here without changing endpoint topology.

### 2. Existing dependency classifications hidden in code
- `src/nebula/services/governance_store.py`
  - `health_status()` is hard fail: `required=True`, `status=not_ready` when DB query/schema fails.
  - This is the clearest current **serving-critical** dependency.
- `src/nebula/services/semantic_cache_service.py`
  - Returns `degraded`, `required=False` when Qdrant is unavailable or collection missing.
  - Lookup/store failures already preserve serving continuity by returning `None` / logging warnings.
  - Strong candidate for **serving-optional**.
- `src/nebula/services/premium_provider_health_service.py`
  - Probe failure returns `degraded`, `required=False`.
  - In runtime semantics this is nuanced: premium can be optional for some routes but effectively required for premium-only tenants / fallback paths. S01 should document this mismatch explicitly; later slices may need request-path truth separate from global dependency optionality.
- `src/nebula/services/embeddings_service.py`
  - Local Ollama health is optional in the current model.
  - It influences cache viability and embeddings endpoint behavior, but not necessarily core chat serving for all paths.
- `src/nebula/services/retention_lifecycle_service.py`
  - Already demonstrates an optional background dependency with richer health metadata (`last_status`, `last_run_at`, `last_error`). This is the best local example for adding richer failure/recovery fields without breaking surfaces.

### 3. Request-path failure semantics already implemented
- `src/nebula/services/chat_service.py`
  - Cache disabled/unavailable path degrades silently to miss behavior.
  - Local provider failure can:
    - fail closed with `502` + explicit `route_reason=local_provider_error_fallback_blocked`
    - degrade into premium fallback when allowed
  - Premium fallback failure returns `502`.
- `tests/test_response_headers.py`
  - Already locks explicit headers and ledger terminal status for denied/fallback-blocked outcomes.
- Implication: the resilience contract must cover **dependency health** and **request handling consequences** together. If S01 only annotates health endpoints, later slices will still lack a shared serving-truth vocabulary.

### 4. Existing operator/hosted constraints
- `console/src/app/(console)/observability/page.tsx`
  - Explicit copy says dependency health is supporting runtime context and does not replace the ledger record.
  - S01 must preserve this hierarchy.
- `console/src/components/health/runtime-health-cards.tsx`
  - UI is generic and tolerant of extra fields; it already renders optional metrics when present. Good for additive backend fields later.
- `src/nebula/models/hosted_contract.py`
  - Hosted dependency reporting is intentionally coarse: `healthy`, `degraded`, `unavailable` lists only.
  - Hosted remains metadata-only; do not make hosted the first consumer of the new contract.

## Natural seams for planner decomposition
1. **Shared backend contract/types**
   - Add resilience/dependency-state models/enums/literals.
   - Preserve compatibility with existing `status` contract while introducing class/effect/recovery fields.
2. **Dependency producers migration**
   - Update `governance_store`, `semantic_cache_service`, `premium_provider_health_service`, `embeddings_service`, and `retention_lifecycle_service` to emit typed payloads.
   - Most independent work is here; each dependency can be migrated with focused tests.
3. **Runtime aggregation rules**
   - Update `RuntimeHealthService` overall-status logic to derive readiness from typed dependency classes/effects instead of only `required`.
   - Highest risk because it locks the milestone’s fail-closed vs degraded semantics.
4. **Contract tests**
   - Expand backend tests to prove serving-critical vs serving-optional behavior and payload vocabulary.
   - Do this before any operator-surface changes.

## First proof / highest-risk unblocker
- **First proof should be a pure backend contract test suite around `RuntimeHealthService` plus at least one serving-critical and one serving-optional producer.**
- Why this first:
  - It locks the meaning of “critical / optional / metadata-only” before implementation fans out.
  - It prevents later slices from building operator surfaces or outage harnesses against unstable wording.
  - It exposes the biggest ambiguity now: premium provider is globally optional in readiness but can still be request-critical in some tenant policies.
- Recommended initial examples:
  - `governance_store` => serving-critical, `not_ready`, effect `fail_closed`
  - `semantic_cache` => serving-optional, `degraded`, effect `continuity_limited`
  - one metadata/background seam (likely `retention_lifecycle`) => metadata-only, degraded but non-blocking

## Risks and changed assumptions
- **Premium provider classification is the main modeling trap.** Globally it is currently optional in health, but request-level semantics can become critical for premium-only/fallback scenarios. S01 should likely classify the dependency itself separately from per-request route consequences; otherwise the contract will lie.
- **`local_ollama` is also ambiguous.** It is optional in current health, but local-first serving can fail if Ollama is down and premium fallback is disabled. Again, system-level dependency class and request-level route effect must not be collapsed into one boolean.
- **Recovery is currently mostly implicit.** Existing health payloads usually report current state only; only `retention_lifecycle` carries historical fields. If S01 wants real recovery semantics later, it should reserve fields now even if only some dependencies can populate them immediately.
- **`/health/dependencies` currently mirrors readiness output exactly.** If future slices want a richer dependency contract without changing readiness semantics, keep `/health/ready` lightweight and let `/health/dependencies` be the richer truth payload; otherwise callers may assume both stay identical forever.

## Testing / verification targets
- Backend unit tests in `tests/test_health.py`
  - Extend current degraded/not-ready readiness tests to assert dependency class/effect/recovery fields.
  - Add overall-status derivation tests from typed dependency classes.
- Focused producer tests:
  - `tests/test_retention_lifecycle_service.py` is the best pattern for rich health payload assertions.
  - Add/extend tests for `semantic_cache_service.health_status()` and `governance_store.health_status()` behavior under failure.
- Request-path proof already has hooks:
  - `tests/test_response_headers.py`
  - `tests/test_chat_completions.py`
  - `tests/test_service_flows.py`
  - These should later assert mapping from provider/dependency failures to the shared resilience vocabulary, but for S01 the planner should likely keep this focused unless the contract directly touches headers or ledger row reasons.
- Verification commands:
  - `pytest tests/test_health.py`
  - `pytest tests/test_retention_lifecycle_service.py`
  - `pytest tests/test_response_headers.py -k fallback_blocked`
  - optionally `make test` after focused pass

## File list for planner
- `src/nebula/services/runtime_health_service.py` — aggregate dependency truth; primary contract seam
- `src/nebula/main.py` — readiness/dependencies endpoint behavior
- `src/nebula/services/governance_store.py` — serving-critical producer
- `src/nebula/services/semantic_cache_service.py` — serving-optional producer
- `src/nebula/services/premium_provider_health_service.py` — optional-but-request-sensitive producer
- `src/nebula/services/embeddings_service.py` — optional producer with local serving implications
- `src/nebula/services/retention_lifecycle_service.py` — richest existing health payload; pattern source
- `src/nebula/core/container.py` — dependency wiring if new health/resilience service types are introduced
- `tests/test_health.py` — contract-first verification
- `tests/test_retention_lifecycle_service.py` — example of richer health fields
- `tests/test_response_headers.py` — fail-closed continuity proof already locked for request path
- `console/src/components/health/runtime-health-cards.tsx` — additive consumer, likely no immediate change needed
- `console/src/app/(console)/observability/page.tsx` — supporting-context wording already aligned; avoid touching in S01 unless contract shape forces it

## Skill discovery notes
- Installed skills already cover the important planning patterns here:
  - `api-design` — relevant if the team wants to shape `/health/ready` vs `/health/dependencies` as distinct stability contracts.
  - `observability` — relevant because S01 is primarily about truthful runtime state and failure evidence.
  - `write-docs` — relevant if the contract should also be captured as a decision/spec.
- External skill search found relevant, not-installed options:
  - FastAPI: `npx skills add wshobson/agents@fastapi-templates` (17.8K installs)
  - Qdrant: `npx skills add giuseppe-trisciuoglio/developer-kit@qdrant` (961 installs)
  - Next.js search returned mostly docs-maintenance skills and does **not** look directly relevant to S01.
- Recommendation: no new install is necessary for this slice; local codebase patterns are already stronger than generic framework guidance.

## Planner guidance
- Plan S01 as **backend contract first, outage semantics second, UI later**.
- Keep compatibility for existing consumers by extending payloads rather than replacing `status`/`required` immediately.
- Separate:
  1. dependency class
  2. current lifecycle state
  3. effect on safe serving
  4. request-level consequence
- If only one deep change fits in S01, choose the shared typed contract and tests; later slices can attach real outage exercises and operator rendering to that stable base.
