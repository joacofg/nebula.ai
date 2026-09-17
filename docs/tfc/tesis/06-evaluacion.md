# 6. Evaluación

## 6.1 Preguntas de investigación
RQ1 ¿Cuánto gasto premium evita cada estrategia de ruteo a igual calidad?
RQ2 ¿La similitud coseno sirve como métrica de calidad? (estudio de validación: no, AUC 0.25)
RQ3 ¿Cuánto se aproximan los jueces LLM a un lector humano, en inglés y en español?
RQ4 ¿Cómo cambia la frontera con el tamaño del modelo local (3B vs 7B)?

## 6.2 Corpus
> PENDIENTE (fase 2): origen público, estratificación por tarea, traducción, tamaño.

## 6.3 Jueces y validación contra humanos
Antecedente ya medido: sobre 22 pares en inglés, sustituibles según gpt-4o-mini 32 %, gemini-2.5-flash 68 %,
lector humano 91 % (p = 1.2e-4). <!-- GEN: judge-vs-human -->
> PENDIENTE (fase 2): ensamble, rúbrica "lector satisfecho", 50 pares en español.

## 6.4 Resultados de ruteo
Línea de base (heurística de dos reglas, 14 escenarios, 2026-08-19): 41.2 % (corrida 20260819T225557Z), 38.2 % (20260819T225703Z) y 40.0 % (20260819T225713Z) de gasto
premium evitado. <!-- GEN: baseline-savings -->
> PENDIENTE (fase 3): curva costo/calidad del router aprendido vs heurística.

## 6.5 Amenazas a la validez
