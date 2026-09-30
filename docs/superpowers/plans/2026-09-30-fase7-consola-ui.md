# Fase 7 — Refactor visual de la consola · Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consola de Nebula rehecha con el sistema "Plano" (+ tabla de características y pies de figura de "Hoja de datos"), en español neutro y con poco texto, lista para las capturas de la tesis.

**Architecture:** Cuatro PRs. (a) migra a Tailwind 4 y reemplaza las clases crudas por roles de color con los valores actuales; (b) agrega shadcn/ui tematizado por esos roles y los componentes propios; (c) rehace página por página y cambia los valores de los roles al sistema nuevo; (d) cierra e2e, backlog, capturas y tesis.

**Tech Stack:** Next.js 15.5, React 19, TypeScript, Tailwind 4, shadcn/ui (Radix), TanStack Query, vitest + Testing Library, Playwright, lucide-react.

**Spec:** `docs/superpowers/specs/2026-09-30-fase7-consola-ui.md` (leerla antes de cada PR). Producto: `PRODUCT.md`. Mockup de referencia: `docs/superpowers/fase7/direcciones/a-plano.html` y `b-hoja-de-datos.html`.

## Global Constraints

- Solo tema claro.
- Copy en español neutro, sin voseo; infinitivos en acciones. Sin párrafos en encabezados.
- Términos sin traducir: tenant, ledger, playground, local, economy, frontier.
- Números: `USD 1.70`, punto decimal, `31 %`, tabulares.
- Colores solo por roles (`bg-surface`, `text-ink`, `border-line`, …); cero clases slate/sky/zinc/gray/rose/amber/emerald y cero hex en componentes (salvo `DESIGN.md`/`globals.css`).
- Sin `uppercase`, sin `tracking-[…]`, sin eyebrows, sin gradientes, sin sombras decorativas, radio 0 (2 px inputs).
- Suites pesadas con `darwin-throttle`; vitest `--maxWorkers=2`; Playwright 2 workers; nunca dos suites a la vez.
- Lint: `ESLINT_USE_FLAT_CONFIG=false npx eslint .` (no `npm run lint`).
- Tras tocar la config de Tailwind/CSS global: `rm -rf console/.next` y reiniciar el dev server.
- Sesión de admin en memoria: en el navegador, navegar por clic, nunca `goto` después del login.
- No tocar `scripts/metric_validation/`, `benchmarks/metric-validation/`, `docs/evaluation.md`, `tests/test_metric_validation.py`. No activar el router aprendido en `.env`.
- Tests de vitest que afirman textos se actualizan en el mismo commit que el cambio de copy, afirmando el texto nuevo (nunca debilitar).
- Commits convencionales (feat/fix/style/refactor/test/docs/chore) con la atribución de la sesión.

## Review Focus

1. Tenant sin datos (ledger vacío, sin tenants, replay ausente): cada vista muestra un estado vacío con la acción siguiente, no un panel en blanco. → tests en Tasks 7, 11, 13, 14.
2. Error del backend (401 por sesión vencida, 404, 500) en cualquier query: `Alert` de error con el mensaje; un 404 del replay no oculta otros códigos. → Tasks 7, 11.
3. Textos largos (prompt de 2000 caracteres, id de modelo largo, nombre de tenant largo): nada desborda; celdas con elipsis y `title` completo. → Tasks 10, 13.
4. `prefers-reduced-motion`: el camino de señal y el punto de la frontera aparecen sin animación. → Tasks 6, 9.
5. Teclado: foco visible en todo control; Dialog con trap de foco y Escape; slider operable con flechas. → Tasks 4, 7, 9.

---

## PR (a) — Tailwind 4, roles de color y codemod

Branch: `fase7a-tokens-tailwind4` (ya creada; contiene la spec).

### Task 1: Migrar a Tailwind 4

**Files:**
- Modify: `console/package.json`, `console/postcss.config.*`, `console/src/app/globals.css`
- Delete: `console/tailwind.config.ts` (el upgrade lo pasa a `@theme` en CSS)

- [ ] **Step 1:** Árbol limpio (`git status`). Correr en `console/`: `npx @tailwindcss/upgrade --force` (requiere árbol limpio; `--force` solo si se queja del branch).
- [ ] **Step 2:** Revisar el diff: `postcss.config` debe usar `@tailwindcss/postcss`; `globals.css` con `@import "tailwindcss";` y un bloque `@theme` con `--color-panel`, `--color-surface`, … y las fuentes; clases renombradas (`shadow-sm`→`shadow-xs`, `rounded`→`rounded-sm`, `outline-none`→`outline-hidden`, `ring`→`ring-3`). Si `@layer components { .panel { @apply … } }` quedó como `@utility`, verificar que `.panel` siga funcionando.
- [ ] **Step 3:** v4 cambia el color de borde por defecto a `currentColor`. Agregar en `globals.css`:

