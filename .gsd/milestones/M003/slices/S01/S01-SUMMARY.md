# S01: Public embeddings endpoint — Summary

## Slice Summary

**Status:** done  
**Goal achieved:** yes

### What this slice actually delivered

S01 turned Nebula's previously internal embeddings capability into a real public adoption entrypoint by adding an authenticated `POST /v1/embeddings` route under the existing `/v1` surface. The new path accepts only the intended narrow contract — `model` plus `input` as either a single string or a flat list of strings — and returns an OpenAI-style float embeddings payload with stable ordering for batch inputs.

The route reuses the existing API-key and tenant-auth boundary rather than introducing a new auth mode, and it depends directly on the embeddings service instead of flowing through chat orchestration. Underneath that route, the embeddings service now truthfully forwards the caller-supplied `model`, supports ordered batch embedding generation, and exposes explicit internal failure modes for validation problems, upstream failures, and empty or malformed upstream embedding results.

S01 also established the first durable evidence path for embeddings adoption requests. Every `/v1/embeddings` response now carries `X-Request-ID`, and the same request can be correlated through the existing usage ledger via `/v1/admin/usage/ledger?request_id=...`. The persisted record stays metadata-only: request id, tenant id, requested model, route target, provider, terminal status, route reason, and policy outcome are recorded, while raw inputs and embedding vectors remain excluded.

### Key implementation outcomes

- Added `src/nebula/api/routes/embeddings.py` with a dedicated authenticated public embeddings route.
- Registered the router in `src/nebula/main.py` and exposed the service through `src/nebula/api/dependencies.py`.
- Added narrow public request/response models in `src/nebula/models/openai.py`:
  - `EmbeddingsRequest`
  - `EmbeddingsResponse`
  - `EmbeddingData`
  - `EmbeddingsUsage`
- Extended `src/nebula/services/embeddings_service.py` so the real service can:
  - accept single-string or flat list inputs
  - forward the caller's requested model upstream
  - preserve batch ordering
  - reject blank/invalid inputs explicitly
  - fail explicitly on upstream HTTP errors and empty/malformed embedding results
- Preserved backward compatibility for existing semantic-cache callers through the legacy `embed()` helper.
- Added focused coverage in:
  - `tests/test_embeddings_api.py`
  - `tests/test_governance_api.py -k embeddings`
  - `tests/test_service_flows.py -k embedding`

### Verification run for slice close-out

All slice-plan verification commands were re-run in the assembled worktree and passed:

1. `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`
2. `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings`
3. `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k embedding`
4. `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_service_flows.py -k 'embedding and (blank or upstream or empty)'`

### Observability / diagnostic confirmation

The slice plan's observability surfaces are working:

- Public `/v1/embeddings` responses emit `X-Request-ID`.
- Embeddings requests can be queried through `/v1/admin/usage/ledger?request_id=...`.
- The ledger row exposes embeddings-specific metadata such as:
  - `final_route_target="embeddings"`
  - `final_provider="ollama"`
  - `terminal_status`
  - `route_reason`
  - `policy_outcome`
- Tests confirm that ledger evidence does **not** include raw `input` text or returned `embedding` vectors.

### Patterns established for downstream slices

- **Public-surface first, narrow contract first:** new compatibility routes should lock down a typed request/response boundary before docs or migration proof widen the story.
- **Direct service wiring over orchestration reuse:** embeddings is intentionally not routed through chat orchestration; future embeddings work should preserve that separation unless a concrete need proves otherwise.
- **Request-scoped dependency access pattern:** public routes should use request-scoped accessors / `request.app.state.container`, not `Depends(get_container)`, to avoid FastAPI misreading helper parameters as request inputs.
- **Metadata-only evidence reuse:** adoption proof can usually piggyback on the existing usage ledger rather than inventing a new evidence store or persisting sensitive payloads.
- **Explicit internal failure taxonomy:** validation, upstream failure, and empty-result branches are now distinct and test-locked; later slices should document and demonstrate these branches rather than collapsing them into generic failure language.

### Requirement impact

- **R020** is now validated for the runtime slice scope: Nebula has a real authenticated narrow `/v1/embeddings` path with test-backed happy-path behavior and request-ID-linked durable evidence.
- **R021–R023** are not closed by S01 alone. S02 must publish the canonical contract boundary, S03 must prove realistic minimal-change migration, and S04 must assemble the broader evidence story around this runtime truth.
- **R024** remains a milestone-level guardrail, but S01 stayed within it by avoiding broad embeddings-option parity, SDK additions, new auth modes, hosted-plane expansion, or unrelated infrastructure changes.

### What the next slices should know

- S02 should treat this runtime path as the source of truth and document only the strict supported boundary: `model` + `input`, string or flat list input, standard float embeddings response shape, and explicit exclusions for broader OpenAI embeddings options.
- S03 can now build a realistic caller-swap proof directly against `/v1/embeddings` without inventing helper layers.
- S04 should reuse the established `X-Request-ID` → usage-ledger correlation pattern rather than adding new storage or console-first proof machinery unless a genuine trust gap appears.
- The current local verification path still depends on the repo-root virtualenv interpreter because `pytest` is not exposed directly on PATH in this worktree shell.

## UAT Readiness

This slice is ready for targeted human validation of the public embeddings runtime path. See `S01-UAT.md` for concrete test cases covering happy path, batch ordering, auth reuse, invalid-shape rejection, upstream failure mapping, and request-ID-to-ledger correlation.
