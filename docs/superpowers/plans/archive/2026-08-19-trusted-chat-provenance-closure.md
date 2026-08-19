# 可信问答与运行时收口 Implementation Plan

**Goal:** 完成 HF dataset 发布，并把当前 OpenAI Agents + MCP 问答主链收成可回收、可溯源、默认不暴露原始 Cypher 的可信问答闭环。

**Architecture:** 继续保留 `/api/v1/chat/stream`、OpenAI Agents SDK、现有 MCP structured tools 和中文 Neo4j 图模型。复用现有 `证据` / `来源` 节点与 `由证据支持` / `来源于` 关系生成结构化 citation，不新增第二套 provenance 存储，不重做 agent runtime，也不扩知识模型。

**Tech Stack:** Python 3.12, FastAPI, OpenAI Agents SDK, MCP, Neo4j, Pydantic v2, React 18, TypeScript, Pytest, Vitest, GitHub Actions

**Status:** done（2026-08-19；用户确认改为 public 后，Viewer 阻塞已解除）

**Predecessor:** `2026-08-16-baicao-knowledge-dataset.md` 仍为 `partial`；其唯一剩余的真实 HF 上传由本计划 Task 1 接管。方向已经由当前代码事实和仓库评估收敛，本轮不再创建平行 spec。

## Scope

- 完成 `ticoAg/baicao-knowledge` private dataset 真实上传，并如实记录 private Viewer 的账号能力限制
- 收口 OpenAI Agents SDK 迁移后的会话回收、页面文案和稳定文档
- 把旧英文 provenance 查询迁到当前中文图模型
- 从实际查询子图生成结构化 evidence/source citation，并接到 chat UI 与验证申请
- 在没有数据库只读身份前，从 MCP 暂停原始 `read_cypher`
- 把知识模型、数据采集和 E2E smoke 纳入与当前开发方式一致的 CI 门禁

## Non-Goals

- 不新增数据源，不重抽药典或苏子阳
- 不做登录、RBAC、机构租户或完整专家治理
- 不做 Redis 事件总线、多 worker 会话共享或监控平台
- 不让 LLM 自己生成 citation；citation 只能来自图查询结果
- 不恢复 `packages/graph_runtime/` 为 chat 主链

## Done Definition

1. 已完成 plan/spec 已归档，根索引只保留当前入口与 archive 导航，仓库内链接无断链
2. private HF Viewer 可读取 `records` / `edges` Parquet，且上传清单不含原文、JSONL、work、exports
3. 过期 chat session 会从实际 `SQLiteSession` registry 移除并关闭；应用退出也会关闭全部 session
4. provenance API 使用中文标签、关系和属性查询真实 Neo4j 数据
5. chat `final.evidence` 至少包含可解析的 `evidence_id`、`snippet`，有来源时包含 `source_id` / `source_name`
6. UI 能展示 citation、打开对应溯源并以正确的实体/来源预填验证申请
7. OpenAI agent 不再获得原始 `read_cypher`，直到 MCP 使用数据库级只读身份
8. API、Web、knowledge model、data ingestion、integration、E2E smoke 均有 fresh 通过证据

---

### Task 0: 归档已完成 plan/spec 并收口导航

**Files:**
- Create: `docs/superpowers/plans/archive/README.md`
- Create: `docs/superpowers/specs/archive/README.md`
- Move: `docs/superpowers/plans/` 中索引标记 completed 的 18 份 plan
- Move: `docs/superpowers/specs/` 中索引标记已落地的 11 份 spec
- Modify: `docs/superpowers/plans/README.md`
- Modify: `docs/superpowers/specs/README.md`
- Modify: 引用上述历史文档的稳定架构与验收文档

