# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

1. **Jurado de ingeniería (primario).** Evalúa el Trabajo Final de Carrera de Joaquín (Ingeniería
   Informática, UB). Ve la consola en la demo en vivo y en las capturas del documento de tesis
   (Word, fondo blanco). Tiene que entender en segundos qué decidió el router, por qué y cuánto
   costó, sin leer párrafos.
2. **Operador de plataforma.** Administra un gateway self-hosted: da de alta tenants y claves,
   ajusta la política, audita el costo y las decisiones de ruteo pedido por pedido.

## Product Purpose

Nebula es un gateway de LLM self-hosted, compatible con la API de OpenAI, que baja el gasto
premium mandando cada pedido al nivel más barato que cumple un objetivo de calidad, y lo prueba
con evidencia por pedido (ledger persistido y headers `X-Nebula-*`). La consola es la cara
operable de eso: configurar, probar, auditar y evaluar.

Éxito: el jurado sale convencido de que el ruteo es inteligente, medido y controlable; el
operador encuentra cualquier decisión y su costo sin buscar.

## Positioning

Router aprendido de tres niveles (local / economy / frontier) que expone una frontera
costo–calidad operable: el operador elige la calidad con un slider, el router elige el punto de
operación más barato que la cumple y lo aplica al tenant (`routing_quality_target`). Cifra
anidada reportada: 31 % de ahorro contra todo-frontier a calidad 0.95.

## Operating Context

- Laptop, 1280–1440 px. Uso de escritorio; mobile no es prioridad.
- Sesión de admin solo en memoria: una recarga completa desloguea (decisión de diseño).
- Demo en vivo ante el jurado y capturas estáticas para la tesis.
- Datos reales del gateway local (tenant de demo `acme-demo`, "Acme Robotics") y del replay del
  router (`src/nebula/data/router_replay_v1.json`), que funciona sin red ni Ollama.

## Capabilities and Constraints

- Páginas: Tenants, API keys, Política, Playground, Observabilidad (ledger), Evaluación; login y
  navegación.
- Stack existente: Next.js 15, React 19, TypeScript, Tailwind; vitest y Playwright.
- Solo tema claro.
- Terminología de la tesis: tenant, ledger, playground, y los niveles local / economy / frontier
  quedan sin traducir.

## Brand Commitments

- Nombre: Nebula.
- Copy en español neutro, sin voseo: infinitivos o forma impersonal en acciones y etiquetas
  ("Crear tenant", "Aplicar a este tenant"), "tú" solo si hace falta dirigirse al usuario.
- **Poco texto.** Solo lo necesario: nada de párrafos explicativos grises en los encabezados,
  tooltips cortos, descripciones solo donde evitan un error. El dato habla.

## Evidence on Hand

- Replay del router y reportes en `benchmarks/router/v1/` (frontera, cifra anidada, IC 95 %).
- Ledger real del gateway local; semilla de demo en `scripts/seed_demo_data.py`.
- No inventar cifras, clientes ni testimonios: todo número visible sale del replay, los
  benchmarks o el ledger.

## Product Principles

1. **La evidencia primero.** Cada pantalla responde qué pasó, por qué y cuánto costó, con el
   número a la vista.
2. **Pocas palabras.** Si un texto no cambia lo que el usuario hace, se borra.
3. **Legible en una captura.** Cada vista clave se entiende en una imagen estática sobre fondo
   blanco, sin interacción.
4. **El operador decide.** Nada se guarda sin una acción explícita; las simulaciones se ven antes
   de aplicar.

## Accessibility & Inclusion

WCAG 2.1 AA: contraste de texto, foco visible, navegación por teclado, gráficos con alternativa
textual (tabla). Respetar `prefers-reduced-motion`.
