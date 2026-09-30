#!/usr/bin/env bash
# One command for the defense demo: `make demo`.
# Checks Ollama, Docker and the premium key, starts Qdrant, resets the semantic cache, starts the
# gateway with the learned router (via env vars, never .env: the test suite reads .env), prepares
# the demo tenant, starts the console in production mode and opens the browser. Ctrl-C stops it all.
set -uo pipefail
cd "$(dirname "$0")/.."

LOGS=.nebula/demo
mkdir -p "$LOGS"
OLLAMA=http://localhost:11434
QDRANT=http://localhost:6333
CACHE_COLLECTION=nebula-semantic-cache
ADMIN_KEY=nebula-admin-key

step() { printf '\n\033[1m▸ %s\033[0m\n' "$*"; }
ok() { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
fail() {
  printf '\n  \033[31m✗ %s\033[0m\n\n' "$*"
  exit 1
}

# Wait until a URL answers 2xx, up to $2 seconds.
wait_for() {
  local url=$1 seconds=$2
  for _ in $(seq 1 "$seconds"); do
    curl -sf -o /dev/null "$url" && return 0
    sleep 1
  done
  return 1
}

# Stop an earlier Nebula gateway or console on a port; refuse to touch anything else.
free_port() {
  local port=$1 pid cmd
  for pid in $(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null); do
    cmd=$(ps -o command= -p "$pid")
    case "$cmd" in
      *nebula.main* | *next-server* | *next\ dev* | *next\ start* | *multiprocessing*) kill "$pid" 2>/dev/null ;;
      *) fail "El puerto $port lo usa otro programa: $cmd" ;;
    esac
  done
  pkill -f "uvicorn nebula.main" 2>/dev/null || true
  for _ in $(seq 1 10); do
    lsof -ti "tcp:$port" -sTCP:LISTEN >/dev/null 2>&1 || return 0
    sleep 1
  done
  fail "No se pudo liberar el puerto $port."
}

GATEWAY_PID=""
CONSOLE_PID=""
stop_all() {
  printf '\n\033[1m▸ Apagando la demo\033[0m\n'
  [ -n "$CONSOLE_PID" ] && kill "$CONSOLE_PID" 2>/dev/null
  [ -n "$GATEWAY_PID" ] && kill "$GATEWAY_PID" 2>/dev/null
  wait 2>/dev/null
  ok "Gateway y consola detenidos (Qdrant sigue en Docker)."
  exit 0
}

step "Chequeos"
[ -x .venv/bin/uvicorn ] || fail "Falta el entorno de Python: corré 'make setup'."
[ -d console/node_modules ] || fail "Faltan las dependencias de la consola: corré 'make console-install'."
curl -sf -o /dev/null "$OLLAMA/api/tags" || fail "Ollama no responde: abrí la app de Ollama (o 'ollama serve')."
tags=$(curl -s "$OLLAMA/api/tags")
for model in qwen2.5:7b nomic-embed-text; do
  grep -q "\"$model" <<<"$tags" || fail "Ollama no tiene $model: corré 'ollama pull $model'."
done
ok "Ollama con qwen2.5:7b y nomic-embed-text"
docker info >/dev/null 2>&1 || fail "Docker no está corriendo: abrí Docker Desktop."
ok "Docker"
premium_key=$(grep -E '^NEBULA_PREMIUM_API_KEY=' .env 2>/dev/null | cut -d= -f2-)
[ -n "$premium_key" ] || fail "Falta NEBULA_PREMIUM_API_KEY en .env."
credits=$(curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $premium_key" |
  .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin)["data"]; print(f"{d["total_credits"]-d["total_usage"]:.2f}")' 2>/dev/null)
if [ -z "$credits" ]; then
  warn "No se pudo leer el saldo de OpenRouter (¿sin red?). Premium puede fallar."
