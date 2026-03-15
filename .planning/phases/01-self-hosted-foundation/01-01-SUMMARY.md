---
phase: 01-self-hosted-foundation
plan: "01"
subsystem: infra
tags: [docker, compose, self-hosting, postgres, qdrant]
requires: []
provides:
  - Canonical Docker image for the Nebula API
  - Premium-first self-hosted Compose topology with Nebula, PostgreSQL, and Qdrant
  - Operator runbook and env template for the supported deployment path
  - Makefile helpers for self-hosted stack operations
affects: [deployment, docs, operations]
tech-stack:
  added: [docker, docker-compose]
  patterns: [premium-first self-hosted topology, single-path deployment documentation]
key-files:
  created: [Dockerfile, .dockerignore, docker-compose.selfhosted.yml, deploy/selfhosted.env.example, docs/self-hosting.md]
  modified: [README.md, Makefile]
key-decisions:
  - "Docker Compose is the single supported self-hosted entrypoint for Phase 1."
  - "The canonical runtime topology is Nebula plus PostgreSQL and Qdrant, with local Ollama kept optional."
patterns-established:
  - "Deployment docs live in docs/self-hosting.md and the README points there instead of duplicating flow."
  - "Operator-facing stack commands are exposed through dedicated selfhost-* Makefile targets."
requirements-completed: [PLAT-01]
duration: 2min
completed: 2026-03-15
---

# Phase 01: Self-Hosted Foundation Summary

**Premium-first self-hosted packaging with a canonical Nebula, PostgreSQL, and Qdrant Compose stack**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-15T23:25:12Z
- **Completed:** 2026-03-15T23:27:07Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Added a runnable Docker image and self-hosted Compose topology for Nebula, PostgreSQL, and Qdrant.
- Created the operator-facing env template and runbook for the supported premium-first deployment path.
- Exposed the self-hosted workflow through named Makefile helpers without changing the local-dev commands.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the canonical container and self-hosted compose topology** - `f63b075` (feat)
2. **Task 2: Add a dedicated self-hosted environment template and deployment runbook** - `488ea12` (docs)
3. **Task 3: Expose the self-hosted workflow through Makefile helpers** - `72f305b` (feat)

## Files Created/Modified
- `Dockerfile` - Builds the FastAPI application image and starts `uvicorn` on port 8000.
- `.dockerignore` - Excludes local state and cache directories from the container build context.
- `docker-compose.selfhosted.yml` - Defines the supported Nebula, PostgreSQL, and Qdrant topology.
- `deploy/selfhosted.env.example` - Provides the premium-first runtime template and bootstrap secrets placeholders.
- `docs/self-hosting.md` - Documents the supported self-hosted deployment and verification path.
- `README.md` - Routes deployment readers to the dedicated self-hosting runbook.
- `Makefile` - Adds `selfhost-up`, `selfhost-down`, and `selfhost-logs` helpers.

## Decisions Made
- Kept Docker Compose as the only supported self-hosted entrypoint for this phase so operators have one clear runtime story.
- Positioned PostgreSQL and Qdrant as always-on deployment dependencies while keeping Ollama documented as optional optimization only.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added a temporary env-file placeholder during topology bring-up**
- **Found during:** Task 1 (Create the canonical container and self-hosted compose topology)
- **Issue:** `docker compose -f docker-compose.selfhosted.yml config` would fail before Task 2 because the referenced `deploy/selfhosted.env.example` file did not exist yet.
- **Fix:** Added the env file as a minimal placeholder in Task 1 so Compose verification could run, then replaced it with the real deployment template in Task 2.
- **Files modified:** `deploy/selfhosted.env.example`
- **Verification:** `docker compose -f docker-compose.selfhosted.yml config`
- **Committed in:** `f63b075` (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The fix kept the plan order intact and avoided a false-negative verification failure. No scope change.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- The repo now has a concrete self-hosted deployment surface for runtime hardening work.
- Phase 01-02 can layer runtime-profile validation and health/readiness endpoints on top of the new operator path.

---
*Phase: 01-self-hosted-foundation*
*Completed: 2026-03-15*
