# BaiCao 全阶段补齐实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 补齐 IMPL_PLAN.md Phase 2-5 所有未实现目标，从"骨架 + TDD 测试"升级为功能完整系统。

**Architecture:** 4 个方向分阶段推进——数据层完善 → 溯源 API 暴露 → LLM 集成 + SSE 流式 → 前端工程化。遵循 contract-first 原则：模型/类型先行，服务逻辑次之，消费端最后。

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0 async, Alembic, LangChain, Neo4j async, React 18, TypeScript, vite-plus, Zustand, TanStack Query

---

## Target File Map

### Phase 1: 数据层补全

- Modify: `packages/api/app/models/herb.py`
- Create: `packages/api/app/models/evidence.py`
- Modify: `packages/api/app/models/__init__.py`
- Create: `packages/api/alembic.ini`
- Create: `packages/api/alembic/env.py`
- Create: `packages/api/alembic/versions/001_initial_schema.py`
- Modify: `packages/shared/types/index.ts`

### Phase 2: 溯源 API

- Create: `packages/api/app/api/provenance.py`
- Create: `packages/api/app/schemas/provenance.py`
- Modify: `packages/api/app/main.py`
- Modify: `packages/web/src/services/api.ts`
- Create: `packages/api/tests/api/test_provenance_routes.py`

### Phase 3: LLM + SSE

- Modify: `packages/api/app/services/chat_service.py`
- Modify: `packages/api/app/api/chat.py`
- Modify: `packages/api/app/core/config.py`
- Modify: `packages/web/src/pages/ChatPage.tsx`
- Modify: `packages/web/src/services/api.ts`
- Modify: `packages/shared/types/index.ts`

### Phase 4: 前端工程化

- Create: `packages/web/src/types/index.ts`
- Create: `packages/web/src/types/graph.ts`
- Create: `packages/web/src/types/chat.ts`
- Create: `packages/web/src/hooks/useChat.ts`
- Create: `packages/web/src/hooks/useGraph.ts`
- Create: `packages/web/src/hooks/useVerification.ts`
- Create: `packages/web/src/stores/chatStore.ts`
- Create: `packages/web/src/stores/graphStore.ts`
- Create: `packages/web/src/components/chat/MessageList.tsx`
- Create: `packages/web/src/components/chat/MessageInput.tsx`
- Create: `packages/web/src/components/chat/ReasoningChain.tsx`
- Create: `packages/web/src/components/graph/GraphDetail.tsx`
- Create: `packages/web/src/components/graph/NodeCard.tsx`
- Modify: `packages/web/src/pages/ChatPage.tsx`
- Modify: `packages/web/src/pages/GraphPage.tsx`
- Modify: `packages/web/src/services/api.ts`
- Modify: `packages/web/package.json`

### Phase 5: 集成验证

- Modify: `packages/api/app/kg/graph_service.py`
- Modify: `docs/architecture/data-model.md`
- Modify: `docs/acceptance/chat-mainline.md`
- Modify: `IMPL_PLAN.md`

---

## Task 1: 数据层补全 — HerbModel 字段 + Evidence 模型 + Alembic

**Files:**
- Modify: `packages/api/app/models/herb.py`
- Create: `packages/api/app/models/evidence.py`
- Modify: `packages/api/app/models/__init__.py`
- Create: `packages/api/alembic.ini`
- Create: `packages/api/alembic/env.py`
- Create: `packages/api/alembic/versions/001_initial_schema.py`
- Modify: `packages/shared/types/index.ts`
- Test: `cd packages/api && .venv/bin/python -c "from app.models import HerbModel, EvidenceModel; print('OK')"`

- [x] **Step 1: 扩展 HerbModel 字段**

在 `packages/api/app/models/herb.py` 中补充以下字段：
- `english_name: Mapped[Optional[str]]` — String(200)
- `alias: Mapped[Optional[list]]` — JSON 类型，存储别名列表
- `efficacy: Mapped[Optional[list]]` — JSON 类型，功效列表
- `flavor: Mapped[Optional[list]]` — JSON 类型，性味列表
- `meridian: Mapped[Optional[list]]` — JSON 类型，归经列表
- `dosage: Mapped[Optional[str]]` — Text 类型，用法用量
- `contraindications: Mapped[Optional[str]]` — Text 类型，禁忌

