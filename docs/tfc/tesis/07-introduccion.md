# 7. Introducción

## 7.1 Planteamiento y contexto del problema

Los equipos que integran modelos de lenguaje de gran escala en sus productos enfrentan una
disyuntiva que se repite. Necesitan la capacidad de un modelo premium para las consultas difíciles,
pero la práctica más común es elegir un modelo y usarlo para todo, y entonces pagan ese mismo
precio por la totalidad del tráfico, incluidas las consultas simples que un modelo más barato, o
incluso uno local, podría haber resuelto igual de bien. Los precios por token cambian hasta en
órdenes de magnitud de un modelo a otro [1], así que la diferencia no es menor.

A eso se suma un problema de visibilidad. Si la aplicación habla directamente con el proveedor, no
queda registro de qué modelo respondió cada consulta, cuánto costó ni por qué se eligió esa ruta, y
el gasto solo aparece agregado en la factura. Y aun cuando se decide usar modelos más baratos para
una parte del tráfico, falta la pieza más difícil: saber si lo que se entregó por la ruta barata le
sirvió a quien lo pidió. Sin esa medición, ahorrar es fácil; lo que no se sabe es cuánto se perdió.

El problema se ubica, entonces, en el punto donde se toma la decisión: el gateway que se interpone
entre las aplicaciones y los proveedores. Este trabajo estudia cómo ese gateway puede decidir,
consulta por consulta, qué modelo la atiende, de modo que el ahorro sea real y la pérdida de calidad
sea medida, acotada y elegida por el operador.

## 7.2 Idea directriz

Un gateway de IA self-hosted que decide, consulta por consulta, si conviene responder con un modelo
local, con una respuesta ya guardada en caché o con un modelo premium, le permite a un equipo de
software reducir de forma sustancial su gasto en modelos premium sin resignar la calidad de las
respuestas que entrega, y le muestra al operador cuánto ahorra y cuánta calidad pone en juego en
cada decisión.

## 7.3 Hipótesis de trabajo

> Un gateway de IA self-hosted que decide la ruta de cada consulta (modelo local, caché semántica o
> modelo premium) reduce el gasto en inferencia premium en al menos un 30 % respecto de la línea
> base de uso exclusivo del modelo premium, sobre el mismo conjunto de escenarios, y mantiene una
> tasa de respuestas aceptables para el usuario no inferior en más de 5 puntos porcentuales a la de
> esa línea base.

- **H0 (nula):** el gateway no reduce el gasto premium en al menos un 30 %, o lo reduce a costa de
  que la tasa de respuestas aceptables caiga más de 5 puntos respecto de la línea base.
- **H1 (alternativa):** el gateway reduce el gasto premium en al menos un 30 % y la tasa de
  respuestas aceptables no cae más de 5 puntos.

Es una hipótesis de desempeño y comparativa a la vez: el gateway tiene que alcanzar dos umbrales
propios, y tiene que hacerlo contra una alternativa concreta, que es mandar siempre todo al modelo
premium. Las dos magnitudes se miden en la misma evaluación, sobre el mismo corpus y contra la
misma línea base.

La **aceptabilidad** se juzga con una rúbrica de sustituibilidad (si la respuesta podría haber
reemplazado a la del modelo de referencia sin que quien preguntó quedara peor), aplicada por jueces
LLM cuyo acuerdo con un lector humano se valida antes de usarlos. Se encuadra en el modelo de
calidad en uso de la ISO/IEC 25019:2023 y en su adaptación a sistemas de IA de la ISO/IEC
25059:2023 [2], [3]. El gasto de inferencia se encuadra como utilización de
recursos, dentro de la eficiencia de desempeño de la ISO/IEC 25010:2023 [4].

## 7.4 Objetivo general y objetivos específicos

**Objetivo general.** Desarrollar y validar un gateway de IA self-hosted que enrute cada consulta
entre un modelo local, una caché semántica y un modelo premium, y que reduzca el gasto en modelos
premium en al menos un 30 % frente al uso exclusivo del modelo premium, sin degradar la calidad de
las respuestas entregadas.

**Objetivos específicos.**

- **OE1.** Relevar el estado del arte de gateways, routers sensibles al costo y cachés semánticas,
  y definir el estándar de referencia del trabajo: la línea base de uso exclusivo del modelo
  premium, el conjunto de escenarios de evaluación y el procedimiento de cálculo del gasto evitado.
- **OE2.** Diseñar e implementar el enrutamiento entre modelo local, caché semántica y modelo
  premium, con fallback ante la falla de un proveedor, y una consola operativa que exponga la
  decisión de ruteo y el costo de cada consulta.
- **OE3.** Implementar la medición de calidad comparada entre la respuesta de una ruta económica y
  la del modelo premium, y ejecutar de forma reproducible la evaluación contra la línea base.
- **OE4.** Documentar los resultados, los límites de validez de la evidencia y las conclusiones
  respecto de la hipótesis.

## 7.5 Metodología

