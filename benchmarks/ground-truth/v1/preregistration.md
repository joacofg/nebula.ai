# Pre-registro — ensamble de jueces (fase 2)

Fijado antes de correr cualquier juez sobre el corpus. El commit de este archivo es anterior a `judgements/corpus.*`.

- Rúbrica: `scripts/metric_validation/rubric.py` (4 grados; sustituible = `equivalent` o `minor_loss`).
- Jueces: `google/gemini-2.5-flash`, `deepseek/deepseek-chat-v3-0324`, temperatura 0, razonamiento apagado.
- Cada par candidato–referencia se juzga en las dos posiciones (`ab`, `ba`) por los dos jueces: 4 notas.
- Un par con menos de 4 notas válidas queda fuera de reglas, kappa y niveles.
- Reglas (índices 0–3 de la escala):
  - R1 unánime: las 4 notas ≤ `minor_loss`.
  - R2 mayoría: ≥ 3 de 4 notas ≤ `minor_loss`.
  - R3 ordinal: media de índices ≤ 1.5.
- Selección: mayor kappa de Cohen binario contra `human-3` sobre los 22 pares EN del piloto; empate → R1 > R2 > R3.
- Hold-out: 50 pares ES sorteados (semilla 20260927) antes de los jueces, etiquetados por `human-es-1`. Se reporta el kappa de la regla elegida con IC bootstrap 95 % (2000 remuestras, semilla 20260927). No se usa para elegir.
- Umbral: kappa ES < 0.4 → la tesis declara el ground truth "limitado por los jueces".
- Nivel por prompt: `local` si qwen2.5:7b es sustituible por gpt-4.1; si no, `economy` si claude-haiku-4.5 lo es; si no, `frontier`. Sensibilidad: lo mismo con llama3.2:3b como local.

## Enmienda 1 — 2026-09-27, antes de correr cualquier juez

Motivo: la revisión del código señaló que los 22 pares EN de selección no son una muestra aleatoria. El piloto los eligió por desacuerdo entre dos jueces previos (gpt-4o-mini y gemini-2.5-flash) y `human-3` los calificó 20 sustituibles y 2 no, así que el kappa de selección descansa en dos negativos. La regla de selección no cambia; se agrega:

- La tesis y el reporte declaran la composición del conjunto de selección (criterio de elección y balance 20/2).
- Análisis de sensibilidad: los niveles por prompt se calculan con las tres reglas (`tiers.R1_unanimous.jsonl`, `tiers.R2_majority.jsonl`, `tiers.R3_ordinal_mean.jsonl`) y el reporte muestra la distribución de niveles bajo cada una.
- El hold-out ES reporta el kappa de las tres reglas como referencia secundaria; no se usa para elegir.
- El hold-out tiene 50 pares calificados: el par que `label.py` usa para la calibración (idéntico y truncado) se toma aparte y no forma parte del sorteo.
