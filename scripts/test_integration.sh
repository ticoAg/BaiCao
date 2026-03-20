#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_DIR="$ROOT/packages/api"

export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://baicao:baicao_password@localhost:15433/baicao}"
export NEO4J_URI="${NEO4J_URI:-bolt://localhost:17687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-neo4j_password}"
export REDIS_URL="${REDIS_URL:-redis://localhost:16380}"

has_integration_tests() {
  rg -l \
    --glob 'tests/**/*.py' \
    'pytest\.mark\.integration|pytestmark\s*=\s*pytest\.mark\.integration' \
    "$API_DIR" >/dev/null 2>&1
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

docker compose -f "$ROOT/infra/docker-compose.yml" up -d postgres neo4j redis
wait_for_port localhost 15433 120
wait_for_port localhost 17687 120
wait_for_port localhost 16380 120

cd "$API_DIR"
uv sync --extra dev

if ! has_integration_tests; then
  echo "No integration tests collected yet; skipping packages/api integration suite."
  exit 0
fi

uv run python ../../scripts/seed_demo_data.py
uv run python -m pytest -q -m integration