- [x] 使用显式 `git mv` 移动索引中已完成的文档，不用 glob 或 checkbox 重新推断状态。
- [x] archive 索引保留日期、标题、毕业去向与替代关系；历史正文不复制到当前 plan。
- [x] 根索引只保留 active、partial predecessor 和 archive 入口。
- [x] 更新仓库内指向已移动根路径的导航链接，不创建旧路径 stub。

**Verification:**

```bash
git diff --check
rg -n --glob '!docs/superpowers/plans/archive/**' \
  --glob '!docs/superpowers/specs/archive/**' \
  'superpowers/(plans|specs)/2026-(03|04)-' README.md docs packages datasets
```

**Evidence (2026-08-19):** 显式归档 18 份 completed plan 与 11 份已落地 spec；根目录分别只剩 3/2 个 Markdown 入口文件；`git diff --check` 通过，49 个变更 Markdown 文件的本地链接目标校验通过，非 archive 文档无旧根路径引用。

---

### Task 1: 完成 dataset 发布并关闭 predecessor plan

**Files:**
- Modify: `docs/superpowers/plans/2026-08-16-baicao-knowledge-dataset.md`
- Modify: `docs/superpowers/plans/README.md`
- Modify: `datasets/baicao-knowledge/catalog.json`
- Modify: `datasets/baicao-knowledge/README.md`
- Modify: `docs/acceptance/baicao-knowledge-dataset.md`
- Modify: `README.md`
- Modify: `docs/architecture/system-overview.md`

- [x] 运行 catalog/publish 测试并重新生成发布 Parquet。
- [x] 运行 `dataset_publish --dry-run`，断言清单只包含元数据与 `data/*.parquet`。
- [x] 使用当前 `hf auth` 登录身份执行一次非 dry-run private 上传。
- [x] 使用匿名 HF `is-valid` / `splits` / rows 接口验证 public Viewer；不得在日志或文档写出 token。
- [x] Viewer 验证通过后，把 predecessor plan/spec 改为 `done` 并移入对应 archive。

**Verification:**

```bash
cd packages/data_ingestion
uv run --with pytest pytest tests/test_dataset_catalog.py tests/test_dataset_publish.py -q
uv run --with pyarrow python -m data_ingestion.cli.export_dataset_parquet \
  --dataset-root ../../datasets/baicao-knowledge
uv run --with huggingface_hub python -m data_ingestion.cli.dataset_publish \
  --dataset-root ../../datasets/baicao-knowledge --dry-run
hf auth whoami
uv run --with huggingface_hub python -m data_ingestion.cli.dataset_publish \
  --dataset-root ../../datasets/baicao-knowledge
```

**Stop condition:** 真实上传是外部写操作；执行前必须确认当前操作者有权更新 `ticoAg/baicao-knowledge`。认证或 Viewer 仍失败时保留 `partial`，记录原始错误，不伪造完成状态。

**Evidence (2026-08-19):** 用户确认 dataset 可改为 public 后，发布器按 catalog visibility 更新 repo；public 导出清空 `evidence_text` 并删除 properties 原文字段。定向测试 `9 passed`，远端保持 10 个允许文件 + `.gitattributes`，匿名 `/is-valid`、`/splits`、`records`/`edges` rows 均返回 200，总行数 5,118 / 11,202。

---

### Task 2: 收口 OpenAI Agents 会话生命周期与文档口径

**Files:**
- Modify: `packages/api/app/services/chat_agent_runtime/session_memory.py`
- Modify: `packages/api/app/services/chat_agent_runtime/runtime.py`
- Modify: `packages/api/app/services/chat_agent_runtime/__init__.py`
- Modify: `packages/api/app/main.py`
- Modify: `packages/api/tests/services/test_session_memory.py`
- Modify: `packages/api/tests/services/test_chat_agent_runtime.py`
- Modify: `packages/web/src/pages/ChatPage.tsx`
- Modify: `docs/README.md`
- Modify: `docs/architecture/system-overview.md`
- Modify: `docs/architecture/knowledge-model-and-ingestion.md`
- Modify: `docs/acceptance/chat-mainline.md`

