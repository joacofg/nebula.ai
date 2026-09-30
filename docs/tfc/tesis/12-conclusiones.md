# 12. Conclusiones

## 12.1 Sobre el estado del arte

Los trabajos comparables con este son los routers y las cascadas de la Tabla 7.1, y la comparación
exige cuidado, porque ninguna de sus cifras se obtuvo en las mismas condiciones. FrugalGPT reporta
ahorros del 59 % al 98 % [1] y el blog de RouteLLM del 35 % al 85 % según el benchmark
[11], ambos contra usar siempre GPT-4. Las dos cifras son mayores que el 31 % de este
trabajo, pero se midieron en inglés, sobre tareas con respuesta verificable (clasificación, opción
múltiple, matemática) o con un juez que no se validó contra personas, y con dos modelos en lugar de
tres. En el caso de RouteLLM, además, la reducción que reporta el artículo (más de 2 veces) se mide
contra un router aleatorio y no contra el modelo grande [10]. La comparación más cercana en
condiciones es Hybrid LLM, que entre modelos de brecha media logra un 40 % de ventaja de costo con
una caída de calidad de hasta 4 % [9]; este trabajo ahorra un 31 % con una caída de 4.3
puntos, en un orden de magnitud parecido.

La conclusión de posicionamiento es entonces doble. En magnitud de ahorro, el resultado queda por
debajo de las cifras de cabecera de la literatura y cerca de las de los trabajos que miden con más
cuidado la calidad. Ese es el resultado esperable cuando la calidad se mide en español, sobre
tareas abiertas, con un instrumento más estricto que un lector humano y con una estimación anidada
que no deja elegir los umbrales mirando los datos de prueba: cada una de esas decisiones baja la
cifra, y cada una la vuelve más creíble. En lo que mide, el trabajo va más allá de lo que publican
tanto la investigación como el mercado. Ninguno de los antecedentes valida su instrumento de calidad
contra una persona antes de usarlo, ninguno integra el router en un gateway que opera con caché,
fallas de proveedor y varios clientes, y ninguna de las herramientas de mercado (LiteLLM, Portkey,
Cloudflare) reporta el ahorro contra una línea base ni la calidad de lo que sirve. La contribución
del trabajo no es un ahorro más grande, sino un ahorro medido, con su costo en calidad a la vista y
elegido por el operador.

Para el campo, el resultado aporta una advertencia concreta: una regla de ruteo puede ahorrar mucho
y no servir. La heurística del gateway ahorraba un 40 % y tenía la calidad de mandar todo al modelo
local, y la métrica de similitud que se proponía para detectarlo separaba peor que el azar. Mientras
las evaluaciones de ruteo no midan la calidad con instrumentos validados, las cifras de ahorro no
son comparables entre sí [8], ni tampoco confiables.

## 12.2 Sobre la investigación y sus aplicaciones

### Respuesta a la hipótesis

La hipótesis se verifica. Con el objetivo de calidad en 0.95, el router de tres niveles gasta
USD 1.70 cada mil prompts contra USD 2.47 de mandar todo al modelo frontier: un ahorro del 31 %
sobre el gasto premium, por encima del 30 % que planteaba la hipótesis. En el mismo punto, la tasa
de respuestas sustituibles es 0.957, es decir, 4.3 puntos por debajo de la línea base, dentro de
los 5 puntos que la hipótesis admitía. Las dos cifras salen de la misma evaluación, sobre los mismos
1250 prompts y contra la misma línea base, y son las de la estimación anidada: los umbrales y los
pesos que decidieron la ruta de cada prompt se eligieron sin mirarlo.

El resultado es, además, conservador, y por dos razones independientes. La primera está en el
instrumento. Los jueces con que se midió la calidad resultaron más exigentes que el lector humano,
que es la referencia de lo que le sirve a quien pregunta: en los desacuerdos del hold-out en
español, los jueces rechazaron respuestas que el lector aceptaba siete veces, y aceptaron respuestas
que el lector rechazaba solo dos. Un instrumento más estricto marca como insuficientes respuestas
baratas que servían, y eso empuja al router a mandar más pedidos al frontier. Aun medido con esa
vara, el ahorro supera el umbral; con un criterio tan exigente como el del lector, la dirección del
sesgo indica que sería mayor. La segunda razón es que el 31 % sale solo del router: el corpus no
tiene consultas repetidas, así que el caché semántico, que es la otra mitad del gateway, no aporta
nada a esa cifra, y en tráfico real sí lo haría.