El trabajo sigue un **enfoque cuantitativo-experimental**. La pregunta admite una respuesta medible
(cuánto gasto premium se evita y cuánta calidad se conserva) que se obtiene generando datos sobre un
conjunto de escenarios y comparando el resultado contra una línea base.

El **proceso de desarrollo** fue iterativo e incremental. El entregable se construyó en seis fases:
limpieza del gateway y aislamiento del caché, construcción del corpus y de las etiquetas de
referencia, router de tres niveles, consola de evaluación, limitación de pedidos y cierre de la
documentación. Cada fase tuvo una especificación y un plan con criterios de aceptación explícitos,
se desarrolló guiada por pruebas, se integró con un pull request solo con la suite en verde, y pasó
por una revisión independiente del código antes de integrarse. El historial del repositorio deja
registro de todo el proceso.

El **diseño de la validación** tiene tres ideas. La primera es validar el instrumento antes de
medir: la calidad no se mide con una métrica elegida por conveniencia, sino con jueces cuyo acuerdo
con una persona se estima primero. La segunda es fijar de antemano las reglas: la regla que combina
las notas de los jueces, el criterio para elegirla y el umbral de acuerdo que se consideraría
suficiente se escribieron en un pre-registro antes de correr los jueces sobre el corpus. La tercera
es separar la elección de los parámetros de la medición: el desempeño del router se reporta con una
estimación anidada, en la que ningún prompt evaluado influye en los umbrales ni en los pesos que lo
rutean.

Los **datos** se generaron a partir de tres conjuntos públicos (Dolly, GSM8K y MBPP)
[5], [6], [7], muestreados por tarea, traducidos al español y respondidos por cuatro
modelos. El español es la carga principal y el inglés se usa como subconjunto pareado. El **análisis**
compara, sobre ese corpus, el costo y la calidad de cada política de ruteo contra la línea base,
con intervalos de confianza por bootstrap.

## 7.6 Justificación del trabajo

La justificación es práctica y metodológica a la vez. En lo práctico, el gasto en modelos premium
es hoy un costo operativo relevante para cualquier producto que use LLM de manera intensiva, y la
alternativa de correr modelos locales ya es viable en hardware de consumo. Lo que falta es un
criterio para repartir el tráfico entre ambos que se apoye en evidencia y que el equipo que opera el
sistema pueda entender y ajustar. Un gateway self-hosted, además, deja los datos de las consultas y
de la gobernanza dentro de la infraestructura propia, que es una condición frecuente en
organizaciones con requisitos de privacidad.

En lo metodológico, el relevamiento del capítulo 8 muestra que las cifras publicadas sobre ruteo no
son comparables entre sí, que la calidad se mide casi siempre en inglés y sobre tareas cerradas, y
que los instrumentos automáticos rara vez se validan contra personas [8]. Del lado del
mercado, las herramientas existentes rutean y cachean, pero no miden la calidad de lo que sirven ni
el ahorro contra una línea base. El trabajo aporta evidencia reproducible de cuánto se ahorra y a
qué costo en calidad, medida en español y con un instrumento validado, y la integra en un componente
que opera con fallas, varios clientes y presupuestos.

## 7.7 Alcances y limitaciones

Esta sección retoma los alcances y limitaciones de la Práctica 5, actualizados a lo que el trabajo
efectivamente construyó y midió.

**Alcances.** Los siguientes puntos son verificables sobre el prototipo y sobre el corpus de
evaluación versionado en el repositorio:

1. El gateway enruta cada consulta entre un modelo local, un modelo premium económico y un modelo
   premium frontier, consulta una caché semántica aislada por tenant y aplica fallback al premium
   ante la falla del modelo local.
2. La consola operativa expone, para cada consulta, la decisión de ruteo, el nivel y el costo
   estimado, y muestra la frontera costo–calidad con un simulador que permite elegir el objetivo de
   calidad de cada tenant.
3. La evaluación reproducible mide, sobre un corpus versionado de 1250 prompts, el gasto premium
   evitado y la tasa de respuestas sustituibles de cada política de ruteo frente a la línea base.
4. El estándar de referencia (uso exclusivo del modelo frontier, mismos prompts, costo registrado al
   generar cada respuesta) se aplica de forma idéntica a todas las políticas comparadas.
5. La medición se encuadra en la familia ISO/IEC 25000: el gasto de inferencia como utilización de
   recursos, dentro de la eficiencia de desempeño, y la aceptabilidad de la respuesta dentro de la
   calidad en uso.

**Limitaciones.**

- **Límite de dominio.** El enrutamiento y el caché se diseñaron y validaron sobre pedidos de chat
  compatibles con la API de OpenAI. El gateway expone también un endpoint de embeddings, que no
  pasa por el router; otras modalidades, como imágenes o audio, quedan fuera.
- **Límite de escala.** La validación se hizo sobre un corpus de 1250 prompts construido a partir
  de conjuntos de datos públicos, no sobre tráfico de producción, porque reunir y etiquetar tráfico
  real excede el tiempo y el presupuesto del trabajo.