- [x] 先写失败测试：TTL 到期后 `_OPENAI_SESSIONS` 不再含该 session，且对应 `SQLiteSession.close()` 被调用。
- [x] 把 `InMemorySessionManager` 的旧 LangGraph checkpointer 删除职责改为最小 eviction callback；保留同 session 串行锁和 30 分钟 TTL。
- [x] runtime 在 eviction callback 中 `pop` 并关闭实际 `SQLiteSession`；新增应用 shutdown 时关闭全部 session 的入口。
- [x] 把页面与稳定文档中的 deepagents/LangGraph/InMemorySaver 表述改为 OpenAI Agents SDK + MCP + 进程内 SQLiteSession。
- [x] `rg` 确认旧 adapter 没有运行时调用后，才删除无调用的 LangGraph adapter/测试；否则只修事实，不做顺手重构。

**Verification:**

```bash
cd packages/api
uv run pytest tests/services/test_session_memory.py tests/services/test_chat_agent_runtime.py \
  tests/services/test_openai_event_adapter.py -q
uv run ruff check app tests
uv run ty check
rg -n --glob '!docs/superpowers/**' \
  "InMemorySaver|LangGraph thread_id|memory checkpointer|deepagents runtime|基于 deepagents" \
  README.md docs packages/web/src/pages/ChatPage.tsx
```

**Evidence (2026-08-19):** Codex 集成后 targeted tests `11 passed`；代理 worktree 另有 API 非集成 `278 passed, 3 deselected`、ruff/ty 通过。`openai_event_adapter.py` 仍复用 `event_adapter.py` 的事件归一化 helper，因此保留旧 adapter 文件与测试，只移除主链旧口径。

---

### Task 3: 把 provenance API 迁到中文图模型

**Files:**
- Create: `packages/api/app/schemas/provenance.py`
- Modify: `packages/api/app/provenance/__init__.py`
- Modify: `packages/api/app/api/provenance.py`
- Modify: `packages/api/tests/unit/provenance/test_provenance.py`
- Modify: `packages/api/tests/api/test_provenance_routes.py`
- Create: `packages/api/tests/unit/provenance/test_provenance_neo4j_smoke.py`
- Modify: `packages/shared/types/index.ts`

**Contract:**

- 图存储继续使用 `标识`、`名称`、`证据原文`、`状态`
- 实体到证据：`(entity)-[:由证据支持]->(evidence:证据)`
- 实体到来源：`(entity)-[:来源于]->(source:来源)`
- API 返回稳定的 frontend-friendly 字段，不把中文存储键直接泄漏成跨端协议

- [x] 先把共享 citation / lineage 类型写入 `packages/shared/types/index.ts`，再定义对应 Pydantic schema。
- [x] 写失败测试锁住中文标签、中文关系、`标识` 查询和 API 响应字段。
- [x] 将 create/get/link/lineage/evidence/completeness 查询全部改到中文图模型；使用 `NodeType` / `EdgeType` 真源，避免再手写第二套英文枚举。
- [x] 实体、证据、来源映射统一在 provenance service 完成，route 只负责请求/响应。
- [x] 增加真实 Neo4j integration smoke：写入一个隔离实体、证据、来源及两条关系，然后验证 lineage 和 completeness。

**Verification:**

```bash
cd packages/api
uv run pytest tests/unit/provenance/test_provenance.py tests/api/test_provenance_routes.py -q
cd ../..
pnpm --dir packages/shared typecheck
pnpm run test:integration
```

**Evidence (2026-08-19):** provenance route/service targeted tests `25 passed`，shared typecheck、ruff、ty 通过；查询以 `(entity)-[:来源于]->(source)` 为主并兼容 `(evidence)-[:来源于]->(source)`。全新 Docker volumes 上 integration `4 passed, 293 deselected`，覆盖隔离 provenance smoke、中文图存储、边端点与英文 API status 出站契约。