```css
@layer base {
  *, ::after, ::before, ::backdrop, ::file-selector-button { border-color: var(--color-line, currentColor); }
}
```

- [ ] **Step 4:** `rm -rf .next && npx tsc --noEmit && ESLINT_USE_FLAT_CONFIG=false npx eslint . && darwin-throttle npx vitest run --maxWorkers=2`. Esperado: todo verde.
- [ ] **Step 5:** Dev server, login, captura de las 6 páginas a 1440 y comparar con `docs/superpowers/fase7/baseline/`. Diferencias aceptables: antialiasing, 1 px de borde. Corregir cualquier otra.
- [ ] **Step 6:** Commit `chore(console): migrate to Tailwind 4`.

### Task 2: Roles de color con los valores actuales + codemod

**Files:**
- Modify: `console/src/app/globals.css` (bloque `@theme`)
- Modify: todos los `.tsx` de `console/src` que no son test
- Create (fuera del repo): `$SCRATCH/codemod-colors.mjs`

**Interfaces — Produces:** roles de Tailwind que usan todas las tareas siguientes:
`surface, canvas, rail, ink, ink-2, ink-3, ink-4, line, line-strong, mark, mark-soft, mark-line, danger, danger-soft, danger-line, warn, warn-soft, warn-line, ok, ok-soft, ok-line, on-panel, on-panel-2, panel, tier-local, tier-economy, tier-frontier, tier-cache`.

- [ ] **Step 1:** En `@theme` de `globals.css` definir los roles con los valores **actuales** (sin cambio visual):

```css
@theme {
  --color-surface: #ffffff;
  --color-canvas: #f8fafc;      /* slate-50/100 */
  --color-rail: #0f172a;        /* panel oscuro actual */
  --color-panel: #0f172a;
  --color-ink: #020617;         /* slate-950/900 */
  --color-ink-2: #334155;       /* slate-700/800 */
  --color-ink-3: #475569;       /* slate-600 */
  --color-ink-4: #64748b;       /* slate-500/400 */
  --color-line: #cbd5e1;        /* slate-300/200 */
  --color-line-strong: #94a3b8; /* slate-400 */
  --color-mark: #0369a1;        /* sky-700 (accent actual) */
  --color-mark-soft: #f0f9ff;   /* sky-50 */
  --color-mark-line: #bae6fd;   /* sky-200 */
  --color-danger: #881337;      /* rose-900 */
  --color-danger-soft: #fff1f2; /* rose-50 */
  --color-danger-line: #fecdd3; /* rose-200 */
  --color-warn: #78350f;        /* amber-900 */
  --color-warn-soft: #fffbeb;
  --color-warn-line: #fde68a;
  --color-ok: #064e3b;          /* emerald-900 */
  --color-ok-soft: #ecfdf5;
  --color-ok-line: #a7f3d0;
  --color-on-panel: #f1f5f9;    /* slate-100 */
  --color-on-panel-2: #cbd5e1;  /* slate-300/400 */
  --color-tier-local: #2a78d6;
  --color-tier-economy: #eb6834;
  --color-tier-frontier: #1baf7a;
  --color-tier-cache: #94a3b8;
}
```

Borrar los viejos `--color-accent`, `--color-accent-strong`, `--color-border`, `--color-text`, `--color-success`, `--color-danger` (RGB) y sus alias en `@theme`, mapeando sus usos (`text-accent`→`text-mark`, `border-border`→`border-line`, `bg-accentStrong`→`bg-ink`, `text-text`→`text-ink`).

- [ ] **Step 2:** Escribir el codemod (`$SCRATCH/codemod-colors.mjs`): recorre `console/src/**/*.{ts,tsx}` excepto `*.test.*`, y reemplaza por regex con límites de palabra, preservando prefijos de variante (`hover:`, `focus:`, `group-hover:`) y sufijo de opacidad (`/60`):

