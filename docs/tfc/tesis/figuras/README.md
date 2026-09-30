# Figuras de la tesis

`make thesis-figures` regenera los diagramas y la frontera: la frontera sale de `benchmarks/router/v1/report.json`
(`scripts/thesis/figures.py`, matplotlib) y el resto de las fuentes Mermaid (`*.mmd`, con
mermaid-cli vía `npx`). Para Word conviene insertar el PNG; la frontera también está en SVG.

| Figura | Archivo | Sección que la cita |
|---|---|---|
| 10.1 Arquitectura del gateway | `arquitectura.png` | 10.1 |
| 10.2 Modelo de datos | `modelo-datos.png` | 10.2 |
| 10.3 Edición de la política del tenant (consola) | `consola-politica.png` | 10.2 |
| 10.4 Recorrido de un pedido de chat | `secuencia-request.png` | 10.3 |
| 10.5 Pipeline de etiquetado y entrenamiento del router | `pipeline-ml.png` | 10.3 |
| 10.6 Página Evaluación (consola) | `consola-evaluacion.png` | 10.3 |
| 10.7 Playground con "Por qué este nivel" (consola) | `consola-playground.png` | 10.3 |
| 11.1 Vista de observabilidad (consola) | `consola-observabilidad.png` | 11.1 |
| 11.2 Frontera costo–calidad del router aprendido | `frontera.png` / `frontera.svg` | 11.2.3 |

Las capturas de la consola (`consola-*.png`) no se regeneran con `make thesis-figures`: se sacan a
mano con la consola en marcha, a 1440 × 900 y escala 2, con el router aprendido activado por
variables de entorno (`docs/demo-runbook.md`) y el tenant de demo Acme Robotics.
