# Console Coherence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every console page consistent and truthful (U1–U31, the `client_disconnected` filter), let policy simulation re-decide learned-router traffic per tier, and recapture the four console figures of the thesis.

**Architecture:** Two small backend changes (learned-router replay in the simulation; a `tier` filter on the ledger endpoint). Then shared console foundations: errors, formatting, labels, quality-target constants, a selected-tenant provider. Then page-by-page fixes, live UI QA, and figure recapture.

**Tech Stack:** FastAPI + SQLAlchemy (pytest); Next.js 15 / React 19 / TanStack Query / Tailwind 4 (vitest + Testing Library, Playwright e2e).

**Spec:** `docs/superpowers/specs/2026-10-22-console-coherence-design.md`

## Global Constraints

- Copy: neutral Spanish, no voseo, infinitives in actions, little text; numbers like the thesis ("USD 1.70", "31 %", point decimal); tenant, ledger, playground, local, economy, frontier untranslated (PRODUCT.md, DESIGN.md "Copy").
- Exact strings are the ones quoted in the spec; reuse them verbatim.
- Colors only through DESIGN.md roles (no raw palette classes, no hex in components); DESIGN.md "Prohibido" applies.
- Admin session and the selected tenant live in memory only (no localStorage/sessionStorage).
- Tests asserting UI text change in the same commit as the text.
- No paid API calls anywhere; live runs use `NEBULA_PREMIUM_PROVIDER=mock`; Ollama local only.
- Don't edit `scripts/metric_validation/`, `docs/evaluation.md`, `scripts/ground_truth/label.py`, `benchmarks/ground-truth/v1/`, `benchmarks/cache/v1/`.
- Heavy runs: prefix with `darwin-throttle`; vitest `--maxWorkers=2` via CLI only. Backend: `darwin-throttle .venv/bin/pytest <files> -q`. Console: `cd console && darwin-throttle npm test -- --run --maxWorkers=2 <files>`.
- Commits: prefixes fix/feat/docs/chore/test; trailers `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_012JwPQqsnEebt9XQ2BG378E`; stage by path only.

## Review Focus

- No tenants at all (fresh install): every page shows its empty state and sends no request with an undefined tenant — Task 4.
- A selected tenant id that is no longer in the list (deleted, or a list filtered by another page): pages fall back to the first tenant instead of rendering blank — Task 4.
- Gateway down mid-session: every query and mutation shows "No se pudo conectar con el gateway." (never "[object Object]", never a Next 500 page) — Task 2.
- A simulation window that mixes learned-router rows, rows with 4-decimal rounded probabilities from before this change, heuristic rows and strict-minimization rows: each row gets the right `decision_source`, counts add up to `evaluated_rows` — Task 1.
- Policy numeric input "10,5", "", "abc", " 3 ": 10.5, sin límite, error, 3 — never "sin límite" for a typo — Task 5.

---

### Task 1: Learned-router replay in policy simulation (backend)

**Files:**
- Modify: `src/nebula/services/router_service.py` (`_learned_decision` signals; new `choose_target_for_learned_replay`)
- Modify: `src/nebula/services/policy_service.py` (evaluation entry that accepts a precomputed `RouteDecision`), `src/nebula/services/policy_simulation_service.py`, `src/nebula/models/governance.py` (`PolicySimulationChangedRequest`, `PolicySimulationOutcomeCounts`, `PolicySimulationResponse`)
- Test: `tests/test_policy_simulation_learned.py` (new), existing rounding assertions in `tests/test_router_signals.py` / `tests/test_learned_routing.py` updated

**Interfaces:**
- Produces: `RouterService.choose_target_for_learned_replay(p_local: float, p_economy: float, policy: TenantPolicy) -> RouteDecision | None` (None when no learned router is loaded).
- Produces (API): `PolicySimulationChangedRequest.baseline_tier: str | None`, `.simulated_tier: str | None`, `.decision_source: Literal["learned_router", "heuristic"]`; `PolicySimulationOutcomeCounts.baseline_tier_counts: dict[str, int]`, `.simulated_tier_counts: dict[str, int]` (keys `local`, `economy`, `frontier`, always present), `.learned_router_rows: int`, `.heuristic_rows: int`; `PolicySimulationResponse.approximation_note_codes: list[str]` (same order as `approximation_notes`; existing notes get codes `ledger_metadata_replay`, `token_count_approximation`, `pricing_estimate`; new `heuristic_fallback_rows`).
- Produces (ledger): `route_signals.p_local` / `p_economy` unrounded floats; `route_signals.economy_model: str | None`.

