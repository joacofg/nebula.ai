# 8. Marco teórico

Este capítulo reúne lo que se sabe sobre el problema que aborda el trabajo y lo ordena en función
de la hipótesis. La sección 8.1 recorre cómo evolucionó la idea de repartir consultas entre modelos
y de reutilizar respuestas, y qué problemas deja abiertos. La sección 8.2 desarrolla los conceptos
sobre los que se apoya la solución: cómo se cobra la inferencia, qué es un gateway, cómo funcionan
los modelos locales, los embeddings y el caché semántico, cómo se decide una ruta, cómo se evalúa
una respuesta abierta y cómo se mide si un instrumento de evaluación es confiable.

## 8.1 Antecedentes

La pregunta de qué modelo usar para cada consulta apareció en cuanto los modelos de lenguaje de
gran escala (LLM) empezaron a consumirse como servicio. Chen, Zaharia y Zou la formularon de
manera explícita en FrugalGPT: mostraron que el costo de consultar APIs populares de LLM puede
diferir en dos órdenes de magnitud y propusieron tres estrategias para aprovecharlas: adaptar el prompt para que sea más corto,
aproximar el modelo caro con uno barato o con una caché, y encadenar modelos en cascada, de modo
que una consulta solo llegue al modelo caro si el barato no da una respuesta confiable
[@frugalgpt]. Su resultado más citado es que una cascada bien calibrada puede igualar al mejor
modelo individual con una fracción muy pequeña de su costo, y su idea de fondo, que el costo se
puede bajar mucho si no se trata a todas las consultas por igual, es la premisa de todo el campo.

El trabajo siguiente se dividió en dos líneas. La primera mantuvo la cascada y trabajó sobre el
control que decide si hace falta escalar. AutoMix, por ejemplo, hace que el modelo chico responda y
después verifique su propia respuesta, y un controlador decide, con esa verificación como señal
ruidosa, si conviene pasar al modelo grande [@automix]. La ventaja de la cascada es que juzga la
respuesta real y no una predicción; su costo es que cada consulta difícil paga dos generaciones y
una verificación, y eso se nota en la latencia.

La segunda línea decidió antes de generar. Hybrid LLM entrena un clasificador que, mirando solo la
consulta, predice la brecha de calidad entre un modelo chico y uno grande, y manda la consulta al
chico cuando la brecha esperada es pequeña; el umbral del clasificador se puede mover en tiempo de
ejecución para cambiar el equilibrio entre costo y calidad [@hybridllm]. RouteLLM llevó esa idea a
datos de preferencia humana: entrena varios routers (factorización de matrices, un clasificador
BERT, un LLM ajustado) con las comparaciones de Chatbot Arena, más datos aumentados, y muestra que
los routers generalizan a pares de modelos distintos de los usados para entrenarlos [@routellm].
Estos dos trabajos son los antecedentes más directos del router de este trabajo, que también
decide antes de generar y también expone un umbral operable.

En paralelo avanzó la reutilización de respuestas. Las cachés tradicionales devuelven una respuesta
solo si la consulta es idéntica, y en lenguaje natural eso ocurre poco. GPTCache propuso una caché
semántica genérica, que representa cada consulta como un embedding y devuelve la respuesta guardada
de una consulta suficientemente parecida, y que se puede ubicar delante de cualquier proveedor
[@gptcache]. SCALM analizó trazas reales de servicios de chat, encontró patrones de consultas
semánticamente repetidas que una caché por coincidencia exacta no aprovecha y propuso mejores
criterios para decidir qué entradas conservar [@scalm]. MeanCache llevó la caché al lado del
usuario, con aprendizaje federado para no centralizar sus consultas y con manejo de las preguntas
que dependen de la conversación previa [@meancache]. Liu et al. estudiaron la caché semántica como
un problema de decisión en línea, en el que conviene guardar y descartar entradas según el costo de
cada respuesta y la distribución de consultas que se observa [@liu2025cache].

El relevamiento reciente de Moslem y Kelleher ordena todo este campo según cómo se estima la
dificultad de una consulta (clasificadores, aprendizaje de preferencias, cuantificación de
incertidumbre) y según si se decide antes o después de generar [@moslem2026]. Su conclusión
coincide con la de los trabajos anteriores: un sistema de ruteo bien diseñado puede acercarse, e
incluso superar, al mejor modelo individual a un costo mucho menor. Pero el mismo relevamiento
reconoce dos problemas abiertos que son centrales para este trabajo.

