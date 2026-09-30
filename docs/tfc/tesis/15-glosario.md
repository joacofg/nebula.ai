# 15. Glosario

**API compatible con OpenAI.** Interfaz HTTP que acepta los mismos pedidos y devuelve las mismas
respuestas que la API de chat de OpenAI, de modo que una aplicación puede cambiar de proveedor
cambiando solo la URL.

**AUC (área bajo la curva ROC).** Probabilidad de que un ejemplo positivo al azar reciba una
puntuación mayor que un negativo al azar. 0.5 es azar; 1, separación perfecta.

**Bootstrap.** Técnica que estima la incertidumbre de una cifra remuestreando los datos con
reposición y observando cómo varía.

**Caché semántico.** Caché que devuelve una respuesta guardada cuando la consulta nueva es
suficientemente parecida, en significado, a una ya respondida.

**Cascada.** Estrategia de ruteo que prueba primero un modelo barato y escala a uno más caro si la
respuesta no supera un control.

**Conjunto dirigido.** Muestra elegida a propósito, no al azar, para medir algo específico; en este
trabajo, los rechazos de los jueces.

**Embedding.** Vector de números que representa un texto de modo que textos de significado parecido
quedan cerca.

**Ensamble de jueces.** Combinación de las notas de varios jueces mediante una regla fijada de
antemano.

**Estimación anidada.** Evaluación en la que los parámetros que deciden sobre un conjunto de datos se
eligen sin mirar ese conjunto.

**Fallback.** Reenvío automático de un pedido a otro proveedor cuando el elegido falla.

**Frontera de Pareto.** Conjunto de puntos de operación que no están dominados: ninguno otro es a la
vez más barato y de mejor calidad.

**Gateway de IA.** Proxy entre las aplicaciones y los proveedores de modelos que decide la ruta de
cada pedido, aplica políticas y registra lo ocurrido.

**Ground truth.** Etiquetas que se toman como verdad de referencia para entrenar y evaluar; en este
trabajo, la sustituibilidad de cada respuesta según los jueces.

**Hold-out.** Subconjunto de datos que se reserva y no se usa para tomar decisiones, solo para medir.

**κ de Cohen.** Medida de acuerdo entre dos evaluadores que descuenta el acuerdo esperable por azar.

**Ledger.** Registro de cada pedido atendido, con su ruta, costo, latencia y motivo.

**LLM como juez.** Uso de un modelo de lenguaje para evaluar las respuestas de otros modelos.

**Nivel (tier).** Cada una de las opciones de ruta del router: local, económico o frontier.

**Objetivo de calidad.** Calidad mínima que un tenant declara; el router usa el punto de operación
más barato que la alcanza.

**Oráculo.** Política hipotética que conoce de antemano la etiqueta de cada prompt; marca el mínimo
costo alcanzable.

**Punto de operación.** Par de umbrales del router, con el costo y la calidad que produce.

**Pre-registro.** Documento que fija, antes de ver los datos, las reglas, umbrales y criterios con
que se van a analizar.

**Self-hosted.** Desplegado y operado en la infraestructura propia de quien lo usa, sin un servicio
alojado por terceros.

**Sustituible.** Respuesta que podría haber reemplazado a la del modelo de referencia sin que quien
preguntó quedara peor (grados `equivalent` o `minor_loss` de la rúbrica).

**Tenant.** Unidad de aislamiento del gateway (un equipo o un cliente) con sus claves, su política y
su historial.

**Token.** Unidad en que los modelos dividen el texto y por la que cobran los proveedores.

**TTL (tiempo de vida).** Antigüedad máxima con que una entrada del caché se sigue sirviendo.

**Validación cruzada agrupada.** Validación cruzada en la que los ejemplos relacionados (un prompt y
su traducción) quedan siempre en el mismo fold.
