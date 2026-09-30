# Fase 3 — Router aprendido de tres niveles — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Train and evaluate a cascaded logistic router over nomic prompt embeddings on the phase-2 tier labels, publish its cost/quality frontier against the heuristic and random baselines, and wire it into the gateway so `nebula-auto` routes to local / economy / frontier by a per-tenant quality target.

**Architecture:** Offline half in `scripts/router/` (numpy, dev-only): embed → cross-validate → sweep thresholds → frontier + baselines → artifact JSON + report + thesis block. Online half in `src/nebula/`: a stdlib `learned_router.py` that loads the artifact and turns a vector + quality target into a tier; `RouterService` consults it when enabled; `ChatService` embeds once and reuses the vector for the router and the cache; the premium provider receives the tier's model.

**Tech Stack:** Python 3.12, numpy (dev), FastAPI, SQLAlchemy + Alembic, Ollama (nomic-embed-text), OpenRouter.

**Spec:** `docs/superpowers/specs/2026-09-30-fase3-router-aprendido.md`

## Global Constraints

- Branch `fase3-router`; commit per task; PR + merge after `make lint`, `make test`, `make console-test` green (pre-authorised).
- Never modify `scripts/metric_validation/`, `benchmarks/metric-validation/`, `docs/evaluation.md`, `tests/test_metric_validation.py`, or `benchmarks/ground-truth/v1/` data.
- Heavy runs via `darwin-throttle`; tests without network, Ollama or Qdrant.
- `numpy` only in `[project.optional-dependencies].dev`; nothing under `src/nebula/` imports numpy.
- `NEBULA_LEARNED_ROUTER_ENABLED` defaults to false; existing tests must pass unchanged in behaviour.
- `RouteTarget` stays `Literal["local","premium"]`; ledger `final_route_target` values unchanged.
- Code/comments/commits in English, thesis text in Spanish. Commit trailer:
  `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_012q5mScYuHfCrhfoySuctuw`.
- Spend for this phase: latency probe only (< USD 0.5).

## Review Focus

1. A tenant whose `routing_quality_target` is above every operating point's quality must get all-frontier, never an index error — Task 1.
2. Embedding failure (Ollama down) with the learned router enabled must fall back to the heuristic with a signal, and the cache must still work as before — Tasks 6–7.
3. The same prompt in ES and EN must never be split across train/test folds (leakage inflates the frontier) — Task 2.
4. `calibrated_routing_enabled=false` must disable the learned router too, and explicit model / `local_only` / `premium_only` must bypass it — Task 6.
5. Fallback local→premium must use the economy model when configured, and the ledger must price by the model that actually answered — Task 7.

---

### Task 0: Corpus loader and embeddings (offline)

**Files:** Create `scripts/router/__init__.py`, `scripts/router/data.py`, `scripts/router/embed.py`; add `numpy>=2.0,<3.0` to dev extras in `pyproject.toml`; test `tests/test_router_offline.py`.

**Interfaces — Produces:**
- `data.Example(key: str, lang: str, prompt_id: str, task_type: str, text: str, local_ok: bool, economy_ok: bool, cost_economy: float, cost_frontier: float)`; `key = f"{lang}:{prompt_id}"`.
- `data.load_examples(root: Path, tiers_file: str) -> list[Example]` — ES prompts from `prompts.es.jsonl`, EN from `prompts.en.jsonl` filtered by the ES `en_subset`; labels from the tiers file (`local_substitutable`, `economy_substitutable`); costs from `responses/haiku.<lang>.jsonl` and `responses/gpt41.<lang>.jsonl` (`cost_usd`). Raises `ValueError` if a label is `None` or a cost row is missing.
- `embed.PREFIXES = ("none", "classification")`; `embed.apply_prefix(text, prefix) -> str` (`none` → text, else `f"{prefix}: {text}"`); `embed.embeddings_path(prefix) -> Path` = `artifacts/router-embeddings/{prefix}.json`; `embed.load_embeddings(prefix) -> dict[str, list[float]]`; CLI `python -m scripts.router.embed` embeds every example key per prefix via Ollama `/api/embed` (batch 32), resumable, and records model digest.

- [ ] Tests: `load_examples` on a tiny fixture tree in `tmp_path` (2 ES prompts one with `en_subset`, tiers rows, response rows) returns 3 examples with right labels and costs; missing cost row raises; `apply_prefix`.
- [ ] Implement, run, lint, commit `feat(router): corpus loader and prompt embeddings`.

### Task 1: Runtime model (stdlib)

**Files:** Create `src/nebula/services/learned_router.py`; test `tests/test_learned_router.py`.