```js
const MAP = {
  "slate-950": "ink", "slate-900": "ink", "slate-800": "ink-2", "slate-700": "ink-2",
  "slate-600": "ink-3", "slate-500": "ink-4", "slate-400": "ink-4",
  "slate-300": "line", "slate-200": "line", "slate-100": "canvas", "slate-50": "canvas",
  "sky-950": "mark", "sky-900": "mark", "sky-800": "mark", "sky-700": "mark", "sky-500": "mark",
  "sky-300": "mark-line", "sky-200": "mark-line", "sky-100": "mark-soft", "sky-50": "mark-soft",
  "rose-950": "danger", "rose-900": "danger", "rose-700": "danger", "rose-200": "danger-line", "rose-50": "danger-soft",
  "amber-950": "warn", "amber-900": "warn", "amber-700": "warn", "amber-200": "warn-line", "amber-100": "warn-line", "amber-50": "warn-soft",
  "emerald-900": "ok", "emerald-700": "ok", "emerald-200": "ok-line", "emerald-50": "ok-soft",
  "white": "surface",
};
// utilities: bg text border ring from to via divide outline fill stroke placeholder accent caret decoration
// Excepción: dentro de operator-shell.tsx y login-page-client.tsx (fondo oscuro) text-slate-100/300/400 → on-panel/on-panel-2, text-sky-200/300 → mark-line, bg-white/5|10 → on-panel/5|10.
```

Tras el reemplazo, `text-surface` en botones sobre fondo `mark` queda como `text-surface` (blanco): correcto. `frontier-chart.tsx` y `format.ts`: reemplazar los hex por `var(--color-…)` (el SVG acepta `stroke="var(--color-mark)"`).

- [ ] **Step 3:** Correr el codemod y verificar con:

```bash
rtk proxy sh -c 'grep -rnoE "\b[a-z-]+-(slate|sky|zinc|gray|rose|amber|emerald|pink)-[0-9]+" console/src --include=*.tsx --include=*.ts | grep -v "\.test\." | wc -l'
```
Esperado: `0`. Y `grep -rnE "#[0-9a-fA-F]{6}" console/src --include=*.tsx --include=*.ts | grep -v test` → 0.

- [ ] **Step 4:** tsc, eslint, vitest (`darwin-throttle npx vitest run --maxWorkers=2`). Esperado verde (los tests no afirman clases).
- [ ] **Step 5:** `rm -rf .next`, reiniciar, capturar las 6 páginas a 1440 y comparar con la línea de base. Diferencias aceptables: matices colapsados (slate-900→950, 400→500, 100→50).
- [ ] **Step 6:** Commit `refactor(console): route every color through design roles`.

### Task 3: DESIGN.md y cierre del PR (a)

**Files:**
- Create: `DESIGN.md` (raíz), `docs/superpowers/plans/2026-09-30-fase7-consola-ui.md` (este plan)
- Modify: `CLAUDE.md` (sección Design System)

- [ ] **Step 1:** Escribir `DESIGN.md` con el sistema objetivo de la spec (secciones: Product Context, Aesthetic Direction "Plano", Typography con escala, Color con los hex objetivo y roles, Spacing base 4 px, Layout, Motion, Components, Decisions Log). Es la fuente de verdad; los valores de `@theme` lo alcanzan en el PR (c).
- [ ] **Step 2:** Agregar a `CLAUDE.md`:

```markdown
## Design System
Always read DESIGN.md before making any visual or UI decisions.
All font choices, colors, spacing, and aesthetic direction are defined there.
Do not deviate without explicit user approval.
In QA mode, flag any code that doesn't match DESIGN.md.
```

- [ ] **Step 3:** `darwin-throttle make test` y `darwin-throttle make console-test -- --run --maxWorkers=2` (o `npm --prefix console run test -- --run --maxWorkers=2`). Verde.
- [ ] **Step 4:** Commit `docs: DESIGN.md for the Plano system`, push, PR "Fase 7a: Tailwind 4 y roles de color", esperar CI, merge.

---

## PR (b) — Componentes

Branch: `fase7b-componentes` desde main actualizado.

### Task 4: shadcn init + primitivas

**Files:**
- Create: `console/components.json`, `console/src/lib/utils.ts`, `console/src/components/ui/{button,input,label,select,table,dialog,alert-dialog,alert,tabs,badge,skeleton,sidebar,sheet,tooltip,separator}.tsx`, `console/src/hooks/use-mobile.ts`
- Modify: `console/package.json`, `console/src/app/globals.css`

- [ ] **Step 1:** En `console/`: `npx shadcn@latest init` (style new-york, base color neutral, CSS variables sí). Luego `npx shadcn@latest add button input label select table dialog alert-dialog alert tabs badge skeleton sidebar sheet tooltip separator`.
- [ ] **Step 2:** El init escribe variables `--background`, `--foreground`, `--primary`, … en `:root`. Re-apuntarlas a los roles del Task 2, sin valores propios:

```css
:root {
  --background: var(--color-surface); --foreground: var(--color-ink);
  --card: var(--color-surface); --card-foreground: var(--color-ink);
  --popover: var(--color-surface); --popover-foreground: var(--color-ink);
  --primary: var(--color-ink); --primary-foreground: var(--color-surface);
  --secondary: var(--color-canvas); --secondary-foreground: var(--color-ink);
  --muted: var(--color-canvas); --muted-foreground: var(--color-ink-3);
  --accent: var(--color-canvas); --accent-foreground: var(--color-ink);
  --destructive: var(--color-danger);
  --border: var(--color-line); --input: var(--color-line); --ring: var(--color-mark);
  --radius: 0rem;
  --sidebar: var(--color-rail); --sidebar-foreground: var(--color-on-panel);
  --sidebar-primary: var(--color-mark); --sidebar-primary-foreground: var(--color-surface);
  --sidebar-accent: var(--color-panel); --sidebar-accent-foreground: var(--color-on-panel);
  --sidebar-border: var(--color-line); --sidebar-ring: var(--color-mark);
}
```

Borrar el bloque `.dark` que agrega el init (solo tema claro). En `input.tsx`/`select.tsx` usar `rounded-[2px]`.

- [ ] **Step 3:** Test de humo `console/src/components/ui/ui-smoke.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

describe("ui primitives", () => {
  it("opens a dialog, traps focus and closes with Escape", async () => {
    const user = userEvent.setup();
    render(
      <Dialog>
        <DialogTrigger>Abrir</DialogTrigger>
        <DialogContent><DialogTitle>Título</DialogTitle><button>Dentro</button></DialogContent>
      </Dialog>,
    );
    await user.click(screen.getByText("Abrir"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    await user.tab();
    expect(screen.getByRole("dialog")).toContainElement(document.activeElement as HTMLElement);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 4:** `npx vitest run src/components/ui --maxWorkers=2` → PASS. tsc + eslint verdes (si eslint marca los archivos generados, ajustar solo esas reglas en los archivos de `ui/`, no la config global).
- [ ] **Step 5:** Commit `feat(console): add shadcn/ui primitives themed by design roles`.

### Task 5: Componentes propios de sistema

**Files:**
- Create: `console/src/components/system/{page-header,readout,figure,tier-badge,state}.tsx` y `system.test.tsx`

**Interfaces — Produces:**
```ts
PageHeader({ title: string; cells?: { label: string; value: ReactNode }[]; actions?: ReactNode })
Readout({ items: { label: string; value: ReactNode; emphasis?: boolean }[] })
Figure({ number: number; caption: ReactNode; children: ReactNode })
TierBadge({ tier: "local" | "economy" | "frontier" | "cache" | "denied" | string })
EmptyState({ title: string; action?: ReactNode })
ErrorAlert({ error: unknown; fallback: string })   // Alert destructive con el mensaje
LoadingRows({ rows?: number })                     // Skeleton
```

- [ ] **Step 1:** Test que falla (`system.test.tsx`): `TierBadge` con `"economy"` renderiza el texto `economy`; con `"cache"` → `caché`; con `"denied"` → `denegado`; con un nivel desconocido `"x"` → `x`. `ErrorAlert` con `new Error("boom")` → `role="alert"` con `boom`; con `"nope"` → el fallback. `Figure number={1} caption="Frontera"` → texto `Figura 1.` y `Frontera`. `PageHeader` → `heading` nivel 1 con el título y cada celda con su rótulo.
- [ ] **Step 2:** Correr → FAIL (módulos inexistentes).
- [ ] **Step 3:** Implementar. `TierBadge`: swatch 10×10 `bg-tier-{tier}` + texto; labels `{ local: "local", economy: "economy", frontier: "frontier", cache: "caché", denied: "denegado" }`. `PageHeader`: `<header class="grid border-b border-ink">` con título `h1` y celdas con `border-l border-line`, rótulo `text-xs text-ink-3` y valor `font-semibold`. `ErrorAlert`: `Alert variant="destructive"` con `error instanceof Error ? error.message : fallback`.
- [ ] **Step 4:** PASS. Commit `feat(console): add system components (page header, readout, figure, tier badge, states)`.

### Task 6: `DecisionPath`

**Files:**
- Create: `console/src/components/system/decision-path.tsx`, `decision-path.test.tsx`

**Interfaces — Produces:**
```ts
type DecisionStep = { tier: "local" | "economy"; p: number | null; tau: number | null };
DecisionPath({ steps: DecisionStep[]; chosen: "local" | "economy" | "frontier" | "cache" | "denied"; animate?: boolean })
```
Consume los datos que ya arma `components/playground/playground-decision.tsx` (p_local, p_economy, τ del punto vigente); leer ese archivo y `ledger-request-detail.tsx` para ver los campos reales de `route_signals`.

- [ ] **Step 1:** Test que falla: con `steps=[{tier:"local",p:0.41,tau:0.82},{tier:"economy",p:0.95,tau:0.92}]` y `chosen="economy"` el `role="img"` tiene `aria-label` "Decisión: local descartado (0.41 < 0.82), economy elegido (0.95 ≥ 0.92)"; no hay elementos focusables dentro; el texto `economy` aparece marcado (`data-chosen="true"`). Con `chosen="frontier"` y ambos p < τ → label termina en "frontier elegido". Con `p:null` → el paso muestra "sin dato" y el label lo dice.
- [ ] **Step 2:** FAIL.
- [ ] **Step 3:** Implementar el SVG (geometría del mockup `a-plano.html`, sección "Por qué economy"): tronco horizontal, una caja por paso con `p …`, comparación `< τ`/`≥ τ` en mono, rama elegida en `stroke-ink` 1.5 px y resto en `stroke-line`; nodo final con `bg-tier-*` + nombre. Animación: `stroke-dasharray`/`stroke-dashoffset` de 0 a longitud en 600 ms ease-out, solo si `animate` y `!matchMedia("(prefers-reduced-motion: reduce)").matches`.
- [ ] **Step 4:** Test adicional: con `matchMedia` mockeado a reduce, el path no tiene la clase `animate-path`. PASS. Commit `feat(console): add animated decision path`.

### Task 7: Reemplazar banners y modales duplicados

**Files:**
- Modify: los 11 archivos con `bg-danger-soft` (lista en Task 2 Step 3: playground, api-keys, observability, tenants, evaluacion, policy pages; admin-login-form, create-api-key-dialog, tenant-editor-drawer, apply-target, policy-form), `components/api-keys/{create,reveal}-api-key-dialog.tsx`, `app/(console)/api-keys/page.tsx`
- Delete: `console/src/lib/use-dialog-dismiss.ts` (si ya no tiene usos)
- Test: los `.test.tsx` vecinos

- [ ] **Step 1:** Cada banner de error → `<ErrorAlert error={…} fallback="…" />`; avisos ámbar → `<Alert>` variante `warning` (agregar la variante en `alert.tsx` con `bg-warn-soft border-warn-line text-warn`).
- [ ] **Step 2:** `CreateApiKeyDialog` y `RevealApiKeyDialog` → `Dialog`; revocar → `AlertDialog` con "Revocar {nombre}" en vez de `window.confirm`. Test nuevo en `api-key-table.test.tsx`/page test: clic en revocar abre alertdialog; confirmar llama a `revokeApiKey`; cancelar no.
- [ ] **Step 3:** Review Focus 2: en `evaluacion/page.test.tsx`, un 500 del endpoint muestra el mensaje del error, y un 404 muestra "No hay replay del router" (el 404 no se trata como "sin datos" si el status es otro). Ajustar `getRouterEvaluation` en `lib/admin-api.ts` para devolver `null` solo en 404 y lanzar en el resto.
- [ ] **Step 4:** vitest completo verde; commit `refactor(console): shared alerts and accessible dialogs`; push, PR "Fase 7b: componentes", CI, merge.

---

## PR (c) — Páginas

Branch: `fase7c-paginas`. En cada página: **shape** (leer el mockup y la sección de la spec; listar qué texto se borra), **implementar**, **captura** 1440 y 1280 (a `docs/superpowers/fase7/after/`), `/impeccable critique` y `/impeccable audit` sobre la página, **corregir**, commit con tests actualizados.

### Task 8: Valores del sistema, fuentes y shell

**Files:**
- Modify: `console/src/app/globals.css`, `console/src/app/layout.tsx`, `console/src/components/shell/operator-shell.tsx`, `console/src/app/(console)/layout.tsx`, `console/src/components/auth/{login-page-client,admin-login-form}.tsx`, `console/src/lib/admin-session-provider.tsx` (destino tras login)
- Test: `admin-login-form.test.tsx`, `admin-session-provider.test.tsx`, nuevo `operator-shell.test.tsx`

- [ ] **Step 1:** `@theme` a los valores de DESIGN.md: surface `#ffffff`, canvas/rail `#f3f4f5`, panel `#f3f4f5`, ink `#111418`, ink-2 `#4a525c`, ink-3 `#5c646e`, ink-4 `#5c646e`, line `#d3d8dd`, line-strong `#111418`, mark `#c62f1d`, mark-soft `#fbf1ef`, mark-line `#e9b9b2`, danger `#9f2616`, danger-soft `#fbf1ef`, danger-line `#e9b9b2`, warn `#7a4b00`, warn-soft `#fdf6e8`, warn-line `#ecd3a1`, ok `#1f5f32`, ok-soft `#eef6f0`, ok-line `#b9d8c1`, on-panel `#111418`, on-panel-2 `#4a525c`, tier-local `#86b6ef`, tier-economy `#2f73cc`, tier-frontier `#103f82`, tier-cache `#aab2bb`. Borrar el gradiente del `body` (`background: var(--color-surface)`); `::selection` con `color-mix(in srgb, var(--color-mark) 16%, transparent)`; scrollbars y `caret-color` desde roles; `font-variant-numeric: tabular-nums` en `body`.
- [ ] **Step 2:** `layout.tsx`: `next/font/google` Barlow (400–700) `--font-sans`, Barlow_Semi_Condensed (500, 600) `--font-label`, Red_Hat_Mono (400, 500) `--font-mono`; `lang="es"`; `metadata.title = "Nebula · consola"`. En `@theme`: `--font-sans`, `--font-label`, `--font-mono`. Reemplazar las 59 `font-[var(--font-fira-code)]` por nada (títulos en sans) o `font-mono` solo en ids/código.
- [ ] **Step 3:** Shell con `Sidebar` de shadcn: marca "Nebula" + "gateway local"; grupos "Operar" (Evaluación, Playground, Observabilidad) y "Configurar" (Tenants, Claves de API, Política); ítem activo `aria-current="page"`, fondo surface con líneas arriba/abajo y número de referencia en `text-mark`; pie "Sesión en memoria" + botón "Cerrar sesión". Por debajo de `lg`, `SidebarTrigger` en una barra superior. Test `operator-shell.test.tsx`: los 6 links con sus nombres en español, el activo con `aria-current`, "Cerrar sesión" llama a `signOut` y navega a `/?reason=signed_out`.
- [ ] **Step 4:** Login: una hoja centrada (máx. 440 px) con `PageHeader title="Nebula"` y celda "Consola del gateway"; `Field` "Clave de admin", placeholder `nb-admin-…`, ayuda "Se guarda solo en memoria: al recargar se cierra la sesión."; botón "Entrar"; mensajes: sesión vencida → "La sesión se cerró. Ingresar la clave de admin otra vez."; salida → "Sesión cerrada."; vacío → "Falta la clave de admin." Tras login, `router.replace("/evaluacion")`. Actualizar `admin-login-form.test.tsx` a estos textos y al destino `/evaluacion`.
- [ ] **Step 5:** Captura + critique/audit, corregir, vitest verde, commit `style(console): Plano system, fonts, shell and login`.