- [ ] **Step 1: Failing tests** in `tests/test_policy_simulation_learned.py`, using the real `LearnedRouterModel` loaded from `src/nebula/data/learned_router_v1.json` and seeded ledger rows:
  - `test_learned_row_is_redecided_per_tier_under_the_candidate_target`: a row with `p_local=0.62, p_economy=0.91, learned_router="v1"` and baseline tier frontier; a candidate target whose operating point has `tau_local > 0.62 ≥ ...` (pick the target from the artifact so the expected tier is computed with `tier_for`) → `simulated_tier == tier_for(0.62, 0.91, model.operating_point(target))`, `decision_source == "learned_router"`, cost priced with the economy model when economy, 0 when local.
  - `test_rows_without_learned_signals_use_the_heuristic` (no p values / other artifact label / strict minimization / explicit model / candidate `calibrated_routing_enabled=False`) → `decision_source == "heuristic"`, note code `heuristic_fallback_rows` present.
  - `test_mixed_window_counts_add_up` (Review Focus): learned + rounded-4-decimal + heuristic + strict rows → `learned_router_rows + heuristic_rows == evaluated_rows`; `sum(simulated_tier_counts.values())` equals the non-denied rows that have a tier.
  - `test_candidate_guardrails_apply_to_learned_rows`: candidate `allowed_premium_models` without the economy model escalates economy → frontier; `premium_only`/`local_only` and hard budget behave as on the live path.
  - `test_learned_signals_are_stored_unrounded`: a live learned decision stores `p_local` with more than 4 decimals when the probability has them, and `economy_model` equal to the configured value (null when unset).
- [ ] **Step 2:** Run `darwin-throttle .venv/bin/pytest tests/test_policy_simulation_learned.py -q` — FAIL.
- [ ] **Step 3:** Implement. The learned replay decision must equal what `_learned_decision` produces for the same probabilities (share one helper, don't duplicate the signal dict). The simulation picks the learned path per the spec's eligibility rule and otherwise keeps today's heuristic replay unchanged. Rounded-4-decimal rows are eligible (they're still numeric). Update tests that pinned `round(…, 4)` on stored probabilities.
- [ ] **Step 4:** Run the new file plus `tests/test_service_flows.py -k simulation`, `tests/test_learned_routing.py`, `tests/test_router_signals.py` — PASS; `ruff check .`.
- [ ] **Step 5: Commit** `feat(simulation): re-decide learned-router traffic per tier with the stored probabilities`.

### Task 2: Error messages and error states (console)

**Files:**
- Modify: `console/src/lib/admin-api.ts` (`adminRequest`, playground request), `console/src/app/api/admin/[...path]/route.ts`, `console/src/app/api/playground/completions/route.ts`, `console/src/app/api/runtime/health/route.ts`, `console/src/lib/admin-session-provider.tsx`, `console/src/components/auth/admin-login-form.tsx` (path as in repo), `console/src/components/system/state.tsx`
- Modify (U26, ErrorAlert): `playground/page.tsx:154,162`, `policy/page.tsx:126`, `admin-login-form.tsx:67`, `create-api-key-dialog.tsx:87`, `tenant-editor-drawer.tsx:111`, `apply-target.tsx:92`, `policy-form.tsx:564,571`
- Modify (U19): `console/src/app/(console)/api-keys/page.tsx:80-100,174`
- Test: `console/src/lib/admin-api.test.ts`, `admin-session-provider.test.tsx`, `admin-login-form.test.tsx`, `api-keys/page.test.tsx`, a proxy route test (new `console/src/app/api/admin/[...path]/route.test.ts`)

**Interfaces:**
- Produces: `class AdminApiError extends Error { status: number; detail: unknown; retryAfterSeconds: number | null }` thrown by every admin/playground request; its `message` is already the Spanish text from the spec's status table. `errorMessage(error: unknown, fallback: string): string` keeps its signature. Proxies answer `503 {"detail": "gateway_unreachable"}` when the upstream fetch throws.