**Interfaces — Produces:**
```python
@dataclass(frozen=True, slots=True)
class OperatingPoint:
    tau_local: float
    tau_economy: float
    quality: float
    cost_per_prompt: float

@dataclass(frozen=True, slots=True)
class TierChoice:
    tier: Literal["local", "economy", "frontier"]
    p_local: float
    p_economy: float
    point: OperatingPoint

class LearnedRouterModel:
    version: str; embedding_model: str; prefix: str
    @classmethod
    def from_dict(cls, raw: dict) -> "LearnedRouterModel"
    @classmethod
    def from_file(cls, path: Path) -> "LearnedRouterModel"
    def probabilities(self, vector: Sequence[float]) -> tuple[float, float]
    def operating_point(self, quality_target: float) -> OperatingPoint
    def choose(self, vector: Sequence[float], quality_target: float) -> TierChoice

ALL_FRONTIER = OperatingPoint(tau_local=inf, tau_economy=inf, quality=1.0, cost_per_prompt=nan)
def tier_for(p_local, p_economy, point) -> Literal["local","economy","frontier"]
```
- `probabilities`: `sigmoid(w·x + b)` per model, stable sigmoid; raises `ValueError` on dimension mismatch.
- `operating_point`: among points with `quality >= quality_target`, the lowest `cost_per_prompt` (ties → higher quality); none → `ALL_FRONTIER`.
- `from_dict` validates `version == 1`, both weight vectors same length, points non-empty.

- [ ] Tests: hand-built 2-dim model — probabilities match `1/(1+e^-z)`; `tier_for` cascade (local wins, economy, frontier); `operating_point` picks cheapest feasible, returns `ALL_FRONTIER` above max quality (Review Focus 1) and `choose` then gives `frontier`; dimension mismatch raises; `from_dict` rejects version 2.
- [ ] Implement, commit `feat(router): stdlib runtime for the learned router`.

### Task 2: Logistic regression and grouped cross-validation (offline)

**Files:** Create `scripts/router/logreg.py`, `scripts/router/cv.py`; tests in `tests/test_router_offline.py`.

**Interfaces — Produces:**
- `logreg.fit(X: np.ndarray, y: np.ndarray, lam: float, iters: int = 50) -> tuple[np.ndarray, float]` — L2-regularised logistic regression by Newton/IRLS (bias unregularised); `logreg.predict(w, b, X) -> np.ndarray`; `logreg.log_loss(y, p) -> float`.
- `cv.folds(examples, k=5, seed=20260930) -> list[int]` — fold index per example; all examples sharing `prompt_id` share a fold; prompts assigned round-robin within each `task_type` after a seeded shuffle.
- `cv.out_of_fold(X, y, fold_of, lam) -> np.ndarray` — OOF probabilities.
- `cv.choose_lambda(X, y, fold_of, grid=(0.01, 0.1, 1.0, 10.0)) -> tuple[float, dict[float, float]]` — lowest mean OOF log-loss.
- `cv.auc(y, p) -> float` (reuse `scripts.metric_validation.stats.roc_auc`).

- [ ] Tests: `fit` recovers the sign of a separable 2-D problem and its predictions beat 0.9 accuracy; larger λ shrinks ‖w‖; `folds` keeps `es:x` and `en:x` together (Review Focus 3) and is deterministic; each fold has every task; `out_of_fold` never uses the test fold (monkeypatch `fit` to record training indices).
- [ ] Implement, commit `feat(router): grouped cross-validated logistic regression`.

### Task 3: Frontier, baselines and kNN (offline)

**Files:** Create `scripts/router/frontier.py`, `scripts/router/knn.py`; tests.

**Interfaces — Produces:**
- `frontier.route(p_local, p_economy, tau_local, tau_economy) -> list[str]` (vectorised cascade, same rule as `learned_router.tier_for`).
- `frontier.evaluate(tiers: Sequence[str], examples) -> tuple[float, float]` — (mean cost per prompt, quality) with local cost 0, economy `cost_economy`, frontier `cost_frontier`; quality: local→`local_ok`, economy→`economy_ok`, frontier→1.
- `frontier.sweep(p_local, p_economy, examples, grid=np.linspace(0,1,51)) -> list[dict]` — every (τ_l, τ_e) point with cost, quality, tier shares.
- `frontier.pareto(points) -> list[dict]` — non-dominated (lower cost, higher quality), sorted by cost.
- `frontier.cost_at_quality(points, q) -> float | None` — cheapest point with quality ≥ q.
- `frontier.heuristic_tiers(examples, premium_tier="frontier") -> list[str]` — current rule: `ceil(len/4) < 500` and no keyword in `("analyze","reason","contract","debug","architecture","design")` → local, else `premium_tier`.
- `frontier.corner_points(examples) -> dict[str, tuple[float, float]]` for all-local / all-economy / all-frontier / oracle (cheapest sufficient tier).
- `frontier.random_cost_at_quality(examples, q) -> float` — cheapest random mixture of the three corners reaching q (lower convex hull of the corner (cost, quality) points).
- `knn.oof_probabilities(X, y, fold_of, k=20) -> np.ndarray` — cosine-similarity-weighted mean label of the k nearest training neighbours.

