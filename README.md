# 白草药坛 BaiCao ShiTan

面向中医药场景的 Agent 驱动可信知识搜集与利用平台。

![Status](https://img.shields.io/badge/status-MVP%20early-f59e0b)
![Architecture](https://img.shields.io/badge/architecture-Modular%20Monolith-2563eb)
![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20React%20%7C%20Neo4j%20%7C%20PostgreSQL-0f766e)
![LLM](https://img.shields.io/badge/LLM-Agent%20Workflow%20%2B%20OpenAI-7c3aed)

> 白草聚焦的不是“再做一个中医药聊天页面”，而是把中医药领域里高密度、强关联、检索成本高的知识，变成可高效搜集、快速利用、持续沉淀、结果可信的知识资产。

## 白草解决什么问题

中医药知识天然具有几个难点：

- 信息密度高，同一药材往往牵连功效、性味、归经、配伍、成分、来源、炮制、禁忌等多层信息
- 来源分散，知识散落在标准、古籍、教材、论文、经验总结与业务资料中
- 关系复杂，很多问题不是“搜到一条答案”就结束，而是要继续比较、追溯、串联和判断
- 人工成本高，检索、整理、比对、复核与再利用常常要消耗大量专家和研究人员时间

白草希望解决的，正是这类“知识工作效率低、复用成本高、结果可信度不透明”的问题。

## 白草的核心价值

- 高效：让知识搜集、检索、关联、整理与复用从“人肉翻找”转向结构化工作流
- 低成本：减少在多来源资料和多页面工具之间来回切换的人力投入
- 兼顾广度与深度：既能快速定位相关知识，也能沿图谱关系继续深入追查上下文
- 可信：尽量保留来源、证据、推理上下文与验证状态，而不是只给黑盒结论

## 白草是什么

白草是一个围绕中医药知识场景构建的产品化平台，不只回答问题，也帮助团队完成知识的持续搜集、组织、验证与利用。

它把以下能力组合在一起：

- 用图谱组织药材、功效、成分、来源、关系与路径
- 用 Agent 执行检索、归纳、串联、比对和知识利用任务
- 用可追溯、可解释、可验证机制提升结果可信度
- 用工作台形态承接问答、图谱探索、验证与数据处理

## 为什么是 Agent + 图谱

传统搜索更擅长“找到片段”，但不擅长把片段快速转成可利用结论。白草把 Agent 与图谱结合，是因为它们分别擅长两件互补的事：

- 图谱负责表达实体、关系、路径和上下文，天然适合处理中医药知识的强关联结构
- Agent 负责把“查、找、串、比、整、用”串成任务流程，减少重复人工操作
- 二者结合后，更适合支持从一次问题出发，逐步扩展到证据、关联关系和后续利用动作
- 再叠加验证与溯源机制，能让结果不只更快，也更容易被复核和复用

## 适合谁

- 中医药研究、内容与知识工程团队
- 需要整理和复用中医药知识资产的机构
- 关注知识图谱、可信 AI、Agent 工作流的产品与技术团队
- 需要在中医药场景里做更高效知识检索与探索的专业用户

## 当前阶段

当前仓库处于 `MVP early` 阶段，已经具备可运行的 monorepo 骨架、基础设施编排、Neo4j 样例数据、问答与图谱相关主链路，以及验证、数据处理、review/export 等工作台能力。

这意味着白草已经不是纯概念草案，但距离生产级产品仍有明显距离。完整溯源闭环、专家治理、事件驱动与更完整监控仍在持续建设中。

## 快速导航

- 项目与阶段入口：`README.md`
- 架构入口：`docs/architecture/README.md`
- 系统总览：`docs/architecture/system-overview.md`
- 数据模型：`docs/architecture/data-model.md`
- Graph Workbench：`docs/architecture/graph-workbench.md`
- 数据处理工作台：`docs/architecture/data-pipeline-workbench.md`
- 共享知识模型 / 数据采集：`docs/architecture/knowledge-model-and-ingestion.md`
- 验收入口：`docs/acceptance/README.md`
- brainstorm 入口：`docs/_dev/brainstorm/README.md`
- 实施计划入口：`docs/superpowers/README.md`

## 快速开始

### 运行环境

- Python 3.12+
- Node.js 22+
- `pnpm`
- Docker / Docker Compose
- 推荐安装 `uv`

### 方案 A：推荐，使用 `make` 管理本地开发栈

这是当前仓库推荐的本地开发方式：依赖服务走 Docker Compose，前后端走本地进程，并统一挂在一个 tmux session 里。

如果你使用 Infisical CLI 管理本地环境变量，`make deps/api/web/stack ...` 和仓库测试脚本会在检测到以下任一条件时自动改为通过 `infisical run` 启动：

- 仓库根目录的 `infisical.defaults.env`、`.env`、`.env.local` 中存在任一 Infisical 相关环境变量
- 当前 shell 配置了任一 Infisical 相关环境变量：`INFISICAL_TOKEN`、`INFISICAL_PROJECT_ID`、`INFISICAL_ENV`、`INFISICAL_SECRET_PATH`、`INFISICAL_API_URL`

这样本地只需要配置 Infisical 相关变量，业务变量如 `DATABASE_URL`、`OPENAI_API_KEY`、`NEO4J_PASSWORD`、`WEB_API_BASE_URL` 等都可以放在 Infisical secret 中统一注入。

```bash
cp infra/.env.example infra/.env
make deps up
make stack up
```

如果仓库根目录的 `infisical.defaults.env` / `.env` 已配置好，或当前 shell 已导出 Infisical 相关变量，上面的命令不需要再手动加 `infisical run` 前缀。

仓库根目录的 `infisical.defaults.env`、`.env`、`.env.local` 都会被本地运行时和测试脚本自动读取。推荐做法是：

- 把固定不变的默认项放进仓库跟踪的 `infisical.defaults.env`
- 把 `INFISICAL_TOKEN` 这类敏感鉴权项放进本地 `.env`
- 如需切换环境，再在本地 `.env` 中覆盖 `INFISICAL_ENV`

一个最小示例：

`infisical.defaults.env`

```env
INFISICAL_API_URL=https://infisical.ticoag.fun
INFISICAL_PROJECT_ID=0c396ff3-177f-4347-a716-d3107dadfcf1
INFISICAL_SECRET_PATH=/
```

`.env`

```env
INFISICAL_TOKEN=your_service_token
INFISICAL_ENV=dev
```

如果你只是想快速得到一份本地同步模板，可以直接：

```bash
cp .env.example .env
```

根目录的 `.env.example` 已经包含 Infisical 本地注入所需的最小字段和注释说明；通常只需要补 `INFISICAL_TOKEN`，其余稳定默认项继续由仓库跟踪的 `infisical.defaults.env` 提供。

```bash
make stack up
```

启动后可访问：

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Neo4j Browser: `http://localhost:17474`
- PostgreSQL: `localhost:15433`
- Redis: `localhost:16380`
- MinIO API: `http://localhost:19000`
- MinIO Console: `http://localhost:19001`

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

如果本机已有服务占用默认端口，可临时改端口启动：

```bash
make api up API_PORT=8010
make web up WEB_PORT=3010
make stack up API_PORT=8010 WEB_PORT=3010
```

### 方案 B：手动启动 API / Web，数据库走 Docker

先启动基础设施：

```bash
cp infra/.env.example infra/.env
docker compose -f infra/docker-compose.yml up -d postgres neo4j redis minio
```

如果不用 Infisical，可以为本地 API 准备环境变量，例如在 `packages/api/.env` 中配置：

```env
DATABASE_URL=postgresql+asyncpg://baicao:baicao_password@localhost:15433/baicao
NEO4J_URI=bolt://localhost:17687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password
REDIS_URL=redis://localhost:16380
OPENAI_API_KEY=your_api_key_here
```

启动后端：

```bash
cd packages/api
uv sync --extra dev
uv run ruff check app tests
uv run ty check
uv run uvicorn app.main:app --reload --port 8000
```

如果手动模式下也想走 Infisical，建议从仓库根目录执行：

```bash
infisical run --project-config-dir="$PWD" -- \
  bash -lc 'cd packages/api && uv sync --extra dev && uv run uvicorn app.main:app --reload --port 8000'
```

启动前端：

```bash
cd packages/web
corepack enable
pnpm install
pnpm exec vp dev --host 0.0.0.0 --port 3000
```

对应前端也可以从仓库根目录执行：

```bash
infisical run --project-config-dir="$PWD" -- \
  bash -lc 'cd packages/web && pnpm install && pnpm dev --host 0.0.0.0 --port 3000'
```

> **工具链说明**：前端使用 **vite-plus (`vp`)**。`pnpm-workspace.yaml` 的 catalog 将 `vite` 映射到 `@voidzero-dev/vite-plus-core`、`vitest` 映射到 `@voidzero-dev/vite-plus-test`。`packages/web` 的 `dev` / `build` / `test` / `preview` 一律以 `vp` 为执行器；仓库根脚本（如 `pnpm run test:web`）只是对 `vp` 命令的统一封装。

手动开发时：

- Web 默认运行在 `http://localhost:3000`
- Vite 已配置 `/api` 代理到 `http://localhost:8000`

### 方案 C：统一验证入口

仓库根目录提供统一验证入口：

```bash
pnpm run test:api
pnpm run test:integration
pnpm run test:web
pnpm run test:e2e
pnpm run verify
pnpm run verify:full
```

如果根目录存在 `infisical.json` / `.infisical.json`，或当前 shell 配置了 Infisical 相关变量，上述集成测试和 E2E 脚本也会自动通过 `infisical run` 注入环境变量。

含义如下：

- `pnpm run test:api`：运行后端统一工具链验证（`uv + ruff + ty + pytest -m "not integration"`）
- `pnpm run test:integration`：运行后端真实依赖 integration 测试
- `pnpm run test:web`：运行前端 Vitest + Testing Library 单测
- `pnpm run test:e2e`：运行 Playwright 主链路 smoke
- `pnpm run verify`：执行 API + Web 两层快速回归
- `pnpm run verify:full`：执行 API + Integration + Web + E2E 全量验证

如果是第一次跑 E2E，脚本会自动确保 Chromium 浏览器可用。

GitHub Actions 的默认门禁也采用同一套分层语义：

- `ci-fast / api-tests`
- `ci-fast / web-tests`
- `ci-e2e / e2e-smoke`

其中：

- `ci-fast` 是快速主门禁，只跑 API fast suite 和 Web tests/build
- `ci-e2e` 是独立的慢门禁，只跑最小主链路浏览器 smoke

## 图谱与样例数据

项目当前已经提供 Neo4j 侧的初始化脚本和样例数据，便于先跑通“图谱查询 + 前端展示”的基础链路。

- 约束与索引：`packages/db/neo4j/init_cypher.cql`
- 陈皮样例图谱：`packages/db/neo4j/seed_chenpi.cql`
- 导入样例：`packages/db/import/herbs.csv`、`packages/db/import/herbs.jsonl`

如果只想先验证导入解析是否正确，可以先跑 dry-run：

```bash
cd packages/api
uv run python -m app.importers.cli ../db/import/herbs.csv --dry-run
uv run python -m app.importers.cli ../db/import/herbs.jsonl --dry-run
```

## 技术概览

当前实现采用以 FastAPI 为应用入口、React 为前端工作台、Neo4j 为图谱查询底座、PostgreSQL 为结构化事务与业务数据底座的组合。

```mermaid
flowchart LR
    U[用户 / 研究者 / 专家] --> W[React Web]
    W --> A[FastAPI API]
    A --> KG[图谱查询 / 问答 / 验证 / 溯源服务]
    KG <--> N[(Neo4j)]
    A <--> P[(PostgreSQL)]
    A <--> R[(Redis)]
    A --> O[OpenAI]
```

在产品路径上，白草追求的是“知识搜集与利用效率”与“结果可信度”同时成立，而不是只追求更像聊天机器人的交互体验。

## 仓库结构

```text
BaiCao/
├── packages/
│   ├── api/              # FastAPI 后端
│   ├── web/              # React 前端
│   ├── shared/           # 跨端共享类型与工具
│   ├── knowledge_model/  # 共享知识模型 Python 包
│   ├── data_ingestion/   # 数据采集边界包
│   └── db/               # 数据脚本、Cypher、导入数据
├── infra/                # Docker Compose 与基础设施配置
├── docs/                 # 架构、验收、草案与 superpowers 文档
└── AGENTS.md             # 仓库级 AI Agent 协作规范
```

## 知识可信度模型

白草药坛不是把“模型输出”直接当成事实，而是希望让知识经历一个显式生命周期：

1. 导入或生成知识
2. 标记为待验证
3. 关联来源与证据
4. 进入专家审查
5. 更新为已验证 / 已拒绝
6. 在问答和图谱界面中透明展示状态

这也是为什么仓库里同时存在：

- 知识图谱模块
- 问答模块
- 验证模块
- 溯源模块

它们服务的是同一个问题：如何让一条知识“可信地被使用”。

## 文档入口

- 项目总入口：`README.md`
- 仓库规范：`AGENTS.md`
- 架构文档：`docs/architecture/README.md`
- 数据模型：`docs/architecture/data-model.md`
- 系统总览：`docs/architecture/system-overview.md`
- Graph Workbench：`docs/architecture/graph-workbench.md`
- 验收文档：`docs/acceptance/README.md`
- brainstorm 总索引：`docs/_dev/brainstorm/README.md`

## 当前限制

请把当前仓库视为“持续建设中的研发仓库”，而不是开箱即用的生产系统。

目前仍然存在这些明显边界：

- 仍有不少功能处于原型或骨架阶段
- 完整鉴权、权限模型和专家工作流尚未闭环
- 完整溯源链路、跨模块审计与更多集成回归仍需继续补强
- 问答质量依赖后续图谱质量、提示词工程和审查机制
- 部分能力已经在 architecture / brainstorm 文档中设计，但尚未全部代码化
