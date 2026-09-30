# Fase 7 — Refactor visual de la consola

Fecha: 2026-09-30. Plan maestro: tesis 10x (fases 1–6 mergeadas, PRs #5–#11).

## Objetivo

Rehacer la consola (`console/`, Next.js 15 + React 19) con un sistema visual propio y común a
todas las páginas, para que: (1) el jurado entienda en segundos qué decidió el router, por qué y
cuánto costó, en vivo y en las capturas del Word; (2) el operador audite costo y ruteo sin leer
párrafos. Lo único que cambia de la tesis son las capturas.

Contexto de producto: `PRODUCT.md` (jurado primero, español neutro sin voseo, poco texto).
Dirección elegida por Joaquín: **A · Plano + préstamos de B · Hoja de datos**
(`docs/superpowers/fase7/direcciones/`). Referencias: `docs/superpowers/fase7/referencias/`.
Línea de base: `docs/superpowers/fase7/baseline/` (1440 y 1280).

## Diagnóstico verificado (main, 52ce60a)

- 447 clases de color crudas slate/sky/zinc/gray fuera de los tokens (552 contando rose, amber,
  emerald…); 69 `uppercase`; 68 `tracking-[…]`; 29 `rounded-2xl/3xl/[2rem]`; fondo con gradiente
  radial. Fira Sans + Fira Code.
- Copy mayormente en inglés; párrafos explicativos en todos los encabezados (Observabilidad:
  ~3000 px de alto por texto y celdas que envuelven).
- 28 archivos de test de vitest con ~700 aserciones de texto.
- e2e `observability.spec.ts` y `playground.spec.ts` fallan desde antes de la fase 4 (selectores
  ambiguos).

## Decisiones

### Stack

- **Tailwind 3.4 → 4** en el PR (a) con `@tailwindcss/upgrade`. Motivo: shadcn 4.x genera
  componentes para v4; con v3 habría que fijar `shadcn@2.3.0` y componentes viejos. El codemod
  de clases ya toca todo, así que el costo marginal es bajo.
- **shadcn/ui** (CLI `shadcn@latest`, primitivas Radix) como capa de componentes, tematizada
  **solo por tokens**: ningún componente usa colores crudos.
- Fuentes vía `next/font/google`: Barlow (400/500/600/700), Barlow Semi Condensed (500/600),
  Red Hat Mono (400/500).

### Sistema visual (se documenta en `DESIGN.md`, única fuente de verdad)

- Solo tema claro. Superficie `#ffffff`, riel `#f3f4f5`, tinta `#111418`, texto secundario
  `#4a525c`, terciario `#5c646e` (AA sobre blanco y riel), líneas `#d3d8dd`, línea fuerte = tinta.
- Marca `#c62f1d`: solo selección del operador (punto elegido, fila seleccionada, nav activa),
  foco y denegado. Botón primario = tinta.
- Niveles, rampa ordinal validada con `dataviz/validate_palette.js --ordinal`: local `#86b6ef`,
  economy `#2f73cc`, frontier `#103f82`; caché `#aab2bb`; denegado = marca. El nivel nunca va
  solo por color: siempre muestra texto.
- Radio 0 (2 px en inputs). Bordes 1 px. Sin sombras decorativas, sin gradientes, sin eyebrows,
  sin `uppercase` ni tracking sueltos, sin tarjetas anidadas.
- Números tabulares en toda la app; mono solo para ids, ejes, headers y código.
- Movimiento: un momento firmado por vista (camino de señal, punto de la frontera), ease-out,
  ≤ 600 ms, desactivado con `prefers-reduced-motion`.

### Copy

- Español neutro, infinitivos en acciones ("Crear tenant", "Aplicar al tenant").
- Términos de la tesis sin traducir: tenant, ledger, playground, local / economy / frontier.
- Formato de la tesis: `USD 1.70`, punto decimal, `31 %`.
- Encabezados sin párrafo. Una línea de ayuda solo donde evita un error (p. ej. sesión en
  memoria en el login).

### Navegación

- Riel izquierdo con dos grupos: **Operar** (Evaluación, Playground, Observabilidad) y
  **Configurar** (Tenants, Claves de API, Política). Pie: sesión en memoria + Cerrar sesión.
- Después del login se aterriza en **/evaluacion**.
- Debajo de `lg` el riel se colapsa a una barra superior con menú.

## Componentes

shadcn re-tematizados: `Sidebar`, `Table`, `Field` (label + control + error/ayuda), `Dialog`,
`AlertDialog` (reemplaza `window.confirm` al revocar), `Alert` (reemplaza los banners rosa y
ámbar duplicados), `Tabs`, `Badge`, `Skeleton`, `Select`, `Input`, `Button`, `Slider` si encaja.

Propios (`console/src/components/ui/` junto a los de shadcn, o `components/system/`):

- `PageHeader`: el rótulo de plano. Título + celdas de contexto o filtros separadas por líneas.
- `Readout`: lista valor/rótulo con reglas finas.
- `Figure`: contenedor con pie "Figura N. …".
- `TierBadge`: swatch + nombre del nivel (incluye caché y denegado).
- `DecisionPath`: SVG de la cascada local → economy → frontier con p y τ de cada paso, rama
  elegida marcada; se traza al montar (≤ 600 ms), estático con reduced-motion; `role="img"`
  con `aria-label` que dice la decisión, sin hijos focusables. Lo usan Playground y el detalle
  del ledger.
- `FrontierChart` (existente) re-estilado: grilla tipo osciloscopio (10 divisiones), punto
  elegido en marca, tabla alternativa accesible (ya existe "Ver tabla").

## Páginas

- **Login**: una hoja con rótulo "Nebula" y el campo de la clave; mensaje de sesión expirada en
  `Alert`. Se va la grilla de 3 columnas.
- **Evaluación**: `PageHeader` (router, corpus, idiomas, "sin red ni Ollama"); tabla de
  características a 0.95 (ahorro vs todo frontier con IC, vs aleatoria con IC, calidad, costo,
  latencia mediana por modelo con su n tomado del replay); Figura 1 frontera + panel de control
  (slider, readouts, reparto por nivel, aplicar); replay acelerado; aplicar.
- **Playground**: formulario a la izquierda; respuesta, "Por qué este nivel" (`DecisionPath`) y
  readouts a la derecha.
- **Observabilidad**: filtros en el `PageHeader`; ledger (columnas fijas, sin envolver) + detalle
  con `DecisionPath`; debajo `Tabs`: Recomendaciones · Caché · Calibración · Dependencias.
- **Política**: secciones Ruteo (objetivo de calidad) · Límites (pedidos, presupuesto) · Caché ·
  Modelos permitidos · Avanzado; vista previa de la simulación fija a la derecha; guardar solo
  explícito.
- **Tenants** y **Claves de API**: tabla + editor lateral; crear/revelar/revocar en `Dialog`.

## Entregas (PRs)

1. **(a) Tokens, Tailwind 4 y codemod** — `@tailwindcss/upgrade`; tokens en `globals.css` con
   los valores **actuales** mapeados a roles; codemod de clases crudas a roles; fuera
   `uppercase`/tracking sueltos solo donde no cambia el render. Sin cambio visual intencional:
   se verifica contra la línea de base. Incluye PRODUCT.md, DESIGN.md (sistema objetivo), spec,
   plan, referencias, direcciones y baseline.
2. **(b) Componentes** — shadcn init + componentes listados; `Alert` reemplaza banners; `Dialog`
   /`AlertDialog` reemplazan modales propios y `window.confirm` (con trap de foco). Cambio visual
   acotado a esos componentes.
3. **(c) Páginas** — shell + login primero, después Evaluación, Playground, Observabilidad,
   Política, Tenants, Claves de API. Un commit por página con: shape → implementar → captura
   1440/1280 → critique/audit → corregir. Acá entran fuentes y paleta nuevas y el copy en
   español (tests de vitest en el mismo commit).
4. **(d) Cierre** — e2e `observability`/`playground` arreglados; backlog de julio y diferidos de
   la fase 4 (ver abajo); capturas de la tesis; `> CAPTURA (fase 7)` → figuras numeradas;
   `figuras/README.md`; `/design-review` con puntaje de AI slop; review independiente (opus).

## Backlog que se cierra

- Julio: nav colapsable bajo `lg`; banners componentizados; tokens muertos
  `--color-success/--color-danger` y rose vs pink; tracking mágico; encabezados con happy-talk;
  grilla de 3 columnas del login; trap de foco en modales; estados de carga con skeleton.
- Fase 4: a11y del SVG de la frontera (sin `role="img"` con hijos focusables); card "ahorro vs
  aleatoria" cuando el costo aleatorio es 0 (mostrar "—" con motivo); etiqueta "Heurística" →
  "heurística v0 (base)"; latencia "30 prompts, secuencial" hardcodeada → sale del replay;
  barra de reparto que se recorta; "Sin tenants" sin error cuando falla `listTenants`; 404 del
  endpoint que oculta otras causas.

## Capturas para la tesis

Con el router aprendido activo **por variables de entorno** (nunca en `.env`; ver
`docs/demo-runbook.md`), sesión de admin sin recargar, 1440 px:

- Figura: Evaluación con el slider y la frontera (10.3).
- Figura: Playground con "Por qué este nivel" (10.3).
- Figura: Observabilidad / ledger con ruta, nivel y costo (11.1).
- Figura: edición de la política con objetivo de calidad y límite de pedidos (10.2).

Se guardan en `docs/tfc/tesis/figuras/`, cada `> CAPTURA (fase 7)` se reemplaza por la figura
numerada con título y referencia en el texto, se actualiza `figuras/README.md` y
`make thesis-tables --check` sigue pasando.

## Fuera de alcance

Tema oscuro; cambios de API del gateway; `scripts/metric_validation/`,
`benchmarks/metric-validation/`, `docs/evaluation.md`, `tests/test_metric_validation.py`;
activar el router aprendido en `.env`.

## Verificación

- Por PR: `tsc --noEmit`, `ESLINT_USE_FLAT_CONFIG=false npx eslint .`, vitest `--maxWorkers=2`,
  `make test`, todo con `darwin-throttle`, nunca dos suites a la vez. Playwright con 2 workers.
- Tras tocar la config de Tailwind: `rm -rf console/.next` y reiniciar el dev server.
- PR (a): capturas contra la línea de base, diferencias solo por render de v4.
- PR (c)/(d): detector de Impeccable sin hallazgos mecánicos; `/design-review` con el puntaje de
  AI slop como número principal; e2e completos en verde.
- CI verde antes de cada merge.