- [ ] Tests: `route` cascade; `evaluate` on 3 hand examples; `pareto` drops a dominated point; `cost_at_quality` None above max; `heuristic_tiers` on a short/long/keyword prompt; oracle quality = 1 and cost ≤ all-frontier; `random_cost_at_quality` interpolates linearly between local and frontier when economy is dominated; `knn` with k=1 returns the nearest neighbour's label.
- [ ] Implement, commit `feat(router): cost-quality frontier and baselines`.

### Task 4: Train + report CLI and latency probe (offline)

**Files:** Create `scripts/router/train.py`, `scripts/router/latency.py`; tests for the pure helpers.

**Interfaces — Produces:**
- `train.PREFIX_MARGIN = 0.02`; `train.choose_prefix(aucs: dict[str, float]) -> str` (`classification` only if mean AUC beats `none` by > margin).
- `train.operating_points(pareto_points) -> list[dict]` in artifact form (`tau_local`, `tau_economy`, `quality`, `cost_per_prompt`).
- `train.artifact(...) -> dict` matching `LearnedRouterModel.from_dict`.
- CLI `python -m scripts.router.train`:
  1. For each prefix: X from embeddings; λ by `choose_lambda` per target; OOF probabilities; AUC per target (overall + per lang). Choose prefix.
  2. With chosen prefix: sweep → pareto; baselines (heuristic ×2, corners, oracle, random); kNN OOF sweep → pareto; same pipeline on R1 and R2 tiers (sensitivity).
  3. Fit both models on all data with chosen λ; write `src/nebula/data/learned_router_v1.json` (operating points from the **OOF** pareto).
  4. Write `benchmarks/router/v1/report.json` + `report.md`; replace thesis block `router-fase3` in `docs/tfc/tesis/06-evaluacion.md` (use `scripts.ground_truth.report.replace_block`).
- CLI `python -m scripts.router.latency --n 30`: first 30 ES prompts (sorted id, 6 per task), timed per role via `scripts.ground_truth.llm` + `cli`, `max_tokens=1024`; writes `benchmarks/router/v1/latency.jsonl`; spend through a `SpendLedger` at `benchmarks/router/v1/spend.jsonl` cap USD 1.

- [ ] Tests: `choose_prefix` margin both ways; `artifact` round-trips through `LearnedRouterModel.from_dict`; `operating_points` keeps order and fields.
- [ ] Implement; add the `<!-- GEN:router-fase3 -->` markers around the §6.4 "PENDIENTE (fase 3)" line; commit `feat(router): training, report and latency probe`.

### Task 5: Settings, catalog and policy field

**Files:** Modify `src/nebula/core/config.py`, `benchmarks/pricing.json`, `src/nebula/models/governance.py`, `src/nebula/db/models.py`, `src/nebula/services/governance_store.py` (policy read/write), `src/nebula/api/routes/admin.py` (policy fields list if enumerated); create `migrations/versions/20260930_0002_routing_quality_target.py`; tests.

- Settings: `economy_model: str | None = Field(default=None, alias="NEBULA_ECONOMY_MODEL")`, `learned_router_enabled: bool = Field(default=False, alias="NEBULA_LEARNED_ROUTER_ENABLED")`, `learned_router_path: str = Field(default=<package data path>, alias="NEBULA_LEARNED_ROUTER_PATH")`.
- pricing.json: add `anthropic/claude-haiku-4.5` (1.0/5.0), `openai/gpt-4.1` (2.0/8.0).
- `TenantPolicy.routing_quality_target: float = Field(default=0.95, ge=0.5, le=1.0)`; DB column `Float, nullable=False, default=0.95, server_default="0.95"`; store maps it both ways; migration adds the column.
- [ ] Tests: policy round-trips the field through the store (existing store test pattern); API rejects 0.3 (422); pricing estimates haiku cost; migration upgrade on an empty SQLite creates the column (follow existing migration test if present, else `alembic upgrade head` in a tmp DB via `command.upgrade`).
- [ ] Commit `feat(router): economy model, router settings and per-tenant quality target`.

### Task 6: RouterService consults the learned model

**Files:** Modify `src/nebula/services/router_service.py`, `src/nebula/services/policy_service.py`, `src/nebula/core/container.py`; test `tests/test_learned_routing.py`.