---

### Task 4: 从查询子图生成 chat citation 并接入 UI

**Files:**
- Create: `packages/api/app/services/chat_agent_runtime/citations.py`
- Modify: `packages/api/app/services/chat_agent_runtime/openai_event_adapter.py`
- Modify: `packages/api/app/services/chat_agent_runtime/system_prompt.py`
- Create: `packages/api/tests/services/test_citations.py`
- Modify: `packages/api/tests/services/test_openai_event_adapter.py`
- Modify: `packages/web/src/types/chat.ts`
- Modify: `packages/web/src/hooks/useChat.ts`
- Modify: `packages/web/src/components/chat/GraphAgentBasisPanel.tsx`
- Modify: `packages/web/src/components/chat/MessageList.tsx`
- Modify: `packages/web/src/components/chat/ReviewRequestModal.tsx`
- Modify: `packages/web/src/pages/ChatPage.test.tsx`
- Modify: `docs/acceptance/chat-mainline.md`

- [x] 写纯函数失败测试：只从 `证据` / `来源` 节点和两类 provenance 边生成 citation，忽略断链或无标识节点，并稳定去重。
- [x] `openai_event_adapter` 在 final 阶段从已收集 graph state 生成 `evidence`；禁止从模型答案文本解析或补造引用。
- [x] system prompt 要求回答知识结论前展开证据/来源邻居；无图证据时明确说“当前图谱没有可引用证据”。
- [x] 前端扩展现有 `GraphAgentEvidence`，展示证据摘要与来源；点击后以 citation 的实体 ID 打开 lineage，而不是把 source ID 当 entity ID。
- [x] 验证申请预填必须区分 `entity_id` 与 `source_id`，并带入 evidence quote。
- [x] 补有 citation、无 citation、来源缺失三种前端/事件适配测试。

**Verification:**

```bash
cd packages/api
uv run pytest tests/services/test_citations.py \
  tests/services/test_openai_event_adapter.py tests/api/test_chat_routes.py -q
cd ../..
pnpm --dir packages/web test --run src/pages/ChatPage.test.tsx
pnpm --dir packages/web build
```

**Evidence (2026-08-19):** citation/MCP/session 组合测试 `22 passed`；主工作区 API 非集成全量 `293 passed, 4 deselected`。Web citation 定向 `13 passed`，Web 全量 `61 passed`，typecheck 与 production build 通过。`final.evidence` 只从已查询图状态生成，UI lineage 只使用 `entity_id`，验证申请分别预填 `entity_id`、`source_id` 与 `snippet`；旧 `sources` 展示保留为 fallback。

---

### Task 5: 在数据库只读身份落地前暂停原始 Cypher 工具

**Files:**
- Modify: `packages/api/app/services/knowledge_mcp/server.py`
- Modify: `packages/api/app/services/knowledge_mcp/handlers.py`
- Modify: `packages/api/app/services/chat_agent_runtime/system_prompt.py`
- Modify: `packages/api/tests/services/test_knowledge_mcp.py`
- Modify: `docs/architecture/system-overview.md`
- Modify: `docs/acceptance/chat-mainline.md`

- [x] 先改测试，要求 MCP 只暴露 `search_nodes`、`search_edges`、`expand_neighbors`、`lookup_nodes` 四个 structured tools。
- [x] 从 MCP server 移除 `read_cypher` 注册；保留内部代码仅当其他已验证调用方仍使用它。
- [x] 删除 prompt 和文档中“agent 可执行 readonly cypher”的承诺。
- [x] 在架构文档记录恢复条件：独立 Neo4j READ-only 身份、查询 timeout/limit、procedure allowlist 和对应集成测试全部落地。

```python
# ponytail: raw Cypher stays disabled until MCP uses a database-level read-only identity.
```

**Verification:**

