#!/bin/bash
# BaiCao 本地开发启动脚本（使用 tmux）
# 依赖 Docker 中的数据库服务（postgres/redis/neo4j）
# 用法: ./scripts/dev-tmux.sh

set -e

# 端口配置（与 docker-compose.yml 一致）
export DATABASE_URL="postgresql+asyncpg://baicao:baicao_password@localhost:15433/baicao"
export DATABASE_PORT="15433"
export NEO4J_URI="bolt://localhost:17687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="neo4j_password"
export REDIS_URL="redis://localhost:16380"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"

# API 端口
export API_PORT="${API_PORT:-8000}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$PROJECT_ROOT/packages/api"
WEB_DIR="$PROJECT_ROOT/packages/web"

# 创建 tmux session
SESSION="baicao-dev"

# 如果已存在则分离并删除
tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION" 2>/dev/null || true

# 新建 session，window 0
tmux new-session -d -s "$SESSION" -n "api"

# 窗口 1: API
tmux send-keys -t "$SESSION:0" "cd $API_DIR && uv run uvicorn app.main:app --host 0.0.0.0 --port $API_PORT --reload" Enter
tmux split-window -t "$SESSION:0" -h
tmux send-keys -t "$SESSION:0.1" "cd $API_DIR && uv run python -m pytest -v" Enter

# 新窗口: Web
tmux new-window -t "$SESSION" -n "web"
tmux send-keys -t "$SESSION:1" "cd $WEB_DIR && pnpm dev" Enter

# 选择 API 窗口
tmux select-window -t "$SESSION:0"

echo "✅ BaiCao 开发环境已启动 (tmux session: $SESSION)"
echo ""
echo "快捷操作:"
echo "  tmux attach -t $SESSION   # 进入 tmux"
echo "  Ctrl+b d                  # 离开 tmux"
echo ""
echo "Pane 0 (上): API server  |  Pane 1 (右): pytest"
echo "Window 1: Web dev server"
echo ""
echo "服务地址:"
echo "  API:  http://localhost:$API_PORT/docs"
echo "  Web: http://localhost:5173"
echo "  Neo4j: bolt://localhost:17687"
echo "  PG:    localhost:15433"
echo "  Redis: localhost:16380"