### Task 9: Evaluación

**Files:**
- Modify: `app/(console)/evaluacion/page.tsx`, `components/evaluation/{frontier-chart,quality-slider,tier-share-bar,replay-feed,apply-target,format}.tsx|ts`
- Test: `evaluacion/page.test.tsx`, `frontier-chart.test.tsx`, `replay-feed.test.tsx`

- [ ] **Step 1 (shape):** estructura del mockup A con préstamos de B: `PageHeader` (Evaluación del router · Router v1 · 3 niveles · Corpus {n} pedidos · Idiomas {es} es · {en} en · Sin red ni Ollama); **Tabla de características** a 0.95 (Parámetro · Condición · Valor · IC 95 %): ahorro vs todo frontier, ahorro vs mezcla aleatoria, calidad lograda, costo por 1000 pedidos, latencia mediana por modelo (condición = modelo, n del replay: `latency[k].n`); **Figura 1** frontera (grilla 10×10 tipo osciloscopio, punto elegido en `mark` con cruz de medición) + panel (Calidad objetivo con valor grande, slider, Readout costo/calidad/ahorro/umbrales, reparto por nivel, Aplicar); **Figura 2** replay acelerado; nota de datos (Dolly, GSM8K, MBPP) en una línea.
- [ ] **Step 2:** Diferidos fase 4 con tests: (i) ahorro vs aleatoria con costo aleatorio 0 o null → "—" y condición "sin mezcla comparable" (test con baselines forzados); (ii) etiqueta del punto heurístico "heurística v0 (base)"; (iii) latencia sin "30 prompts, secuencial" fijo: condición "{model} · n = {n}"; (iv) SVG: contenedor `role="group"` con `aria-label`, sin `role="img"` que envuelva focusables; tabla alternativa "Ver tabla" sigue; (v) barra de reparto: segmentos con `min-width` 2 px y etiquetas fuera de la barra (no se recortan).
- [ ] **Step 3:** Punto animado: al cambiar el objetivo, el punto y la cruz transicionan (`transition: cx,cy 250ms ease-out` vía CSS `transform` en un `<g>`), sin animación con reduced-motion.
- [ ] **Step 4:** Copy en español neutro; tests actualizados en el mismo commit. Captura + critique/audit + fix. Commit `style(console): evaluation as a characteristics sheet`.

