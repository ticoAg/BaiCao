#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_DIR="$ROOT/packages/api"

export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://baicao:baicao_password@localhost:15433/baicao}"
export NEO4J_URI="${NEO4J_URI:-bolt://localhost:17687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-neo4j_password}"
export REDIS_URL="${REDIS_URL:-redis://localhost:16380}"
export OBJECT_STORAGE_ENDPOINT="${OBJECT_STORAGE_ENDPOINT:-localhost:19000}"
export OBJECT_STORAGE_ACCESS_KEY="${OBJECT_STORAGE_ACCESS_KEY:-minioadmin}"
export OBJECT_STORAGE_SECRET_KEY="${OBJECT_STORAGE_SECRET_KEY:-minioadmin}"
export OBJECT_STORAGE_BUCKET="${OBJECT_STORAGE_BUCKET:-baicao-pipeline-exports}"
export OBJECT_STORAGE_SECURE="${OBJECT_STORAGE_SECURE:-false}"

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

wait_for_health() {
  local container="$1"
  local retries="${2:-120}"

  for _ in $(seq 1 "$retries"); do
    local status
    status="$(docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null || true)"
    if [[ "$status" == "healthy" ]]; then
      return 0
    fi
    sleep 1
  done

  echo "Timed out waiting for healthy container: $container" >&2
  return 1
}

wait_for_neo4j_bolt() {
  local retries="${1:-60}"

  for _ in $(seq 1 "$retries"); do
    if uv run python - <<'PY' >/dev/null 2>&1
import asyncio
from neo4j import AsyncGraphDatabase

async def main():
    driver = AsyncGraphDatabase.driver("bolt://localhost:17687", auth=("neo4j", "neo4j_password"))
    try:
        await driver.verify_connectivity()
    finally:
        await driver.close()

asyncio.run(main())
PY
    then
      return 0
    fi
    sleep 1
  done

  echo "Timed out waiting for Neo4j Bolt connectivity" >&2
  return 1
}

# 集成脚本需要从干净卷启动，避免旧 schema 让 create_all 无法补齐字段。
docker compose -f "$ROOT/infra/docker-compose.yml" down -v --remove-orphans >/dev/null 2>&1 || true
docker compose -f "$ROOT/infra/docker-compose.yml" up -d postgres neo4j redis minio
wait_for_port localhost 15433 120
wait_for_port localhost 17687 120
wait_for_port localhost 16380 120
wait_for_port localhost 19000 120
wait_for_health baicao-postgres 120
wait_for_health baicao-neo4j 120
wait_for_health baicao-redis 120
wait_for_health baicao-minio 120

cd "$API_DIR"
uv sync --extra dev
wait_for_neo4j_bolt 120

if ! has_integration_tests; then
  echo "No integration tests collected yet; skipping packages/api integration suite."
  exit 0
fi

uv run python ../../scripts/seed_demo_data.py
uv run python -m pytest -q -m integration
