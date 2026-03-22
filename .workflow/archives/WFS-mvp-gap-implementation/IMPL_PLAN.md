# Implementation Plan: MVP 功能缺口补全

## Session: WFS-mvp-gap-implementation
## Parent Session: WFS-2026-03-19-001 (头脑风暴)
## Status: planning
## Created: 2026-03-22

---

## 1. Context Analysis

### 1.1 项目背景

BaiCao ShiTan (白草药坛) 是一个可溯源的中药材知识图谱智能问答系统。在 WFS-2026-03-19-001 头脑风暴中，product-owner 和 system-architect 完成了 14 个 User Stories 的定义和系统架构设计。经过 gap analysis，发现后端 API 大部分已就绪，但前端存在 8 个功能缺口需要补全。

### 1.2 缺口概览

| # | 功能 | 优先级 | 后端就绪 | User Story | 前端状态 |
|---|------|--------|---------|------------|---------|
| 1 | 独立药材详情页 | Must Have | Yes | US-005 | 未实现 |
| 2 | 前端溯源展示组件 | Must Have | Yes | US-007/008 | 未实现 |
| 3 | 答案实体高亮+溯源按钮 | Must Have | Yes | US-001 | 未实现 |
| 4 | 推理链实体可点击 | Must Have | Yes | US-002 | 未实现 |
| 5 | 追问与上下文延续 | Should Have | Yes | US-003 | 部分(已传 sessionId) |
| 6 | 关系路径探索 UI | Should Have | Yes | US-006 | 未实现 |
| 7 | 从答案提交审查申请 | Should Have | Yes | US-010 | 未实现 |
| 8 | 审查结果通知 | Should Have | No | US-012 | 未实现(含后端) |

### 1.3 技术栈

- **后端**: FastAPI, SQLAlchemy 2.0, LangChain, Neo4j, PostgreSQL, Redis
- **前端**: React 18, TypeScript, Ant Design 5, Zustand 5, TanStack Query, @ant-design/graphs
- **工具**: vite-plus (vp), uv, ruff

### 1.4 冲突风险

- **风险等级**: Medium
- **核心冲突点**: `MessageList.tsx` 是多功能集成点，IMPL-3(实体高亮+溯源)和 IMPL-7(审查按钮)都需修改此文件
- **缓解策略**: 按依赖顺序执行，IMPL-1/IMPL-2 先创建独立组件，IMPL-3 再集成到 MessageList，IMPL-7 最后追加审查按钮

---

## 2. Task Breakdown

### Phase 1: 独立组件/页面 (无冲突，可并行)

#### IMPL-1: 独立药材详情页 (HerbDetailPage)
- **Priority**: Must Have | **User Story**: US-005
- **Scope**: 新建 HerbDetailPage.tsx + useHerbDetail.ts + 注册 /herb/:id 路由
- **新建文件**: 2 个 (HerbDetailPage.tsx, useHerbDetail.ts)
- **修改文件**: 2 个 (App.tsx 路由注册, NodeDetail.tsx 导航入口)
- **依赖**: 无
- **Task JSON**: [.task/IMPL-1.json](./.task/IMPL-1.json)

#### IMPL-2: 前端溯源展示组件 (ProvenanceDisplay)
- **Priority**: Must Have | **User Stories**: US-007, US-008
- **Scope**: 新建 EvidenceList/LineageChain/EvidenceDetail 组件套件 + useProvenance hook
- **新建文件**: 4 个 (EvidenceList.tsx, LineageChain.tsx, EvidenceDetail.tsx, useProvenance.ts)
- **修改文件**: 0 个
- **依赖**: 无 (可与 IMPL-1 并行)
- **Task JSON**: [.task/IMPL-2.json](./.task/IMPL-2.json)

### Phase 2: 集成到现有页面 (有序执行)

#### IMPL-3: 答案实体高亮 + 溯源按钮 (MessageList 集成)
- **Priority**: Must Have | **User Story**: US-001
- **Scope**: 新建 EntityHighlighter 组件，修改 MessageList 渲染逻辑，扩展 Message 类型
- **新建文件**: 1 个 (EntityHighlighter.tsx)
- **修改文件**: 3 个 (MessageList.tsx, chat.ts, useChat.ts)
- **依赖**: IMPL-1 (实体点击跳转 /herb/:id), IMPL-2 (溯源展示组件)
- **Task JSON**: [.task/IMPL-3.json](./.task/IMPL-3.json)

