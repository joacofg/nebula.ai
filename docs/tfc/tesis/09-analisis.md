# 9. Análisis del sistema

Este capítulo fija el punto de partida de la investigación: qué hacía el gateway antes de las
mejoras que se describen en los capítulos 10 y 11, qué medía y, sobre todo, qué no medía. De esa
situación salen los requerimientos que la solución tiene que cumplir.

## 9.1 Situación inicial

La primera versión de Nebula ya era un gateway self-hosted completo. Recibía pedidos en una API
compatible con la de OpenAI, identificaba al tenant por su clave, aplicaba una política
(presupuestos, modelos premium permitidos, caché habilitado o no), consultaba un caché semántico
en Qdrant, elegía entre un modelo local servido por Ollama y un modelo premium, hacía fallback al
premium si el local fallaba y registraba cada pedido en un ledger con su costo estimado. La consola
mostraba ese ledger. Lo que no tenía era un criterio para decidir la ruta que estuviera respaldado
por datos.

La decisión la tomaba una heurística de dos reglas. Un pedido iba al modelo premium si su
longitud estimada (caracteres divididos cuatro) llegaba a 500 tokens o si contenía alguna de seis
palabras clave en inglés (*analyze*, *reason*, *contract*, *debug*, *architecture*, *design*); en
cualquier otro caso iba al modelo local. La regla es fácil de explicar y de auditar, pero no
tiene ninguna relación medida con la calidad de la respuesta: una pregunta corta puede ser muy
difícil, y una larga puede ser trivial.

Con esa heurística, la suite de benchmarks del proyecto producía la cifra que se usó en el TP4
para anclar la hipótesis:

<!-- GEN:baseline-savings -->
Línea de base (heurística de dos reglas, 14 escenarios, 2026-08-19): 41.2 % (corrida 20260819T225557Z), 38.2 % (corrida 20260819T225703Z), 40.0 % (corrida 20260819T225713Z) de gasto premium evitado. En cada corrida pasaron 14/14 escenarios y 8 de 14 pedidos se sirvieron por el modelo local o por el caché. Estas corridas no miden la calidad de lo que se sirvió.
<!-- /GEN:baseline-savings -->

El ahorro existía, pero la última oración del bloque es la que importa. La suite verificaba que
cada escenario tomara la ruta esperada, no que la respuesta servida fuera buena. Un 40 % de gasto
evitado no dice nada si la mitad de esas respuestas no le servían a quien preguntó.

Para cubrir ese hueco, el TP4 propuso medir la calidad como similitud coseno entre el embedding de
la respuesta económica y el de la respuesta premium, con un umbral de 0.90. Antes de usar esa
métrica se la validó contra un lector humano, con un estudio piloto que forma parte del
repositorio (`benchmarks/metric-validation/`). El resultado fue negativo:

<!-- GEN:metric-validation -->
Sobre 22 pares en inglés con nota humana, la similitud coseno del embedding (prefijo `search_document`) separó las respuestas sustituibles de las que no lo eran con AUC 0.25 (IC 95 % 0.00–0.56), por debajo del azar. La mediana del coseno entre una respuesta local y una premium fue 0.944, prácticamente la misma que entre dos modelos premium (0.939): en ese rango la métrica está saturada y no distingue calidad. En esos mismos pares, la proporción juzgada sustituible fue el lector humano 91 %, google/gemini-2.5-flash 68 %, openai/gpt-4o-mini 32 %.
<!-- /GEN:metric-validation -->

Dos conclusiones salieron de ese estudio y condicionaron todo lo que vino después. La primera es
que la similitud semántica no sirve como criterio de calidad en este problema: casi cualquier
respuesta que contesta la pregunta correcta tiene un coseno alto con cualquier otra, sea buena o
mala. La segunda es que los jueces LLM tampoco se pueden usar sin validarlos, porque en el piloto
eran bastante más estrictos que el lector humano, y además distintos entre sí. De ahí que el
instrumento de calidad del trabajo pasara a ser un ensamble de jueces de otra familia, validado
contra una persona antes de usarlo (sección 11.2), y que la hipótesis del TP8 se formulara sobre
la tasa de respuestas aceptables y no sobre la similitud.