- [ ] **Step 1: Failing tests:** one per status row of the spec table (401, 403, 404, 409, 422-list → "Revisar los campos: name, tenant_id.", 422-string and 400 → "El gateway rechazó los datos.", 429 with `Retry-After: 7` → "Demasiados pedidos. Reintentar en 7 s.", 429 without, 500 → "El gateway devolvió un error (500).", 503 gateway_unreachable → "No se pudo conectar con el gateway."); proxy test: upstream fetch rejects → 503 body; login: 401 → "La clave de admin no es válida.", unreachable → "No se pudo conectar con el gateway."; api-keys: revoke rejects → ErrorAlert text visible and no unhandled rejection (vitest fails on unhandled rejections; assert with `await screen.findByRole("alert")`).
- [ ] **Step 2:** Run them — FAIL.
- [ ] **Step 3:** Implement; replace the 8 inline banners with `ErrorAlert` (the warning banner at `playground/page.tsx:162` uses `errorMessage`).
- [ ] **Step 4:** Run the touched test files — PASS; `npx tsc --noEmit -p tsconfig.json` in console.
- [ ] **Step 5: Commit** `fix(console): Spanish error messages by status and one error state everywhere`.

### Task 3: Shared formatting, labels, quality-target constants, figure caption, tier-cache color, dead code (console)