```bash
cd packages/api
uv run pytest tests/services/test_knowledge_mcp.py tests/services/test_chat_agent_runtime.py -q
rg -n "read_cypher|readonly cypher|只读 Cypher" \
  packages/api/app/services/knowledge_mcp/server.py \
  packages/api/app/services/chat_agent_runtime/system_prompt.py \
  docs/architecture/system-overview.md docs/acceptance/chat-mainline.md
```

**Evidence (2026-08-19):** Codex 集成后 MCP/system-prompt/graph-tools targeted tests `9 passed`。`KnowledgeMcpHandlers.read_cypher` 因 `graph_tools.read_cypher` 仍有有效调用而保留，但当前 OpenAI Agents 主链只接 MCP，MCP server 不再注册该工具。

---

### Task 6: 补 CI 门禁与最终验收证据

**Files:**
- Modify: `.github/workflows/ci-fast.yml`
- Modify: `.github/workflows/ci-e2e.yml`
- Modify: `packages/web/src/test/setup.ts`（仅当定位到未 mock XHR 来源）
- Modify: `tests/e2e/mainline.spec.ts`
- Modify: `docs/acceptance/README.md`
- Modify: `docs/acceptance/chat-mainline.md`
- Modify: `docs/architecture/system-overview.md`
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-08-19-trusted-chat-provenance-closure.md`
- Modify: `docs/superpowers/plans/README.md`

- [x] `ci-fast` 增加 `knowledge_model` 与 `data_ingestion` package tests，不重复安装无关依赖。
- [x] 若仓库继续直接 push `main`，让 `ci-e2e` 同时监听 `push: main`；若改为强制 PR，则记录 branch protection 证据，不加重复触发器。
- [x] 定位 Web 测试中的真实 XHR；只补缺失 mock，不用全局吞掉网络错误。
- [x] 运行完整验证；E2E 必须覆盖 chat 页面、一次 citation 展示和 citation 到 provenance 的跳转。
- [x] 用当前真实 provider + Neo4j 对药材、方剂、医案、穴位/治法至少各做一个 smoke；只有实际使用到图证据的问题才要求 citation 非空。
- [x] 回填 fresh 证据、残余风险和验证日期。
- [x] Viewer 验证通过、全部 Done Definition 满足后，把本 plan 改为 `done` 并移入 archive。

**Verification:**

```bash
pnpm run verify
cd packages/knowledge_model && uv run --with pytest pytest tests -q
cd ../data_ingestion && uv run --with pytest pytest tests -q
cd ../..
pnpm run test:integration
CI=true pnpm run test:e2e
git diff --check
```

**Evidence (2026-08-19):** API 非集成 `293 passed, 4 deselected`；Web `61 passed`；knowledge model `27 passed`；data ingestion `70 passed`；integration `4 passed, 293 deselected`；Playwright E2E `1 passed`；shared/Web typecheck、Web build、API ruff/ty、`git diff --check` 通过。真实 Fireworks + MCP + Neo4j smoke：药材 2 次工具调用 / 21 节点 / 19 边 / 2 citations；方剂 3 / 29 / 33 / 1；医案 2 / 5 / 5 / 1；穴位/治法 4 / 11 / 12 / 2。public HF Viewer 验收亦已通过，全部 Done Definition 满足。

## Blocker Resolution

- 用户于 2026-08-19 明确允许 dataset 改为 public。
- public 发布前增加导出层脱敏，原始 JSONL/staging 不改；Viewer 随后通过匿名 200 验收。

## Deferred Follow-Ups

- 可信问答小型 golden set 与持续质量评分：citation 闭环稳定后单独计划
- 登录、专家 RBAC、审计日志：进入多用户试点前单独计划
- 共享会话存储、多 worker、事件驱动与监控：出现部署或负载需求后单独计划
- 新数据源：由 `2026-08-19-fengxi177-tcm-kg-cleaning.md` 接管