El primero es la **evaluación**. No existe un marco estandarizado para comparar sistemas de ruteo:
cada trabajo mide con sus propios modelos, benchmarks y criterios de calidad, y las cifras
publicadas no son comparables entre sí [@moslem2026]. La mayoría de los benchmarks usados están en
inglés y tienen respuesta verificable (matemática, código, opción múltiple), donde la calidad se
reduce a acertar o no. Las consultas abiertas, que son una parte importante del tráfico real, y las
consultas en otros idiomas quedan subrepresentadas. Esto no es un detalle para este trabajo, cuya
carga principal está en español: la literatura sobre sesgo cultural muestra que los modelos de uso
masivo rinden mejor sobre contenidos de países angloparlantes [@tao2024], [@naous2024], que la
brecha crece en idiomas con menos recursos [@blend], y que para el español hizo falta construir
conjuntos de evaluación propios porque los existentes no representaban sus variedades
[@laleaderboard]. Es razonable esperar que un modelo local chico tenga esa brecha más marcada que
uno premium, y por eso la evaluación de este trabajo se hizo sobre un corpus mayoritariamente en
español.

El segundo problema es la **operación**. Los trabajos anteriores evalúan una sola palanca (router,
cascada o caché) dentro de un experimento controlado. Ninguno la integra en un componente que tenga
que convivir con fallas del proveedor, con presupuestos, con varios clientes que no deben ver las
respuestas de los otros y con un operador que necesita decidir cuánta calidad está dispuesto a
resignar. Ese es el lugar que ocupan los gateways de IA, que se describen en la sección 8.2.1, y es
el hueco que este trabajo intenta cubrir.

## 8.2 Conceptos fundamentales

### 8.2.1 La inferencia como servicio tarifado y el gateway de IA

Desde que los LLM se consumen a través de APIs, la inferencia pasó a ser un costo operativo
variable, parecido al de cualquier servicio en la nube, pero con una particularidad: se cobra por
token de entrada y por token de salida, y el precio cambia mucho de un modelo a otro. En los
modelos que usa este trabajo, gpt-4.1 cobra USD 2 por millón de tokens de entrada y USD 8 por
millón de salida, y claude-haiku-4.5 USD 1 y USD 5 (tabla de precios del repositorio, septiembre
de 2026). Como las respuestas suelen ser más largas que las preguntas, el precio de salida domina.
Esa dispersión de precios es la que vuelve relevante la pregunta de qué modelo usar: si todos
costaran lo mismo, elegir siempre el más capaz sería razonable y no habría nada que optimizar
[@frugalgpt].

Entre la aplicación y los proveedores aparece entonces una pieza de arquitectura que concentra esas
decisiones: el **gateway de IA**. Es un proxy especializado que expone una API única, en general
compatible con la de OpenAI, y detrás de ella decide a qué modelo mandar cada pedido, reintenta ante
fallas, aplica límites de uso y registra lo que ocurrió. Es el punto natural para intervenir,
porque ve todo el tráfico sin que la aplicación cliente tenga que cambiar. Un gateway self-hosted,
además, deja los datos de gobernanza (quién consultó, qué se respondió, cuánto costó) dentro de la
infraestructura de quien lo opera. Este trabajo no propone un modelo nuevo ni una técnica de
entrenamiento de LLM, sino una forma de decidir, en ese punto de control, cómo se atiende cada
consulta.

Un gateway que atiende a varios equipos o clientes tiene que separar sus datos. En este documento se
llama **tenant** a cada una de esas unidades: tiene sus claves, su política y su historial, y nada
de lo que hace un tenant debería ser visible para otro. La **política** del tenant es el conjunto de
parámetros que el operador ajusta: qué modelos premium están permitidos, qué presupuesto tiene, si
usa caché y con qué criterio, qué nivel de calidad exige.

La dependencia de un proveedor externo trae además un problema de disponibilidad. El patrón
*circuit breaker*, que viene de la ingeniería de sistemas distribuidos, corta las llamadas a un
servicio que viene fallando y deriva el tráfico hacia una alternativa hasta que se recupera
[@nygard]. En un gateway esto se traduce en **fallback**: si el modelo elegido no responde, el pedido
se reenvía a otro. La técnica es madura, pero interactúa con el ruteo por costo, porque el fallback
puede terminar mandando al modelo caro tráfico que la política había decidido resolver de forma
barata. Por eso el gateway tiene que registrar cuándo ocurrió.

