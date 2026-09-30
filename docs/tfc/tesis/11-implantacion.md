# 11. Implantación y desarrollo del prototipo

## 11.1 Herramientas

## 11.2 Pruebas y resultados

### 11.2.1 Plan de pruebas

### 11.2.2 Casos de prueba

### 11.2.3 Resultados

<!-- GEN:corpus-fase2 -->
El corpus combina tres conjuntos públicos: dolly (CC BY-SA 3.0); gsm8k (MIT); mbpp (CC BY 4.0). Se muestrearon 1000 prompts estratificados por tarea (code 200, factual_qa 200, multistep_reasoning 200, open_writing 200, summarisation 200) con semilla fija, y un subconjunto pareado de 250 en inglés. La traducción al español la hizo `mistralai/mistral-medium-3.1`, de una familia ajena a candidatos y jueces. Un control mecánico rechazó 10 traducciones que alteraban bloques de código, o números en razonamiento y código (donde los números son la tarea), y se reemplazaron desde la reserva del mismo estrato; en las tareas de Dolly, 31 traducciones reescribieron números por estilo (p. ej. «siglo XV») y quedaron marcadas para la revisión humana. Una revisión humana de 40 traducciones encontró 0 infieles (0%).
<!-- /GEN:corpus-fase2 -->

<!-- GEN:judges-fase2 -->
Cada par candidato–referencia recibe cuatro notas (dos jueces, dos posiciones). La regla se eligió sobre 22 pares en inglés etiquetados por un lector humano; esos pares se eligieron en el piloto por desacuerdo entre dos jueces previos y quedaron 20 sustituibles y 2 no, así que el kappa de selección descansa en muy pocos negativos. Kappa binario por regla: R1 -0.015, R2 0.327, R3 0.645; se eligió R3. Como análisis de sensibilidad pre-registrado, los niveles se reportan bajo las tres reglas. Sobre el hold-out en español (50 pares sorteados antes de correr los jueces) la regla elegida obtuvo kappa 0.31 (IC 95 % -0.07–0.64). El acuerdo bruto fue 82%; el lector juzgó sustituibles 45 de 50, y en los desacuerdos el ensamble fue más estricto que el lector 7 veces y más laxo 2. Al quedar por debajo de 0.4, el ground truth se declara limitado por los jueces. Análisis post hoc, no pre-registrado: el evaluador marcó como de baja confianza sus notas sobre pares de código, porque la terminal de etiquetado reenvuelve los bloques de código; sin esos pares (40) el kappa es 0.44 (IC 95 % 0.00–0.78). Como el hold-out tuvo pocos negativos, un segundo conjunto dirigido —no aleatorio, sin pares de código— mezcló a ciegas pares que el ensamble rechazó con pares que aceptó: el lector coincidió con el rechazo en 20 de 25 (80%, IC 95 % 61%–91%), y juzgó sustituibles 9 de 10 aceptados. Tasa de cambio de veredicto al invertir posiciones: deepseek-chat-v3-0324 8%, gemini-2.5-flash 12%.
<!-- /GEN:judges-fase2 -->

<!-- GEN:router-fase3 -->
El router aprendido son dos regresiones logísticas sobre el embedding del prompt (prefijo `none`), evaluadas con validación cruzada de 5 folds agrupada por prompt sobre 1250 prompts; AUC fuera de fold: local 0.66, economy 0.65, una señal modesta. En la estimación anidada —umbrales y pesos elegidos sin el fold que se rutea— con objetivo de calidad 0.95 el router logra calidad 0.957 a USD 1.70 cada mil prompts, 31% menos que enviar todo al modelo frontier (USD 2.47; IC 95 % 28%–35%) y 17% menos que la mejor mezcla aleatoria de niveles a igual calidad (IC 95 % 12%–21%). Con objetivo 0.90 logra 0.903 a USD 1.06. El objetivo se cumple sobre el conjunto; por idioma la calidad fue 0.961 en español y 0.940 en inglés. La heurística de dos reglas no mejora a enviar todo al modelo local: calidad 0.759 contra 0.754, a USD 0.23 cada mil prompts. El oráculo, que conoce la etiqueta, costaría USD 0.51: queda margen. El costo local se cuenta en cero; su precio es el tiempo: en esta máquina la mediana por respuesta fue openai/gpt-4.1 2.5 s, anthropic/claude-haiku-4.5 3.9 s, llama3.2:3b 9.8 s, qwen2.5:7b 21.3 s (30 prompts, secuencial). Las reglas de etiquetado R1 y R2 se reportan como sensibilidad.
<!-- /GEN:router-fase3 -->

<!-- GEN:router-fixed-policies -->
| Política | Costo (USD cada 1000 prompts) | Calidad |
|---|---|---|
| todo local (qwen2.5:7b) | 0.00 | 0.754 |
| todo económico (claude-haiku-4.5) | 1.84 | 0.880 |
| todo frontier (gpt-4.1) | 2.47 | 1.000 |
| oráculo | 0.51 | 1.000 |
| heurística de dos reglas → frontier | 0.23 | 0.759 |
| heurística de dos reglas → económico | 0.12 | 0.756 |
| router aprendido, objetivo 0.95 (estimación anidada) | 1.70 | 0.957 |
<!-- /GEN:router-fixed-policies -->

<!-- GEN:router-sensitivity -->
| Regla de etiquetado | calidad ≥ 0.85 | calidad ≥ 0.90 | calidad ≥ 0.95 | todo frontier |
|---|---|---|---|---|
| R1 unanimidad | 1.31 | 1.59 | 1.97 | 2.47 |
| R2 mayoría | 1.04 | 1.32 | 1.83 | 2.47 |
| R3 media ordinal (elegida) | 0.56 | 1.01 | 1.70 | 2.47 |
<!-- /GEN:router-sensitivity -->

<!-- GEN:router-frontier-points -->
| Calidad mínima | τ local | τ económico | Costo (USD cada 1000) | Local | Económico | Frontier |
|---|---|---|---|---|---|---|
| 0.80 | 0.64 | 0.84 | 0.26 | 89 % | 4 % | 7 % |
| 0.85 | 0.70 | 0.90 | 0.56 | 76 % | 1 % | 23 % |
| 0.90 | 0.76 | 0.90 | 1.01 | 56 % | 4 % | 40 % |
| 0.95 | 0.82 | 0.92 | 1.70 | 27 % | 6 % | 67 % |
| 0.98 | 0.86 | 0.94 | 2.17 | 10 % | 1 % | 89 % |
<!-- /GEN:router-frontier-points -->

<!-- GEN:router-latency -->
| Modelo | Mediana (s) | p90 (s) | Respuestas |
|---|---|---|---|
| openai/gpt-4.1 | 2.5 | 5.2 | 30 |
| anthropic/claude-haiku-4.5 | 3.9 | 6.4 | 30 |
| llama3.2:3b | 9.8 | 17.4 | 30 |
| qwen2.5:7b | 21.3 | 36.2 | 30 |
<!-- /GEN:router-latency -->

### 11.2.4 Análisis de resultados

### 11.2.5 Amenazas a la validez