### Task 10: Playground

**Files:**
- Modify: `app/(console)/playground/page.tsx`, `components/playground/*.tsx`
- Test: `components/playground/*.test.tsx`

- [ ] **Step 1 (shape):** `PageHeader` (Playground · Tenant [select] · Modelo [select] · "Sin streaming"); izquierda: `Field` prompt (textarea), botón "Enviar"; derecha: respuesta, **Por qué {nivel}** con `DecisionPath animate` (usa p/τ del registro del ledger), `Readout` (modelo, proveedor, costo, tokens, latencia, caché, fallback, request id en mono, headers `X-Nebula-*`). Sin párrafo introductorio; estado vacío "Enviar un prompt para ver la respuesta y la decisión."
- [ ] **Step 2:** Review Focus 3: test con un prompt de 2000 caracteres y un modelo largo: la respuesta envuelve (`overflow-wrap:anywhere`) y el Readout no desborda (clase presente).
- [ ] **Step 3:** Copy + tests; captura + critique/audit + fix; commit `style(console): playground with decision path`.

### Task 11: Observabilidad

**Files:**
- Modify: `app/(console)/observability/page.tsx` (partir en `components/observability/{recommendations,cache-summary,calibration-summary}.tsx`), `components/ledger/*.tsx`, `components/health/runtime-health-cards.tsx`
- Test: `observability/*.test.tsx`, `components/ledger/*.test.tsx`, `runtime-health-cards.test.tsx`