Conviene decir también qué no se verifica. El intervalo de confianza del ahorro va de 28 % a 35 %,
así que con esta muestra no se puede excluir, al 95 %, un ahorro algo menor que el 30 %; la
dirección del sesgo del instrumento compensa esa incertidumbre, pero no la elimina. Y el punto de
operación importa: con el objetivo en 0.90 el ahorro llega al 57 %, pero la calidad cae casi 10
puntos y la hipótesis no se cumpliría. La hipótesis se verifica en un punto concreto de la frontera,
que es el que el gateway usa por defecto.

### Análisis de los resultados

El resultado se explica, antes que nada, por una decisión de diseño: medir la calidad antes de
optimizar el costo. La heurística de dos reglas que tenía el gateway ahorraba un 40 % en la suite de
agosto, más que el router, pero cuando se la evaluó sobre el corpus con el mismo instrumento, su
calidad (0.759) resultó prácticamente la de mandar todo al modelo local (0.754). No estaba
eligiendo: casi todo le parecía fácil. El router aprendido ahorra menos que la heurística, pero su
ahorro es el que queda después de pagar la calidad. Esa diferencia es el aporte principal del
trabajo, y no se habría visto si la métrica de calidad hubiera sido la similitud coseno que proponía
el TP4, que en la validación separó peor que el azar (AUC 0.25).

La segunda explicación está en la estructura de precios y de capacidades de los modelos. El ahorro
sale casi entero del modelo local, que atiende el 27 % de los pedidos en el objetivo 0.95, y muy
poco del nivel económico, que atiende el 6 %. Sobre este corpus, claude-haiku-4.5 cuesta tres
cuartos de lo que cuesta gpt-4.1 y es sustituible en el 88 % de los casos: mandarle un pedido ahorra
poco y arriesga bastante, y el router lo aprendió solo. El nivel intermedio sería más útil con un
modelo económico más barato en relación con el frontier.

La tercera tiene que ver con el idioma. En inglés, el modelo local atiende el 49 % de los pedidos;
en español, el 21 %. El modelo local de 7B es claramente más débil en español, que es justamente la
carga principal del trabajo. Esto va en la línea de lo que la literatura documenta sobre la brecha
de los modelos fuera del inglés [23], [24], y muestra por qué evaluar solo en inglés,
como hacen la mayoría de los trabajos de ruteo, sobreestimaría el ahorro para un equipo que atiende
usuarios hispanohablantes.

Por último, las señales del router son modestas (AUC 0.66 y 0.65), y aun así alcanzan. El router no
necesita acertar cada caso: necesita ordenar los prompts mejor que el azar, para que los primeros que
manda al modelo local sean los que tienen más chances de salir bien. Contra la mezcla aleatoria de
niveles que llega a la misma calidad, es un 17 % más barato. El oráculo, que conoce la etiqueta de
cada prompt, gastaría USD 0.51 cada mil prompts: queda mucho margen para un clasificador mejor, y el
gateway ya tiene la estructura para aprovecharlo.

### Aplicaciones

El resultado tiene una aplicación directa para cualquier equipo que opere su propio gateway. El
operador no tiene que confiar en una regla ni en una promesa de ahorro: ve la frontera medida sobre
un corpus, mueve el objetivo de calidad, observa en el simulador cómo se reparte el tráfico y cuánto
cuesta, y aplica el punto a cada tenant. El mismo procedimiento que produjo la evidencia de este
trabajo (corpus, jueces validados, reentrenamiento con un comando) sirve para rehacer la frontera
con el tráfico propio de cada organización.

### Limitaciones del trabajo

1. **El instrumento de calidad descansa en un único lector humano.** Todas las notas humanas son
   del autor, y el κ del hold-out en español quedó por debajo del umbral pre-registrado. *Impacto:*
   no se puede estimar el acuerdo entre personas, y la magnitud exacta del sesgo de los jueces queda
   abierta, aunque su dirección esté establecida. *Superación:* sumar al menos un segundo lector,
   con la misma calibración, y ampliar el hold-out con más negativos.