保持现有字段不变，仅追加新字段。

- [x] **Step 2: 创建 Evidence 模型**

新建 `packages/api/app/models/evidence.py`：
```python
class EvidenceModel(Base):
    __tablename__ = "evidences"
    id: UUID (PK)
    herb_id: UUID (FK -> herbs.id)
    source_id: UUID (FK -> sources.id)
    content: Text
    quote: Text (原文引用)
    chapter: Optional[str]
    page_number: Optional[str]
    verification_status: String (default "pending")
    confidence_score: Float (default 0.0)
    extraction_method: String (default "manual")
    created_at: DateTime
```

在 `__init__.py` 中导出 EvidenceModel。

- [x] **Step 3: 初始化 Alembic**

```bash
cd packages/api && .venv/bin/python -m alembic init alembic
```

修改 `alembic/env.py` 配置异步引擎（使用 asyncpg），引入所有模型的 Base.metadata。
修改 `alembic.ini` 的 sqlalchemy.url 指向配置中的 DATABASE_URL。

- [x] **Step 4: 生成初始迁移**

```bash
cd packages/api && .venv/bin/python -m alembic revision --autogenerate -m "initial schema"
```

验证生成的迁移脚本包含 herbs、sources、users、verifications、verification_evidences、evidences 表。

- [x] **Step 5: 同步 shared types**

在 `packages/shared/types/index.ts` 中更新 Herb 接口，补充 english_name, alias, efficacy, flavor, meridian, dosage, contraindications 字段。

新增 Evidence 接口定义。

- [x] **Step 6: 验证**

```bash
cd packages/api && .venv/bin/python -c "from app.models import HerbModel, EvidenceModel; print('Models OK')"
cd packages/api && .venv/bin/python -m pytest tests/ -v --tb=short
```

确认现有 146 个测试不退化。

## Task 2: 溯源 API 端点暴露

**Files:**
- Create: `packages/api/app/schemas/provenance.py`
- Create: `packages/api/app/api/provenance.py`
- Modify: `packages/api/app/main.py`
- Modify: `packages/web/src/services/api.ts`
- Create: `packages/api/tests/api/test_provenance_routes.py`
- Test: `cd packages/api && .venv/bin/python -m pytest tests/api/test_provenance_routes.py -v`

**Depends on:** Task 1（Evidence 模型影响 schema 设计）

- [x] **Step 1: 创建 Provenance schemas**

新建 `packages/api/app/schemas/provenance.py`：
- `EvidenceCreate` — 创建证据请求体
- `EvidenceResponse` — 证据详情响应
- `LinkSourceRequest` — 关联来源请求体
- `LineageResponse` — 溯源链响应
- `DerivationsResponse` — 来源派生响应

- [x] **Step 2: 创建 Provenance router**

新建 `packages/api/app/api/provenance.py`，5 个端点：

| Method | Path | Handler | 调用 ProvenanceService 方法 |
|--------|------|---------|---------------------------|
| POST | `/provenance/evidence` | create_evidence | create_evidence |
| GET | `/provenance/evidence/{id}` | get_evidence | get_evidence |
| POST | `/provenance/evidence/{id}/link-source` | link_source | link_evidence_to_source |
| GET | `/provenance/entity/{id}/lineage` | get_lineage | query_entity_lineage |
| GET | `/provenance/source/{id}/derivations` | get_derivations | query_source_derivations |

- [x] **Step 3: 注册路由**

在 `packages/api/app/main.py` 中添加：
```python
from .api.provenance import router as provenance_router
app.include_router(provenance_router, prefix="/provenance", tags=["provenance"])
```

- [x] **Step 4: 前端 API 调用**

在 `packages/web/src/services/api.ts` 中新增 `provenanceApi` 对象，封装 5 个端点调用。

