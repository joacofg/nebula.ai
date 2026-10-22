# 6. Resumen

Los equipos que usan modelos de lenguaje grandes suelen mandar todo el tráfico a un modelo premium,
aunque muchas consultas las resolvería igual de bien uno más barato o local. Los gateways de IA
existentes rutean y cachean con reglas del operador, sin medir si lo servido por la ruta barata
alcanzaba. Este trabajo presenta Nebula, un gateway de IA self-hosted que elige, consulta por
consulta, entre un modelo local (qwen2.5:7b), uno premium económico (claude-haiku-4.5) y uno
frontier (gpt-4.1) con un router aprendido: dos regresiones logísticas sobre el embedding del
prompt estiman si la respuesta de cada nivel barato podría reemplazar a la del frontier, y una
cascada sobre dos umbrales elige el nivel más barato que alcanza. El operador
elige por tenant un punto de la frontera costo–calidad. Cuatro modelos respondieron 1000 prompts en
español y 250 en inglés, y dos jueces LLM de otras familias, validados contra un lector humano con
reglas pre-registradas, juzgaron las respuestas. En una estimación anidada con objetivo de calidad
0.95, el router logra una calidad de 0.957 a USD 1.70 cada mil prompts: un 31 % menos que mandar
todo al frontier (IC 95 % 28–35 %) y un 17 % menos que una mezcla aleatoria de niveles de igual
calidad. La hipótesis, al menos un 30 % de ahorro con una caída no mayor a 5 puntos en las
respuestas aceptables, se verifica, con una medición conservadora, porque los jueces son más
estrictos que el lector humano. El caché semántico, medido aparte con otro pre-registro, no
alcanzó una precisión de 0.95 en ningún umbral, y el gateway adoptó 0.99, un valor conservador;
aun así, en una traza en español con la tasa de duplicados de LMSYS-Chat-1M (12.1 %), baja otro
7.9 % el costo del router, con prácticamente la misma calidad.

**Palabras clave:** gateway de IA, enrutamiento de modelos, caché semántico, LLM como juez,
optimización de costos, self-hosted.

## Abstract

Teams that build products on large language models usually send all their traffic to one premium
model, paying premium prices for queries that a cheaper or locally hosted model could answer just
as well. Existing AI gateways route, fall back and cache by operator-written rules, and do not
measure whether what they served through the cheap path was good enough. This thesis presents
Nebula, a self-hosted AI gateway that routes each query among a local model (qwen2.5:7b), an
economy premium model (claude-haiku-4.5) and a frontier model (gpt-4.1) with a learned router: two
logistic regressions over the prompt embedding estimate whether each cheaper tier's answer could
replace the frontier one, and a cascade over two thresholds picks the cheapest tier that
qualifies. The operator chooses a point on the cost–quality frontier per tenant. A corpus of 1,000
Spanish and 250 English prompts was answered by four models and labelled by two LLM judges from
other model families, validated against a human reader under pre-registered rules. In a nested
cross-validated estimate at a quality target of 0.95, the router reaches 0.957 quality at USD 1.70
per thousand prompts: 31% cheaper than sending everything to the frontier model (95% CI 28–35%)
and 17% cheaper than a random tier mix of equal quality. The hypothesis — at least 30% premium
savings with no more than a 5-point drop in acceptable answers — holds, and the measurement is
conservative, since the judges are stricter than the human reader. The semantic cache, measured
separately under its own pre-registration, reached a precision of 0.95 at no threshold, so the
gateway ships a conservative default of 0.99; even so, on a Spanish trace with the duplicate rate
reported for LMSYS-Chat-1M (12.1%), it cuts the router's cost by a further 7.9% at practically
the same quality.

**Keywords:** AI gateway, model routing, semantic caching, LLM-as-a-judge, cost optimization,
self-hosted.
