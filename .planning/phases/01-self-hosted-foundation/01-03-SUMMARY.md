---
phase: 01-self-hosted-foundation
plan: "03"
subsystem: database
tags: [sqlalchemy, alembic, postgres, sqlite, migrations]
requires:
  - phase: 01-self-hosted-foundation
    provides: Runtime guardrails and readiness endpoints for self-hosted deployments
provides:
  - Migration-backed governance persistence through SQLAlchemy and Alembic
  - Database URL configuration for Postgres self-hosting and SQLite local development
  - Self-hosted operations that run migrations before API startup
affects: [deployment, persistence, testing]
tech-stack:
  added: [sqlalchemy, alembic, psycopg]
  patterns: [database URL configuration, migration-backed startup, brownfield-safe baseline migration]
key-files:
  created: [alembic.ini, migrations/env.py, migrations/versions/20260315_0001_governance_baseline.py, src/nebula/db/models.py, src/nebula/db/session.py]
  modified: [pyproject.toml, src/nebula/core/config.py, src/nebula/core/container.py, src/nebula/services/governance_store.py, tests/support.py, Makefile, docker-compose.selfhosted.yml, deploy/selfhosted.env.example, docs/self-hosting.md, README.md]
key-decisions:
  - "NEBULA_DATABASE_URL is the primary persistence setting for self-hosted runtime, with SQLite retained only as the local fallback."
  - "The baseline Alembic migration must safely adopt an existing bootstrap-created SQLite schema instead of assuming a pristine database."
patterns-established:
  - "Governance storage uses a session factory plus SQLAlchemy models instead of inline sqlite3 DDL."
  - "Self-hosted startup runs Alembic before uvicorn so schema state is explicit and repeatable."
requirements-completed: [PLAT-03]
duration: 2min
completed: 2026-03-15
---

# Phase 01: Self-Hosted Foundation Summary

**Migration-backed governance persistence with PostgreSQL-first self-hosted startup and SQLite-compatible local development**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-15T23:41:03Z
- **Completed:** 2026-03-15T23:42:49Z
- **Tasks:** 3
- **Files modified:** 15

## Accomplishments
- Added SQLAlchemy, Alembic, and psycopg plus a baseline governance migration.
- Replaced runtime schema creation with a migrated, session-backed governance store.
- Wired migrations into the operator workflow through Make targets, Compose startup, and Postgres-first documentation.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the database URL and Alembic migration scaffold** - `9af1a7b` (chore)
2. **Task 2: Refactor governance persistence to rely on migrated schema instead of runtime DDL** - `0f8a302` (feat)
3. **Task 3: Wire migrations into the operator workflow and self-hosted runtime** - `516cd5a` (docs)

## Files Created/Modified
- `pyproject.toml` - Adds runtime migration and database dependencies.
- `alembic.ini` - Configures the Alembic CLI for the repo.
- `migrations/env.py` - Resolves the active database URL for online and offline migrations.
- `migrations/versions/20260315_0001_governance_baseline.py` - Defines the baseline governance schema migration.
- `src/nebula/db/models.py` - Defines the governance SQLAlchemy models.
- `src/nebula/db/session.py` - Builds the database engine and session factory from settings.
- `src/nebula/services/governance_store.py` - Uses migrated SQLAlchemy sessions instead of runtime `CREATE TABLE` DDL.
- `tests/support.py` - Migrates temporary test databases before app startup.
- `Makefile` - Adds `migrate` and `migrate-create`.
- `docker-compose.selfhosted.yml` - Runs `alembic upgrade head` before the API starts.
- `deploy/selfhosted.env.example` - Documents the canonical Postgres database URL.
- `docs/self-hosting.md` - Documents Postgres and the migration workflow for operators.
- `README.md` - Points self-hosted readers at the migration-backed deployment path.

## Decisions Made
- Promoted `NEBULA_DATABASE_URL` to the primary persistence surface so the self-hosted runtime can target PostgreSQL explicitly while local development stays on SQLite through the same migration workflow.
- Kept the baseline migration brownfield-safe so existing local SQLite databases can be adopted by Alembic without manual cleanup.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Made the baseline migration adopt existing bootstrap-created schemas**
- **Found during:** Task 1 (Add the database URL and Alembic migration scaffold)
- **Issue:** `alembic upgrade head` initially failed against the pre-existing local SQLite database because the legacy bootstrap tables already existed.
- **Fix:** Updated the baseline migration to create tables and the usage-ledger index only when they are missing, allowing Alembic to stamp and adopt the brownfield schema.
- **Files modified:** `migrations/versions/20260315_0001_governance_baseline.py`, `alembic.ini`
- **Verification:** `./.venv/bin/alembic upgrade head`
- **Committed in:** `9af1a7b` (completed by follow-up edit before final verification)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The migration workflow now works for both fresh databases and the repo’s existing bootstrap SQLite state. No feature scope changed.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 1 now has a credible self-hosted deployment path, explicit runtime safety rules, and durable persistence with migrations.
- The remaining phase step is phase-goal verification, including the real deployment checks that require a live premium provider key and Docker host.

---
*Phase: 01-self-hosted-foundation*
*Completed: 2026-03-15*