- [ ] **Step 1 (shape):** `PageHeader` con filtros como celdas (Tenant · Ruta · Estado · Desde · Hasta · "Actualizar"); **ledger** con columnas fijas (Hora · Pedido · Nivel · Modelo · Tokens · USD · Latencia · Estado), sin envolver, elipsis con `title`; fila seleccionada con `mark-soft` y barra interna de 2 px; **detalle** a la derecha: "Por qué {nivel}" con `DecisionPath`, `Readout`; debajo `Tabs`: Recomendaciones · Caché · Calibración · Dependencias, cada una con su contenido actual sin párrafos explicativos (máximo una línea de contexto).
- [ ] **Step 2:** Review Focus 1 y 2: ledger vacío → `EmptyState` "No hay pedidos en este rango." con acción "Abrir Playground"; error del ledger → `ErrorAlert`; `listTenants` falla → `ErrorAlert` en vez de "Sin tenants".
- [ ] **Step 3:** Copy + tests (son los más numerosos: actualizar `observability-page.test.tsx`, `page.test.tsx`, `ledger-*.test.tsx`); captura + critique/audit + fix; commit `style(console): observability ledger first, context in tabs`.

### Task 12: Política

**Files:**
- Modify: `app/(console)/policy/page.tsx`, `components/policy/{policy-form,policy-advanced-section,model-allowlist-input}.tsx` (partir `policy-form.tsx` en `policy-sections/{routing,limits,cache,models,advanced}.tsx` + `policy-preview.tsx`)
- Test: `components/policy/*.test.tsx`

- [ ] **Step 1 (shape):** `PageHeader` (Política · Tenant [select]); formulario a la izquierda en secciones con título y campos `Field` (Ruteo: objetivo de calidad, modo; Límites: pedidos por minuto, ráfaga, presupuesto; Caché: activado, umbral, antigüedad; Modelos permitidos; Avanzado); a la derecha, fija, **Vista previa**: botón "Simular", resultado (cambiados/sin cambio, muestra de pedidos) y "Guardar" deshabilitado hasta simular o con confirmación explícita (mantener la regla actual del formulario).
- [ ] **Step 2:** Cada help text largo se recorta a una línea o se mueve a `Tooltip` junto al label.
- [ ] **Step 3:** Copy + tests; captura + critique/audit + fix; commit `style(console): policy editor in sections with sticky preview`.

### Task 13: Tenants

**Files:** `app/(console)/tenants/page.tsx`, `components/tenants/{tenant-table,tenant-editor-drawer}.tsx` + tests.

- [ ] **Step 1:** `PageHeader` (Tenants · {n} activos · "Crear tenant"); búsqueda + filtro de estado en una fila; `Table` con Nombre · Id (mono) · Estado (Badge) · Creado; editor lateral con `Field`s y "Guardar"; estados vacío/error/carga con los componentes de sistema; nombres largos con elipsis.
- [ ] **Step 2:** Copy + tests; captura + critique/audit + fix; commit `style(console): tenants`.

