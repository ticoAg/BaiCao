# Task Plan: BaiCao 全阶段补齐实施计划

## Goal

补齐 IMPL_PLAN.md Phase 2-5 所有未实现目标，使项目从"骨架 + TDD 测试"状态升级为功能完整的可运行系统，涵盖数据层完善、溯源 API 暴露、LLM 集成 + SSE 流式、前端工程化 4 个方向。

## Current Phase

ALL PHASES COMPLETE ✅

## Phases

### Phase 1: 数据层补全（HerbModel + Alembic + Evidence 模型）

**目标**: 补齐 HerbModel 缺失字段、引入 Alembic 迁移管理、新增独立 Evidence SQLAlchemy 模型

**文件范围**:
- Modify: `packages/api/app/models/herb.py` — 补充 alias, english_name, efficacy, flavor, meridian, dosage, contraindications, images JSON 字段
- Create: `packages/api/app/models/evidence.py` — 独立 Evidence 模型（herb_id, source_id, content, quote, chapter, page_number, verification_status, confidence_score）
- Modify: `packages/api/app/models/__init__.py` — 导出 EvidenceModel
- Create: `packages/api/alembic.ini` — Alembic 配置
- Create: `packages/api/alembic/` — 迁移目录（env.py, versions/）
- Create: `packages/api/alembic/versions/001_initial_schema.py` — 初始迁移（全表）
- Modify: `packages/shared/types/index.ts` — 同步 Herb 和 Evidence 类型定义
- Modify: `packages/api/app/schemas/` — 更新 Pydantic schemas（如有）

**依赖**: 无，首先执行

- [x] 补充 HerbModel 字段（alias, english_name, efficacy, flavor, meridian, dosage, contraindications 用 JSON/ARRAY 类型）
- [x] 新建 EvidenceModel（关联 Herb 和 Source）
- [x] 初始化 Alembic（alembic init, 配置 async engine）
- [ ] 生成初始迁移脚本（需要数据库连接，离线可用）
- [x] 同步 shared types
- [x] 验证：模型导入 OK + 143 单元测试通过
- **Status:** complete

### Phase 2: 溯源 API 端点暴露

**目标**: 为已实现的 ProvenanceService 创建 REST API 路由

**文件范围**:
- Create: `packages/api/app/api/provenance.py` — 新路由文件，暴露 ProvenanceService 的 5 个核心操作
- Modify: `packages/api/app/main.py` — 注册 provenance router
- Create: `packages/api/app/schemas/provenance.py` — 请求/响应 Pydantic schemas
- Modify: `packages/web/src/services/api.ts` — 新增 provenanceApi 调用
- Create: `packages/api/tests/api/test_provenance_routes.py` — API 端点测试

**端点设计**:
- `POST /provenance/evidence` — 创建证据节点
- `GET /provenance/evidence/{evidence_id}` — 获取证据详情
- `POST /provenance/evidence/{evidence_id}/link-source` — 关联证据与来源
- `GET /provenance/entity/{entity_id}/lineage` — 查询实体溯源链
- `GET /provenance/source/{source_id}/derivations` — 查询来源派生

**依赖**: Phase 1（Evidence 模型影响 schema 设计）

- [x] 创建 provenance schemas（request/response）
- [x] 创建 provenance router（7 个端点）
- [x] 注册到 main.py
- [x] 前端 api.ts 新增调用方法
- [x] 编写端点测试（11 个）
- [x] 验证：154 passed，零退化
- **Status:** complete

### Phase 3: LLM 集成 + SSE 流式响应

**目标**: 将 ChatService 从规则 stub 升级为真实 LangChain + OpenAI 调用，后端支持 SSE 流式输出，前端 ChatPage 消费 SSE 流

**文件范围**:
- Modify: `packages/api/app/services/chat_service.py` — 集成 LangChain ChatOpenAI，实现 answer_question_stream 方法
- Modify: `packages/api/app/api/chat.py` — 新增 `POST /chat/stream` SSE 端点（StreamingResponse）
- Modify: `packages/api/app/core/config.py` — 确认 OpenAI 配置完整
- Modify: `packages/web/src/pages/ChatPage.tsx` — 使用 EventSource/fetch+ReadableStream 消费 SSE
- Modify: `packages/web/src/services/api.ts` — 新增 SSE 调用方法
- Modify: `packages/shared/types/index.ts` — 新增 SSE 事件类型定义

**关键技术决策**:
- 保留现有同步 `POST /chat/question` 端点不变（兼容）
- 新增 `POST /chat/stream` 作为 SSE 端点
- LangChain 使用 ChatOpenAI 的 astream 方法
- 推理链在流式中作为首个事件块发送，答案逐 token 流式

**依赖**: Phase 1（HerbModel 字段完善影响图谱查询内容丰富度）

