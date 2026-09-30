# Referencias visuales — rediseño de la consola (fase 7)

Capturas de UI real de productos (no ilustraciones de marketing), en tema claro, para orientar el rediseño de la consola de Nebula. Todas fueron capturadas el 2026-09-30. Las imágenes pertenecen a sus respectivos productos y se usan solo como referencia interna; no se incluyen en la tesis.

| Archivo | Producto | Fuente | Fecha |
|---|---|---|---|
| `langfuse-dashboard-costos.png` | Langfuse (Home / dashboard) | https://langfuse.com/docs/metrics/overview (imagen `/images/docs/llm-analytics.png`) | 2026-09-30 |
| `helicone-tabla-requests.png` | Helicone (tabla Requests) | https://docs.helicone.ai/features/advanced-usage/custom-properties | 2026-09-30 |
| `grafana-slo-latencia.png` | Grafana (dashboard público "Frontend - Latency SLO", tema claro, modo kiosk) | https://play.grafana.org/d/grafana_slo_app-e8kepyem0n585kctqk26n/frontend-latency-e8kepyem0n585kctqk26n?orgId=1&theme=light&kiosk | 2026-09-30 |
| `vercel-analytics-paneles.png` | Vercel (paneles de Web Analytics, "tono de herramienta") | https://vercel.com/docs/analytics (imagen `panels-light-mode.png`) | 2026-09-30 |

## Observaciones por imagen

### `langfuse-dashboard-costos.png` — Langfuse
- El costo se muestra como una cifra grande con unidad (`$0.491333 Total cost`) y, debajo, una tabla compacta Modelo / Tokens / USD con números alineados a la derecha. Es un patrón directamente aplicable a "costo por nivel (local / economy / frontier)".
- Tarjetas con borde gris de 1 px, sin sombra y con fondo blanco sobre un lienzo gris muy claro. Un solo color de acento (violeta) para las series y las barras; el resto es escala de grises.
- Las pestañas de subrayado (`Cost by model / Cost by type / Units by model`) cambian la vista dentro del mismo panel sin agregar pantallas nuevas.

### `helicone-tabla-requests.png` — Helicone
- La tabla por request tiene la estructura que necesita el ledger: fecha, estado, request, response, modelo y columnas configurables (`Columns 19/19`). Las filas son de alto medio, con separadores horizontales finos y sin bandas de color.
- El estado usa una pastilla pequeña verde con texto (`Success`) y el modelo, un chip monoespaciado con tinte violeta. El color codifica categorías, no decora.
- La barra superior agrupa el rango temporal como un control segmentado (`24H 7D 1M 3M All`) y las acciones (filtros, exportar, vista) como botones secundarios con contorno. Nota: el recuadro rojo es una anotación de la documentación de Helicone, no parte de la UI.

### `grafana-slo-latencia.png` — Grafana
- Grilla de paneles con títulos cortos y un ícono de info para la definición de la métrica. Es útil para explicar métricas (p. ej., cuota de ahorro o calidad) sin llenar la pantalla de texto.
- Las cifras de resumen (`95 %`, `99.5 %`) van en un panel angosto al lado de la serie temporal que las explica. La relación "número ↔ gráfico" queda clara sin leyendas extra.
- El verde y el rojo se reservan para el estado (OK / alerta); las series usan líneas finas de 1 px, con cuadrícula tenue y ejes con fechas cortas.

### `vercel-analytics-paneles.png` — Vercel
- Las listas "clave → valor" usan barras de fondo gris proporcionales al valor detrás del texto. Funcionan como un gráfico de barras sin ejes, legible en blanco y negro (apto para Word).
- Tipografía sans neutra con cifras en negrita alineadas a la derecha y rótulos de columna en versalitas grises (`VISITORS`). La jerarquía se construye con peso y tamaño, no con color.
- El cromado es mínimo: borde de 1 px, esquinas levemente redondeadas, pestañas en gris y "View All" como acción secundaria discreta.

## Patrones comunes

- Lienzo gris muy claro con paneles blancos de borde fino (1 px) y sin sombras. La separación viene del borde y el espacio, no de la profundidad.
- Números como protagonistas: cifra grande + unidad + rótulo gris pequeño. Las cifras de las tablas van alineadas a la derecha y con precisión consistente (USD con decimales fijos, latencia en ms/s).
- Tablas densas por request (fecha, estado, modelo, tokens/costo, latencia), con separadores horizontales finos, columnas configurables y detalle en un panel lateral (Langfuse trace, Portkey logs) en lugar de una página nueva.
- El color es semántico y escaso: un único acento para las series y verde/ámbar/rojo solo para el estado. El modelo o nivel se identifica con un chip pequeño con tinte suave.
- Controles de contexto arriba y agrupados: rango temporal como control segmentado (24H/7D/1M), filtros como pastillas y búsqueda con sintaxis (`latency:>2`, `level:ERROR`).
- Pestañas dentro del panel para alternar vistas de la misma métrica (costo por modelo / por tipo, tabla / gráfico) sin multiplicar pantallas.
- Definiciones al alcance: un ícono de info junto al título del panel explica cómo se calcula la métrica. Esto encaja bien con un público de jurado y auditoría.

## Qué evitar

- Tarjetas de KPI con fondo saturado o degradado (como en el dashboard "Banking Executive Overview" de Grafana Play): compiten entre sí, se imprimen mal y no dejan ver cuál importa.
- Capturas "enmarcadas" como marketing (fondos con degradado, ventana flotante, cursor): así vienen el README de Helicone, el dashboard de Portkey y Linear Insights. Para la tesis conviene captura directa a sangre.
- Tema oscuro por defecto (Portkey Logs, Linear): en un documento Word de fondo blanco se ve como un bloque negro y pierde legibilidad impreso.
- Gráficos de torta con muchos colores (panel "Models" del caché de Helicone) y cifras gigantes sin contexto (el "58.5" recortado de Grafana Business Metrics). Es mejor una barra horizontal o una tabla.
- Emojis e íconos decorativos en títulos o celdas (Portkey, Grafana Bank): agregan ruido sin información.
