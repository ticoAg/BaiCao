<!--
---
doc_kind: acceptance
status: stable
tags: ["acceptance", "chat", "llm", "graph"]
summary: 智能问答主链路验收
audience: developer
---
-->

# 智能问答主链路验收

## 1. 概述

- 功能名称：智能问答主链路
- 验收目标：验证问答页面、`/api/v1/chat/stream` 单入口、自然语言回答、agent 工具过程流和可展开依据子图形成完整闭环
- 对应需求：图谱增强智能问答
- 对应计划：`docs/superpowers/plans/archive/2026-04-20-chat-deepagents-graph-agent.md`
- 当前版本 / 日期：pydantic-ai-slim Graph Agent / 2026-09-06

## 2. 验收范围

### 包含

- 问答页面提问
- 后端 chat 单入口响应
- 每轮回答自然语言展示
- provider 原生 reasoning（若 provider 返回）
- agent 工具调用、参数、结果摘要流式展示
- 配置了 TypeSafe 时，工具时间线中出现 `judge`；判定标准来自服务端固定问题，不来自模型临场编写
- 每轮回答可展开依据子图
- 结构化 citation、证据来源、推理轨迹和工具调用展示
- citation 以实体 ID 打开 lineage，并分别预填实体、来源和证据摘录到验证申请
- 图谱预览跳转

### 不包含

- 跨进程 / 跨重启的持久化会话恢复（当前仅支持单进程内 `message_history` registry）

## 3. 前置条件

### 环境

- 运行方式：本地 `make` + tmux 单 session
- 依赖服务：FastAPI、Neo4j、PostgreSQL、Vite
- 样例数据：demo 用户、来源和”人参”图谱
- LLM 配置（必需）：需要提供可用的 `LLM_PROVIDER` 与对应 API key；当前 chat 主链不再降级到旧规则问答链
- 结构化判定（可选）：`TYPESAFE_API_KEY` 与 `TYPESAFE_BASE_URL`。未配置时问答仍只走图工具

### 启动命令

```bash
make deps up
make stack up
corepack pnpm --dir packages/web test --run
```

## 4. 验收步骤

### Step 1

- 操作：打开问答页
- 命令 / 页面入口：`http://localhost:3000/chat`

### Step 2

- 操作：输入“人参有什么功效？”
- 命令 / 页面入口：问答输入框

### Step 3

- 操作：验证 API 响应
- 命令 / 页面入口：

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"question":"人参有什么功效？","session_id":"acceptance-chat-1"}'
```

### Step 4

- 操作：输入“治感冒的中药都有哪些，怎么做”或“外寒入里怎么办”
- 命令 / 页面入口：问答输入框

## 5. 期望结果

### Step 1 预期

- 页面显示”智能问答”

### Step 2 预期

- 页面出现关于”人参”的回答
- 页面能看到”依据子图”、”证据摘要”和”推理与工具”
- 展开依据子图后能看到节点、关系、中心节点和图谱预览

### Step 3 预期

- SSE 事件流中至少可见 `session`、`answer_chunk`、`final`
- 若 agent 调用了图工具，可见 `tool_start` 和 `tool_result`
- 若 provider 返回原生 reasoning，可见 `provider_reasoning`
- 同一 `session_id` 的并发请求会被串行化，30 分钟未访问的会话会被回收

### Step 4 预期

- 页面能展示工具调用名、参数和 `result_summary`
- 若 provider 返回 reasoning，页面展示 `provider_reasoning`
- 若 provider 不返回 reasoning，页面不展示 reasoning 面板
- agent 查询图后，页面会逐步更新依据子图
- `final.evidence` 每项包含 `entity_id`、`evidence_id`、`snippet`；有来源时包含 `source_id`、`source_name`
- citation 只能来自查询子图中的 `由证据支持` / `来源于` 链路，不从回答文本补造
- 点击 citation 的“查看溯源”使用 `entity_id`；验证申请分别预填 `entity_id`、`source_id` 和 `snippet`

## 6. 证据记录

### 实现证据

- `packages/api/app/api/chat.py` — `/api/v1/chat/stream` 唯一入口
- `packages/api/app/services/chat_agent_runtime/runtime.py` — pydantic-ai-slim、同进程 MCP Client 与 `message_history` 真源
- `packages/api/app/services/chat_agent_runtime/session_memory.py` — TTL eviction callback 与同 session 串行锁
- `packages/api/app/services/chat_agent_runtime/citations.py` — 从查询子图生成结构化 citation
- `packages/api/app/services/chat_agent_runtime/provider_reasoning.py` — provider 原生 reasoning 透传
- `packages/api/app/services/knowledge_mcp/server.py` — 外部 `/mcp` 的四个 structured graph tools 与 `graph://schema`
- `packages/web/src/pages/ChatPage.tsx` — 页面入口
- `packages/web/src/hooks/useChat.ts` — chat stream 事件消费与消息归一化
- `packages/web/src/components/chat/GraphAgentBasisPanel.tsx` — 每轮回答的依据子图、provider reasoning、工具调用展示
- `packages/web/src/components/chat/MessageList.tsx` — citation 展示与 lineage 跳转
- `packages/web/src/components/chat/ReviewRequestModal.tsx` — 验证申请预填
- `packages/web/src/services/api.ts` — `chatApi.stream()` 客户端