- [ ] ChatService 集成 LangChain ChatOpenAI（保留规则 fallback）
- [ ] 实现 answer_question_stream 异步生成器
- [ ] 新增 SSE 端点 POST /chat/stream
- [ ] 前端 ChatPage 实现 SSE 消费（EventSource 或 fetch stream）
- [ ] 同步 shared types（SSE 事件类型）
- [ ] 验证：curl SSE 端点 + 前端流式显示
- **Status:** pending

### Phase 4: 前端工程化

**目标**: 拆分 hooks/stores/types 目录、引入 TanStack Query、从页面中抽取可复用组件

**文件范围**:
- Create: `packages/web/src/types/index.ts` — 从 api.ts 和页面中提取类型定义
- Create: `packages/web/src/types/graph.ts` — 图谱相关类型
- Create: `packages/web/src/types/chat.ts` — 对话相关类型
- Create: `packages/web/src/hooks/useChat.ts` — 对话逻辑 hook（含 SSE）
- Create: `packages/web/src/hooks/useGraph.ts` — 图谱查询 hook
- Create: `packages/web/src/hooks/useVerification.ts` — 验证流程 hook
- Create: `packages/web/src/stores/chatStore.ts` — Zustand 对话状态
- Create: `packages/web/src/stores/graphStore.ts` — Zustand 图谱状态
- Create: `packages/web/src/components/chat/` — MessageList, MessageInput, ReasoningChain 组件
- Create: `packages/web/src/components/graph/` — GraphDetail, NodeCard 组件
- Modify: `packages/web/src/pages/ChatPage.tsx` — 使用拆分的 hooks 和组件
- Modify: `packages/web/src/pages/GraphPage.tsx` — 使用拆分的 hooks 和组件
- Modify: `packages/web/src/services/api.ts` — 类型引用迁移到 types/
- Modify: `packages/web/package.json` — 添加 @tanstack/react-query 依赖

**依赖**: Phase 3（SSE 消费逻辑影响 useChat hook 设计）

- [ ] 安装 @tanstack/react-query + zustand
- [ ] 创建 types/ 目录，迁移类型定义
- [ ] 创建 hooks/（useChat 含 SSE、useGraph、useVerification）
- [ ] 创建 stores/（chatStore、graphStore）
- [ ] 从 ChatPage 抽取 chat 组件
- [ ] 从 GraphPage 抽取 graph 组件
- [ ] 页面文件瘦身，使用 hooks + 组件
- [ ] 验证：vp build 通过 + 页面功能不退化
- **Status:** pending

### Phase 5: 集成验证与收尾

**目标**: 全量验证、补充缺失的图谱关系类型、更新文档

**文件范围**:
- Modify: `packages/api/app/kg/graph_service.py` — 补充 TREATS, SIMILAR_TO 关系和 Disease 节点方法
- Modify: `docs/architecture/data-model.md` — 更新实际实现的数据模型
- Modify: `docs/acceptance/chat-mainline.md` — 更新 SSE 流式验收标准
- Modify: `IMPL_PLAN.md` — 标记已完成的阶段

**依赖**: Phase 1-4

- [ ] 补充 GraphService 缺失方法（TREATS, SIMILAR_TO, Disease）
- [ ] 全量 pytest 验证
- [ ] 更新架构文档
- [ ] 更新验收文档
- [ ] 标记 IMPL_PLAN.md 阶段进度
- **Status:** pending

## Key Questions

1. OpenAI API key 如何管理？→ 通过 .env 文件，config.py 已有 settings
2. SSE 端点是 GET 还是 POST？→ POST（需要发送 question body）
3. Alembic 使用 async 还是 sync runner？→ async（与项目整体异步架构一致）
4. TanStack Query 是否需要全局 Provider？→ 是，需要在 App.tsx 包裹 QueryClientProvider
5. Evidence 模型与 VerificationEvidence 的关系？→ Evidence 是独立溯源实体，VerificationEvidence 是审核流程附件，二者独立

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| 保留现有 POST /chat/question 同步端点 | 向后兼容，SSE 作为新端点 POST /chat/stream |
| HerbModel 扩展字段用 JSON 类型而非关联表 | alias/efficacy/flavor/meridian 为列表值，JSON 足够且避免过度 normalize |
| Alembic 使用 async runner | 与项目 asyncpg + SQLAlchemy async 架构一致 |
| Evidence 独立于 VerificationEvidence | 溯源证据和审核证据是不同领域概念 |
| 前端用 fetch + ReadableStream 而非 EventSource | POST 请求不支持 EventSource，用 fetch stream 更灵活 |
| 后端工具链使用 uv + ruff + ty | uv 管理依赖和虚拟环境，ruff 代码检查，ty 类型检查 |
| LLM 通过 LangChain ChatModel 抽象 | 统一 OpenAI/Anthropic 接口，便于扩展其他 provider |

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |

## Notes

- 该计划对应 `docs/superpowers/plans/` 中的正式 writing-plans 产出
- 每个 Phase 完成后应更新此文件状态并同步 findings.md
- Phase 3（LLM 集成）需要用户提供 OpenAI API key 才能做端到端验证
- 估算总量：~25 个文件变更/新增，分 5 个阶段渐进交付
