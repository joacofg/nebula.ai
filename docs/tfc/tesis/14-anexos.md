# 14. Anexos

## Anexo A. Casos de prueba

La Tabla A.1 amplía la Tabla 11.3 con la entrada de cada caso y la evidencia que lo respalda: un
test de la suite (archivo y nombre) o un reporte versionado del repositorio.

**Tabla A.1.** Casos de prueba completos.

| ID | Descripción | Entrada | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|
| CP-01 | Ahorro del router en el objetivo 0.95 | 1250 prompts del corpus, estimación anidada | ≥ 30 % contra todo frontier | 31 % (IC 95 % 28–35 %) | P | `benchmarks/router/v1/report.json` → `nested.0.95` |
| CP-02 | Calidad del router en el objetivo 0.95 | ídem | ≥ 0.95 | 0.957 (español 0.961, inglés 0.940) | P | ídem |
| CP-03 | Router contra mezcla aleatoria a igual calidad | ídem | menor costo | 17 % menos (IC 95 % 12–21 %) | P | ídem, `vs_random` |
| CP-04 | Heurística de dos reglas contra todo local | ídem, heurística → frontier | calidad mayor que todo local | 0.759 contra 0.754 | F | ídem, `baselines` |
| CP-05 | Acuerdo jueces–humano en español | 50 pares sorteados antes de los jueces | κ ≥ 0.4 (pre-registrado) | κ 0.31 (IC −0.07–0.64) | F | `benchmarks/ground-truth/v1/validation.json` |
| CP-06 | Rechazos confirmados por el humano | 25 rechazados + 10 aceptados, a ciegas | mayoría de rechazos confirmados | 20 de 25 (80 %, Wilson 61–91 %) | P | ídem, `negatives_es` |
| CP-07 | Similitud coseno como métrica de calidad | 22 pares EN con nota humana | AUC > 0.5 | AUC 0.25 (IC 0.00–0.56) | F | `benchmarks/metric-validation/report.json` |
| CP-08 | Caché aislado por tenant y antigüedad | búsqueda con tenant y TTL de la política | filtro por tenant y fecha, umbral de la política | aplicado en la consulta a Qdrant | P | `tests/test_semantic_cache_service.py::test_lookup_filters_by_tenant_and_freshness_and_uses_tenant_threshold` |
| CP-09 | Fallback local → premium | falla simulada del proveedor local | completa en el premium | completado, cabecera de fallback | P | `tests/test_service_flows.py::test_stream_completion_falls_back_to_premium_provider`, `tests/test_response_headers.py::test_response_headers_cover_local_premium_cache_and_fallback` |
| CP-10 | Caída de Qdrant | caché inalcanzable | responde sin caché, salud degradada | responde, `/health/ready` degradado | P | `tests/test_phase10_outage_safety.py::test_semantic_cache_outage_keeps_chat_completion_serving_and_health_degraded` |
| CP-11 | Caída de Ollama con el router activo | embedding que falla | decide con la heurística y lo registra | heurística, señal `learned_router` | P | `tests/test_learned_routing.py::test_embedding_failure_falls_back_to_the_heuristic` |
| CP-12 | Límite de pedidos por minuto | límite 2/min, tercer pedido | 429 + `Retry-After`, sin llamar al proveedor | 429, fila `rate_limited` | P | `tests/test_rate_limiting.py::test_the_request_over_the_limit_is_429_and_never_reaches_a_provider`, `::test_the_rejection_is_in_the_ledger` |
| CP-13 | Objetivo de calidad por tenant | mismo prompt con objetivos 0.8, 0.9 y 1.0 | el nivel cambia con el objetivo | todo local, mezcla, todo frontier | P | `tests/test_learned_routing.py::test_learned_router_picks_the_tier_from_the_vector`, `::test_quality_target_above_every_point_routes_to_frontier`; demo del runbook |
| CP-14 | Cabeceras `X-Nebula-*` | pedidos por cada ruta | presentes y coherentes con el ledger | presentes y coherentes | P | `tests/test_response_headers.py::test_response_headers_expose_outcome_grounded_route_mode_and_header_ledger_parity` |
| CP-15 | Replay de la consola | archivo de replay empaquetado | coincide con el artefacto | coincide | P | `tests/test_evaluation_api.py::test_the_packaged_replay_matches_the_artifact` |
| CP-16 | Extremo a extremo de la consola | Playwright contra el stack local | todas las pruebas pasan | fallan `observability.spec.ts` y `playground.spec.ts` (selectores ambiguos, previos a esta etapa) | F | `console/e2e/` |
| CP-17 | Cifras de la tesis al día | `python -m scripts.thesis.tables --check` | ningún bloque desactualizado | al día | P | `tests/test_thesis_tables.py::test_repo_thesis_is_up_to_date` |

