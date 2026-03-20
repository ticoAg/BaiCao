# BaiCao ShiTan：AI Agent 自动化研发行为规范

本文件 `AGENTS.md` 的定位：**指导 AI Agent 在本仓库进行自动化研发的行为规范**。

核心目标：**构建可溯源的中药材知识图谱智能问答系统，一切研发流程可自动化、可自迭代、渐进式探索**。

本仓库按 **Agentic Engineering** 方式组织，围绕五个支柱：上下文工程、验证闭环、工具化、Agentic 代码库、复合式工程。

---

## 0) 项目定位

BaiCao ShiTan = **可溯源的中药材知识图谱 + 智能问答 + 推理链展示**：

- **知识图谱核心**：Neo4j 图数据库存储中药材实体、关系、溯源证据
- **PostgreSQL**：存储结构化关系数据、用户数据、对话历史
- **FastAPI 后端**：提供 REST API、图谱查询、溯源服务
- **React 前端**：对话 UI、知识图谱可视化、推理链展示
- **LLM 集成**：LangChain + OpenAI 实现智能问答

同级包 `packages/` 分工明确：
- `api/` — Python FastAPI 后端服务
- `web/` — React 前端应用
- `shared/` — 跨语言类型定义和工具
- `db/` — 数据库迁移和种子数据

---

## 1) 上下文工程（Context Engineering）

### 1.1 Agent-Naive Quickstart（首条消息 / 任务不明确时）

1. 阅读 `IMPL_PLAN.md` 了解项目定位与当前阶段
2. 阅读 `AGENTS.md` 本文件，建立研发行为规范认知
3. 查看 `.task/` 目录下的任务 JSON 文件定位下一条 TODO
4. 不清晰时：向用户追问要改哪个模块

### 1.2 SSOT 地图

- **需求真源（What/Why）**：`IMPL_PLAN.md`（锚点 `IMPL_PLAN.md#section-*`）
- **任务真源（When/Who/Progress）**：`.task/IMPL-*.json`
- **行为真源（How/Truth）**：仓库代码以 `packages/` 为主
- **长期维护文档（How/Contract）**：`docs/architecture|`、`docs/acceptance/`
- **研发草案（非稳定）**：`docs/_dev/`、`docs/_notes/`

### 1.3 核心目录结构

```text
 BaiCao/
├── packages/
│   ├── api/                    # Python FastAPI 后端
│   │   └── app/
│   │       ├── api/           # API 路由（routes/）
│   │       ├── core/          # 核心配置（config.py）
│   │       ├── models/        # SQLAlchemy 模型
│   │       ├── services/      # 业务逻辑服务
│   │       ├── kg/            # 知识图谱相关
│   │       └── 溯源/          # 数据溯源模块
│   │
│   ├── web/                   # React 前端
│   │   └── src/
│   │       ├── components/    # React 组件
│   │       ├── pages/         # 页面
│   │       ├── hooks/         # 自定义 hooks
│   │       ├── stores/        # Zustand 状态管理
│   │       ├── services/      # API 调用
│   │       └── types/         # TypeScript 类型
│   │
│   ├── shared/                # 共享类型和工具
│   │   └── types/            # TypeScript 类型（Pydantic 模型对齐）
│   │
│   └── db/                    # 数据库脚本
│       ├── migrations/        # Alembic 迁移
│       ├── neo4j/             # Neo4j Cypher 脚本
│       └── seed/              # 种子数据
│
├── infra/                      # 基础设施
│   ├── docker-compose.yml     # 主编排文件
│   ├── postgres/             # PostgreSQL 配置
│   ├── neo4j/                # Neo4j 配置
│   └── nginx/                 # Nginx 配置
│
├── docs/                      # 文档
│   ├── architecture/          # 架构文档
│   ├── acceptance/           # 验收文档
│   └── _dev/                  # 研发草案
│
├── .task/                     # 任务文件
└── AGENTS.md                  # 本文件
```

### 1.4 渐进式披露

- 用 `rg` / `git grep` 定位入口文件
- 先搜后读：优先定位入口，再按需深入
- 避免上下文污染：用摘要 + `path:line` + 可复现命令替代大段内容
- 文档主路径保持低噪声，但提供继续深入的可达路径

### 1.5 生态工具设计原则

以下原则适用于：

- `packages/api/` 中的 API、图谱查询、溯源服务
- `packages/web/` 中的对话 UI、知识图谱可视化、推理链展示
- `packages/shared/` 中的类型定义
- `docs/` 文档与调试入口

#### Everything Reach-able

- 任何能力都必须能从入口追到事实来源：API 端点 -> service 实现 -> model 定义 -> database schema。
- 任何底层实体也必须可反查上层语义：database table / Cypher query -> 对应 API 路由 -> 前端调用方。
- 设计新抽象时，必须明确"如何发现、如何定位、如何验证"。

#### Gradual Disclosure

- 默认先暴露最小可行动信息：能力分类、API 端点、关键参数。
- Schema、内部字段、调试细节按需展开，不在主路径一次性全部暴露。
- API 文档、类型定义的主路径应保持低噪声，但必须提供继续深入的可达路径。

