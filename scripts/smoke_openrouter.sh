#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
VENV_UVICORN="$ROOT_DIR/.venv/bin/uvicorn"
PORT="${PORT:-8000}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${PORT}}"
MODE="${MODE:-premium}"
SERVER_PID=""
LOG_FILE="$(mktemp)"

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -f "$LOG_FILE"
}

trap cleanup EXIT

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    exit 1
  fi
}

wait_for_health() {
  for _ in $(seq 1 40); do
    if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  echo "Nebula did not become healthy at $BASE_URL" >&2
  cat "$LOG_FILE" >&2
  exit 1
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  if [[ "$haystack" != *"$needle"* ]]; then
    echo "Expected response to contain: $needle" >&2
    echo "$haystack" >&2
    exit 1
  fi
}

require_file "$ROOT_DIR/.env"
require_file "$VENV_PYTHON"
require_file "$VENV_UVICORN"

PREMIUM_MODEL="$("$VENV_PYTHON" - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))
from nebula.core.config import get_settings
print(get_settings().premium_model)
PY
)"

PREMIUM_PROVIDER="$("$VENV_PYTHON" - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))
from nebula.core.config import get_settings
print(get_settings().premium_provider)
PY
)"

if [[ "$PREMIUM_PROVIDER" != "openai_compatible" ]]; then
  echo "Expected NEBULA_PREMIUM_PROVIDER=openai_compatible in .env" >&2
  exit 1
fi

SERVER_ENV=()
if [[ "$MODE" == "fallback" ]]; then
  SERVER_ENV+=(NEBULA_OLLAMA_BASE_URL=http://127.0.0.1:9)
fi

(
  cd "$ROOT_DIR"
  if [[ "${#SERVER_ENV[@]}" -gt 0 ]]; then
    env "${SERVER_ENV[@]}" "$VENV_UVICORN" nebula.main:app --host 127.0.0.1 --port "$PORT"
  else
    "$VENV_UVICORN" nebula.main:app --host 127.0.0.1 --port "$PORT"
  fi
) >"$LOG_FILE" 2>&1 &
SERVER_PID=$!

wait_for_health

HEALTH_RESPONSE="$(curl -fsS "$BASE_URL/health")"
assert_contains "$HEALTH_RESPONSE" '"status":"ok"'

PREMIUM_RESPONSE="$(curl -fsS "$BASE_URL/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$PREMIUM_MODEL\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Reply with the word premium.\"}]
  }")"
assert_contains "$PREMIUM_RESPONSE" '"object":"chat.completion"'
assert_contains "$PREMIUM_RESPONSE" '"role":"assistant"'

STREAM_RESPONSE="$(curl -fsS "$BASE_URL/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -d "{
    \"model\": \"$PREMIUM_MODEL\",
    \"stream\": true,
    \"messages\": [{\"role\": \"user\", \"content\": \"Reply with two short words.\"}]
  }")"
assert_contains "$STREAM_RESPONSE" 'chat.completion.chunk'
assert_contains "$STREAM_RESPONSE" '[DONE]'

if [[ "$MODE" == "fallback" ]]; then
  FALLBACK_RESPONSE="$(curl -fsS "$BASE_URL/v1/chat/completions" \
    -H 'Content-Type: application/json' \
    -d '{
      "model": "nebula-auto",
      "messages": [{"role": "user", "content": "hello"}]
    }')"
  assert_contains "$FALLBACK_RESPONSE" '"object":"chat.completion"'
  assert_contains "$FALLBACK_RESPONSE" '"role":"assistant"'
fi

echo "Smoke test passed (mode=$MODE, premium_model=$PREMIUM_MODEL)"
