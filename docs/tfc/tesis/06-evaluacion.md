# 6. Evaluación

## 6.1 Preguntas de investigación
RQ1 ¿Cuánto gasto premium evita cada estrategia de ruteo a igual calidad?
RQ2 ¿La similitud coseno sirve como métrica de calidad? (estudio de validación: no, AUC 0.25)
RQ3 ¿Cuánto se aproximan los jueces LLM a un lector humano, en inglés y en español?
RQ4 ¿Cómo cambia la frontera con el tamaño del modelo local (3B vs 7B)?

## 6.2 Corpus
<!-- GEN:corpus-fase2 -->
El corpus combina tres conjuntos públicos: dolly (CC BY-SA 3.0); gsm8k (MIT); mbpp (CC BY 4.0). Se muestrearon 1000 prompts estratificados por tarea (code 200, factual_qa 200, multistep_reasoning 200, open_writing 200, summarisation 200) con semilla fija, y un subconjunto pareado de 250 en inglés. La traducción al español la hizo `mistralai/mistral-medium-3.1`, de una familia ajena a candidatos y jueces. Un control mecánico rechazó 10 traducciones que alteraban bloques de código, o números en razonamiento y código (donde los números son la tarea), y se reemplazaron desde la reserva del mismo estrato; en las tareas de Dolly, 31 traducciones reescribieron números por estilo (p. ej. «siglo XV») y quedaron marcadas para la revisión humana. Una revisión humana de 40 traducciones encontró 0 infieles (0%).
<!-- /GEN:corpus-fase2 -->

## 6.3 Jueces y validación contra humanos
Antecedente ya medido: sobre 22 pares en inglés, sustituibles según gpt-4o-mini 32 %, gemini-2.5-flash 68 %,
lector humano 91 % (p = 1.2e-4). <!-- GEN: judge-vs-human -->
<!-- GEN:judges-fase2 -->
Cada par candidato–referencia recibe cuatro notas (dos jueces, dos posiciones). La regla se eligió sobre 22 pares en inglés etiquetados por un lector humano; esos pares se eligieron en el piloto por desacuerdo entre dos jueces previos y quedaron 20 sustituibles y 2 no, así que el kappa de selección descansa en muy pocos negativos. Kappa binario por regla: R1 -0.015, R2 0.327, R3 0.645; se eligió R3. Como análisis de sensibilidad pre-registrado, los niveles se reportan bajo las tres reglas. Sobre el hold-out en español (50 pares sorteados antes de correr los jueces) la regla elegida obtuvo kappa 0.31 (IC 95 % -0.07–0.64). El acuerdo bruto fue 82%; el lector juzgó sustituibles 45 de 50, y en los desacuerdos el ensamble fue más estricto que el lector 7 veces y más laxo 2. Al quedar por debajo de 0.4, el ground truth se declara limitado por los jueces. Análisis post hoc, no pre-registrado: el evaluador marcó como de baja confianza sus notas sobre pares de código, porque la terminal de etiquetado reenvuelve los bloques de código; sin esos pares (40) el kappa es 0.44 (IC 95 % 0.00–0.78). Como el hold-out tuvo pocos negativos, un segundo conjunto dirigido —no aleatorio, sin pares de código— mezcló a ciegas pares que el ensamble rechazó con pares que aceptó: el lector coincidió con el rechazo en 20 de 25 (80%, IC 95 % 61%–91%), y juzgó sustituibles 9 de 10 aceptados. Tasa de cambio de veredicto al invertir posiciones: deepseek-chat-v3-0324 8%, gemini-2.5-flash 12%.
<!-- /GEN:judges-fase2 -->

## 6.4 Resultados de ruteo
Línea de base (heurística de dos reglas, 14 escenarios, 2026-08-19): 41.2 % (corrida 20260819T225557Z), 38.2 % (20260819T225703Z) y 40.0 % (20260819T225713Z) de gasto
premium evitado. <!-- GEN: baseline-savings -->
<!-- GEN:router-fase3 -->
El router aprendido son dos regresiones logísticas sobre el embedding del prompt (prefijo `none`), evaluadas con validación cruzada de 5 folds agrupada por prompt sobre 1250 prompts; AUC fuera de fold: local 0.66, economy 0.65, una señal modesta. En la estimación anidada —umbrales y pesos elegidos sin el fold que se rutea— con objetivo de calidad 0.95 el router logra calidad 0.957 a USD 1.70 cada mil prompts, 31% menos que enviar todo al modelo frontier (USD 2.47; IC 95 % 28%–35%) y 17% menos que la mejor mezcla aleatoria de niveles a igual calidad (IC 95 % 12%–21%). Con objetivo 0.90 logra 0.903 a USD 1.06. El objetivo se cumple sobre el conjunto; por idioma la calidad fue 0.961 en español y 0.940 en inglés. La heurística de dos reglas no mejora a enviar todo al modelo local: calidad 0.759 contra 0.754, a USD 0.23 cada mil prompts. El oráculo, que conoce la etiqueta, costaría USD 0.51: queda margen. El costo local se cuenta en cero; su precio es el tiempo: en esta máquina la mediana por respuesta fue openai/gpt-4.1 2.5 s, anthropic/claude-haiku-4.5 3.9 s, llama3.2:3b 9.8 s, qwen2.5:7b 21.3 s (30 prompts, secuencial). Las reglas de etiquetado R1 y R2 se reportan como sensibilidad.
<!-- /GEN:router-fase3 -->

## 6.5 Amenazas a la validez
