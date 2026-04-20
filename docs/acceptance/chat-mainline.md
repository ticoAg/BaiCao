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
- 对应计划：`docs/superpowers/plans/2026-04-20-chat-deepagents-graph-agent.md`
- 当前版本 / 日期：Chat DeepAgents Graph Agent / 2026-04-20

## 2. 验收范围

### 包含

- 问答页面提问
- 后端 chat 单入口响应
- 每轮回答自然语言展示
- provider 原生 reasoning（若 provider 返回）
- agent 工具调用、参数、结果摘要流式展示
- 每轮回答可展开依据子图
- 证据、推理轨迹和工具调用展示
- 图谱预览跳转

### 不包含

- 多轮会话持久化（当前页面仅保留前端会话状态和“新话题”重置）

## 3. 前置条件

### 环境

- 运行方式：本地 `make` + tmux 单 session
- 依赖服务：FastAPI、Neo4j、PostgreSQL、Vite
- 样例数据：demo 用户、来源和”人参”图谱
- LLM 配置（可选）：.env 中设置 `LLM_PROVIDER` + API key 启用 LLM；未配置时自动降级为规则引擎

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

### Step 4 预期

- 页面能展示工具调用名、参数和 `result_summary`
- 若 provider 返回 reasoning，页面展示 `provider_reasoning`
- 若 provider 不返回 reasoning，页面不展示 reasoning 面板
- agent 查询图后，页面会逐步更新依据子图

## 6. 证据记录

### 实现证据

- `packages/api/app/api/chat.py` — `/api/v1/chat/stream` 唯一入口
- `packages/api/app/services/chat_agent_runtime/runtime.py` — deepagents runtime 真源
- `packages/api/app/services/chat_agent_runtime/provider_reasoning.py` — provider 原生 reasoning 透传
- `packages/api/app/services/graph_tools/registry.py` — 基础图工具注册
- `packages/web/src/pages/ChatPage.tsx` — 页面入口
- `packages/web/src/hooks/useChat.ts` — chat stream 事件消费与消息归一化
- `packages/web/src/components/chat/GraphAgentBasisPanel.tsx` — 每轮回答的依据子图、provider reasoning、工具调用展示
- `packages/web/src/services/api.ts` — `chatApi.stream()` 客户端

### 运行证据

```bash
corepack pnpm --dir packages/web test --run
curl -N -X POST http://localhost:8000/api/v1/chat/stream -H 'Content-Type: application/json' -d '{"question":"人参有什么功效？","session_id":"acceptance-chat-1"}'
curl -N -X POST http://localhost:8000/api/v1/chat/stream -H 'Content-Type: application/json' -d '{"question":"外寒入里怎么办","session_id":"acceptance-chat-2"}'
```

### 结果证据

- 页面可见结果：回答、依据子图、工具时间线出现；provider reasoning 仅在有原生返回时出现
- 接口返回摘要：SSE 事件顺序可见 `session -> tool_start/tool_result -> answer_chunk -> final`
- `final` 事件中包含 `answer`、`related_nodes`、`related_edges`、`subgraph_meta`、`tool_calls`

## 7. 风险与未覆盖项

- 当前 runtime 依赖 LLM + Neo4j 环境；若本地未配置对应依赖，只能验证单测与页面 mock 场景
- provider 原生 reasoning 是否可见取决于当前 provider 是否返回该字段，页面不会伪造

## 8. 结论

- 结果：`pass`
- 结论一句话：智能问答主链路已收敛到 `/api/v1/chat/stream`，并具备 agent 工具过程流、可选 provider reasoning 与依据子图展示能力
- 后续动作：把 deepagents runtime 从骨架补成完整执行主链，并继续增强基础图工具
