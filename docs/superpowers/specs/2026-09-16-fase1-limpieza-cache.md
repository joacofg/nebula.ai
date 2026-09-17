# Spec — Fase 1: limpieza del repo y caché semántico por tenant

Origen: sesión de grilling 2026-09-16 (decisiones en memoria `tesis-10x-decisiones-2026-09`).
Nebula es el Trabajo Final de Carrera de Joaquín (UB, Ing. Informática). Prioridad: rigor > demo > features > ingeniería.

## Objetivo

Dejar el repo con únicamente lo que entra en la tesis (gateway self-hosted v1.0 + v3.0 embeddings + estudio de métrica) y corregir el defecto más serio del serving path: el caché semántico no distingue tenants y los knobs de política del caché (umbral y TTL por tenant) no están conectados a nada.

## Alcance

### A. Borrar el hosted control plane (v2.0) por completo
- Backend: enrollment, heartbeat, remote management, modelos `deployment`/`heartbeat`/`hosted_contract`, tablas `deployments`, `enrollment_tokens`, `deployment_remote_actions`, `local_hosted_identity`, settings `NEBULA_ENROLLMENT_TOKEN`, `NEBULA_HOSTED_PLANE_URL`, `NEBULA_REMOTE_MANAGEMENT_*`.
- Consola: páginas `/deployments` y `/trust-boundary`, componentes `deployments/` y `hosted/`, `lib/hosted-contract.ts`, `lib/freshness.ts`, e2e `deployments-proof` y `trust-boundary`, funciones y tipos hosted de `admin-api.ts`.
- Docs: `docs/hosted-default-export.schema.json`, secciones "Hosted control plane" (README) y "Hybrid trust boundary" (architecture), `.planning/` completo, sección "v2.0 Context" de CLAUDE.md.
- Tests: los 8 archivos de test hosted + los 2 tests hosted de `test_phase10_outage_safety.py`.

### B. Colapsar migraciones Alembic
Una sola migración inicial `20260916_0001_initial_schema` derivada de `Base.metadata`. Rompe bases existentes: aceptado (proyecto solo para la tesis). El tenant demo se recrea con `scripts/seed_demo_data.py`.

### C. Caché semántico correcto
- Cada punto en Qdrant lleva `tenant_id`; `lookup` filtra por `tenant_id` del tenant autenticado. Nunca una respuesta cruza tenants.
- `lookup` aplica el umbral de similitud **de la política del tenant** (`semantic_cache_similarity_threshold`) y descarta entradas más viejas que `semantic_cache_max_entry_age_hours` (filtro por `created_at`). Los dos knobs de la consola pasan a estar conectados.
- `lookup` devuelve el score de similitud; el score se persiste en `route_signals` del ledger (`cache_similarity_score`) para poder analizarlo en la fase 2.
- Se eliminan las settings muertas `NEBULA_ROUTER_COMPLEXITY_CHARS` y `NEBULA_SEMANTIC_CACHE_THRESHOLD` (el umbral vive en la política por tenant).

### D. Artefactos de benchmark
`artifacts/` está gitignored: las 23 corridas son locales. Las cinco corridas citadas (golden `20260314T193127Z`, las tres del 2026-08-19 que anclan 38.2/40.0/41.2 %, y la degradada `20260903T143128Z` como ejemplo del banner NOT COMPARABLE) se mueven a `benchmarks/results/` **trackeado**, con un `README.md` índice. El resto se borra.

### E. Esqueleto de la tesis
`docs/tfc/tesis/` con capítulos en Markdown y español, con marcadores de qué se llena en cada fase. `docs/tfc/*.docx` y `docs/tfc/assets/` quedan gitignored; el Markdown se trackea.

## Fuera de alcance (fases siguientes)
- Cambiar el modelo local a qwen2.5:7b (fase 2, cuando se mida).
- Prefijo `search_document` en embeddings (fase 2, cuando exista corpus para medir el efecto).
- Router aprendido, tres niveles, catálogo (fase 3). Consola/WOW (fase 4). Rate limiting (fase 5).
- Deuda de ingeniería general (cobertura, ruff ampliado, split de `chat_service.py`).

## Criterios de aceptación
1. `make lint`, `make test`, `npx tsc --noEmit`, `npm run lint`, `npm run test -- --run` verdes.
2. `grep -rniE "enrollment|heartbeat|remote_management|hosted|deployment" src console/src docs README.md CLAUDE.md` no devuelve nada salvo la palabra "self-hosted".
3. Test que demuestra que un `lookup` del tenant B no ve lo que guardó el tenant A, y que el umbral y el TTL usados son los de la política del tenant.
4. Una sola migración en `migrations/versions/`; `make migrate` sobre una base vacía crea el esquema completo; `scripts/seed_demo_data.py` funciona.
5. La demo del profesor (`docs/demo-runbook.md`) sigue funcionando.