#### IMPL-4: 推理链实体可点击 (ReasoningChain 增强)
- **Priority**: Must Have | **User Story**: US-002
- **Scope**: 修改 ReasoningChain.tsx，使用 entities 字段渲染可点击实体
- **新建文件**: 0 个
- **修改文件**: 1 个 (ReasoningChain.tsx)
- **依赖**: IMPL-1 (实体点击跳转 /herb/:id)
- **Task JSON**: [.task/IMPL-4.json](./.task/IMPL-4.json)

### Phase 3: 独立增强功能 (与 Phase 2 无冲突)

#### IMPL-5: 追问与上下文延续 (多轮对话)
- **Priority**: Should Have | **User Story**: US-003
- **Scope**: 增强 chatStore 和 useChat，添加 session 自动创建和新话题功能
- **新建文件**: 0 个
- **修改文件**: 3 个 (chatStore.ts, useChat.ts, ChatPage.tsx)
- **依赖**: 无
- **Task JSON**: [.task/IMPL-5.json](./.task/IMPL-5.json)

#### IMPL-6: 关系路径探索 UI (GraphPage 增强)
- **Priority**: Should Have | **User Story**: US-006
- **Scope**: 新增 graphApi.getPath 方法，新建 PathExplorer 组件，集成到 GraphPage
- **新建文件**: 1 个 (PathExplorer.tsx)
- **修改文件**: 2 个 (api.ts, GraphPage.tsx)
- **依赖**: 无
- **Task JSON**: [.task/IMPL-6.json](./.task/IMPL-6.json)

### Phase 4: 跨模块功能 (依赖前序任务)

#### IMPL-7: 从答案提交审查申请 (MessageList 审查按钮)
- **Priority**: Should Have | **User Story**: US-010
- **Scope**: 新建 ReviewRequestModal，在 MessageList 添加'申请审查'按钮
- **新建文件**: 1 个 (ReviewRequestModal.tsx)
- **修改文件**: 1 个 (MessageList.tsx)
- **依赖**: IMPL-3 (MessageList 实体高亮改造完成后再追加)
- **Task JSON**: [.task/IMPL-7.json](./.task/IMPL-7.json)

#### IMPL-8: 审查结果通知 (通知模块)
- **Priority**: Should Have | **User Story**: US-012
- **Scope**: 后端通知 API + 前端通知 store/hook/组件，唯一需要后端开发的任务
- **新建文件**: 6 个 (后端 notification.py model + api, 前端 notificationStore.ts + useNotifications.ts + NotificationBell.tsx)
- **修改文件**: 3 个 (main.py, api.ts, Header.tsx)
- **依赖**: IMPL-7 (审查提交流程完成后才有通知需求)
- **Task JSON**: [.task/IMPL-8.json](./.task/IMPL-8.json)

---

## 3. Execution Strategy

### 3.1 依赖图

```
IMPL-1 (药材详情页) ─────┬──→ IMPL-3 (实体高亮+溯源) ──→ IMPL-7 (审查按钮) ──→ IMPL-8 (通知)
                          │
IMPL-2 (溯源组件) ────────┘
                              IMPL-4 (推理链可点击)
                              ↑
IMPL-1 (药材详情页) ──────────┘

IMPL-5 (追问上下文) ──── 独立，无依赖
IMPL-6 (路径探索) ────── 独立，无依赖
```

### 3.2 执行顺序

| 执行批次 | 任务 | 可并行 | 预计复杂度 |
|---------|------|--------|-----------|
| Batch 1 | IMPL-1, IMPL-2 | Yes (无共享文件) | 中 |
| Batch 2 | IMPL-3, IMPL-4, IMPL-5, IMPL-6 | IMPL-4/5/6 可并行; IMPL-3 需等 Batch 1 | 高(IMPL-3), 低-中(IMPL-4/5/6) |
| Batch 3 | IMPL-7 | No (需等 IMPL-3) | 低-中 |
| Batch 4 | IMPL-8 | No (需等 IMPL-7) | 中-高(含后端) |

### 3.3 执行模式

全部任务使用 **agent 直接执行**模式，无需 CLI 工具辅助。每个任务由 agent 独立完成，按依赖顺序执行。

---

## 4. File Impact Analysis

### 4.1 新建文件清单 (15 个)

