# Figuras de la tesis

`make thesis-figures` regenera todas: la frontera sale de `benchmarks/router/v1/report.json`
(`scripts/thesis/figures.py`, matplotlib) y el resto de las fuentes Mermaid (`*.mmd`, con
mermaid-cli vía `npx`). Para Word conviene insertar el PNG; la frontera también está en SVG.

| Figura | Archivo | Sección que la cita |
|---|---|---|
| 10.1 Arquitectura del gateway | `arquitectura.png` | 10.1 |
| 10.2 Recorrido de un pedido de chat | `secuencia-request.png` | 10.3 |
| 10.3 Modelo de datos | `modelo-datos.png` | 10.2 |
| 10.4 Pipeline de etiquetado y entrenamiento del router | `pipeline-ml.png` | 10.3 |
| 11.1 Frontera costo–calidad del router aprendido | `frontera.png` / `frontera.svg` | 11.2.3 |

## Capturas pendientes (fase 7, después del refactor de la UI)

- `CAPTURA (fase 7)`: página Evaluación con el slider de calidad y la frontera (sección 10.3).
- `CAPTURA (fase 7)`: Playground con el panel "Por qué este nivel" (sección 10.3).
- `CAPTURA (fase 7)`: vista de observabilidad / ledger con la ruta y el costo por pedido (sección 11.1).
- `CAPTURA (fase 7)`: edición de la política del tenant, con el objetivo de calidad y el límite de pedidos (sección 10.2).
