# Spec — Fase 2: corpus bilingüe y ground truth de calidad

Origen: plan maestro `tesis-10x-decisiones-2026-09` (grilling 2026-09-16) y brainstorming 2026-09-27.
Prioridad: rigor > demo > features > ingeniería. Presupuesto API total del plan: ~USD 50; esta fase tiene tope duro de USD 35.

## Objetivo

Producir, para cada prompt de un corpus público estratificado, el **nivel más barato cuya respuesta sustituye a la de la referencia frontier** (`local` / `economy` / `frontier`), con jueces LLM cuyo acuerdo con un lector humano está medido en inglés y en español. Esa etiqueta es el dato de entrenamiento del router aprendido de la fase 3 y responde OE3 (la calidad deja de ser no medida).

## Decisiones

| Tema | Decisión |
|---|---|
| Fuente | Dolly-15k (CC BY-SA 3.0) + GSM8K (MIT) + MBPP (CC BY 4.0), revisiones fijadas por hash |
| Tareas | `factual_qa`, `summarisation`, `open_writing` (Dolly), `multistep_reasoning` (GSM8K), `code` (MBPP); 200 por tarea |
| Idiomas | 1000 prompts en ES (carga principal) + subset pareado de 250 en EN (50 por tarea) |
| Traducción | `mistralai/mistral-large` (familia ajena a candidatos y jueces), temperatura 0; muestra de 40 revisada por Joaquín, tasa de error reportada |
| Candidatos | `qwen2.5:7b` (local), `llama3.2:3b` (local, sensibilidad), `anthropic/claude-haiku-4.5` (economy), `openai/gpt-4.1` (frontier y referencia) |
| Jueces | `google/gemini-2.5-flash` + `deepseek/deepseek-chat-v3`, temperatura 0, razonamiento apagado |
| Rúbrica | `scripts/metric_validation/rubric.py` sin cambios (escala de 4, "¿el lector quedaría igual de bien servido?"), para que las 22 etiquetas human-3 sigan valiendo |
| Pares | cada candidato barato vs gpt-4.1, en las dos posiciones, con cada juez: 4 notas por par |
| Código | paquete nuevo `scripts/ground_truth/`; reutiliza `metric_validation` **por import**, sin modificarlo |
| Datos | `benchmarks/ground-truth/v1/` trackeado |

## Etapas

Cada etapa es un comando `python -m scripts.ground_truth.<etapa>`, reanudable (caché por clave), y escribe JSONL.

1. **sample** — descarga los tres datasets (HF datasets-server, sin dependencia nueva), filtra (prompt+contexto ≤ 1500 tokens aprox., sin vacíos), muestrea 200 por tarea con semilla fija y marca 50 por tarea como subset EN. Salida: `prompts.en.jsonl`, `NOTICE`.
   - Dolly: `open_qa`+`general_qa`+`closed_qa` → `factual_qa`; `summarization` → `summarisation`; `creative_writing`+`brainstorming` → `open_writing`. El `context` de Dolly se incluye en el prompt.
   - MBPP: se usa la descripción + la firma del primer test como pedido; no se ejecuta código.
2. **translate** — traduce al español. Validador: el multiconjunto de números y los bloques de código/identificadores entre backticks deben coincidir con el original. Falla → un reintento → si vuelve a fallar se descarta y se reemplaza por el siguiente prompt del mismo estrato (el sample reserva un pool de reemplazo). Salida: `prompts.es.jsonl`. `review_translation` presenta la muestra de 40 y registra aciertos/errores.
3. **capture** — corre los 4 candidatos sobre 1000 ES + 250 EN, `max_tokens=1024`, temperatura 0. Registra `finish_reason`, tokens y costo real. Salida: `responses/<rol>.<lang>.jsonl`.
4. **judge** — arma los pares (qwen-7b, llama-3b, haiku) × gpt-4.1, cegados con `metric_validation.blinding`, en las dos posiciones, con los dos jueces. Salida: `judgements/<juez>.jsonl`.
5. **validate** — (a) corre los dos jueces sobre los 22 pares EN del piloto etiquetados por human-3; (b) la sesión de etiquetado ES (`label`) sobre los 50 pares hold-out; (c) aplica las tres reglas. Salida: `validation.json`.
6. **tiers** — con la regla elegida etiqueta cada prompt. Salida: `tiers.jsonl` (local = qwen-7b) y `tiers.llama3b.jsonl` (sensibilidad).
7. **report** — `report.md` + `report.json`, y los bloques `<!-- GEN: ... -->` de §6.2 y §6.3 de la tesis.