| 文件 | 创建任务 | 类型 |
|------|---------|------|
| packages/web/src/pages/HerbDetailPage.tsx | IMPL-1 | 页面组件 |
| packages/web/src/hooks/useHerbDetail.ts | IMPL-1 | Hook |
| packages/web/src/components/provenance/EvidenceList.tsx | IMPL-2 | 组件 |
| packages/web/src/components/provenance/LineageChain.tsx | IMPL-2 | 组件 |
| packages/web/src/components/provenance/EvidenceDetail.tsx | IMPL-2 | 组件 |
| packages/web/src/hooks/useProvenance.ts | IMPL-2 | Hook |
| packages/web/src/components/chat/EntityHighlighter.tsx | IMPL-3 | 组件 |
| packages/web/src/components/chat/ReviewRequestModal.tsx | IMPL-7 | 组件 |
| packages/web/src/components/graph/PathExplorer.tsx | IMPL-6 | 组件 |
| packages/web/src/stores/notificationStore.ts | IMPL-8 | Store |
| packages/web/src/hooks/useNotifications.ts | IMPL-8 | Hook |
| packages/web/src/components/NotificationBell.tsx | IMPL-8 | 组件 |
| packages/api/app/api/notification.py | IMPL-8 | API 路由 |
| packages/api/app/models/notification.py | IMPL-8 | Model |

### 4.2 修改文件清单

| 文件 | 修改任务 | 修改内容 |
|------|---------|---------|
| packages/web/src/App.tsx | IMPL-1 | 新增 /herb/:id 路由 |
| packages/web/src/components/graph/NodeDetail.tsx | IMPL-1 | 添加'查看完整详情'按钮 |
| packages/web/src/types/chat.ts | IMPL-3 | Message 新增 entities 字段 |
| packages/web/src/hooks/useChat.ts | IMPL-3, IMPL-5 | entities 映射 + session 管理 |
| packages/web/src/components/chat/MessageList.tsx | IMPL-3, IMPL-7 | 实体高亮 + 溯源按钮 + 审查按钮 |
| packages/web/src/components/chat/ReasoningChain.tsx | IMPL-4 | 实体可点击 |
| packages/web/src/stores/chatStore.ts | IMPL-5 | 新增 conversationContext + startNewTopic |
| packages/web/src/pages/ChatPage.tsx | IMPL-5 | 新话题按钮 |
| packages/web/src/services/api.ts | IMPL-6, IMPL-8 | graphApi.getPath + notificationApi |
| packages/web/src/pages/GraphPage.tsx | IMPL-6 | 集成 PathExplorer |
| packages/web/src/components/Header.tsx | IMPL-8 | 集成 NotificationBell |
| packages/api/app/main.py | IMPL-8 | 注册 notification router |

### 4.3 冲突热点

- **MessageList.tsx**: IMPL-3 (实体高亮+溯源) -> IMPL-7 (审查按钮)，严格按序执行
- **useChat.ts**: IMPL-3 (entities 映射) 和 IMPL-5 (session 管理) 修改不同区域，低冲突
- **api.ts**: IMPL-6 (graphApi.getPath) 和 IMPL-8 (notificationApi) 修改不同区域，低冲突

---

## 5. Risk Assessment

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| MessageList.tsx 多次修改冲突 | 高 | 中 | 严格按 IMPL-3 -> IMPL-7 顺序执行 |
| 后端通知 API 的 DB migration | 中 | 高 | IMPL-8 需要 Alembic migration，确认 PostgreSQL 连接可用 |
| ReasoningStep.entities 是 string[] 而非结构化对象 | 低 | 确定 | IMPL-4 中使用 graphApi.search 解析实体类型，或统一用 /graph/:name 跳转 |
| provenanceApi 返回的 Record<string, unknown> 类型过于宽泛 | 低 | 确定 | IMPL-2 中需要做类型断言或渐进式类型收窄 |
| chat_service.py 实体提取格式与前端 entities 字段不匹配 | 中 | 低 | IMPL-3 pre_analysis 中确认后端返回格式，必要时做适配层 |

---

## 6. Quantification Summary

| 指标 | 数值 |
|------|------|
| 总任务数 | 8 |
| Must Have 任务 | 4 (IMPL-1/2/3/4) |
| Should Have 任务 | 4 (IMPL-5/6/7/8) |
| 新建前端文件 | 12 |
| 新建后端文件 | 2 |
| 修改前端文件 | 11 |
| 修改后端文件 | 1 |
| 新建组件 | 8 |
| 新建 Hooks | 4 |
| 新建 Stores | 1 |
| 涉及 User Stories | 8 (US-001/002/003/005/006/007/008/010/012) |

---

## 7. Verification Strategy

每个任务完成后需通过:
1. **构建验证**: `vp build` exit code 0 (前端)
2. **语法检查**: `ruff check` (后端, 仅 IMPL-8)
3. **文件存在性**: ls 验证新建文件
4. **功能标记**: grep 验证关键代码特征
5. **集成验证**: 任务间依赖的组件接口匹配

全部任务完成后:
- 前端完整构建: `cd packages/web && vp build`
- 后端语法检查: `cd packages/api && ruff check app/`
- 前端测试: `cd packages/web && vp test` (若有对应测试)