- **Límite tecnológico.** El gateway se diseña, implementa y valida exclusivamente en modo
  self-hosted, sin plano de control alojado, y sobre una única computadora de consumo (Apple M4, 16
  GB). En ese hardware el modelo local es varias veces más lento que el premium.
- **Límite de validación de la evidencia.** El costo de cada política se calcula con el costo que
  el proveedor informó al generar cada respuesta del corpus, no con una operación en paralelo en
  producción. El ahorro del caché no entra en esa cifra, porque el corpus no tiene consultas
  repetidas.
- **Límite del instrumento de calidad.** La aceptabilidad la juzgan jueces LLM validados contra un
  único lector humano, no un panel de personas sobre todo el corpus, porque una evaluación humana
  sistemática no es factible en el cronograma del trabajo.
- **Fuera de alcance.** El entrenamiento o ajuste fino de modelos de lenguaje (el router es un
  clasificador liviano, que sí se entrena), el aprendizaje en línea del router y cualquier
  certificación de calidad para dominios regulados.

## 7.8 Trabajos relacionados

Los trabajos más cercanos a este son de dos tipos: los de investigación, que proponen una técnica de
ruteo o de caché y la miden en un experimento controlado, y las herramientas de mercado, que
integran esas técnicas en un producto. La Tabla 7.1 resume los más relevantes con la cifra principal
que publican, verificada contra su fuente primaria. Estas cifras no se reprodujeron: se citan tal
como las reporta cada fuente, y la sección 12.1 discute en qué condiciones se obtuvieron y cómo se
comparan con las de este trabajo.

**Tabla 7.1.** Trabajos relacionados y cifras publicadas.

| Trabajo | Tipo | Qué hace | Cifra publicada | Qué no mide |
|---|---|---|---|---|
| FrugalGPT [1] | cascada de modelos | prueba modelos de menor a mayor costo y se detiene cuando un puntuador confía en la respuesta | iguala a GPT-4 con hasta un 98 % menos de costo, o mejora su exactitud un 4 % al mismo costo; el ahorro va del 59 % al 98 % según el conjunto de datos | tareas en inglés con respuesta verificable; no opera como servicio |
| Hybrid LLM [9] | router aprendido de dos niveles | predice la brecha de calidad entre un modelo chico y uno grande | hasta un 40 % menos de llamadas al modelo grande sin caída de calidad (entre dos modelos de calidad parecida) | un solo par de modelos por experimento; sin caché ni fallas |
| RouteLLM [10], [11] | router aprendido de dos niveles | aprende la decisión con datos de preferencia humana | el artículo reporta una reducción de costo de más de 2 veces sin perder calidad (contra un router aleatorio); el blog de los autores, reducciones del 85 % en MT-Bench, 45 % en MMLU y 35 % en GSM8K contra usar solo GPT-4, con el 95 % de su desempeño | benchmarks en inglés; dos modelos |
| AutoMix [12] | cascada con autoverificación | el modelo chico verifica su respuesta y un controlador decide si escalar | más de un 50 % menos de costo computacional a desempeño comparable | paga dos generaciones en las consultas que escalan |
| GPTCache [13] | caché semántico | devuelve la respuesta de una consulta parecida ya respondida | respuestas de 2 a 10 veces más rápidas en los aciertos; tasa de aciertos de alrededor del 50 % en su prueba | no reporta ahorro en dinero ni calidad de lo servido |
| MeanCache [14] | caché semántico por usuario | caché local con aprendizaje federado | alrededor del 31 % de las consultas de 20 usuarios eran similares a otras anteriores; 17 % más de F-score en las decisiones de acierto | aislamiento por usuario, con menos reuso |
| Portkey [15], [16] | gateway comercial | ruteo condicional, reintentos, caché semántica | pruebas preliminares del proveedor: alrededor del 20 % de aciertos del caché con 99 % de precisión en casos de preguntas y respuestas | la calidad de las respuestas ruteadas; el ahorro contra una línea base |
| LiteLLM [17] | proxy open source | ruteo por reglas, fallback, presupuestos, caché | no publica cifras de ahorro | ídem |
| Cloudflare AI Gateway [18] | gateway administrado | registro, límites, caché exacta | no publica cifras de ahorro | ídem; no es self-hosted |

Leídos en conjunto, estos trabajos confirman que la premisa del trabajo es sólida (se puede ahorrar
mucho si no se trata a todas las consultas por igual) y dejan ver lo que falta. Los trabajos de
investigación optimizan una sola palanca y la miden en inglés, sobre benchmarks con respuesta
verificable o con un juez que no se valida contra personas. Las herramientas de mercado integran
todas las palancas, pero no miden la calidad de lo que sirven. Este trabajo se ubica entre ambos: un
gateway que integra ruteo, caché y fallback, cuyo ruteo se apoya en una medición de calidad validada
y en español.