### Task 14: Claves de API

**Files:** `app/(console)/api-keys/page.tsx`, `components/api-keys/*.tsx` + tests.

- [ ] **Step 1:** `PageHeader` (Claves de API · Tenant [select] · "Crear clave"); `Table` Nombre · Prefijo (mono) · Tenant por defecto · Tenants permitidos · Estado · Creada · acción Revocar; revocadas visibles con Badge "revocada"; Dialog crear; Dialog revelar (clave en mono sobre `canvas`, "Copiar"/"Copiada", aviso "No se vuelve a mostrar."); AlertDialog revocar.
- [ ] **Step 2:** Copy + tests; captura + critique/audit + fix; commit `style(console): api keys`.
- [ ] **Step 3:** vitest + tsc + eslint + `make test`; `impeccable detect --json console/src` sin hallazgos mecánicos; push, PR "Fase 7c: páginas", CI, merge.

---

## PR (d) — Cierre

Branch: `fase7d-cierre`.

### Task 15: e2e

**Files:** `console/e2e/*.spec.ts`

- [ ] **Step 1:** Correr `darwin-throttle npx playwright test --workers=2` y registrar fallas. Esperado: fallan observability/playground (selectores ambiguos, previo) y el resto por copy nuevo.
- [ ] **Step 2:** Reescribir selectores a roles accesibles con nombre exacto (`getByRole("row", { name: /b91e4d17/ })`, `getByRole("tab", { name: "Caché" })`, `exact: true`), textos en español y destino post-login `/evaluacion`.
- [ ] **Step 3:** Suite completa verde con 2 workers. Commit `test(console): fix ambiguous e2e selectors and follow the new copy`.

### Task 16: Capturas y tesis

**Files:** `docs/tfc/tesis/figuras/*.png`, `docs/tfc/tesis/figuras/README.md`, `docs/tfc/tesis/10-diseno.md`, `docs/tfc/tesis/11-implantacion.md`, `docs/tfc/tesis/00-indice.md` (si lista figuras)

- [ ] **Step 1:** Gateway con el router activo por entorno (bloque de tres niveles de `.env.example` exportado en el shell, `NEBULA_LEARNED_ROUTER_ENABLED=true`), `scripts/seed_demo_data.py`, tenant Acme Robotics con `routing_quality_target` 0.90 para que aparezcan los tres niveles; enviar los tres prompts del runbook desde el Playground.
- [ ] **Step 2:** Con `/browse` a 1440 (escala 2 para nitidez): `consola-evaluacion.png` (slider en 0.95), `consola-playground.png` (Por qué este nivel visible), `consola-observabilidad.png` (ledger con los tres niveles y el detalle), `consola-politica.png` (objetivo de calidad y límite de pedidos). Abrir cada una y verificar.
- [ ] **Step 3:** Reemplazar cada `> CAPTURA (fase 7): …` por:

```markdown
![Figura 10.5 — Edición de la política del tenant en la consola](figuras/consola-politica.png)

*Figura 10.5. Edición de la política del tenant: objetivo de calidad del router y límite de pedidos.*
```
numerando según el orden de aparición en cada capítulo (10.5 política en 10.2; 10.6 Evaluación y 10.7 Playground en 10.3; 11.2 observabilidad en 11.1, después de la 11.1 frontera ya existente — verificar numeración real leyendo los capítulos) y agregando la referencia en el párrafo ("como muestra la Figura 10.6, …"). Respetar [[feedback-tesis-redaccion]]: prosa de Joaquín, sin muletillas.
- [ ] **Step 4:** `figuras/README.md`: agregar filas y borrar "Capturas pendientes". `make thesis-tables` con `--check` verde.
- [ ] **Step 5:** Commit `docs(tesis): console screenshots as numbered figures`.

### Task 17: Design review, review independiente y merge

- [ ] **Step 1:** `/design-review` sobre la consola; reportar el puntaje de AI slop antes/después (antes = línea de base C+/B de julio y capturas de baseline).
- [ ] **Step 2:** Subagente opus con la spec, el plan y el diff de las fases 7a–7d: review de correctitud, a11y y fidelidad al DESIGN.md. Corregir lo confirmado.
- [ ] **Step 3:** Suites completas (una por vez, con darwin-throttle): `make test`, vitest, Playwright. Push, PR "Fase 7d: cierre", CI, merge.
- [ ] **Step 4:** Actualizar la memoria `tesis-fase7-consola-ui` con lo mergeado y diferidos.