### 8.2.2 Modelos locales cuantizados

Servir un LLM en infraestructura propia se volvió mucho más accesible en los últimos años. Del lado
de los servidores, Kwon et al. mostraron que el principal cuello de botella está en la gestión de la
memoria de la caché de atención, y que administrarla por páginas, como hace un sistema operativo con
la memoria virtual, multiplica el throughput con el mismo hardware [@pagedattention]. Del lado de las
computadoras personales, la **cuantización** de los pesos (representarlos con 4 u 8 bits en lugar
de 16) reduce la memoria necesaria a una fracción, con una pérdida de calidad moderada, y permite
correr modelos de 3 a 8 mil millones de parámetros en una notebook. Ollama empaqueta ese proceso:
descarga modelos ya cuantizados y los sirve con una API HTTP simple [@ollama].

Para este trabajo lo que importa es la consecuencia económica. Un modelo local como qwen2.5:7b
[@qwen25] tiene un costo marginal por consulta prácticamente nulo, pero es menos capaz que un
modelo premium y, en una máquina sin GPU dedicada, bastante más lento. La pregunta no es si el
modelo local es bueno en general, sino para qué consultas su respuesta alcanza. Esa es exactamente
la pregunta que tiene que responder el router.

### 8.2.3 Embeddings y similitud coseno

Un **embedding** es una representación de un texto como un vector denso de números reales, tal que
textos con significado parecido quedan cerca en el espacio. Los modelos de embeddings de oraciones
se entrenan para que esa cercanía sea útil: Sentence-BERT mostró que ajustar una red tipo BERT con
pares de oraciones permite comparar significados a gran escala con una simple operación vectorial
[@sbert], y modelos posteriores como nomic-embed-text, que usa este trabajo, extendieron la idea a
textos largos con pesos y datos de entrenamiento abiertos [@nomic].

La medida de cercanía más usada es la **similitud coseno**, el coseno del ángulo entre dos vectores:

$$
\cos(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\lVert\mathbf{u}\rVert \, \lVert\mathbf{v}\rVert}
$$

Vale 1 si los vectores apuntan en la misma dirección y 0 si son ortogonales. Algunos modelos, entre
ellos nomic-embed-text, esperan que el texto lleve un prefijo que indique la tarea (por ejemplo
`search_query` o `classification`), y el prefijo cambia el vector resultante.

Las métricas basadas en embeddings también se usaron para evaluar texto generado. BERTScore, por
ejemplo, compara los embeddings de los tokens de una respuesta con los de una referencia y captura
el significado mejor que las métricas de solapamiento de palabras [@bertscore]. Pero siguen midiendo
distancia a una referencia, y dos respuestas pueden hablar de lo mismo, y por lo tanto estar muy
cerca, aunque una sea correcta y la otra no. Esa limitación es la que el estudio de la sección 9.1
encontró en la práctica.

### 8.2.4 Caché semántico

Un **caché semántico** guarda pares de consulta y respuesta junto con el embedding de la consulta.
Ante una consulta nueva, busca la guardada más cercana y, si la similitud supera un **umbral de
admisión**, devuelve la respuesta guardada sin llamar a ningún modelo [@gptcache]. Tres decisiones
definen su comportamiento:

- **El umbral.** Si es bajo, el caché devuelve respuestas a preguntas que solo se parecen en la
  superficie; si es alto, casi no hay aciertos. No hay un valor correcto en general: depende del
  modelo de embeddings y del tipo de consulta, y por eso conviene que sea configurable.
- **La antigüedad máxima.** Una respuesta puede dejar de ser válida (un precio, una fecha, una
  versión de software). Un tiempo de vida (TTL) limita cuánto tiempo se sigue sirviendo.
- **El aislamiento.** Si el caché es compartido, una respuesta generada para un cliente puede
  servirse a otro. En un gateway con varios tenants eso es un problema de confidencialidad, además
  de calidad. Aislar por usuario, como MeanCache, lo resuelve pero reduce mucho los aciertos
  [@meancache]; aislar por tenant mantiene el reuso dentro de cada organización.

Las bases de datos vectoriales como Qdrant resuelven la búsqueda del vecino más cercano de forma
aproximada y permiten combinarla con filtros sobre metadatos (tenant, fecha) en la misma consulta
[@qdrant], que es lo que necesita un caché aislado con TTL.