- [x] **Step 5: 编写测试**

新建 `packages/api/tests/api/test_provenance_routes.py`，覆盖 5 个端点的正常路径和错误路径。

- [x] **Step 6: 验证**

```bash
cd packages/api && .venv/bin/python -m pytest tests/api/test_provenance_routes.py -v --tb=short
cd packages/api && .venv/bin/python -m pytest tests/ --tb=short  # 全量不退化
```

## Task 3: LLM 集成 + SSE 流式响应

**Files:**
- Modify: `packages/api/app/services/chat_service.py`
- Modify: `packages/api/app/api/chat.py`
- Modify: `packages/api/app/core/config.py`
- Modify: `packages/web/src/pages/ChatPage.tsx`
- Modify: `packages/web/src/services/api.ts`
- Modify: `packages/shared/types/index.ts`
- Test: `curl -N -X POST http://localhost:8000/chat/stream -H "Content-Type: application/json" -d '{"question":"人参有什么功效？"}'`

**Depends on:** Task 1（HerbModel 字段丰富化影响图谱查询内容）

- [x] **Step 1: 确认 LLM 配置**

检查 `packages/api/app/core/config.py` 中 OpenAI 相关配置字段完整性。确保 `openai_api_key`、`openai_model`（默认 gpt-4o-mini）、`openai_base_url`（可选，支持兼容 API）。

- [x] **Step 2: ChatService 集成 LangChain**

修改 `packages/api/app/services/chat_service.py`：

1. 新增 `_get_llm()` 方法，返回 `ChatOpenAI` 实例（从 langchain_openai 导入）
2. 新增 `answer_question_stream()` 异步生成器方法：
   - 第一步：调用现有 `_extract_entities()` 和 `_query_knowledge_graph()`
   - 第二步：构建带图谱上下文的 prompt
   - 第三步：用 `llm.astream()` 逐 token 生成
   - yield SSE 格式事件：`event: reasoning` → `event: token` → `event: done`
3. 保留现有 `answer_question()` 同步方法作为 fallback（当无 API key 时使用规则引擎）

- [x] **Step 3: 新增 SSE 端点**

在 `packages/api/app/api/chat.py` 中新增：

```python
@router.post("/stream")
async def stream_answer(request: QuestionRequest, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        async for event in chat_service.answer_question_stream(...):
            yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

- [x] **Step 4: 前端 SSE 消费**

修改 `packages/web/src/pages/ChatPage.tsx`：

1. 新增 `streamChat()` 函数，使用 `fetch` + `ReadableStream` 消费 SSE
2. 解析 `event: reasoning` 更新推理链面板
3. 解析 `event: token` 逐字追加到回答区域
4. 解析 `event: done` 标记完成
5. 保留同步调用作为 fallback（SSE 失败时降级）

- [x] **Step 5: 同步 shared types**

在 `packages/shared/types/index.ts` 中新增：

```typescript
interface SSEEvent {
  type: 'reasoning' | 'token' | 'sources' | 'done' | 'error'
  data: Record<string, unknown>
}
```

- [x] **Step 6: 验证**

```bash
# 后端 SSE 验证
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"陈皮有什么功效？"}'