## Anexo B. Rúbrica y prompt de los jueces

El lector humano y los jueces responden la misma pregunta con la misma escala, definida en
`scripts/metric_validation/rubric.py`. La pregunta es:

> *Could either response have replaced the other for the person who asked this question, without
> them being worse off?*

La escala tiene cuatro grados; los dos primeros cuentan como sustituible:

| Grado | Descripción (traducida) |
|---|---|
| `equivalent` | Mismo contenido. Pueden cambiar la redacción, el orden o la longitud, pero un lector se llevaría la misma respuesta de cualquiera de las dos. |
| `minor_loss` | Mismo contenido, una de las dos un poco más pobre: una advertencia omitida, un ejemplo más flojo, una estructura más torpe. El lector igual queda bien servido. |
| `partial` | Se superponen pero difieren en lo sustancial: una contesta solo parte de la pregunta, o agrega una afirmación que la otra no respalda. |
| `divergent` | Respuestas distintas, o una es incorrecta, está fuera de tema o no se puede usar. Un lector notaría el cambio enseguida. |

El prompt que reciben los jueces (`scripts/metric_validation/llm_judge.py`) no dice qué modelo
escribió cada respuesta ni cuál es la referencia, y el orden se invierte en la segunda pasada:

```text
You are grading how interchangeable two candidate responses to the same prompt are.
You are not judging which one is better, and you are not being asked which model wrote them.
{question}
Grade on this scale, and reply with JSON only, in the form {"grade": "<grade>"}:
{scale}
PROMPT
------
{prompt}
RESPONSE A
----------
{response_a}
RESPONSE B
----------
{response_b}
```

Los jueces son `google/gemini-2.5-flash` y `deepseek/deepseek-chat-v3-0324`, a temperatura 0, con el
razonamiento apagado y un máximo de 200 tokens de salida.

## Anexo C. Pre-registro de la validación

El texto completo está en `benchmarks/ground-truth/v1/preregistration.md`; su commit es anterior a
cualquier juicio sobre el corpus. Lo esencial:

- Cada par se juzga por los dos jueces en las dos posiciones: cuatro notas. Un par con menos de
  cuatro notas válidas queda fuera.
- Reglas: R1 unanimidad (las cuatro notas sustituibles), R2 mayoría (al menos tres de cuatro), R3
  media ordinal (media de los índices de la escala ≤ 1.5).
- Selección: la regla con mayor κ de Cohen binario contra el lector humano sobre los 22 pares en
  inglés del piloto; en caso de empate, R1 antes que R2 y R2 antes que R3.
- Hold-out: 50 pares en español sorteados (semilla 20260927) antes de correr los jueces,
  etiquetados por el lector. Se reporta el κ de la regla elegida con intervalo bootstrap de 2000
  remuestras. No se usa para elegir.
- Umbral: un κ en español menor que 0.4 obliga a declarar el ground truth "limitado por los
  jueces".
- Nivel de cada prompt: local si la respuesta de qwen2.5:7b es sustituible por la de gpt-4.1; si
  no, económico si lo es la de claude-haiku-4.5; si no, frontier. Como sensibilidad, lo mismo con
  llama3.2:3b como local.
- Enmienda 1 (antes de correr los jueces): se declara que los 22 pares de selección se eligieron
  por desacuerdo y quedaron 20/2, y se agrega el reporte de niveles bajo las tres reglas.

## Anexo D. Reproducción

Todo lo que cita este documento se regenera desde el repositorio.

```bash
make setup && cp .env.example .env         # entorno Python 3.12
docker compose up -d qdrant                 # caché
make test && make console-test              # suites
python -m scripts.router.train              # router: artefacto, replay y reporte (sin red)
make thesis-tables                          # bloques GEN de la tesis
make thesis-figures                         # figuras
```

Las etapas que llaman a modelos (traducción, respuestas, jueces) están en `scripts/ground_truth/` y
registran el gasto en `benchmarks/ground-truth/v1/spend.jsonl`; sus salidas ya están versionadas,
así que no hace falta volver a correrlas para reproducir las cifras.

Para ver el router de tres niveles en funcionamiento, sin tocar el archivo `.env` (que la suite de
pruebas lee), se exportan las variables al levantar el gateway:

```bash
NEBULA_LEARNED_ROUTER_ENABLED=true \
NEBULA_PREMIUM_MODEL=openai/gpt-4.1 \
NEBULA_ECONOMY_MODEL=anthropic/claude-haiku-4.5 \
make run
```

## Anexo E. Repositorio

El código, los datos, los reportes y la fuente de este documento están en
<https://github.com/joacofg/nebula.ai>. Las especificaciones y planes de cada fase están en
`docs/superpowers/specs/` y `docs/superpowers/plans/`.