El caché y el router no son independientes cuando conviven. Si el caché se consulta antes que el
router, una respuesta guardada evita la decisión de ruteo, y con ella cualquier control sobre qué
modelo la había generado. El router, a su vez, determina qué respuestas entran al caché: si la
política manda mucho tráfico al modelo local, el caché se llena de respuestas locales. Esta
interacción es una de las razones para tratarlos como un único plano de decisión, que es como los
diseña este trabajo (sección 10.3).

### 8.2.5 Ruteo de modelos

Se llama **ruteo** a elegir, para cada consulta, qué modelo la atiende. La literatura distingue tres
familias [@moslem2026]:

- **Reglas fijas.** Deciden con señales observables, como la longitud del prompt o la presencia de
  palabras clave. Son fáciles de explicar, pero no están ligadas a la calidad de la respuesta. Es lo
  que hacía la primera versión de Nebula (sección 9.1).
- **Cascadas.** Mandan la consulta al modelo más barato y escalan si la respuesta no supera un
  control [@frugalgpt], [@automix]. Juzgan la respuesta real, pero pagan latencia y costo extra en
  las consultas que escalan.
- **Routers aprendidos.** Un clasificador estima, antes de generar, la probabilidad de que un modelo
  barato alcance, y decide con un umbral [@hybridllm], [@routellm]. Cuestan una inferencia barata
  por consulta y necesitan datos etiquetados para entrenarse.

En un router aprendido, el umbral es la perilla que conecta la técnica con la operación. Bajarlo
manda más consultas al modelo barato: se ahorra más y se pierde más calidad. Si para cada umbral se
mide el costo y la calidad resultantes sobre un conjunto de evaluación, se obtiene una curva. Los
puntos de esa curva que no están dominados por ningún otro (ningún otro punto es a la vez más
barato y de mejor calidad) forman la **frontera de Pareto** costo–calidad. Elegir un punto de la
frontera es elegir un compromiso, y esa elección es del operador, no del algoritmo.

Con más de dos niveles, la frontera ya no sale de un solo umbral. Con tres niveles (local,
económico, frontier) hacen falta dos probabilidades y dos umbrales, y cada par de umbrales es un
punto de operación distinto. La frontera se obtiene recorriendo la grilla de pares y quedándose con
los no dominados.

### 8.2.6 Regresión logística, validación cruzada y estimación honesta

La **regresión logística** modela la probabilidad de una clase binaria como una función sigmoide de
una combinación lineal de las variables:

$$
p(y = 1 \mid \mathbf{x}) = \sigma(\mathbf{w} \cdot \mathbf{x} + b), \qquad \sigma(z) = \frac{1}{1 + e^{-z}}
$$

Los pesos se ajustan minimizando la pérdida logarítmica, y la **regularización L2** agrega a esa
pérdida un término $\lambda \lVert\mathbf{w}\rVert^2$ que penaliza los pesos grandes y reduce el
sobreajuste cuando hay muchas variables y pocos ejemplos, que es el caso de un embedding de 768
dimensiones y un millar de prompts [@esl]. Tiene dos ventajas prácticas para un gateway: su salida
es una probabilidad, que se puede comparar con un umbral, y servirla es un producto escalar.

Para saber cuánto rinde un clasificador hay que medirlo sobre datos que no vio al entrenarse. La
**validación cruzada** de $k$ folds parte los datos en $k$ grupos, entrena con $k - 1$ y evalúa en
el restante, rotando [@esl]. Si los datos tienen unidades relacionadas, como un prompt y su
traducción, hay que mantenerlas en el mismo fold; si no, el modelo se evaluaría sobre una pregunta
que ya vio en otro idioma. A esto se lo llama validación cruzada **agrupada**.

Hay una trampa más sutil. Si los umbrales del router se eligen mirando las predicciones fuera de
fold de todo el conjunto, y después se reporta el costo y la calidad de ese mismo conjunto, la
elección de los umbrales ya usó los datos con que se mide. La solución es una **estimación
anidada**: para cada fold externo, los pesos y los umbrales se eligen solo con los otros folds, y
el fold externo se rutea con esa elección. Ningún prompt evaluado influye en la decisión que lo
rutea.