elif .venv/bin/python -c "import sys; sys.exit(0 if float('$credits') >= 1 else 1)"; then
  ok "OpenRouter: USD $credits de saldo"
else
  warn "OpenRouter: solo USD $credits de saldo. Cargá crédito o premium va a fallar."
fi

step "Liberando puertos 8000 y 3000"
free_port 8000
free_port 3000
ok "Puertos libres"

step "Qdrant y caché semántica"
docker compose up -d qdrant >"$LOGS/qdrant.log" 2>&1 || fail "No arrancó Qdrant (ver $LOGS/qdrant.log)."
wait_for "$QDRANT/readyz" 30 || fail "Qdrant no respondió en 30 s."
curl -s -o /dev/null -X DELETE "$QDRANT/collections/$CACHE_COLLECTION"
ok "Qdrant listo, caché vacía"

step "Gateway con el router aprendido"
.venv/bin/alembic upgrade head >"$LOGS/migrate.log" 2>&1 || fail "Falló la migración (ver $LOGS/migrate.log)."
trap stop_all INT TERM
NEBULA_LOCAL_MODEL=qwen2.5:7b \
  NEBULA_PREMIUM_PROVIDER=openai_compatible \
  NEBULA_PREMIUM_MODEL=openai/gpt-4.1 \
  NEBULA_ECONOMY_MODEL=anthropic/claude-haiku-4.5 \
  NEBULA_LEARNED_ROUTER_ENABLED=true \
  .venv/bin/uvicorn nebula.main:app --port 8000 >"$LOGS/gateway.log" 2>&1 &
GATEWAY_PID=$!
wait_for http://localhost:8000/health/ready 60 || {
  tail -20 "$LOGS/gateway.log"
  fail "El gateway no quedó listo (log completo en $LOGS/gateway.log)."
}
ok "Gateway en http://localhost:8000"

step "Tenant de demo y modelo local"
.venv/bin/python -m scripts.demo_prepare 2>&1 | sed 's/^/  /' || fail "No se pudo preparar el tenant de demo."

step "Consola"
if [ ! -f console/.next/BUILD_ID ] || [ -n "$(find console/src console/next.config.ts console/package.json -newer console/.next/BUILD_ID -print -quit)" ]; then
  echo "  compilando la consola (una vez, ~1 min)…"
  npm --prefix console run build >"$LOGS/console-build.log" 2>&1 || fail "Falló el build de la consola (ver $LOGS/console-build.log)."
fi
# The console builds as standalone (like the Docker image): its server needs the static assets beside it.
rm -rf console/.next/standalone/.next/static
cp -R console/.next/static console/.next/standalone/.next/static
(cd console/.next/standalone && PORT=3000 HOSTNAME=127.0.0.1 exec node server.js) >"$LOGS/console.log" 2>&1 &
CONSOLE_PID=$!
wait_for http://127.0.0.1:3000 60 || fail "La consola no respondió (ver $LOGS/console.log)."
ok "Consola en http://localhost:3000"

open http://localhost:3000 2>/dev/null || true

cat <<EOF

  ┌──────────────────────────────────────────────────────────────┐
  │  Nebula lista para la demo                                   │
  │                                                              │
  │  Consola    http://localhost:3000                            │
  │  Clave      $ADMIN_KEY                                 │
  │  Tenant     Acme Robotics · objetivo 0.90                    │
  │                                                              │
  │  Playground (Ejemplos):                                      │
  │    Capital de Australia   →  local                           │
  │    Boletos de avión       →  economy                         │
  │    Criba de Eratóstenes   →  frontier                        │
  │    repetir cualquiera     →  caché                           │
  │                                                              │
  │  · No recargues la pestaña: la sesión vive en memoria.       │
  │  · Mostrá los tres niveles antes de mover el objetivo.       │
  │  · Ctrl-C acá apaga todo. Logs en .nebula/demo/              │
  └──────────────────────────────────────────────────────────────┘

EOF

wait
