# Fase 4 — Consola de evaluación — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An Evaluación console page with the router's cost/quality frontier, a quality-target slider over an accelerated corpus replay, an apply-to-tenant button, a policy field for the target, and a Playground panel explaining each routing decision.

**Architecture:** `scripts.router.train` exports a replay JSON (out-of-fold probabilities, labels, costs, operating points, baselines, nested numbers, latency) packaged under `src/nebula/data/`; a read-only admin endpoint serves it; the console computes everything client-side with a TS port of the gateway's selection rule, checked against Python on the real file.

**Tech Stack:** Python/FastAPI; Next.js 15 + React 19 + TanStack Query + Tailwind; hand-rolled SVG; vitest + Playwright.

**Spec:** `docs/superpowers/specs/2026-09-30-fase4-consola-evaluacion.md`

## Global Constraints

- Branch `fase4-consola`; PR + merge after `make lint`, `make test`, `make console-test`, console `npx tsc --noEmit`, console lint (`ESLINT_USE_FLAT_CONFIG=false npx eslint .` if `npm run lint` fails under rtk) and the new e2e are green.
- No new npm dependencies; no network in tests; heavy runs via `darwin-throttle`, vitest `--maxWorkers=2`.
- Selection rule identical to `src/nebula/services/learned_router.py` (target ≥ 1.0 → all frontier; cheapest point with quality ≥ target; cascade).
- UI copy in Spanish (thesis audience); code in English. Follow existing tokens/classes (`.panel`, `.shell-card`, `.field-label`, `.field-input`, `.action-button`), Fira Sans/Code, lucide icons.
- Commit trailers: `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_012q5mScYuHfCrhfoySuctuw`.

## Review Focus

1. Slider at a target above every point → all-frontier shown, no crash — TS tests.
2. Replay file missing → endpoint 404 and the page shows a clear empty state, not a blank screen.
3. Apply to a tenant whose policy fetch fails → error message, no partial write.
4. Playground decision panel on a heuristic route (reason `token_complexity`) or `embedding_unavailable` → says so, no NaN.
5. Chart with 1 or 0 Pareto points, and very small costs (all-local = 0) → axes stay finite.

---

### Task 1 (backend): replay export, endpoint, options, proxy header
- `scripts/router/train.py`: `replay_payload(examples, probs, points, baselines, nested, latency) -> dict` per spec; `main()` writes `src/nebula/data/router_replay_v1.json`; test shape + text truncation + one row per example.
- `Settings.router_replay_path` (`NEBULA_ROUTER_REPLAY_PATH`, default package file); `GET /v1/admin/evaluation/router` in `api/routes/admin.py` (admin auth dependency as siblings; 404 when missing); tests: 200 with a tmp file, 404 without, 401/403 without admin key.
- `routing_quality_target` in `runtime_enforced_fields`; update `test_governance_api` expectation.
- `console/src/app/api/playground/completions/route.ts`: add `X-Nebula-Route-Tier` to `RESPONSE_HEADERS`.
- Re-run `python -m scripts.router.train`; commit data file.

### Task 2 (console): router replay library
- `console/src/lib/router-replay.ts`: types for the payload; `operatingPoint(points, target)`; `routeRow(row, point)`; `evaluate(rows, point) -> {costPerPrompt, quality, share, byLang}`; `randomCostAtQuality(baselines, q)`; `replayOrder(rows, seed)`.
- `router-replay.test.ts`: golden test reading `../src/nebula/data/router_replay_v1.json` (path from repo root) — for every operating point, `evaluate` equals the point's `quality`/`cost_per_prompt` within 1e-9; target 1.0 → all frontier; target above max → all frontier.
- `admin-api.ts`: `getRouterEvaluation(adminKey)`; query key.

### Task 3 (console): Evaluación page
- `app/(console)/evaluacion/page.tsx` + `components/evaluation/{frontier-chart,quality-slider,tier-share-bar,replay-feed,apply-target}.tsx`; nav item in `operator-shell.tsx` (icon `LineChart` or similar).
- Tests: slider change updates cost card; apply calls `updateTenantPolicy` with `{...policy, routing_quality_target}`; empty state on 404; chart renders with degenerate inputs.

### Task 4 (console): policy field + Playground decision panel
- `policy-form.tsx`: field `routing_quality_target` (0.5–1.0, gated by `runtime_enforced_fields`); fixtures updated in policy tests and `e2e/policy.spec.ts`.
- `components/playground/playground-decision.tsx` fed by the ledger entry's `route_signals`; tier from `X-Nebula-Route-Tier` in metadata; tests for learned / heuristic / embedding_unavailable.

### Task 5 (console): e2e
- `e2e/evaluation.spec.ts`: mocked `/api/admin/evaluation/router` (small fixture) + tenants + policy; slider moves displayed cost; apply shows confirmation.

### Task 6: ship
- Full gates; whole-branch review (opus); fixes with TDD; live check of `/evaluacion` against the running gateway; PR, CI, merge; memory.
