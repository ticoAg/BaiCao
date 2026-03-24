#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT/packages/api"
uv sync --extra dev
uv run ruff check app tests
uv run ty check
uv run pytest -m "not integration"