- `RouteDecision` gains `model: str | None = None` (last field).
- `RouterService.__init__(settings, learned: LearnedRouterModel | None = None)`; `uses_embeddings` property = `learned is not None`.
- `choose_target_with_reason(..., prompt_embedding: list[float] | None = None)`: after explicit override, if `learned` and `policy` given:
  - vector present → `choice = learned.choose(vector, policy.routing_quality_target)`; decision `target = "local" if tier == "local" else "premium"`, `reason="learned_router"`, `model = None if local else (settings.economy_model if tier=="economy" and settings.economy_model else settings.premium_model)`, `score = 1 - p_local`, signals = heuristic signals (for continuity) + `{"tier", "p_local", "p_economy", "quality_target", "operating_point": {...}, "learned_router": learned.version}`. If tier is economy but no economy model configured → tier recorded as `frontier`.
  - vector None → heuristic decision with `signals["learned_router"] = "embedding_unavailable"`.
- `PolicyService.evaluate/resolve` accept and forward `prompt_embedding`; `_calibrated_routing_disabled` also true for reason `learned_router`; premium model for allowed-list and cost cap = `route_decision.model or self._resolve_premium_model(request)`.
- Container builds `LearnedRouterModel.from_file(settings.learned_router_path)` when enabled; a missing/invalid file raises at startup (fail loud).
- [ ] Tests (tiny 2-dim artifact written to tmp, fake vectors): local/economy/frontier decisions by vector; quality target 1.0 → frontier; `calibrated_routing_enabled=False` → `calibrated_routing_disabled`; explicit model and `premium_only` bypass; vector None → `token_complexity` + signal; economy unconfigured → frontier model; allowed-models check denies a disallowed economy model.
- [ ] Commit `feat(router): route with the learned model when enabled`.

### Task 7: ChatService — embed once, tier model, fallback, header

**Files:** Modify `src/nebula/services/chat_service.py`, `src/nebula/services/semantic_cache_service.py`, `src/nebula/api/routes/chat.py`, container wiring (embeddings service into ChatService); tests `tests/test_learned_routing.py`.

- `SemanticCacheService.lookup(..., vector: list[float] | None = None)` and `store(..., vector=None)`: use the given vector instead of embedding.
- `ChatService.__init__` gets `embeddings_service` (optional). In both non-stream and stream paths: `embedding = await self._embed_for_routing(prompt)` (None unless `router_service.uses_embeddings`; embed failures → None), pass to `_resolve_policy` → `policy_service.resolve(prompt_embedding=...)`, and to cache lookup/store.
- Provider request: `_provider_request(request, decision_model)` → `request.model_copy(update={"model": decision_model})` when set; used at every `_complete_with_provider` / stream-prepare call for the primary route. Fallback local→premium uses `settings.economy_model` when set.
- `CompletionMetadata.route_tier: str` — local→`local`, cache→`cache`, denied→`denied`, premium→ `signals["tier"]` if present, fallback→ `economy` if economy model else `frontier`, otherwise `frontier`. Header `X-Nebula-Route-Tier` in `_nebula_headers` (and the streaming header builder).
- Ledger: unchanged code path; pricing uses `response_model` which is now the tier model (verify in test).
- [ ] Tests with `configured_app()`-style stubs (StubProvider recording the model it was asked for, fake embeddings service, fake cache): economy decision calls premium provider with haiku model and header tier `economy`; local decision → `local`; embedding failure → heuristic, request succeeds, header tier from heuristic; cache lookup receives the precomputed vector (embed called once); local provider failure → fallback with economy model, tier `economy`; ledger `response_model` is the tier model and cost > 0.
- [ ] Commit `feat(router): gateway routes to three tiers with a single prompt embedding`.

### Task 8: Run offline pipeline

- [ ] `.venv/bin/pip install -e '.[dev]'` (numpy); `python -m scripts.router.embed`; `python -m scripts.router.train`; `python -m scripts.router.latency`.
- [ ] Check acceptance criterion 2 in `report.md`; commit artifact, `benchmarks/router/v1/*`, thesis block: `chore(router): train v1 and publish its frontier`.

### Task 9: Demo configuration

- [ ] `.env.example`: `NEBULA_LOCAL_MODEL=qwen2.5:7b`, `NEBULA_PREMIUM_MODEL=openai/gpt-4.1`, `NEBULA_ECONOMY_MODEL=anthropic/claude-haiku-4.5`, `NEBULA_LEARNED_ROUTER_ENABLED=true`; same in `docker-compose.selfhosted.yml` env defaults; README/architecture/demo-runbook: one paragraph on the three tiers and `X-Nebula-Route-Tier`.
- [ ] Live check against the running gateway (Ollama + OpenRouter): three prompts (short factual → local, open writing → economy/frontier, long reasoning) and a tenant with target 1.0 → frontier; record headers in the PR.
- [ ] Commit `docs(router): three-tier demo configuration`.

### Task 10: Ship

- [ ] Full suite + console tests; final whole-branch review (subagent, opus); fix Critical/Important with TDD; PR, CI, merge; memory update.