2. **El corpus no es tráfico de producción.** Son 1250 prompts de tres datasets públicos y cinco
   tareas, sin consultas repetidas. *Impacto:* la proporción de pedidos que el local puede atender
   depende de la mezcla de tareas, y el aporte del caché no se pudo medir. *Superación:* reentrenar y
   reevaluar con una muestra juzgada del tráfico real de un tenant.
3. **El modelo local es lento en el hardware de la evaluación.** La mediana es de 21.3 s por
   respuesta, contra 2.5 s del frontier. *Impacto:* el ahorro se paga en tiempo de respuesta, y con
   tráfico concurrente la cola del modelo local crecería. *Superación:* servir el modelo local en
   hardware dedicado o con un servidor de inferencia por lotes, y medir la latencia bajo carga.
4. **El router es estático.** Se entrena una vez sobre el corpus y no aprende del tráfico que
   atiende. *Impacto:* si la distribución de consultas cambia, la frontera deja de describir lo que
   pasa. *Superación:* muestrear y juzgar en línea una fracción de las respuestas y reentrenar
   periódicamente.
5. **Las notas humanas sobre código son de baja confianza.** La terminal de etiquetado reenvolvía el
   código. *Impacto:* el κ incluye diez pares con notas dudosas. *Superación:* re-etiquetar el código
   con un visor que preserve el formato.

## 12.3 Sobre el proceso de aprendizaje

> COMPLETAR (Joaquín): este borrador se armó con hechos del proceso; revisalo y reescribilo en tu
> voz.

Lo que más me enseñó este trabajo fue tener que desconfiar de mis propias métricas. El plan original
era medir la calidad con la similitud coseno, y la hipótesis del TP4 tenía un umbral de 0.90 que
parecía razonable. Cuando la validé contra mi propio juicio, la métrica separó las respuestas buenas
de las malas peor que tirar una moneda. Fue incómodo, porque invalidaba la mitad de la hipótesis,
pero fue también lo que le dio sentido al resto: si no la hubiera validado, habría reportado una
cifra de calidad que no medía nada.

Lo segundo fue aprender a etiquetar. Mis dos primeras pasadas como evaluador no sirvieron: en la
primera acepté casi todo, y en la segunda terminé juzgando si las respuestas hablaban del mismo tema
en lugar de si una podía reemplazar a la otra. Recién en la tercera, después de una ronda de
calibración con casos diseñados para detectar esos atajos, las notas fueron consistentes. Entendí
que un evaluador humano también es un instrumento, y que hay que calibrarlo.

Lo tercero fue el valor de escribir las reglas antes de ver los datos. El pre-registro me obligó a
decidir qué haría si el acuerdo con los jueces salía bajo, y salió bajo. Tener esa decisión tomada de
antemano evitó la tentación de elegir la regla que mejor quedaba, y me permitió reportar el resultado
tal como fue, con su explicación.

## 12.4 Líneas futuras de investigación

- Dado que el instrumento descansa en un único lector humano, una línea futura sería **incorporar
  un segundo lector y ampliar el hold-out** con más negativos y con un visor que preserve el código,
  con el fin de estimar el acuerdo entre personas y la magnitud del sesgo de los jueces, y no solo su
  dirección.
- Dado que el corpus no es tráfico real y el router es estático, una línea futura sería el
  **aprendizaje en línea**: juzgar automáticamente una muestra de las respuestas que el gateway
  sirve y reentrenar el router con ellas, con el fin de que la frontera siga describiendo el tráfico
  de cada tenant a medida que cambia.
- Dado que el aporte del caché no se pudo medir, una línea futura sería **evaluar el gateway
  completo sobre trazas con repetición**, midiendo juntos los aciertos del caché, su calidad y la del
  router, con el fin de estimar el ahorro total y la interacción entre ambos (por ejemplo, cuántas
  respuestas locales termina sirviendo el caché).
- Dado que el modelo local es lento y el nivel económico aporta poco, una línea futura sería una
  **cascada local → premium con un juez en línea** para los casos en que el router duda, con el fin de
  aprovechar la respuesta local cuando sale bien sin pagar su latencia en todos los pedidos que
  terminan en el premium.
- Dado que el clasificador es modesto (AUC 0.66) y el oráculo muestra mucho margen (USD 0.51 contra
  USD 1.70), una línea futura sería **probar señales más ricas**, como un embedding ajustado para la
  tarea o rasgos de la conversación previa, con el fin de acercar el costo del router al del oráculo
  sin cambiar la arquitectura del gateway.
