# 6. Resumen

Los equipos que construyen productos sobre modelos de lenguaje grandes suelen elegir un modelo
premium y mandarle todo el tráfico, aunque muchas consultas las resolvería igual de bien un modelo
más barato o uno local. Los gateways de IA existentes rutean, hacen fallback y cachean, pero deciden
con reglas que escribe el operador y no miden si lo que sirvieron por la ruta barata alcanzaba. Este
trabajo presenta Nebula, un gateway de IA self-hosted que elige, consulta por consulta, entre un
modelo local (qwen2.5:7b), uno premium económico (claude-haiku-4.5) y uno frontier (gpt-4.1) con un
router aprendido: dos regresiones logísticas sobre el embedding del prompt estiman si la respuesta
de cada nivel barato podría reemplazar a la del frontier, y una cascada sobre dos umbrales elige el
nivel más barato que alcanza. El operador elige para cada tenant un punto de la frontera
costo–calidad. Para entrenar y evaluar el router, cuatro modelos respondieron un corpus de 1000
prompts en español y 250 en inglés, y un ensamble de dos jueces LLM de otras familias, validado
contra un lector humano con reglas pre-registradas, juzgó las respuestas. La similitud coseno, la
métrica propuesta al inicio, no distinguía calidad (AUC 0.25). En una estimación anidada con el
objetivo de calidad en 0.95, el router logra una calidad de 0.957 a USD 1.70 cada mil prompts: un 31
% menos que mandar todo al frontier (IC 95 % 28–35 %) y un 17 % menos que una mezcla aleatoria de
niveles de igual calidad. La hipótesis, al menos un 30 % de ahorro con una caída no mayor a 5 puntos
en las respuestas aceptables, se verifica, y la medición es conservadora: los jueces son más
estrictos que el lector humano, y el caché semántico, que no aporta en un corpus sin consultas
repetidas, sumaría ahorro en tráfico real.

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
