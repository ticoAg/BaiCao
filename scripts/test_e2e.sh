#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SESSION_NAME="${SESSION_NAME:-baicao-e2e}"
STARTED_LOCAL=0
TMP_DIR=""
API_PID=""
WEB_PID=""
API_BASE_URL="http://localhost:8000"
WEB_BASE_URL="http://localhost:3000"
LOCAL_API_PORT="${API_PORT:-8001}"
LOCAL_WEB_PORT="${WEB_PORT:-3001}"

load_repo_env() {
  local env_file
  for env_file in "$ROOT/infisical.defaults.env" "$ROOT/.env" "$ROOT/.env.local"; do
    if [[ -f "$env_file" ]]; then
      set -a
      # shellcheck disable=SC1090
      source "$env_file"
      set +a
    fi
  done
}

load_repo_env

export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://baicao:baicao_password@localhost:15433/baicao}"
export NEO4J_URI="${NEO4J_URI:-bolt://localhost:17687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-neo4j_password}"
export REDIS_URL="${REDIS_URL:-redis://localhost:16380}"

run_with_infisical() {
  uv run --directory "$ROOT/packages/api" python "$ROOT/scripts/infisical_env.py" run -- "$@"
}

wait_for_url() {
  local url="$1"
  local retries="${2:-60}"

  for _ in $(seq 1 "$retries"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  echo "Timed out waiting for $url" >&2
  return 1
}

wait_for_port() {
  local host="$1"
  local port="$2"
  local retries="${3:-60}"

  for _ in $(seq 1 "$retries"); do
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  echo "Timed out waiting for $host:$port" >&2
  return 1
}

start_ci_stack() {
  TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/baicao-e2e.XXXXXX")"
  local api_port="${API_PORT:-8001}"
  local web_port="${WEB_PORT:-3001}"

  API_BASE_URL="http://localhost:${api_port}"
  WEB_BASE_URL="http://localhost:${web_port}"
  export PLAYWRIGHT_BASE_URL="http://127.0.0.1:${web_port}"
  export WEB_API_BASE_URL="http://localhost:${api_port}"

  run_with_infisical docker compose -f "$ROOT/infra/docker-compose.yml" up -d postgres neo4j redis
  wait_for_port localhost 15433 120
  wait_for_port localhost 17687 120
  wait_for_port localhost 16380 120

  (
    cd "$ROOT/packages/api"
    run_with_infisical uv sync --extra dev
    run_with_infisical uv run python ../../scripts/seed_demo_data.py
    run_with_infisical uv run python -m uvicorn app.main:app --host 0.0.0.0 --port "$api_port"
  ) >"$TMP_DIR/api.log" 2>&1 &
  API_PID=$!

  (
    cd "$ROOT/packages/web"
    pnpm install
    run_with_infisical pnpm dev --host 0.0.0.0 --port "$web_port"
  ) >"$TMP_DIR/web.log" 2>&1 &
  WEB_PID=$!
}

if [ "${CI:-}" = "true" ]; then
  start_ci_stack
elif ! curl -fsS http://localhost:8000/health >/dev/null 2>&1 || ! curl -fsS http://localhost:3000 >/dev/null 2>&1; then
  API_BASE_URL="http://localhost:${LOCAL_API_PORT}"
  WEB_BASE_URL="http://localhost:${LOCAL_WEB_PORT}"
  export PLAYWRIGHT_BASE_URL="http://127.0.0.1:${LOCAL_WEB_PORT}"
  export WEB_API_BASE_URL="http://localhost:${LOCAL_API_PORT}"
  make -C "$ROOT" stack up SESSION="$SESSION_NAME" API_PORT="$LOCAL_API_PORT" WEB_PORT="$LOCAL_WEB_PORT" >/dev/null
  STARTED_LOCAL=1
fi

cleanup() {
  if [ -n "$API_PID" ] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [ -n "$WEB_PID" ] && kill -0 "$WEB_PID" 2>/dev/null; then
    kill "$WEB_PID" 2>/dev/null || true
  fi
  if [ "$STARTED_LOCAL" -eq 1 ]; then
    make -C "$ROOT" api down SESSION="$SESSION_NAME" API_PORT="$LOCAL_API_PORT" >/dev/null 2>&1 || true
    make -C "$ROOT" web down SESSION="$SESSION_NAME" WEB_PORT="$LOCAL_WEB_PORT" >/dev/null 2>&1 || true
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
  fi
  if [ -n "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

wait_for_url "${API_BASE_URL}/health" 120
wait_for_url "${WEB_BASE_URL}" 120

cd "$ROOT"
unset NO_COLOR
pnpm exec playwright install chromium >/dev/null
pnpm exec playwright test
