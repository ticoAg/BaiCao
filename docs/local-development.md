<!--
---
doc_kind: workflow
status: stable
tags: ["local-dev", "makefile", "infisical"]
summary: 本地开发栈、环境变量、手动启动、样例数据与验证命令
audience: developer
---
-->

# 本地开发

仓库推荐路径：依赖服务走 Docker Compose，前后端走本地进程，统一挂在一个 tmux session。产品定位和阶段见 [../README.md](../README.md)；改动该跑哪些测试见 [verification-matrix.md](verification-matrix.md)。

```mermaid
flowchart LR
    Env[配 .env] --> Deps[make deps up]
    Deps --> Stack[make stack up]
    Stack --> App[Web / API]
```

## 环境

- Python 3.12+
- Node.js 22+
- `pnpm`
- Docker / Docker Compose
- 推荐 `uv`

## 推荐：`make`

```bash
cp .env.schema .env
cp infra/.env.schema infra/.env
make deps up
make stack up
```

启动后：

| 服务 | 地址 |
| --- | --- |
| Web | <http://localhost:3000> |
| API | <http://localhost:8000> |
| Neo4j Browser | <http://localhost:17474> |
| PostgreSQL | `localhost:15433` |
| Redis | `localhost:16380` |
| MinIO API | <http://localhost:19000> |
| MinIO Console | <http://localhost:19001> |

常用命令：

```bash
make help
make deps status
make stack status
make api logs LINES=40
make web logs LINES=40
make stack attach
make stack down
```

端口被占时：

```bash
make api up API_PORT=8010
make web up WEB_PORT=3010
make stack up API_PORT=8010 WEB_PORT=3010
```

## Infisical

`make deps/api/web/stack` 和仓库测试脚本通过 `scripts/infisical_env.py` 调 HTTP API 拉 secret，注入子进程。不需要 Infisical CLI。已经出现在进程环境里的变量不会被覆盖。

本地只放鉴权信息；`DATABASE_URL`、`OPENAI_API_KEY`、`NEO4J_PASSWORD` 等业务变量放 Infisical。运行时会读仓库根目录的 `infisical.defaults.env`、`.env`、`.env.local`：

- 固定默认项：仓库跟踪的 `infisical.defaults.env`
- `INFISICAL_TOKEN` 或 `INFISICAL_CLIENT_ID` / `INFISICAL_CLIENT_SECRET`：本地 `.env`
- 切换环境：在 `.env` 里覆盖 `INFISICAL_ENV`

最小做法：`cp .env.schema .env`，补 token。字段说明在 `.env.schema`。

根目录已配好 `infisical.defaults.env` / `.env`，或当前 shell 已导出 Infisical 变量时，`make` 不需要再包一层注入脚本。

## 手动启动

基础设施：

```bash
cp infra/.env.schema infra/.env
docker compose -f infra/docker-compose.yml up -d postgres neo4j redis minio
```

不用 Infisical 时，在 `packages/api/.env` 配业务变量，例如：

```env
DATABASE_URL=postgresql+asyncpg://baicao:baicao_password@localhost:15433/baicao
NEO4J_URI=bolt://localhost:17687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password
REDIS_URL=redis://localhost:16380
OPENAI_API_KEY=your_api_key_here
```

后端：

```bash
cd packages/api
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
```

手动模式也走 Infisical 时，从仓库根目录：

```bash
python3 scripts/infisical_env.py run -- \
  bash -lc 'cd packages/api && uv sync --extra dev && uv run uvicorn app.main:app --reload --port 8000'
```

前端：

```bash
cd packages/web
corepack enable
pnpm install
pnpm exec vp dev --host 0.0.0.0 --port 3000
```

`packages/web` 的 `dev` / `build` / `test` / `preview` 一律走 **vite-plus (`vp`)**。`pnpm-workspace.yaml` 的 catalog 把 `vite` 映射到 `@voidzero-dev/vite-plus-core`、`vitest` 映射到 `@voidzero-dev/vite-plus-test`。仓库根脚本（如 `pnpm run test:web`）只是对 `vp` 的封装。

前端走 Infisical 时，从仓库根目录：

```bash
python3 scripts/infisical_env.py run -- \
  bash -lc 'cd packages/web && pnpm install && pnpm exec vp dev --host 0.0.0.0 --port 3000'
```

Vite 已把 `/api` 代理到 `http://localhost:8000`。

## 样例数据

Neo4j 初始化脚本和样例：

- 约束与索引：`packages/db/neo4j/init_cypher.cql`
- 陈皮样例：`packages/db/neo4j/seed_chenpi.cql`
- 导入样例：`packages/db/import/herbs.csv`、`packages/db/import/herbs.jsonl`

只验证导入解析：

```bash
cd packages/api
uv run python -m app.importers.cli ../db/import/herbs.csv --dry-run
uv run python -m app.importers.cli ../db/import/herbs.jsonl --dry-run
```

## 验证

```bash
pnpm run test:api
pnpm run test:integration
pnpm run test:web
pnpm run test:e2e
pnpm run verify
pnpm run verify:full
```

配置了 Infisical 鉴权变量时，集成测试和 E2E 会经 `scripts/infisical_env.py` 注入 secret。第一次跑 E2E 会自动准备 Chromium。

命令含义和各类改动的最低验证见 [verification-matrix.md](verification-matrix.md)。
