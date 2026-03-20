#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT/packages/api"
uv sync --extra dev
uv run python -m pytest -q -m "unit or contract"
