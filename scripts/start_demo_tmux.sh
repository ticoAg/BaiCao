#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SESSION_NAME="${1:-baicao-demo}"
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://baicao:baicao_password@localhost:15433/baicao}"
export NEO4J_URI="${NEO4J_URI:-bolt://localhost:17687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-neo4j_password}"
export REDIS_URL="${REDIS_URL:-redis://localhost:16380}"

API_COMMAND="cd '$ROOT/packages/api' && export DATABASE_URL='$DATABASE_URL' NEO4J_URI='$NEO4J_URI' NEO4J_USER='$NEO4J_USER' NEO4J_PASSWORD='$NEO4J_PASSWORD' REDIS_URL='$REDIS_URL' && uv sync --extra dev && uv run python ../../scripts/seed_demo_data.py && uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
WEB_COMMAND="cd '$ROOT/packages/web' && pnpm install && pnpm dev --host 0.0.0.0 --port 3000"

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

cd "$ROOT"

docker compose -f infra/docker-compose.yml up -d postgres neo4j redis
wait_for_port localhost 15433 120
wait_for_port localhost 17687 120
wait_for_port localhost 16380 120

tmux has-session -t "$SESSION_NAME" 2>/dev/null && tmux kill-session -t "$SESSION_NAME"

tmux new-session -d -s "$SESSION_NAME" -n api \
  "$API_COMMAND"

tmux new-window -t "$SESSION_NAME" -n web \
  "$WEB_COMMAND"

echo "tmux session started: $SESSION_NAME"
echo "attach: tmux attach -t $SESSION_NAME"
echo "web: http://localhost:3000"
echo "api: http://localhost:8000/health"
