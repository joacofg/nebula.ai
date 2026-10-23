# Console coherence (PR 3 of 3) — design

Date: 2026-10-22. Branch `feat/2026-10-22-console-coherence`, base 829f93d.
Source of the items: the 2026-10-21 UI/UX audit (U1–U31), re-checked against 829f93d: none fixed,
U10/U20/U31 partly. Joaquín approved U1–U31 (U32 excluded), U6 with the learned router, the
`client_disconnected` ledger filter, and recapturing figures 10.3/10.6/10.7/11.1 without the in-app
"Figura N.". Visual rules: `DESIGN.md` ("Plano"); product and copy rules: `PRODUCT.md`;
vocabulary: Route = where a request was served (local / premium / cache / denied), Tier = local /
economy / frontier.

## Goals

1. Every console page tells the truth with the same words, numbers and states (no raw codes, no
   English, no "[object Object]", no silent failures).
2. Policy simulation re-decides learned-router traffic per tier with the stored probabilities.
3. The four console figures of the thesis are recaptured from the fixed console.

Non-goals: redesigns, mobile navigation, skeletons, U32 (code-quality refactors), new pages.

## Backend changes

**B-U6 Learned-router simulation.**
- The learned router stores `p_local` and `p_economy` unrounded in `route_signals` (the score and
  headers keep their rounding), plus `economy_model` (the configured economy model or null). The
  artifact label is already stored as `learned_router`.
- `RouterService.choose_target_for_learned_replay(p_local, p_economy, policy)` returns the same
  `RouteDecision` (target, reason `learned_router`, tier, model, signals) that `_learned_decision`
  would for those probabilities and that policy, using `tier_for(p_local, p_economy,
  learned.operating_point(policy.routing_quality_target))` and the economy→frontier rewrite when no
  economy model is configured.
- The simulation re-decides a row with the learned router iff its `route_signals` carry numeric
  `p_local` and `p_economy`, its `learned_router` equals the loaded artifact's label, the candidate
  policy keeps `calibrated_routing_enabled` and `routing_mode_default = auto`, and the request was
  `nebula-auto`. Every other row keeps today's heuristic replay. The candidate policy's guardrails
  (local_only/premium_only, allowed premium models with the economy→frontier escalation, hard
  budget, per-request cap) apply exactly as on the live path.
- Cost per row: local 0; economy priced with the economy model; frontier with the premium model,
  using the existing pricing rules on the row's token counts.
- Response additions: per changed row `baseline_tier`, `simulated_tier` (local / economy /
  frontier / null) and `decision_source` (`learned_router` | `heuristic`); in the summary
  `baseline_tier_counts`, `simulated_tier_counts` (keys local, economy, frontier) and
  `learned_router_rows`, `heuristic_rows`.
- `approximation_note_codes: list[str]` parallel to `approximation_notes` (text kept for API
  clients). A note `heuristic_fallback_rows` is added when `heuristic_rows > 0`.

**B-U11 Tier filter.** `GET /v1/admin/usage/ledger` accepts `tier` (local | economy | frontier),
matching `route_signals.tier`; portable JSON access for SQLite and Postgres.

No schema migration (route_signals is JSON).

## Console decisions (exact copy in quotes)

Shared foundations
- **U5 Errors.** One `errorMessage` mapping by HTTP status: 401 "La clave de admin no es válida.",
  403 "Acción no permitida.", 404 "No se encontró el recurso.", 409 "Ya existe un recurso con ese
  identificador.", 422 with a FastAPI list "Revisar los campos: {campos}." (field = last `loc`
  element, joined with ", "), 400 or 422 with a string "El gateway rechazó los datos.", 429
  "Demasiados pedidos. Reintentar en {n} s." (Retry-After) or "Demasiados pedidos. Reintentar en
  unos segundos.", other 5xx "El gateway devolvió un error ({status}).". The Next proxies catch a
  failed upstream fetch and answer 503 `{"detail": "gateway_unreachable"}`, shown as "No se pudo
  conectar con el gateway."; login distinguishes it from a wrong key.
- **U26** Every inline error banner uses `ErrorAlert`.
- **U23** One formatting module (`console/src/lib/format.ts`): USD as "USD 1.70" (digits chosen
  per call), per-1000 as "USD 1.70 / 1000"; every page uses it; no `$`, no en-US `Intl` currency.
- **U20** Spanish for every visible code: routing modes "Automático", "Solo local", "Solo
  premium"; `token_complexity` "Heurística por complejidad"; Dialog/Sheet close "Cerrar"; route
  labels "Local", "Premium", "Caché", "Denegado", "Embeddings"; missing reason labels
  (`policy_local_only`, `policy_premium_only`, `embeddings_*`); runtime statuses, cache insights
  (by code), simulation parity strings, approximation notes (by code), ledger-detail values.
  Unknown codes fall back to the raw value, never to an empty cell.
- **U24** `Figure` keeps its caption without number ("Figura N." removed); DESIGN.md's component
  line and Decisions Log are updated.
- **U25** Dead code removed (formatSaving, formatCi, TIER_LABELS, unused ui/select, ui/table,
  ui/badge, ui/separator, duplicate formatProb).