Para describir la capacidad de un clasificador de separar las clases, sin depender de un umbral,
se usa el **área bajo la curva ROC** (AUC): la probabilidad de que un ejemplo positivo elegido al
azar reciba una puntuación mayor que uno negativo elegido al azar. Vale 0.5 para un clasificador
que no distingue nada y 1 para uno perfecto; un valor menor que 0.5 indica que la puntuación ordena
al revés [@fawcett2006].

Por último, las cifras que salen de una muestra finita tienen incertidumbre. El **bootstrap**
estima esa incertidumbre remuestreando los datos con reposición muchas veces y mirando cómo varía la
cifra; los percentiles 2.5 y 97.5 de esa distribución dan un intervalo de confianza del 95 %
[@efron1993]. Para una proporción con pocos casos, el **intervalo de Wilson** se comporta mejor que
la aproximación normal [@wilson1927].

### 8.2.7 LLM como juez

Evaluar respuestas abiertas es caro: no hay una respuesta correcta única y un humano tarda en leer
cada una. La alternativa más difundida es usar otro LLM como juez. Zheng et al. mostraron que un
modelo fuerte, con un prompt adecuado, puede alcanzar con evaluadores humanos un acuerdo comparable
al que tienen los humanos entre sí [@zheng2023judge], y G-Eval propuso guiar al juez con criterios
explícitos y razonamiento paso a paso para mejorar esa correlación [@geval].

La misma línea de trabajo documentó sesgos sistemáticos que hay que controlar:

- **Posición.** Cuando se le muestran dos respuestas, el juez tiende a favorecer la que aparece
  primero [@wang2024fair]. Se controla juzgando cada par en los dos órdenes.
- **Longitud.** Tiende a premiar las respuestas más largas, aunque no sean mejores
  [@zheng2023judge].
- **Autopreferencia.** Los jueces reconocen y prefieren las respuestas generadas por su propio
  modelo o su familia [@panickssery]. Para un sistema que compara la salida de un modelo local con
  la de un premium, esto no es un detalle: si el juez es de la misma familia que el premium, la
  comparación arranca inclinada. Se controla usando jueces de familias distintas a las de los
  modelos evaluados.

Combinar varios jueces en un **ensamble** reduce la varianza de cada uno, pero exige fijar de
antemano la regla que combina sus notas (unanimidad, mayoría, promedio), porque elegirla después de
ver los resultados permite acomodar la conclusión. Fijar las reglas, los umbrales y los criterios
de decisión antes de mirar los datos, y dejarlo por escrito, se llama **pre-registro**.

La evaluación holística de modelos de lenguaje ya había advertido que juzgar por una sola métrica de
exactitud oculta dimensiones importantes y que conviene medir varias sobre los mismos escenarios
[@helm]. En este trabajo, la dimensión que se mide es una sola, pero se define con cuidado: si la
respuesta barata podría haber reemplazado a la del modelo de referencia sin que quien preguntó
quedara peor. A eso se lo llama **sustituibilidad**, y es la pregunta que responden tanto los jueces
como el lector humano.

### 8.2.8 Cómo se mide la confiabilidad de un instrumento

Un juez automático solo sirve como instrumento de medición si coincide con lo que haría una persona.
Ese acuerdo no se puede medir con el porcentaje de coincidencias, porque dos evaluadores que dicen
"sí" casi siempre coinciden mucho aunque decidan al azar. El **κ de Cohen** corrige esa coincidencia
esperable [@cohen1960]:

$$
\kappa = \frac{p_o - p_e}{1 - p_e}
$$

