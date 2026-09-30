# Spec — Fase 3: router aprendido de tres niveles

Origen: plan maestro `tesis-10x-decisiones-2026-09`, brainstorming 2026-09-30 (aprobado por Joaquín). Entrada: `benchmarks/ground-truth/v1/` de la fase 2.

## Objetivo

Reemplazar la heurística de dos reglas por un router aprendido que elige entre **local** (qwen2.5:7b), **economy** (claude-haiku-4.5) y **frontier** (gpt-4.1), demostrar offline que a igual calidad gasta menos que la heurística y que el ruteo aleatorio, y hacer que el gateway rutee de verdad a tres niveles con un knob operable por tenant.

## Decisiones

| Tema | Decisión |
|---|---|
| Clasificador | dos regresiones logísticas L2 en cascada sobre el embedding nomic del prompt: `p_local` = P(local sustituye a frontier), `p_economy` = P(economy sustituye) |
| Decisión | `local` si `p_local ≥ τ_l`; si no `economy` si `p_economy ≥ τ_e`; si no `frontier` |
| Etiquetas | `tiers.R3_ordinal_mean.jsonl` (regla elegida); R1 y R2 como sensibilidad |
| Datos | 1250 prompts (1000 ES + 250 EN), CV de 5 folds **agrupada por `prompt_id`** (un prompt y su traducción caen en el mismo fold), estratificada por tarea |
| Hiperparámetro | λ ∈ {0.01, 0.1, 1, 10}, elegido por log-loss media fuera de fold (declarado) |
| Prefijo de embedding | `none` (el mismo vector que usa el caché) salvo que `classification:` mejore el AUC medio de ambos clasificadores en > 0.02; criterio fijado acá, antes de entrenar |
| Costo | local USD 0; economy/frontier = costo real capturado en la fase 2 para ese prompt |
| Calidad | fracción de prompts servidos por un nivel sustituible (frontier cuenta como sustituible por definición) |
| Latencia | se reporta aparte: sonda de 30 prompts ES por modelo |
| Frontera | barrido de (τ_l, τ_e) sobre probabilidades fuera de fold → puntos Pareto (costo por prompt, calidad) |
| Comparaciones | heurística actual (premium = frontier y premium = economy), todo-local, todo-economy, todo-frontier, aleatorio a igual costo, oráculo, kNN ponderado por similitud (ablación, k=20) |
| Knob por tenant | `routing_quality_target` ∈ [0.5, 1.0], default 0.95: el router usa el punto de operación más barato cuya calidad fuera de fold ≥ objetivo; si ninguno, todo frontier |
| Artefacto | `src/nebula/data/learned_router_v1.json`: pesos de los dos modelos (entrenados con todos los datos), λ, prefijo, modelo de embedding, puntos de operación (de las probabilidades fuera de fold), versión y hash de etiquetas |
| Dependencias | `numpy` solo en `dev` (entrenamiento); la inferencia en el gateway es stdlib |

## Integración en el gateway

- **Catálogo**: `NEBULA_ECONOMY_MODEL` nuevo (sin default → sin nivel economy, el comportamiento de hoy); `NEBULA_PREMIUM_MODEL` es el frontier. Ambos por el mismo proveedor OpenAI-compatible (OpenRouter). `benchmarks/pricing.json` suma haiku-4.5 y gpt-4.1. `.env.example` y el compose self-hosted pasan a qwen2.5:7b / haiku-4.5 / gpt-4.1.
- **Activación**: `NEBULA_LEARNED_ROUTER_ENABLED` (default `false`, así la suite y los despliegues viejos no cambian) y `NEBULA_LEARNED_ROUTER_PATH` (default el artefacto empaquetado).
- **Destino**: `RouteTarget` sigue siendo `local`/`premium` (ledger, métricas, consola intactos). `RouteDecision` gana `model: str | None`; el nivel va en `route_signals.tier` y en el header nuevo `X-Nebula-Route-Tier` (`local`/`economy`/`frontier`/`cache`/`denied`).
- **Motivo**: `learned_router` cuando decide el router aprendido. Explícitos, `local_only`/`premium_only`, presupuesto y `calibrated_routing_disabled` siguen como hoy (este último también apaga el aprendido).
- **Embedding único**: el chat embebe el último mensaje del usuario una vez (solo si el router aprendido está activo) y pasa el vector al router y al caché (`lookup`/`store` aceptan un vector precalculado). Si el embedding falla, el router cae a la heurística y lo marca (`route_signals.learned_router = "embedding_unavailable"`).
- **Proveedor**: para `premium` con `model` de la decisión, el pedido al proveedor lleva ese modelo. El fallback local→premium usa economy si existe.
- **Política**: chequeo de modelos permitidos y tope por request usan el modelo de la decisión. Columna nueva `routing_quality_target` (migración Alembic nueva, default 0.95), expuesta en la API de políticas.
- **Replay/simulación**: sin cambios (sigue sobre la heurística; declarado).

## Salidas de evaluación

`benchmarks/router/v1/`: `report.json`, `report.md` (tabla de frontera, costo a calidad 0.95/0.90, AUC por clasificador e idioma, comparación de prefijos, kNN, sensibilidad R1/R2, latencias), `latency.jsonl`. Bloque `<!-- GEN:router-fase3 -->` en §6.4 de la tesis.

## Fuera de alcance

Consola y slider (fase 4), rate limiting (fase 5), aprendizaje en línea, replay del router aprendido en la simulación de políticas, bug `avoided_premium_cost_usd = 0` de `recommendation_service`.

## Criterios de aceptación

1. `make lint`, `make test`, `make console-test` verdes; tests nuevos sin red.
2. En CV, a calidad ≥ 0.95 el router aprendido cuesta menos por prompt que la heurística y que el aleatorio a igual calidad (si no, se reporta tal cual: es un resultado).
3. Con `NEBULA_LEARNED_ROUTER_ENABLED=true`, una request `nebula-auto` rutea a los tres niveles según el prompt y el objetivo del tenant, con `X-Nebula-Route-Tier` y costo en el ledger por el modelo real.
4. Embedding caído → heurística, sin error al cliente.
5. Tabla de §6.4 generada por script.
