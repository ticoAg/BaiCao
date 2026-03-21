# 白草药坛 BaiCao ShiTan

可溯源、可解释、可验证的中药材知识图谱智能问答系统。

![Status](https://img.shields.io/badge/status-MVP%20early-f59e0b)
![Architecture](https://img.shields.io/badge/architecture-Modular%20Monolith-2563eb)
![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20React%20%7C%20Neo4j%20%7C%20PostgreSQL-0f766e)
![LLM](https://img.shields.io/badge/LLM-LangChain%20%2B%20OpenAI-7c3aed)

> 当前阶段：MVP 早期实现中。仓库内已具备 monorepo 骨架、基础设施编排、首批后端接口、前端页面原型和 Neo4j 样例数据，但距离生产可用仍有较大差距。

## 一页看懂

- 定位：把中药材问答从“黑盒回答”升级为“图谱支撑 + 推理可见 + 证据可查 + 专家可审”的可信知识系统
- 架构：以 FastAPI 为应用入口，Neo4j 承担图谱查询，PostgreSQL 承担结构化事务数据，React 提供问答与探索界面
- 现状：主骨架、首批 API、前端原型、样例图谱和导入脚本已具备；审查闭环、完整溯源、SSE 和事件驱动仍在持续建设
- 适合谁：中医师、执业药师、研究者，以及关心知识图谱问答和可信 AI 的开发者

## 快速导航

- 项目规划：`IMPL_PLAN.md`
- 架构入口：`docs/architecture/README.md`
- 系统总览：`docs/architecture/system-overview.md`
- 数据模型：`docs/architecture/data-model.md`
- brainstorm：`docs/_dev/brainstorm/README.md`
- 实施计划入口：`docs/superpowers/README.md`

## 项目定位

白草药坛希望解决的不是“再做一个中药材问答页面”，而是把中药材知识从黑盒答案，升级为一套可追踪、可审查、可探索的知识系统。

传统问答产品通常只能给出结论，用户难以继续追问：

- 这条结论来自哪里？
- 模型为什么这样回答？
- 这条知识是否经过专家审查？
- 药材、功效、成分、归经之间还能看到哪些关联？

白草药坛的目标，是把这些问题放到产品主路径里，而不是当成附加信息。

## 核心价值

- 可溯源：答案尽量关联到来源、证据和引用链路
- 可解释：回答不仅给结果，还展示推理链和图谱上下文
- 可验证：知识默认未验证，支持专家审查与状态透明化
- 可探索：用户不仅能问答，还能浏览图谱、查看路径和关系

## 愿景与目标用户

面向的不是单一“聊天用户”，而是多类对知识可信度要求很高的角色：

- 中医师：需要高可信度的临床参考
- 执业药师：需要明确的用药依据和风险提示
- 研究者：需要证据链、关系网络和可追踪来源
- 普通用户：需要更容易理解、但不过度神化的中药材知识解释

从产品视角，本项目的长期形态是：

1. 用 Neo4j 组织中药材知识图谱
2. 用 PostgreSQL 保存结构化实体、验证记录、会话与用户数据
3. 用 FastAPI 提供图谱、问答、验证、溯源接口
4. 用 React 提供问答、图谱探索、验证工作台等前端视图
5. 用 LLM 结合图谱上下文生成更可信、更可解释的回答

## 当前项目状态

截至目前，仓库中的事实状态大致如下：

| 模块 | 当前状态 | 说明 |
| --- | --- | --- |
| Monorepo 骨架 | 已有 | `packages/`、`infra/`、`docs/` 与 `docs/superpowers/` 已建立 |
| 基础设施编排 | 已有 | Docker Compose 编排 PostgreSQL、Neo4j、Redis、API、Web、Nginx |
| 后端 API | 初步可用 | 已有 `health`、`herbs`、`graph`、`verifications`、`chat` 路由骨架 |
| 前端页面 | 原型可用 | 已有首页、搜索、图谱、验证、问答等页面原型 |
| 图谱数据 | 样例可用 | 已有 Neo4j 约束脚本和“陈皮”样例图谱种子数据 |
| 数据导入 | 初步可用 | 已有 CSV / JSONL 导入器和 dry-run CLI |
| 溯源链路 | 设计明确 | 完整证据链与来源联动仍在继续实现 |
| 专家审查闭环 | 初步可用 | 验证申请与审核接口已有骨架，完整角色/权限流未完成 |
| 事件驱动 / 缓存 / SSE | 规划中 | 已写入架构草案，尚未在仓库内完整落地 |

换句话说：这是一个“方向明确、主干已立、能力还在持续生长”的仓库，而不是一个已经封版的成品。

## 目标架构

```mermaid
flowchart LR
    U[用户 / 研究者 / 专家] --> W[React Web]
    W --> A[FastAPI API]

    subgraph App[Application Modules]
        KG[kg 图谱查询]
        QA[qa 智能问答]
        RV[review 专家审查]
        PV[provenance 溯源]
    end

    A --> KG
    A --> QA
    A --> RV
    A --> PV

    KG <--> N[(Neo4j)]
    QA <--> P[(PostgreSQL)]
    RV <--> P
    PV <--> P
    A <--> R[(Redis)]
    QA --> O[OpenAI / LangChain]
```

这套设计遵循当前 brainstorm 文档中确定的几个原则：

- 架构形态优先采用 Modular Monolith，先保证开发效率和认知清晰
- 知识图谱与结构化事务数据分库存储，职责边界明确
- 溯源、审查、问答不是孤立功能，而是围绕同一知识事实协同工作
- 后续演进上，为事件驱动、缓存和异步任务预留接口

## 一条回答是如何形成的

```mermaid
sequenceDiagram
    autonumber
    participant User as 用户
    participant Web as Web 前端
    participant API as FastAPI
    participant Graph as Graph Service
    participant Neo4j as Neo4j
    participant Chat as Chat Service

    User->>Web: 输入问题
    Web->>API: 提交问题
    API->>Chat: 解析问题
    Chat->>Graph: 请求相关图谱
    Graph->>Neo4j: 查询实体/关系
    Neo4j-->>Graph: 返回子图
    Graph-->>Chat: 返回图谱上下文
    Chat-->>API: 生成回答 + 推理链 + 来源
    API-->>Web: 返回结构化响应
    Web-->>User: 展示答案、推理链、图谱预览
```

在最终目标里，系统返回的不只是自然语言答案，还应尽量同时返回：

- 相关实体
- 推理链步骤
- 来源列表
- 图谱预览
- 验证状态

## 仓库结构

```text
BaiCao/
├── packages/
│   ├── api/          # FastAPI 后端
│   ├── web/          # React 前端
│   ├── shared/       # 共享类型与工具
│   └── db/           # 数据脚本、Cypher、导入数据
├── infra/            # Docker Compose 与基础设施配置
├── docs/             # 架构、验收、研发草案与 superpowers 文档
│   ├── architecture/ # 稳定架构文档
│   ├── acceptance/   # 验收文档
│   ├── _dev/         # 草案与 brainstorm
│   └── superpowers/  # spec / plan 与仓库级实施任务系统
├── IMPL_PLAN.md      # 项目初始化与高层规划
└── AGENTS.md         # 仓库级 AI Agent 研发规范
```

## 已有能力一览

### 后端

当前后端已经有一批可继续演进的接口骨架：

- `GET /health`：健康检查
- `GET /api/v1/herbs/`：药材列表
- `GET /api/v1/herbs/search/{name}`：按名称查询药材
- `GET /api/v1/graph/herb/{name}`：按药材获取图谱
- `GET /api/v1/graph/search`：图谱节点搜索
- `GET /api/v1/graph/path`：查询两个节点之间的路径
- `GET /api/v1/graph/pending`：获取待验证节点或关系
- `GET/POST /api/v1/verifications/...`：验证申请与审核
- `POST /api/v1/chat/question`：原型版智能问答接口

### 前端

当前前端已具备基础导航和页面原型：

- 首页
- 知识搜索页
- 图谱浏览页
- 验证管理页
- 智能问答页

### 数据与脚本

- Neo4j 初始化约束脚本
- “陈皮”样例图谱种子数据
- `herbs.csv` / `herbs.jsonl` 样例导入文件
- CSV / JSONL 导入 CLI（支持 dry-run）

## 快速开始

### 运行环境

- Python 3.12+
- Node.js 22+
- `pnpm`
- Docker / Docker Compose
- 推荐安装 `uv`

### 方案 A：直接使用 Docker Compose 启动全栈

这是最省心的启动方式。

```bash
cp infra/.env.example infra/.env
docker compose -f infra/docker-compose.yml up --build
```

启动后可访问：

- Web: `http://localhost:13001`
- API: `http://localhost:18001`
- Nginx 统一入口: `http://localhost:18080`
- Neo4j Browser: `http://localhost:17474`
- PostgreSQL: `localhost:15433`
- Redis: `localhost:16380`

### 方案 B：本地开发 API / Web，数据库走 Docker

先启动基础设施：

```bash
cp infra/.env.example infra/.env
docker compose -f infra/docker-compose.yml up -d postgres neo4j redis
```

然后为本地 API 准备环境变量，例如在 `packages/api/.env` 中配置：

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
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

启动前端：

```bash
cd packages/web
corepack enable
pnpm install
pnpm dev
```

> **工具链说明**：前端使用 **vite-plus (`vp`)**。`pnpm-workspace.yaml` 的 catalog 将 `vite` 映射到 `@voidzero-dev/vite-plus-core`、`vitest` 映射到 `@voidzero-dev/vite-plus-test`。所有脚本（`dev` / `build` / `test` / `preview`）均通过 `vp` 命令执行。

本地开发时：

- Web 默认运行在 `http://localhost:3000`
- Vite 已配置 `/api` 代理到 `http://localhost:8000`

### 方案 C：演示与统一验证入口

仓库根目录已经提供统一测试与演示入口，推荐优先使用：

```bash
pnpm run demo
pnpm run test:api
pnpm run test:integration
pnpm run test:web
pnpm run test:e2e
pnpm run verify
pnpm run verify:full
```

含义如下：

- `pnpm run demo`：用 `tmux` 启动本地演示环境，并自动灌入 demo 数据
- `pnpm run test:api`：运行后端 pytest 测试
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

## 近期路线图

结合 `IMPL_PLAN.md`、`docs/superpowers/plans/` 实施计划和 `docs/_dev/brainstorm`，当前比较清晰的研发路线是：

### Phase 1：基础骨架

- monorepo 结构
- FastAPI / React 初始化
- Docker Compose 基础设施
- Neo4j 初始 schema 与样例数据

### Phase 2：核心能力

- 药材、来源、证据、验证数据模型
- 图谱查询服务
- 基础问答接口
- 基础图谱可视化

### Phase 3：可信问答闭环

- 推理链展示
- 溯源链路查询
- 专家审查工作台
- 验证状态反哺图谱与回答

### Phase 4：增强能力

- Redis 缓存
- 事件驱动模块集成
- SSE 流式输出
- 更完整的监控、追踪和性能优化

## 文档入口

- 项目规划：`IMPL_PLAN.md`
- 仓库规范：`AGENTS.md`
- 架构文档：`docs/architecture/README.md`
- 数据模型：`docs/architecture/data-model.md`
- 系统总览：`docs/architecture/system-overview.md`
- 验收文档：`docs/acceptance/README.md`
- brainstorm 总索引：`docs/_dev/brainstorm/README.md`

## 适合谁关注这个仓库

如果你关心以下任一方向，这个仓库都值得继续跟进：

- 图谱驱动问答
- AI + 知识库 + 溯源的可信系统设计
- 中药材知识数字化
- Neo4j 与应用层联动
- 专家审查与 AI 生成内容协同

## 当前限制

请把当前仓库视为“持续建设中的研发仓库”，而不是开箱即用的生产系统。

目前仍然存在这些明显边界：

- 仍有不少功能处于原型或骨架阶段
- 完整鉴权、权限模型和专家工作流尚未闭环
- 问答质量依赖后续图谱质量、提示词工程和审查机制
- 部分能力已经在 brainstorm / architecture 文档中设计，但尚未全部代码化

如果你希望参与推进，推荐先从以下入口阅读：

1. `README.md`
2. `IMPL_PLAN.md`
3. `docs/_dev/brainstorm/README.md`
4. `docs/architecture/system-overview.md`
5. `docs/superpowers/plans/` 下的实施计划文件
