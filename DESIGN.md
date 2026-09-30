# Design System — Nebula consola

Única fuente de verdad visual de la consola (`console/`). Producto y público: `PRODUCT.md`.
Los valores se aplican como roles de Tailwind en `console/src/app/globals.css` (`@theme`); los
componentes nunca usan colores crudos ni hex.

## Product Context

- **Qué es:** la consola de operación de un gateway de LLM self-hosted que rutea cada pedido al
  nivel más barato que cumple un objetivo de calidad (local / economy / frontier).
- **Para quién:** primero, el jurado de ingeniería del TFC (demo en vivo y capturas en un Word
  de fondo blanco); después, el operador que audita costo y decisiones de ruteo.
- **Tipo:** herramienta de operación (Operate), escritorio 1280–1440 px.

## Aesthetic Direction

- **Dirección:** "Plano" — la consola como hoja de ingeniería: tinta negra sobre blanco, líneas de
  1 px, esquinas rectas, rótulo de plano como encabezado, grilla de osciloscopio en los gráficos,
  la decisión del router dibujada como un camino de señal. Préstamos de "Hoja de datos": tabla de
  características (valor + IC 95 %) y pies "Figura N".
- **Decoración:** mínima. Lo que no es dato, control o estructura se borra.
- **Mood:** instrumento de medición; serio, exacto, legible en una captura.
- **Referencias:** `docs/superpowers/fase7/referencias/` (Langfuse, Helicone, Grafana, Vercel);
  mockups aprobados en `docs/superpowers/fase7/direcciones/`.

## Typography

- **UI y títulos:** Barlow (400, 500, 600, 700) — rotulado técnico de familia DIN, números
  tabulares.
- **Rótulos:** Barlow Semi Condensed (500, 600).
- **Datos y tablas:** Barlow con `font-variant-numeric: tabular-nums`.
- **Código, ids, ejes, headers:** Red Hat Mono (400, 500). Nunca como disfraz "técnico".
- **Carga:** `next/font/google` (self-hosted en build).
- **Escala (px / peso):** display 44/600 · h1 26/600 · h2 18/600 · h3 16/600 · cuerpo 16/400 ·
  tablas y readouts 14/500 · rótulos 13/500 · ejes e ids 12/400 mono. Interlineado 1.45 (cuerpo),
  1.15 (títulos). Tracking 0 salvo display (−0.02em). Sin `uppercase`.

## Color

- **Estrategia:** restringida. Neutros + un acento de selección + rampa ordinal para los niveles.
- **Roles:**

| Rol | Hex | Uso |
|---|---|---|
| `surface` | `#ffffff` | fondo de la app y de todo panel |
| `canvas` / `rail` | `#f3f4f5` | riel de navegación, fondos de código y filas alternas |
| `ink` | `#111418` | texto principal, botón primario, línea fuerte |
| `ink-2` | `#4a525c` | texto secundario |
| `ink-3` / `ink-4` | `#5c646e` | rótulos y metadatos (mínimo AA; nunca más claro) |
| `line` | `#d3d8dd` | líneas de 1 px, bordes, grilla |
| `line-strong` | `#111418` | regla bajo encabezados de tabla y rótulo de página |
| `mark` | `#c62f1d` | lo que eligió el operador: punto de la frontera, fila seleccionada, nav activa, foco |
| `mark-soft` / `mark-line` | `#fbf1ef` / `#e9b9b2` | fondo y borde de la selección |
| `danger` · `-soft` · `-line` | `#9f2616` · `#fbf1ef` · `#e9b9b2` | errores, denegado |
| `warn` · `-soft` · `-line` | `#7a4b00` · `#fdf6e8` · `#ecd3a1` | avisos |
| `ok` · `-soft` · `-line` | `#1f5f32` · `#eef6f0` · `#b9d8c1` | estado sano |
| `tier-local` | `#86b6ef` | nivel local |
| `tier-economy` | `#2f73cc` | nivel economy |
| `tier-frontier` | `#103f82` | nivel frontier |
| `tier-cache` | `#aab2bb` | respuesta de caché |

- La rampa de niveles es ordinal (costo creciente), un solo tono, validada con el script de
  dataviz (`--ordinal`: monotonía, saltos de L ≥ 0.06, extremo claro ≥ 2:1). El nivel nunca se
  comunica solo con color: siempre va con su nombre.
- Estados siempre con ícono o texto además del color.
- **Modo oscuro:** no existe. Solo tema claro.

## Spacing

- **Base:** 4 px. **Densidad:** cómoda-compacta.
- **Escala:** 4 · 8 · 12 · 16 · 24 · 32 · 48. Más espacio arriba de un título que abajo.

## Layout

- **Enfoque:** grilla disciplinada. Riel de 216 px + contenido. Sin tarjetas decorativas: las
  regiones se separan con líneas de 1 px, no con sombras.
- **Rótulo de página (`PageHeader`):** título h1 + celdas de contexto o filtros separadas por
  líneas verticales; regla fuerte abajo.
- **Cortes:** objetivo 1280–1440. 1024–1279: paneles laterales pasan debajo. < 1024: riel
  colapsado a barra superior; tablas con scroll horizontal dentro de su contenedor.
- **Radio:** 0 en todo; 2 px en inputs y selects.
- **Controles:** 40 px de alto; foco `outline: 2px solid mark` con offset 2 px.

## Motion

- **Enfoque:** mínimo-funcional, un momento por vista.
- **Firmados:** el camino de señal de la decisión se traza al aparecer (≤ 600 ms, ease-out); el
  punto de la frontera y la cruz de medición se deslizan al mover el slider (250 ms).
- **Duraciones:** micro 100 ms · corta 200 ms · media 250–400 ms · larga 600 ms. Easing
  `cubic-bezier(0.16, 1, 0.3, 1)`.
- `prefers-reduced-motion`: todo estático.

## Components

- **shadcn/ui re-tematizado por roles:** Sidebar, Table, Input, Select, Label, Button, Dialog,
  AlertDialog, Alert, Tabs, Badge, Skeleton, Tooltip, Separator, Sheet.
- **Propios:** `PageHeader`, `Readout`, `Figure` (pie "Figura N."), `TierBadge`, `EmptyState`,
  `ErrorAlert`, `LoadingRows`, `DecisionPath` (cascada local → economy → frontier con p y τ).

## Copy

- Español neutro, sin voseo; infinitivos en acciones ("Crear tenant", "Aplicar al tenant").
- Sin párrafos en encabezados. Una línea de ayuda solo donde evita un error.
- Términos de la tesis sin traducir: tenant, ledger, playground, local, economy, frontier.
- Números como la tesis: `USD 1.70`, punto decimal, `31 %`.

## Prohibido

Eyebrows o kickers sobre títulos; `uppercase` y tracking sueltos; gradientes; sombras
decorativas; tarjetas anidadas; bordes laterales de color; íconos en círculos de color;
monospace como disfraz; emojis como íconos; texto gris por debajo de AA.

## Decisions Log

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-09-30 | Sistema "Plano" + préstamos de "Hoja de datos" | Elegido por Joaquín entre 3 direcciones; equilibra operador (claridad) y jurado (figuras de tesis, momentos animados) |
| 2026-09-30 | Solo tema claro | Las capturas van a un Word de fondo blanco |
| 2026-09-30 | Tailwind 4 + shadcn/ui tematizado por roles | shadcn 4.x genera para v4; roles como única vía de color |
| 2026-09-30 | Rampa azul ordinal para los niveles, rojo solo para selección | Los niveles están ordenados por costo; el rojo marca la decisión del operador |
