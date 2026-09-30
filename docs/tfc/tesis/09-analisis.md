# 9. Análisis del sistema

## 9.1 Situación inicial

<!-- GEN:baseline-savings -->
Línea de base (heurística de dos reglas, 14 escenarios, 2026-08-19): 41.2 % (corrida 20260819T225557Z), 38.2 % (corrida 20260819T225703Z), 40.0 % (corrida 20260819T225713Z) de gasto premium evitado. En cada corrida pasaron 14/14 escenarios y 8 de 14 pedidos se sirvieron por el modelo local o por el caché. Estas corridas no miden la calidad de lo que se sirvió.
<!-- /GEN:baseline-savings -->

<!-- GEN:metric-validation -->
Sobre 22 pares en inglés con nota humana, la similitud coseno del embedding (prefijo `search_document`) separó las respuestas sustituibles de las que no lo eran con AUC 0.25 (IC 95 % 0.00–0.56), por debajo del azar. La mediana del coseno entre una respuesta local y una premium fue 0.944, prácticamente la misma que entre dos modelos premium (0.939): en ese rango la métrica está saturada y no distingue calidad. En esos mismos pares, la proporción juzgada sustituible fue el lector humano 91 %, google/gemini-2.5-flash 68 %, openai/gpt-4o-mini 32 %.
<!-- /GEN:metric-validation -->

## 9.2 Requerimientos
