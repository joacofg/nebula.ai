# 6. Evaluación

## 6.1 Preguntas de investigación
RQ1 ¿Cuánto gasto premium evita cada estrategia de ruteo a igual calidad?
RQ2 ¿La similitud coseno sirve como métrica de calidad? (estudio de validación: no, AUC 0.25)
RQ3 ¿Cuánto se aproximan los jueces LLM a un lector humano, en inglés y en español?
RQ4 ¿Cómo cambia la frontera con el tamaño del modelo local (3B vs 7B)?

## 6.2 Corpus
<!-- GEN:corpus-fase2 -->
El corpus combina tres conjuntos públicos: dolly (CC BY-SA 3.0); gsm8k (MIT); mbpp (CC BY 4.0). Se muestrearon 1000 prompts estratificados por tarea (code 200, factual_qa 200, multistep_reasoning 200, open_writing 200, summarisation 200) con semilla fija, y un subconjunto pareado de 250 en inglés. La traducción al español la hizo `mistralai/mistral-medium-3.1`, de una familia ajena a candidatos y jueces. En razonamiento y código, donde los números son la tarea, 10 traducciones fueron rechazadas por el control mecánico de números y código y reemplazadas desde la reserva del mismo estrato; en las tareas de Dolly, 31 traducciones reescribieron números por estilo (p. ej. «siglo XV») y quedaron marcadas para la revisión humana. Una revisión humana de 40 traducciones encontró 0 infieles (0%).
<!-- /GEN:corpus-fase2 -->

## 6.3 Jueces y validación contra humanos
Antecedente ya medido: sobre 22 pares en inglés, sustituibles según gpt-4o-mini 32 %, gemini-2.5-flash 68 %,
lector humano 91 % (p = 1.2e-4). <!-- GEN: judge-vs-human -->
<!-- GEN:judges-fase2 -->
Cada par candidato–referencia recibe cuatro notas (dos jueces, dos posiciones). La regla se eligió sobre 22 pares en inglés etiquetados por un lector humano; esos pares se eligieron en el piloto por desacuerdo entre dos jueces previos y quedaron 20 sustituibles y 2 no, así que el kappa de selección descansa en muy pocos negativos. Kappa binario por regla: R1 -0.015, R2 0.327, R3 0.645; se eligió R3. Como análisis de sensibilidad pre-registrado, los niveles se reportan bajo las tres reglas. La validación sobre el hold-out en español está pendiente. Tasa de cambio de veredicto al invertir posiciones: deepseek-chat-v3-0324 8%, gemini-2.5-flash 12%.
<!-- /GEN:judges-fase2 -->

## 6.4 Resultados de ruteo
Línea de base (heurística de dos reglas, 14 escenarios, 2026-08-19): 41.2 % (corrida 20260819T225557Z), 38.2 % (20260819T225703Z) y 40.0 % (20260819T225713Z) de gasto
premium evitado. <!-- GEN: baseline-savings -->
> PENDIENTE (fase 3): curva costo/calidad del router aprendido vs heurística.

## 6.5 Amenazas a la validez