- **U31 colors** `tier-cache` is darkened so local and cache differ in grayscale (luminance ratio
  between them ≥ 1.5:1, cache ≥ 3:1 against white), validated with the dataviz ordinal/contrast
  check; DESIGN.md table and Decisions Log updated. Tier names stay next to every color.

Tenant scope
- **U13** A `SelectedTenantProvider` in the console layout holds the selected tenant id in memory
  (no storage: the admin session is in memory by design). Pages that need one tenant read it; with
  none selected, or a stale id not in the list, they use the first tenant and store it. Selecting
  a tenant on any page updates it.
- **U21** Observability's "Todos los tenants" is a local filter value that the default no longer
  overrides; the ledger shows date and time ("22/10 14:05:03", local time).
- **U3** "Cerrar" closes the tenant drawer; the drawer holds the tenant id, not a copy.
- **U17** "Crear tenant" focuses the first field; saving shows "Tenant creado." and opens the new
  tenant in edit mode.
- **U22** Signing out ends on the login page with "Sesión cerrada.".

Policy
- **U2** Saving shows "Política guardada." (status, ok tone) until the next edit.
- **U4** The checkbox reads "Ruteo automático por nivel" (it gates both the learned router and the
  heuristic; backend behavior and its test stay).
- **U8** Numeric fields accept a decimal comma ("10,5" → 10.5); empty means "sin límite"; anything
  else shows "Número inválido." and blocks save and simulate; one validation function serves both.
- **U27** Quality target range 0.75–1.00 in Policy and the Evaluación slider (one constant; the
  artifact's lowest operating point is 0.7544), always shown with two decimals ("0.90"). The API
  keeps accepting 0.5–1.0.
- **U6 console** The simulation result shows tier counts baseline → simulated (local / economy /
  frontier) and how many rows the learned router re-decided vs the heuristic.
- **U31** Field hints are linked with `aria-describedby`.

Playground
- **U1** While the request runs, the result shows "Esperando respuesta…" with `LoadingRows`.
- **U14** Each fact appears once: request-level facts in "Detalle", recorded outcome in the ledger
  block; one latency (the ledger's, same format as the ledger table).
- **U15** Header cells: tenant, "Objetivo" (two decimals) and routing mode.
- **U9** DecisionPath: unchosen branches without opacity (AA text, dashed line); each node shows its
  comparison as text, e.g. "p 0.82 ≥ τ 0.75".

Observability
- **U11** "Ruta" filter with Spanish labels; new "Nivel" filter (local / economy / frontier) using
  B-U11; table column "Nivel" shows tier.
- **U12** Date filters are sent as UTC ISO from the local `datetime-local` value.
- **U18** The cost summary says how many rows it sums ("USD 0.0123 en 100 pedidos") and adds USD /
  1000 for those rows.
- **client_disconnected** appears in the status filter.
- **U23** Selected row uses `aria-current`, not `aria-selected`.
- **U31** The ledger is one tab stop (roving tabindex; arrows move, Enter opens).

Evaluación
- **U7** The slider opens at the tenant's current target; "Objetivo actual 0.90" is shown; the
  success alert clears when the slider moves; a "Probar en Playground" link opens Playground for
  the same tenant.
- **U10** "Ahorro vs todo frontier" is the most prominent readout.
- **U16** Replay default speed 10× (1250 prompts ≈ 2 min).
- **U28** "jueces" → "ensamble de jueces"; cost readout "Costo por 1000 pedidos" (detail
  "promedio hasta ahora"); quality shows "—" before the first prompt.
- **U29** Tier share shows each tier's model; per-language rows carry units ("calidad 0.950 · USD
  1.70 / 1000").
- **U31** "Ver tabla" has `aria-expanded`.

API keys
- **U19** A failed revoke shows an `ErrorAlert`; no unhandled rejection.
- **U30** "Prefijo" column with `key_prefix` (mono); "Copiada" resets after 2 s and on reopen; the
  default-tenant select has "Sin tenant por defecto".

## Figures and thesis

Recapture `consola-politica.png` (10.3), `consola-evaluacion.png` (10.6), `consola-playground.png`
(10.7), `consola-observabilidad.png` (11.1) per `docs/tfc/tesis/figuras/README.md` (1440 × 900,
scale 2, learned router on, tenant Acme Robotics), with the seeded ledger
(`scripts/seed_demo_data.py`), `NEBULA_PREMIUM_PROVIDER=mock`, and a Playground prompt the router
sends to local. Check the captions and the prose that describes those screens in chapters 10–11
still match; no "Figura N." inside any capture.

## Constraints

No paid API calls (premium provider mocked; Ollama local only). No edits to
`scripts/metric_validation/`, `docs/evaluation.md`, `scripts/ground_truth/label.py`,
`benchmarks/ground-truth/v1/`, `benchmarks/cache/v1/`. Copy: neutral Spanish, no voseo,
infinitives, little text, numbers like the thesis ("USD 1.70", "31 %"). Colors only through
DESIGN.md roles.
