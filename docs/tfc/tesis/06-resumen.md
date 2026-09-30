# 6. Resumen

Los equipos que integran modelos de lenguaje de gran escala en sus productos suelen elegir un modelo
premium y usarlo para todo el tráfico. Así pagan el precio más alto también por consultas que un
modelo más barato, o uno local, resolvería igual de bien. Los gateways de IA que existen ya rutean
entre proveedores, hacen fallback y cachean respuestas, pero deciden con reglas que escribe el
operador y no miden si lo que sirvieron por la ruta barata le sirvió a quien lo pidió.

Este trabajo presenta Nebula, un gateway de IA self-hosted que decide, consulta por consulta, qué
modelo la atiende. La hipótesis es que un gateway así puede reducir el gasto en inferencia premium
en al menos un 30 % respecto de mandar todo al modelo premium, manteniendo una tasa de respuestas
aceptables no más de 5 puntos por debajo de la de esa línea base.

El gateway expone una API compatible con la de OpenAI, aplica la política de cada cliente (tenant),
consulta un caché semántico aislado por tenant y elige entre tres niveles: un modelo local
(qwen2.5:7b, servido con Ollama), un modelo premium económico (claude-haiku-4.5) y un modelo
premium frontier (gpt-4.1). La decisión la toma un router aprendido: dos regresiones logísticas
estiman, a partir del embedding del prompt, la probabilidad de que la respuesta del modelo local y
la del económico puedan reemplazar a la del frontier, y una cascada sobre dos umbrales elige el
nivel más barato que alcanza. Cada par de umbrales es un punto de una frontera costo–calidad, y el
operador elige el de cada tenant declarando la calidad que necesita, desde una consola que simula
el efecto antes de aplicarlo.

Para entrenar y evaluar el router hubo que construir la evidencia. Se armó un corpus de 1000
prompts en español y 250 en inglés, a partir de tres conjuntos de datos públicos, y cuatro modelos
respondieron cada uno. La calidad se definió como sustituibilidad: si la respuesta barata podría
haber reemplazado a la del frontier sin que quien preguntó quedara peor. La similitud coseno, la
métrica propuesta al inicio, resultó no distinguir calidad (AUC 0.25 contra un lector humano), así
que el instrumento pasó a ser un ensamble de dos jueces LLM de otras familias, con reglas fijadas en
un pre-registro y validado contra el lector humano antes de usarlo. Los jueces coincidieron con el
lector en el 82 % de los pares en español; en los desacuerdos fueron más estrictos que el lector
(siete veces contra dos), así que la calidad que miden tiende a subestimarse.

El router se evaluó con una estimación anidada, que no deja que un prompt influya en los parámetros
que lo rutean. Con el objetivo de calidad en 0.95 entrega una calidad de 0.957 y gasta USD 1.70
cada mil prompts, un 31 % menos que mandar todo al frontier (intervalo del 95 %: 28 % a 35 %) y un
17 % menos que una mezcla aleatoria de niveles de igual calidad. La hipótesis se verifica, y con
una medición conservadora: los jueces son más exigentes que el lector humano, y el caché, que no
aporta en un corpus sin consultas repetidas, sumaría ahorro en tráfico real. La heurística que usaba
la versión anterior, que en la suite de escenarios ahorraba un 40 %, resultó tener sobre el corpus
la calidad de mandar todo al modelo local. El ahorro se paga en latencia (21.3 s de mediana del modelo local contra 2.5 s del frontier)
y es menor en español que en inglés.

El trabajo aporta un gateway self-hosted funcional, un router con una frontera costo–calidad
operable, un corpus bilingüe con etiquetas validadas contra una persona y un procedimiento
reproducible para rehacer la evidencia. Quedan como líneas futuras un segundo evaluador humano, el
aprendizaje en línea del router y la evaluación del caché sobre tráfico con repetición.

**Palabras clave:** gateway de IA, enrutamiento de modelos, caché semántico, LLM como juez,
optimización de costos, self-hosted.

## Abstract

Teams that build products on large language models usually pick one premium model and send it all
their traffic, paying premium prices for queries that a cheaper or locally hosted model could answer
just as well. Existing AI gateways route, fall back and cache, but they route by operator-written
rules and do not measure whether what they served through the cheap path was good enough. This
thesis presents Nebula, a self-hosted AI gateway that routes each query among a local model
(qwen2.5:7b), an economy premium model (claude-haiku-4.5) and a frontier model (gpt-4.1) with a
learned router: two logistic regressions over the prompt embedding estimate whether each cheaper
tier's answer could replace the frontier one, and a cascade over two thresholds picks the cheapest
tier that qualifies. Each threshold pair is a point on a cost–quality frontier, and the operator
chooses a point per tenant by stating the quality they need. To train and evaluate the router, a
corpus of 1,000 Spanish and 250 English prompts was answered by four models and labelled by an
ensemble of two LLM judges from other model families, validated against a human reader under
pre-registered rules. In a nested cross-validated estimate at a quality target of 0.95, the router
reaches 0.957 quality at USD 1.70 per thousand prompts: 31% cheaper than sending everything to the
frontier model (95% CI 28–35%) and 17% cheaper than a random tier mix of equal quality. The
hypothesis — at least 30% premium savings with no more than a 5-point drop in acceptable answers —
holds, and the measurement is conservative: the judges are stricter than the human reader, and the
semantic cache, which adds nothing on a corpus without repeated queries, would add savings on real
traffic.

**Keywords:** AI gateway, model routing, semantic caching, LLM-as-a-judge, cost optimization,
self-hosted.