### 运行证据

```bash
cd packages/api && uv run pytest -m 'not integration' -q
pnpm run test:web
pnpm --dir packages/web build
pnpm run test:integration
CI=true pnpm run test:e2e
curl -N -X POST http://localhost:8000/api/v1/chat/stream -H 'Content-Type: application/json' -d '{"question":"人参有什么功效？","session_id":"acceptance-chat-1"}'
curl -N -X POST http://localhost:8000/api/v1/chat/stream -H 'Content-Type: application/json' -d '{"question":"外寒入里怎么办","session_id":"acceptance-chat-2"}'
```

### 结果证据

- 页面可见结果：回答、依据子图、工具时间线出现；provider reasoning 仅在有原生返回时出现
- 接口返回摘要：SSE 事件顺序可见 `session -> tool_start/tool_result -> answer_chunk -> final`
- `final` 事件中包含 `answer`、`evidence`、`related_nodes`、`related_edges`、`subgraph_meta`、`tool_calls`
- 2026-08-19 fresh 自动验证：API 非集成 `293 passed, 4 deselected`；Web `61 passed`；citation 前端定向 `13 passed`；Web typecheck/build 与 API ruff/ty 通过
- fresh-volume Neo4j integration：`4 passed, 293 deselected`；Playwright 主线 E2E：`1 passed`，覆盖首页、搜索、图谱、citation 展示、lineage 跳转和验证页
- 真实 Fireworks + MCP + Neo4j smoke：药材 2 次工具调用 / 21 节点 / 19 边 / 2 citations；方剂 3 / 29 / 33 / 1；医案 2 / 5 / 5 / 1；穴位/治法 4 / 11 / 12 / 2
- 运行时策略摘要：上下文由进程内 `message_history` 续接；单进程内 30 分钟未访问会话会从 registry 移除，应用退出清空全部 session
- 2026-09-06 runtime 收口：API 非集成 `296 passed, 4 deselected`；ruff/ty 通过。真实 Fireworks + Neo4j smoke 本轮未重跑

## 7. 风险与未覆盖项

- 当前 runtime 依赖 LLM + Neo4j 环境；若本地未配置对应依赖，只能验证单测与页面 mock 场景
- provider 原生 reasoning 是否可见取决于当前 provider 是否返回该字段，页面不会伪造
- 当前会话策略仅适用于单进程部署；多 worker 或服务重启后不会保留会话状态
- 原始 Cypher 不向 agent MCP 暴露；恢复前必须先落地数据库级只读身份和查询防护
- 真实 provider 仍受外部网络和速率限制影响；本轮 429 由 SDK 自动重试成功，一次 TLS 错误单独重试后通过

## 8. 结论

- 结果：`pass`
- 结论一句话：pydantic-ai-slim 执行流、结构化 citation、同进程 MCP 图工具、外部 `/mcp`、进程内会话回收已由单测覆盖；真实 Neo4j/provider E2E 仍以 2026-08-19 证据为历史基线，本轮未重跑
- 后续动作：多 worker 需求出现后再引入共享会话存储；用小型 golden set 持续评估回答与 citation 质量
