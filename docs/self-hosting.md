# Self-Hosting Nebula

Nebula Phase 1 supports one serious deployment path: a premium-first Docker Compose stack with the Nebula API, PostgreSQL, and Qdrant. PostgreSQL is the canonical governance store for self-hosted deployments.

## Supported Topology

- `nebula` serves the FastAPI gateway on port `8000`
- `postgres` is the canonical governance datastore for self-hosted runtime
- `qdrant` stores semantic cache vectors

## Deploy

1. Copy the environment template and set real secrets.

   ```bash
   cp deploy/selfhosted.env.example deploy/selfhosted.env
   ```

2. Edit `deploy/selfhosted.env` and replace these placeholders before startup:
   - `NEBULA_DATABASE_URL`
   - `NEBULA_RUNTIME_PROFILE=premium_first`
   - `NEBULA_PREMIUM_API_KEY`
   - `NEBULA_ADMIN_API_KEY`
   - `NEBULA_BOOTSTRAP_API_KEY`

3. Start the supported stack.

   ```bash
   docker compose -f docker-compose.selfhosted.yml up -d
   ```

   The `nebula` container runs `alembic upgrade head` before starting `uvicorn`, so the governance schema is migrated on every boot.

4. Verify the API is alive.

   ```bash
   curl http://localhost:8000/health
   ```

5. Verify readiness and dependency detail before sending traffic.

   ```bash
   curl http://localhost:8000/health/ready
   curl http://localhost:8000/health/dependencies
   ```

## Notes

- This is the only supported self-hosted path for Phase 1.
- `NEBULA_PREMIUM_PROVIDER=openai_compatible` is the intended production-facing configuration.
- `NEBULA_RUNTIME_PROFILE=premium_first` is required outside local development.
- `NEBULA_DATABASE_URL` should target PostgreSQL for the supported self-hosted runtime.
- Local Ollama remains optional and is configured as an advanced optimization path, not a deployment prerequisite.
- A `degraded` readiness state means Nebula can still serve traffic while optional dependencies such as Qdrant or local Ollama are unavailable.