El estado inicial se resume entonces en tres carencias. El gateway decidía la ruta con una regla
sin respaldo empírico; no existía un conjunto de datos con la calidad de cada modelo sobre los
mismos prompts, así que no había con qué entrenar ni con qué evaluar una regla mejor; y el
operador no tenía ninguna forma de expresar cuánta calidad estaba dispuesto a resignar a cambio de
ahorro.

## 9.2 Requerimientos

Los requerimientos se derivan de esas carencias y de los objetivos específicos de la sección 7.4.
Cada uno indica el objetivo al que responde. La Tabla 9.1 lista los funcionales y la Tabla 9.2 los
no funcionales.

**Tabla 9.1.** Requerimientos funcionales.

| ID | Requerimiento | OE |
|---|---|---|
| RF-01 | El gateway expone `POST /v1/chat/completions` compatible con la API de OpenAI, con y sin streaming, y autentica cada pedido con una clave asociada a un tenant. | OE2 |
| RF-02 | Para cada pedido, el gateway elige entre tres niveles (modelo local, premium económico, premium frontier) según la probabilidad estimada de que la respuesta del nivel barato sea aceptable. | OE2 |
| RF-03 | El operador fija, por tenant, un objetivo de calidad; el gateway usa el punto de operación más barato que lo cumple. | OE2 |
| RF-04 | El caché semántico sirve una respuesta guardada solo si pertenece al mismo tenant, supera el umbral de similitud de su política y no es más vieja que la antigüedad máxima configurada. | OE2 |
| RF-05 | Si el modelo local falla y la política lo permite, el pedido se reenvía al proveedor premium. | OE2 |
| RF-06 | Cada respuesta informa, en cabeceras `X-Nebula-*`, la ruta, el nivel, el motivo de la decisión y si hubo caché o fallback, y cada pedido queda en el ledger con su costo estimado. | OE2 |
| RF-07 | La consola muestra el ledger, la política de cada tenant, la frontera costo–calidad y un simulador que reproduce las decisiones del router sobre el corpus sin llamar a ningún modelo. | OE2 |
| RF-08 | Se construye un corpus bilingüe con respuestas de cuatro modelos y una etiqueta de calidad por par, a partir de conjuntos de datos públicos. | OE1, OE3 |
| RF-09 | El instrumento de calidad se valida contra un lector humano con criterios fijados de antemano. | OE3 |
| RF-10 | El entrenamiento del router y la estimación de su desempeño son reproducibles con un comando, a partir de los datos versionados. | OE3 |
| RF-11 | El gateway limita los pedidos por minuto de cada tenant y responde 429 al superarlo. | OE2 |
| RF-12 | Las cifras que cita este documento se regeneran desde los reportes del repositorio. | OE4 |

**Tabla 9.2.** Requerimientos no funcionales.

| ID | Requerimiento | OE |
|---|---|---|
| RNF-01 | Despliegue self-hosted con un único `docker compose`, sin plano de control alojado. | OE2 |
| RNF-02 | Si Qdrant u Ollama no están disponibles, el gateway sigue respondiendo (sin caché o con la regla de respaldo), y lo informa. | OE2 |
| RNF-03 | La decisión de ruta agrega a lo sumo un embedding por pedido, compartido con el caché. | OE2 |
| RNF-04 | La evaluación separa la elección de umbrales de los datos sobre los que se mide (estimación anidada). | OE3 |
| RNF-05 | El gasto total en APIs para construir la evidencia no supera los USD 50. | OE3 |
| RNF-06 | Todo el sistema y los experimentos corren en una única computadora personal (Apple M4, 16 GB). | OE2, OE3 |