**Files:**
- Create: `console/src/lib/format.ts`, `console/src/lib/quality-target.ts`
- Modify: `console/src/components/system/labels.ts`, `console/src/components/system/figure.tsx` (+ callers at `evaluacion/page.tsx:137,178`, `playground-decision.tsx:162`, `ledger-request-detail.tsx:178`), `console/src/components/ui/dialog.tsx:79,118`, `console/src/components/ui/sheet.tsx:80`, `console/src/app/globals.css` (`--color-tier-cache`), `DESIGN.md` (tier-cache row, `Figure` line, Decisions Log rows dated 2026-10-22)
- Modify (U23 call sites): `evaluation/format.ts`, `policy-form.tsx:97`, `ledger-table.tsx:34`, `playground-recorded-outcome.tsx:29`, `cache-summary.tsx:14`, `observability/page.tsx:119`, `ledger-request-detail.tsx:48-69`, `frontier-chart.tsx:159,294,375,381`
- Delete (U25): `formatSaving`, `formatCi`, `TIER_LABELS` in `evaluation/format.ts`; `ui/select.tsx`, `ui/table.tsx`, `ui/badge.tsx`, `ui/separator.tsx`; `formatProb` in `playground-decision.tsx` (use DecisionPath's formatter)
- Test: `console/src/lib/format.test.ts`, `console/src/lib/quality-target.test.ts`, `labels.test.ts`, `system.test.tsx`

**Interfaces:**
- Produces: `formatUsd(value: number, digits?: number): string` → `"USD 1.70"` (default 2 digits; negative values keep the sign after "USD"); `formatUsdPer1000(costPerRequest: number, digits?: number): string` → `"USD 1.70 / 1000"`.
- Produces: `TARGET_MIN = 0.75`, `TARGET_MAX = 1`, `TARGET_STEP` (the slider's current step), `formatTarget(t: number): string` → `"0.90"`, `snapTarget(t: number): number` (moved from `quality-slider.tsx`; the slider re-exports nothing).
- Produces: `routingModeLabel(mode: string): string` ("Automático", "Solo local", "Solo premium"), `routeLabel` covering local/premium/cache/denied/embeddings, `reasonLabel` with `policy_local_only`, `policy_premium_only`, `embeddings_*`, `routerLabel(name: string)` (`token_complexity` → "Heurística por complejidad", `learned_router` → "Router aprendido"), `runtimeStatusLabel(status: string)`; every label function returns the raw value for an unknown code.
- Produces: `<Figure caption=…>` without a number prop.

- [ ] **Step 1: Failing tests:** format cases (0, 1.7, 0.0123 with 4 digits, negative, per-1000 from 0.0017); quality-target (`formatTarget(0.9) === "0.90"`, `snapTarget` clamps to [0.75, 1]); labels for each code above and an unknown code; `Figure` renders the caption and never "Figura"; Dialog/Sheet close button has accessible name "Cerrar".
- [ ] **Step 2:** Run — FAIL.
- [ ] **Step 3:** Implement and move every call site to the shared helpers. Pick the new `tier-cache` value with the dataviz skill's checks (luminance ratio local↔cache ≥ 1.5:1, cache vs white ≥ 3:1, still reads as neutral gray); record both decisions in DESIGN.md.
- [ ] **Step 4:** Run touched tests + `npx tsc --noEmit` + `npm run lint` in console — PASS. `grep -rn "\$[0-9]\|en-US\|Figura " console/src --include=*.tsx --include=*.ts` returns nothing outside tests.
- [ ] **Step 5: Commit** `fix(console): one formatter, one label set and a caption without numbers`.

### Task 4: Shared tenant selection, tenants page, sign-out (console)

**Files:**
- Create: `console/src/lib/selected-tenant.tsx` (`SelectedTenantProvider`, `useSelectedTenant`)
- Modify: `console/src/app/(console)/layout.tsx` (provider; U22 redirect), `components/shell/operator-shell.tsx:99-102`, `playground/page.tsx:30,40-44`, `policy/page.tsx:28,37-41`, `observability/page.tsx:26,39-43`, `components/evaluation/apply-target.tsx:21,29-33`, `tenants/page.tsx:32,55-76,101,167`, `components/tenants/tenant-editor-drawer.tsx:65`
- Test: `console/src/lib/selected-tenant.test.tsx`, `tenants/page.test.tsx`, `tenant-editor-drawer.test.tsx`, `operator-shell.test.tsx`, `observability-page.test.tsx`

**Interfaces:**
- Produces: `useSelectedTenant(tenants: TenantRecord[] | undefined): { tenantId: string | null; tenant: TenantRecord | null; setTenantId: (id: string) => void }`. With tenants loaded and no valid selection it selects `tenants[0]`; with `[]` it returns nulls and pages render their empty state.

- [ ] **Step 1: Failing tests:** selecting a tenant on Policy then rendering Playground in the same provider shows that tenant; Review Focus: `tenants=[]` → nulls and no query fired with an undefined tenant (assert the mocked `admin-api` function was not called); stale id not in the list → falls back to `tenants[0]`; Observability "Todos los tenants" stays selected after re-render (U21); tenants: "Cerrar" closes the drawer (U3), "Crear tenant" focuses the first field, saving shows "Tenant creado." and the drawer is in edit mode for the new tenant (U17); sign-out ends on login with "Sesión cerrada." (U22).
- [ ] **Step 2:** Run — FAIL.
- [ ] **Step 3:** Implement; the drawer state holds `{ mode, tenantId }` and reads the record from the query.
- [ ] **Step 4:** Run touched tests + tsc — PASS.
- [ ] **Step 5: Commit** `fix(console): one selected tenant across pages, a tenant drawer that closes, and a clean sign-out`.

### Task 5: Policy page (console)

**Files:**
- Modify: `console/src/components/policy/policy-form.tsx` (U4 :363-370, U8 :84-88 + :269-324, U27 :66,290,316,337, U20 :108-151,355-358,620-622, U31 :659-691, U6 result display), `console/src/app/(console)/policy/page.tsx:59-70` (U2)
- Create: `console/src/components/policy/policy-validation.ts` (`parsePolicyNumber`, `validatePolicyForm`)
- Modify: `console/src/lib/admin-api.ts` simulation types (Task 1 fields)
- Test: `policy-form.test.tsx`, `policy-page.test.tsx`, `console/src/components/policy/policy-validation.test.ts`

**Interfaces:**
- Consumes: Task 1 response fields; Task 3 `formatUsd`, `formatTarget`, `TARGET_MIN/MAX`, `routingModeLabel`, `routerLabel`; Task 2 `ErrorAlert`; Task 4 `useSelectedTenant`.
- Produces: `parsePolicyNumber(text: string): number | null | "invalid"` (trimmed; "" → null; "10,5" → 10.5); `validatePolicyForm(state: PolicyFormState): { errors: Record<string, string>; payload: TenantPolicyPayload | null }` used by both save and simulate.

- [ ] **Step 1: Failing tests:** Review Focus inputs `"10,5"`, `""`, `"abc"`, `" 3 "` for budgets, cap and rate limit (→ 10.5, null, "Número inválido." and no request, 3); simulate is blocked by the same errors as save (rate limit included); target shows "0.90" and rejects 0.7 with the range message; "Política guardada." appears after save and disappears on the next edit (U2); checkbox label "Ruteo automático por nivel" (U4); routing mode options read "Automático", "Solo local", "Solo premium"; simulation result renders baseline → simulated counts for local/economy/frontier and "N con el router aprendido · M con la heurística"; approximation notes render Spanish by code and the raw text for an unknown code; hints are wired with `aria-describedby`.
- [ ] **Step 2:** Run — FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run touched tests + tsc — PASS.
- [ ] **Step 5: Commit** `fix(console): policy form that parses, confirms and simulates per tier`.

### Task 6: Observability and ledger (backend filter + console)

**Files:**
- Modify (backend): `src/nebula/api/routes/admin.py:249-268`, `src/nebula/services/governance_store.py` (ledger query) — `tier` filter
- Modify (console): `components/ledger/ledger-filters.tsx:23-30,55,65-95`, `components/ledger/ledger-table.tsx:29-43,98-115`, `components/ledger/ledger-request-detail.tsx:106,136,190-197`, `app/(console)/observability/page.tsx:45-55,94,118-119`, `components/observability/cache-summary.tsx`, `components/observability/runtime-health-cards.tsx:83-93`, `lib/admin-api.ts:514-518`
- Test: `tests/test_governance_api.py` (or the ledger-endpoint test file), `ledger-filters.test.tsx`, `ledger-table.test.tsx`, `observability-page.test.tsx`, `cache-summary.test.tsx`, `runtime-health-cards.test.tsx`

**Interfaces:**
- Produces (API): `GET /v1/admin/usage/ledger?tier=local|economy|frontier`; invalid value → 422.
- Consumes: Task 3 labels/formatters, Task 4 hook.

- [ ] **Step 1: Failing tests:** backend: `tier=economy` returns only rows whose `route_signals.tier == "economy"`, rows without a tier never match, invalid tier → 422 (run on the SQLite store the tests use); console: "Ruta" options show Spanish labels; "Nivel" filter sends `tier`; status filter includes "Cliente desconectado" (the existing `client_disconnected` label) and sends `client_disconnected`; a `datetime-local` value "2026-10-22T10:00" is sent as `new Date("2026-10-22T10:00").toISOString()` (U12); the ledger shows "22/10 14:05:03"-style date and time (U21); the cost summary reads "USD … en N pedidos" and shows USD / 1000 for those rows (U18); the selected row has `aria-current="true"` and no `aria-selected` (U23); only one row is in the tab order and ArrowDown/ArrowUp/Enter move and open (U31); cache insights and dependency statuses render Spanish by code, raw for unknown codes (U20).
- [ ] **Step 2:** Run — FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run touched tests (both stacks) — PASS.
- [ ] **Step 5: Commit** `fix(observability): tier filter, local-time dates, honest sums and a one-stop ledger`.

### Task 7: Playground (console)

**Files:**
- Modify: `app/(console)/playground/page.tsx:51-70,143-149`, `components/playground/playground-metadata.tsx:37-45`, `components/playground/playground-recorded-outcome.tsx:26-36`, `components/playground/playground-decision.tsx:101-117,175,180`, `components/system/decision-path.tsx:41-56,141-174`
- Test: `playground-page.test.tsx`, `playground-decision.test.tsx`, `decision-path.test.tsx`

**Interfaces:**
- Consumes: Task 3 `formatTarget`, `routingModeLabel`, `routerLabel`; Task 4 hook; `formatLatency` from `ledger-table.tsx`.

- [ ] **Step 1: Failing tests:** while the mutation is pending the result shows "Esperando respuesta…" and not the empty state (U1); after a response each of Ruta, Motivo, Nivel, Proveedor, Caché, Fallback, Latencia appears exactly once and latency uses the ledger format (U14); header shows the tenant name, "Objetivo 0.90" and the routing mode label, not "Sin streaming"/"Sesión" (U15); DecisionPath: unchosen branches carry no `opacity-` class, each evaluated node shows its comparison text ("p 0.82 ≥ τ 0.75"), the heuristic fallback reads "Heurística por complejidad" (U9, U20).
- [ ] **Step 2:** Run — FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run touched tests — PASS.
- [ ] **Step 5: Commit** `fix(playground): a waiting state, each fact once, and a readable decision path`.

### Task 8: Evaluación (console)

**Files:**
- Modify: `app/(console)/evaluacion/page.tsx:38,56,65,97,109-110,137-178`, `components/evaluation/apply-target.tsx:38,64,84-90`, `components/evaluation/quality-slider.tsx`, `components/evaluation/replay-feed.tsx:72,100,167-168`, `components/evaluation/tier-share-bar.tsx:22`, `components/evaluation/frontier-chart.tsx:356`
- Test: `evaluacion/page.test.tsx`, `replay-feed.test.tsx`, `frontier-chart.test.tsx`, apply-target test if present

**Interfaces:**
- Consumes: Task 3 quality-target constants and formatters; Task 4 hook.

- [ ] **Step 1: Failing tests:** with the tenant's target 0.90 the slider opens at 0.90 and "Objetivo actual 0.90" is visible; moving the slider clears the success alert; "Probar en Playground" links to `/playground` with the same tenant selected (U7); the "Ahorro vs todo frontier" readout carries the emphasis variant and comes first (U10); replay starts at 10× (U16); copy "ensamble de jueces", "Costo por 1000 pedidos", quality "—" before the first prompt (U28); tier share shows each tier's model; per-language rows read "calidad 0.950 · USD 1.70 / 1000" style (U29); "Ver tabla" toggles `aria-expanded` (U31).
- [ ] **Step 2:** Run — FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run touched tests — PASS.
- [ ] **Step 5: Commit** `fix(evaluacion): open at the tenant's target and lead with the saving`.

### Task 9: API keys (console)

**Files:**
- Modify: `components/api-keys/api-key-table.tsx`, `components/api-keys/reveal-api-key-dialog.tsx:16-23`, `components/api-keys/create-api-key-dialog.tsx:103-114,132`, `app/(console)/api-keys/page.tsx:181-185`
- Test: `api-key-table.test.tsx`, `reveal-api-key-dialog.test.tsx`, `create-api-key-dialog.test.tsx`

- [ ] **Step 1: Failing tests:** "Prefijo" column shows `key_prefix` (U30); "Copiada" returns to "Copiar" after 2 s (fake timers) and on reopen; the default-tenant select has "Sin tenant por defecto" mapping to null; hint wired with `aria-describedby` (U31).
- [ ] **Step 2:** Run — FAIL. **Step 3:** Implement. **Step 4:** Run — PASS.
- [ ] **Step 5: Commit** `fix(api-keys): show the prefix, reset the copy state and allow no default tenant`.

### Task 10: e2e, live UI QA and thesis figures

**Files:**
- Modify: `console/e2e/*.spec.ts` (copy and flows changed by Tasks 2–9)
- Create: `docs/design/2026-10-22-console-coherence/after/*.png` (1440, 1280, 375 per page)
- Modify: `docs/tfc/tesis/figuras/consola-politica.png`, `consola-evaluacion.png`, `consola-playground.png`, `consola-observabilidad.png`; captions/prose in `docs/tfc/tesis/10-diseno.md` / `11-implantacion.md` only if they no longer match

- [ ] **Step 1:** Update the e2e specs; run `cd console && darwin-throttle npx playwright test` — PASS (builds once; 1 worker).
- [ ] **Step 2:** Start the stack per `docs/demo-runbook.md` with `NEBULA_PREMIUM_PROVIDER=mock`, the learned router on, Qdrant and Ollama local, `scripts/seed_demo_data.py` for the ledger. Use `/browse` (never claude-in-chrome) to capture every page at 1440, 1280 and 375 into `after/`; check for 375 px horizontal overflow.
- [ ] **Step 3:** Run impeccable `critique` + `audit` on the changed pages and gstack `design-review` scoped to them; fix material findings on those pages (one commit per fix, test first for behavior); list the rest as deferred.
- [ ] **Step 4:** Recapture the four figures at 1440 × 900, scale 2, tenant Acme Robotics, Playground with a prompt the router sends to local; confirm no "Figura N." inside any capture; read each PNG before committing; adjust captions/prose only where they no longer describe the screen.
- [ ] **Step 5: Commit** `test(e2e): follow the console copy` / `docs(tesis): recapture the console figures` (separately).

### Task 11: Full verification

- [ ] `darwin-throttle make test`, `make lint`, `cd console && darwin-throttle npm test -- --run --maxWorkers=2`, `npx tsc --noEmit -p tsconfig.json`, `npm run lint`, `darwin-throttle npm run build`, `darwin-throttle npx playwright test`, `.venv/bin/python -m scripts.thesis.tables --check` — all green; quote the summary lines.