# 前端验证
cd packages/web && pnpm vp build  # 构建不报错
# 手动测试：打开 ChatPage，发送问题，观察流式输出
```

## Task 4: 前端工程化

**Files:**
- Create: `packages/web/src/types/index.ts`, `graph.ts`, `chat.ts`
- Create: `packages/web/src/hooks/useChat.ts`, `useGraph.ts`, `useVerification.ts`
- Create: `packages/web/src/stores/chatStore.ts`, `graphStore.ts`
- Create: `packages/web/src/components/chat/MessageList.tsx`, `MessageInput.tsx`, `ReasoningChain.tsx`
- Create: `packages/web/src/components/graph/GraphDetail.tsx`, `NodeCard.tsx`
- Modify: `packages/web/src/pages/ChatPage.tsx`, `GraphPage.tsx`
- Modify: `packages/web/src/services/api.ts`
- Modify: `packages/web/package.json`
- Test: `cd packages/web && pnpm vp build && pnpm vp test`

**Depends on:** Task 3（SSE 消费逻辑影响 useChat hook 设计）

- [x] **Step 1: 安装依赖**

```bash
cd packages/web && pnpm add @tanstack/react-query zustand
```

在 App.tsx 中包裹 `QueryClientProvider`。

- [x] **Step 2: 创建 types/ 目录**

从 `api.ts` 和页面文件中提取类型定义到：
- `types/index.ts` — 通用类型（ApiResponse, PaginatedResponse 等）
- `types/graph.ts` — 图谱类型（GraphNode, GraphEdge, HerbGraph 等）
- `types/chat.ts` — 对话类型（ChatMessage, ReasoningChain, SSEEvent 等）

更新 api.ts 的类型引用。

- [x] **Step 3: 创建 hooks/**

- `useChat.ts` — 封装对话逻辑（发送问题、SSE 流式、会话管理），使用 TanStack Query 的 useMutation
- `useGraph.ts` — 封装图谱查询（搜索、节点详情、herb graph），使用 useQuery
- `useVerification.ts` — 封装验证流程（列表、创建、审核）

- [x] **Step 4: 创建 stores/**

- `chatStore.ts` — Zustand store：messages, currentSession, isStreaming
- `graphStore.ts` — Zustand store：selectedNode, graphData, searchResults

- [x] **Step 5: 抽取 Chat 组件**

从 ChatPage.tsx 中抽取：
- `components/chat/MessageList.tsx` — 消息列表渲染
- `components/chat/MessageInput.tsx` — 输入框 + 发送按钮 + 示例问题
- `components/chat/ReasoningChain.tsx` — 推理链展示（Collapse 折叠面板）

ChatPage.tsx 瘦身为组合这些组件 + useChat hook 的薄层。

- [x] **Step 6: 抽取 Graph 组件**

从 GraphPage.tsx 中抽取：
- `components/graph/GraphDetail.tsx` — 节点/边详情面板（Drawer 内容）
- `components/graph/NodeCard.tsx` — 节点信息卡片

GraphPage.tsx 瘦身为图谱可视化容器 + useGraph hook。

- [x] **Step 7: 验证**

```bash
cd packages/web && pnpm vp build  # 构建通过
cd packages/web && pnpm vp test   # 测试通过
# 手动验证：所有页面功能不退化
```

## Task 5: 集成验证与文档收尾

**Files:**
- Modify: `packages/api/app/kg/graph_service.py`
- Modify: `docs/architecture/data-model.md`
- Modify: `docs/acceptance/chat-mainline.md`
- Modify: `IMPL_PLAN.md`
- Test: `cd packages/api && .venv/bin/python -m pytest tests/ -v --tb=short`

**Depends on:** Task 1-4

- [x] **Step 1: 补充 GraphService 缺失方法**

在 `packages/api/app/kg/graph_service.py` 中新增：
- `create_disease(name, description)` — Disease 节点创建
- `link_herb_treats(herb_name, disease_name)` — TREATS 关系
- `link_herb_similar(herb_name_1, herb_name_2, similarity_score)` — SIMILAR_TO 关系

- [x] **Step 2: 全量测试验证**

```bash
cd packages/api && .venv/bin/python -m pytest tests/ -v --tb=short --cov
```

确认所有测试通过，无退化。

- [x] **Step 3: 更新架构文档**

更新 `docs/architecture/data-model.md`：
- 补充 Evidence 模型描述
- 补充 HerbModel 新增字段
- 更新图谱关系类型列表（TREATS, SIMILAR_TO）

- [x] **Step 4: 更新验收文档**

更新 `docs/acceptance/chat-mainline.md`：
- 新增 SSE 流式验收步骤
- 新增 LLM 集成验收标准（含降级 fallback）

- [x] **Step 5: 标记 IMPL_PLAN.md 进度**

在 IMPL_PLAN.md 各 Phase 中标注完成状态。
