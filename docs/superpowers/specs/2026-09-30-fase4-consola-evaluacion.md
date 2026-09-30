# Spec — Fase 4: consola de evaluación y slider presupuesto↔calidad

Origen: plan maestro `tesis-10x-decisiones-2026-09`; brainstorming 2026-09-30 (aprobado por Joaquín). Entrada: router v1 de la fase 3.

## Objetivo

Que un operador (y el jurado) vea en una pantalla la frontera costo/calidad del router, mueva un slider de calidad objetivo y observe al instante qué pasa —costo, calidad, reparto de niveles, un replay acelerado de prompts reales— y aplique ese objetivo a un tenant. Que el Playground explique por qué una request fue a su nivel.

## Decisiones

| Tema | Decisión |
|---|---|
| Replay | sobre los 1250 prompts del corpus con probabilidades **fuera de fold**, sin llamar a ningún LLM; funciona sin Ollama ni internet |
| Gráfico | SVG propio, sin dependencias nuevas; tokens de color de `globals.css` |
| Regla | idéntica al gateway: punto de operación más barato con calidad ≥ objetivo; objetivo ≥ 1.0 → todo frontier; cascada `p_local ≥ τ_l` → local, si no `p_economy ≥ τ_e` → economy, si no frontier |
| Aplicar | selector de tenant + botón que guarda `routing_quality_target` vía `PUT /v1/admin/tenants/{id}/policy` |
| Honestidad | la página muestra la cifra anidada de la fase 3 y aclara que el replay usa prompts del corpus |

## Datos

`scripts.router.train` escribe además `src/nebula/data/router_replay_v1.json`:

```json
{
  "version": 1,
  "router_label": "v1",
  "rows": [{"key": "es:code-0001", "lang": "es", "task": "code", "text": "…≤160 chars…",
            "p_local": 0.71, "p_economy": 0.88, "local_ok": true, "economy_ok": true,
            "cost_economy": 0.0019, "cost_frontier": 0.0031}],
  "operating_points": [{"tau_local": 0.7, "tau_economy": 0.9, "quality": 0.85, "cost_per_prompt": 0.00056}],
  "baselines": {"all_local": {"cost": 0, "quality": 0.754}, "all_economy": {…}, "all_frontier": {…},
                "heuristic": {…}, "oracle": {…}},
  "nested": {"0.9": {"quality": 0.903, "cost": 0.00106, "vs_all_frontier": 0.57, "vs_random": 0.30}, "0.95": {…}},
  "latency": {"qwen7b": {"model": "qwen2.5:7b", "median_s": 21.3}, …}
}
```

`p_local`/`p_economy` son las probabilidades fuera de fold con el prefijo y λ elegidos; los puntos de operación son los del artefacto. El texto se recorta a 160 caracteres (el corpus deriva de Dolly CC BY-SA, GSM8K MIT, MBPP CC BY; atribución en la página).

## Backend

- `GET /v1/admin/evaluation/router` (admin key) devuelve ese JSON. Setting `NEBULA_ROUTER_REPLAY_PATH` (default el archivo empaquetado). Archivo ausente → 404 con detalle claro.
- `routing_quality_target` entra en `runtime_enforced_fields` de `/v1/admin/policy/options`.
- El proxy del Playground deja pasar `X-Nebula-Route-Tier`.

## Consola

- **`/evaluacion`** (nav "Evaluación"):
  1. Encabezado con la cifra anidada (0.95: −31 % vs frontier, −17 % vs aleatorio, IC) y la latencia por modelo.
  2. Gráfico SVG: eje X costo USD / 1000 prompts, eje Y calidad; curva Pareto del router, segmento de la mejor mezcla aleatoria, puntos todo-local / todo-economy / todo-frontier / heurística / oráculo, punto actual resaltado.
  3. Slider 0.75–1.00 (paso 0.005) + tarjetas: costo/1000, calidad, ahorro vs frontier y vs aleatorio, barra de reparto local/economy/frontier, calidad por idioma.
  4. Replay acelerado: feed que recorre los prompts en orden fijo (semilla), a velocidad ajustable (1×, 10×, 100×), mostrando nivel y ✓/✗ (etiqueta) por prompt y acumulados; mover el slider re-rutea desde el prompt actual.
  5. "Aplicar a este tenant": selector + botón; confirmación con el valor guardado.
- **Políticas**: campo `routing_quality_target` (0.5–1.0), validación como el umbral del caché.
- **Playground**: panel "Por qué este nivel" desde `route_signals` de la entrada del ledger: nivel, p_local vs τ_local, p_economy vs τ_economy, objetivo; si `learned_router == "embedding_unavailable"` o la razón no es `learned_router`, lo dice. Muestra `X-Nebula-Route-Tier` en los metadatos.

## Tests

- TS: la función de ruteo/evaluación de la página reproduce, para cada punto de operación del archivo real, el costo y la calidad que calculó Python (tolerancia 1e-9). Objetivo ≥ 1 → todo frontier.
- Componentes (vitest): slider cambia tarjetas; aplicar llama a `updateTenantPolicy` con el valor; panel del Playground para learned / heurística / embedding caído.
- e2e (Playwright): la página carga con la API mockeada, el slider mueve el costo mostrado, aplicar muestra confirmación.
- Backend: endpoint 200 con el archivo, 404 sin él, requiere admin key; options incluye el campo.

## Fuera de alcance

Replay en vivo contra el gateway (el Playground ya lo cubre), editar la curva, más de un artefacto a la vez, rate limiting (fase 5).

## Criterios de aceptación

1. `make lint`, `make test`, `make console-test` (y `npx tsc --noEmit`, lint de consola) verdes; e2e nuevo verde.
2. Con el gateway levantado, `/evaluacion` funciona sin Ollama ni red externa.
3. Mover el slider a 0.95 muestra el mismo costo y calidad que `benchmarks/router/v1/report.md` para ese punto.
4. Aplicar cambia `routing_quality_target` del tenant (visible en Políticas).