#### Cite Bidirectional Linking

- 高层抽象必须能 cite 到低层事实：API 路由 -> service 实现 -> model -> database schema。
- 低层实体必须能反向链接回高层语义：database table -> 对应 API 路由 -> 使用场景 -> 相关文档。
- 事件与调试输出优先保留稳定锚点：`herb_id`、`source_id`、`session_id`、`path:line`。

---

## 2) 验证闭环（Agentic Validation）

### 2.1 实现中的自验证

- **改了就要验**：每次代码改动后主动执行相关验证
- 优先选择最小且可复现的验证：
  - API 测试：`cd packages/api && pytest`
  - 前端构建：`cd packages/web && npm run build`
  - 端到端验证：`docker compose up --build`

### 2.2 可观测闭环

- API 响应可追踪（request_id / session_id）
- 图谱查询可解释（Cypher 语句可复现）
- 溯源链路完整（evidence -> source）

### 2.3 交付输出约定

- **结论一句话**
- **证据链**：`IMPL_PLAN.md#section-*` + `.task/IMPL-*.json` + `Impl: path:line`
- **如何复现**：最小命令 + 必要 env
- **如何验证**：最小验收脚本

---

## 3) 工具化（Agentic Tooling）

### 3.1 已有工具

- Docker Compose 基础设施：`docker compose -f infra/docker-compose.yml up`
- API 测试：`cd packages/api && pytest`
- 前端开发：`cd packages/web && npm run dev`
- 数据库迁移：`cd packages/db && alembic upgrade head`

### 3.2 工具化意识

- 发现摩擦 → 提议工具化
- 能脚本跑的不手动跑
- 长时间任务用后台模式

---

## 4) Agentic 代码库

### 4.1 协议与类型系统

- **Protocol-First**：新增/修改 API 协议必须先更新 `packages/shared/types/`
- **强类型**：输入/输出/事件必须有 typed model
- **Pydantic v2**：Python 端使用 Pydantic v2 做数据验证
- **TypeScript 类型**：前端使用 TypeScript 严格模式

### 4.2 代码组织

- Monorepo 结构：`packages/` 下按职责分离
- API 内部：按 `api/` / `core/` / `models/` / `services/` / `kg/` / `溯源/` 分层
- Web 内部：按 `components/` / `pages/` / `hooks/` / `stores/` / `services/` / `types/` 分层
- 允许破坏性调整，不做兼容层

### 4.3 知识图谱具体约束

- **Neo4j Schema**：实体和关系类型必须先在 `packages/db/neo4j/` 中定义
- **Cypher 查询**：复杂的图谱查询必须可复现、可解释
- **溯源链路**：每个药材属性都必须关联到 Evidence，Evidence 必须关联到 Source

### 4.4 安全默认

- 外部输入校验
- 敏感输出脱敏限长
- 不泄露 secrets（使用环境变量管理）

---

## 5) 标准工作流

### 5.1 快速定位

```bash
# 查看任务文件
ls .task/

# 查看项目进度
cat IMPL_PLAN.md
```

### 5.2 需求与任务对齐

- 在 `IMPL_PLAN.md` 找到对应章节
- 在 `.task/` 选择正确模块文件新增/更新任务

### 5.3 实现

- 先改代码，再让文档与任务引用代码事实

### 5.4 实现后同步任务

- 标记为完成 + 补齐 `impl:` + `module:` 证据

### 5.5 验证

改了就要验，验了才算完。

---

## 6) 复合式工程

### 6.1 沉淀规则

- 重复 3 次以上 → 脚本化到 `scripts/`
- 跨模块有效模式 → 提炼到 `docs/architecture/`
- 多次暴露的规则 → 回写到 `IMPL_PLAN.md` 或本文件

### 6.2 自迭代

Agent 应主动识别改进机会：SSOT 漂移 → 修复；验证盲区 → 补 smoke；重复劳动 → 工具化。

---

## 7) Git 与依赖纪律

### Git 安全规则

- 不重写历史，不做不可恢复的清理
- 不用 `git add -A`，只 add 本次改动的文件
- `git push` 必须先征求用户同意

### 依赖与供应链

- Python 依赖统一用 `uv` + `pyproject.toml`
- Node.js 依赖统一用 `pnpm` + `package.json`
- 没有充分理由不新增依赖

---

## 8) 一等公民概念

### 标识与关联键

| 键 | 用途 |
|---|---|
| `herb_id` | 中药材实体唯一标识 |
| `source_id` | 数据来源唯一标识 |
| `evidence_id` | 证据/溯源唯一标识 |
| `session_id` | 用户对话会话标识 |
| `request_id` | API 请求追踪标识 |
| `response_id` | API 响应标识 |

---

## 9) Definition of Done

- `.task/` 中任务已标记，包含 `req:` + `impl:` + `module:` 证据
- 有最小验证闭环
- 若涉及数据模型变更：明确说明数据库迁移
- 复利检查：是否有可沉淀的工具/模式/约束