## Hold-out español

- 50 pares sorteados con semilla fija **antes** de correr los jueces: 10 por tarea, repartidos entre los tres tipos de par. La selección no depende de la opinión de los jueces.
- Sesión con `metric_validation.label` (cegado, A/B aleatorio, reanudable), precedida de calibración de 3 ítems con veredicto fijado por construcción (incluye un truncado del mismo tema). La calibración no cuenta.
- Rater `human-es-1` (persona: Joaquín) registrado en `raters.json`.
- Amenaza a la validez documentada: los 22 pares EN del piloto fueron elegidos por desacuerdo entre jueces viejos.

## Ensamble pre-registrado

Se commitea `benchmarks/ground-truth/v1/preregistration.md` antes de la etapa `judge`. Con las 4 notas de un par como índices 0–3:

- **R1 unánime**: las 4 ≤ `minor_loss`.
- **R2 mayoría**: ≥ 3 de 4 ≤ `minor_loss`.
- **R3 ordinal**: media de índices ≤ 1.5.

Se elige la regla con mayor kappa de Cohen binario contra human-3 en EN; empate → la más conservadora (R1 > R2 > R3). Se reporta su kappa contra `human-es-1` con IC bootstrap 95 %. Si el kappa ES < 0.4, la tesis declara el ground truth "limitado por los jueces"; la fase no se bloquea.

También se reportan: sesgo de posición por juez (tasa de cambio de veredicto binario al invertir A/B), acuerdo entre jueces, distribución de niveles por tarea e idioma.

## Etiqueta de nivel

`local` si el par qwen-7b es sustituible; si no, `economy` si el par haiku es sustituible; si no, `frontier`. Un par sin veredicto (respuesta fallida o juez sin nota tras reintentos) deja el prompt sin etiqueta y se cuenta.

## Errores y procedencia

- API: backoff exponencial, 3 reintentos; luego `failed`, excluido y contado. Nunca un valor por defecto.
- Juez: `metric_validation.llm_judge.parse_grade` sin default, 2 reintentos; luego `missing`.
- `provenance.json`: modelos pedidos y resueltos por OpenRouter, digests de Ollama, versión de Ollama, sha256 de cada JSONL, semillas, revisiones de datasets.

## Gasto

- Costo por llamada desde `usage` de OpenRouter, acumulado en `spend.jsonl`.
- Tope duro configurable (default USD 35): la etapa aborta limpia; lo pagado queda en caché.
- `--dry-run` estima el costo con una tabla de precios propia del paquete antes de gastar.

## Fuera de alcance

Cambiar el modelo local por defecto del gateway a qwen y aplicar el prefijo `search_document` al caché (fase 3, junto con el router). Entrenar el router (fase 3). Consola (fase 4).

## Criterios de aceptación

1. `make lint`, `make test`, `make console-test` verdes.
2. `tests/test_ground_truth.py` sin red cubre: muestreo determinista y balanceado, validador de traducción, las tres reglas y el desempate, etiqueta de nivel, tope de gasto y reanudación sin re-pagar, cegado sin fuga de procedencia.
3. `tiers.jsonl` etiqueta ≥ 95 % de los 1250 prompts.
4. `validation.json` con kappa EN/ES y la regla elegida; `preregistration.md` commiteado antes que `judgements/`.
5. §6.2 y §6.3 de la tesis generadas por script.
6. Gasto real ≤ USD 35.
