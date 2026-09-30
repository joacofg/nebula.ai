# Tesis — fuente en Markdown

Título fijado por la cátedra: **Enrutamiento inteligente y cacheo semántico multi-proveedor
para reducción de costos en gateways de LLM self-hosted**.

La estructura sigue la "Estructura general de tesina — Tipo Desarrollo" del docente. Cada archivo
es una sección de primer nivel; el número del archivo es el número de la sección (la 3, índice,
está en `00-indice.md`, y las secciones 1, 2, 4 y 5 están juntas en `01-preliminares.md`).

## Cómo se regenera

- `make thesis-tables` reescribe todos los bloques `<!-- GEN:nombre -->…<!-- /GEN:nombre -->`
  desde los reportes versionados en `benchmarks/` (no usa la red ni reentrena nada).
  `python -m scripts.thesis.tables --check` falla si algún bloque quedó desactualizado, y la
  suite de tests lo corre. Los bloques GEN no se editan a mano.
- `make thesis-figures` exporta las fuentes Mermaid de `figuras/` a PNG.

## Convenciones

- Citas en formato IEEE, numeradas por orden de primera aparición en el documento.
- Figuras y tablas numeradas por sección (Figura 10.1, Tabla 11.3), con título y referencia en
  el texto.
- `> COMPLETAR (Joaquín): …` marca lo que tiene que escribir el autor (agradecimientos, datos del
  tutor, reflexión personal).
- `> CAPTURA (fase 7): …` marca capturas de la consola que se sacan después del refactor de la UI.

## Qué secciones alimentan cada práctica pendiente

| Práctica (etiqueta del deck) | Entrega | Secciones |
|---|---|---|
| TP9 (P8, Clase 10) — Estructura y diseño de la solución | 14/10/2026 | 10 y 11.1 |
| TP10 (P9, Clase 12) — Plan de testing y primeros resultados | 21/10/2026 | 11.2 |
| TP11 (P10, Clase 13) — Primer borrador de conclusiones | 28/10/2026 | 12 |
| TP12 (P11, Clase 14) — Conclusiones revisadas por el tutor | 04/11/2026 | 12 y 11.2.5 |
| TP13 (P12, Clase 15) — Prototipo y documento completo | 11/11/2026 | todo el documento |