donde $p_o$ es la proporción de acuerdo observada y $p_e$ la que se esperaría por azar dadas las
proporciones de cada evaluador. Vale 1 con acuerdo perfecto, 0 con el acuerdo del azar, y puede ser
negativo. Tiene una propiedad que importa en este trabajo: cuando una clase es muy rara (pocos "no
sustituible"), $p_e$ es alto y cada desacuerdo sobre la clase rara pesa mucho, así que el κ puede
ser bajo aunque el acuerdo bruto sea alto. Para escalas ordinales existe una versión ponderada, y
para más de dos evaluadores o datos faltantes se usa el **α de Krippendorff** [@krippendorff].

En este trabajo el acuerdo no es un dato accesorio: es la condición para usar a los jueces como
instrumento de la hipótesis. Por eso se validó antes de medir, y el umbral de acuerdo que se
consideraría suficiente se fijó en el pre-registro.

### 8.2.9 Calidad del software y normas

La familia de normas ISO/IEC 25000 (SQuaRE) ofrece el vocabulario para decir qué se entiende por
calidad. La ISO/IEC 25010:2023 define el modelo de calidad del producto, en el que el gasto de
inferencia se encuadra como **utilización de recursos**, dentro de la eficiencia de desempeño
[@iso25010]. La ISO/IEC 25019:2023 define la calidad en uso, es decir, cómo un producto influye en
sus partes interesadas cuando se lo usa en un contexto especificado [@iso25019]; que una respuesta
le sirva a quien preguntó se encuadra ahí. La ISO/IEC 25059:2023 adapta ambos modelos a sistemas de
inteligencia artificial [@iso25059]. Ninguna de estas normas define cómo balancear costo y calidad
en un sistema que reparte tráfico entre varios modelos; ese balance es, justamente, lo que la
frontera de este trabajo hace visible y deja en manos del operador.

### 8.2.10 Situación del mercado

El mercado de gateways de IA es bastante maduro. LiteLLM es un proxy open source que se puede alojar
en forma propia y expone una API compatible con la de OpenAI hacia más de cien proveedores, con
estrategias de ruteo y balanceo, fallback, presupuestos por clave y caché exacta y semántica
[@litellm]. Portkey ofrece un gateway con versión open source y versión administrada, ruteo
condicional, reintentos, observabilidad y caché semántica [@portkey]. Cloudflare AI Gateway es un
servicio administrado que suma registro, analítica, límites de uso y caché, aunque esta funciona por
coincidencia exacta de la solicitud [@cloudflare]. OpenRouter, que este trabajo usa como proveedor,
unifica el acceso a modelos de muchos laboratorios detrás de una sola API y ofrece también un modo
de ruteo automático propietario [@openrouter].

Estas herramientas ya resuelven buena parte de la mecánica que el trabajo necesita: rutean, hacen
fallback, cachean y registran costos. La diferencia está en otro lugar. Todas optimizan variables
operativas (costo, latencia, disponibilidad) y tratan la calidad de la respuesta como algo externo
al gateway: el ruteo se configura con reglas que escribe el operador, y ninguna mide si lo que se
sirvió por una ruta barata le sirvió a quien lo recibió. Reportan cuánto se gastó, pero no cuánto se
ahorró contra una línea base, ni a qué costo en calidad. La Tabla 8.1 resume la comparación.

**Tabla 8.1.** Comparación de gateways de mercado con Nebula (según documentación pública,
septiembre de 2026).

| Criterio | LiteLLM | Portkey | Cloudflare AI Gateway | Nebula |
|---|---|---|---|---|
| Despliegue self-hosted | Sí | Sí (versión open source) | No (administrado) | Sí |
| Caché semántica | Sí | Sí | No (coincidencia exacta) | Sí |
| Aislamiento del caché | Por clave, equipo o usuario | Por namespace | Por solicitud idéntica | Por tenant, con umbral y antigüedad de la política |
| Decisión de ruta | Reglas y balanceo configurados | Reglas condicionales sobre metadatos | Reglas | Router aprendido sobre el prompt, con objetivo de calidad por tenant |
| Calidad de lo servido | No se mide | No se mide | No se mide | Tasa de respuestas sustituibles, con jueces validados contra un lector humano |
| Ahorro contra una línea base reproducible | No | No | No | Sí |

El trabajo, por lo tanto, no compite con estas herramientas en cantidad de proveedores ni en
funcionalidades operativas, donde están mucho más maduras. Su aporte es incorporar la calidad medida
como criterio de la decisión de ruta, con un instrumento validado, y mostrarle al operador el
compromiso entre costo y calidad antes de que lo elija.

### 8.2.11 Síntesis: las brechas que toma el trabajo

El recorrido anterior deja tres brechas. La primera es que el ruteo y la caché se estudian y se
ofrecen como piezas separadas, optimizadas para el costo, sin un plano de decisión común que además
opere con fallas de proveedor, varios clientes y presupuestos. La segunda es que la calidad se mide
como acuerdo con una referencia, en general en inglés y sobre tareas cerradas, y con instrumentos
automáticos (similitud o jueces LLM) que rara vez se validan contra personas. La tercera es que ni
la literatura ni el mercado ofrecen evidencia reproducible de cuánto se ahorra y a qué costo en
calidad, y ninguna norma dice cómo balancear ambas cosas. La hipótesis de la sección 7.3 se formula
para cubrir esas tres brechas con evidencia propia.
