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
- 验收目标：验证问答页面、graph runtime agent 接口、自然语言回答和可展开依据子图形成完整闭环，并覆盖复杂自然语言 query 的 cypher agent 路径
- 对应需求：图谱增强智能问答
- 对应计划：`docs/superpowers/plans/2026-04-20-graph-agent-complex-query-langchain.md`
- 当前版本 / 日期：Graph Agent Chat / 2026-04-20

## 2. 验收范围

### 包含

- 问答页面提问
- 后端 graph agent 接口响应
- 每轮回答自然语言展示
- 每轮回答可展开依据子图
- 证据、推理轨迹和工具调用展示
- 复杂 query 的 `graph_cypher_qa`、generated cypher 与结果摘要展示
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
pnpm run test:web
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
curl -sS -X POST http://localhost:8000/api/v1/graph-agent/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"人参有什么功效？"}' | python3 -m json.tool
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

- 响应内有 `answer`、`related_nodes`、`related_edges`、`subgraph_meta`、`evidence`、`reasoning_trace`、`tool_calls`
- `subgraph_meta.node_count` 和 `subgraph_meta.edge_count` 与返回子图规模一致
- `answer` 基于相关节点和关系生成自然语言说明

### Step 4 预期

- 页面能展示 `graph_cypher_qa`
- `tool_calls.arguments` 中可见 `generated_cypher`
- 页面能展示 `result_summary`
- cypher 结果中的候选实体会继续回填为依据子图节点

## 6. 证据记录

### 实现证据

- `packages/api/app/api/graph_agent.py` — `/api/v1/graph-agent/ask` 入口
- `packages/api/app/services/graph_agent_service.py` — graph runtime agent 服务门面
- `packages/api/app/services/graph_cypher_agent.py` — LangChain Neo4j cypher agent 适配器
- `packages/graph_runtime/graph_runtime/agent/graph_agent.py` — 默认图谱探索 agent
- `packages/graph_runtime/graph_runtime/planner/query_intent.py` — 复杂 query 意图分类
- `packages/graph_runtime/graph_runtime/planner/tool_plan_builder.py` — 工具计划构建
- `packages/web/src/pages/ChatPage.tsx` — 页面入口
- `packages/web/src/hooks/useChat.ts` — graph agent 调用与消息归一化
- `packages/web/src/components/chat/GraphAgentBasisPanel.tsx` — 每轮回答的依据子图、证据、推理和工具调用展示
- `packages/web/src/services/api.ts` — `graphAgentApi.ask()` 客户端

### 运行证据

```bash
pnpm run test:web
curl -sS -X POST http://localhost:8000/api/v1/graph-agent/ask -H 'Content-Type: application/json' -d '{"question":"人参有什么功效？"}'
curl -sS -X POST http://localhost:8000/api/v1/graph-agent/ask -H 'Content-Type: application/json' -d '{"question":"治感冒的中药都有哪些，怎么做"}' | python3 -m json.tool
curl -sS -X POST http://localhost:8000/api/v1/graph-agent/ask -H 'Content-Type: application/json' -d '{"question":"外寒入里怎么办"}' | python3 -m json.tool
```

### 结果证据

- 页面可见结果：回答、依据子图、证据摘要、推理与工具同时出现
- 接口返回摘要：`related_nodes` / `related_edges` 为列表，`subgraph_meta` 含中心节点和规模信息
- 复杂 query 返回摘要：`tool_calls[0].tool_name = graph_cypher_qa`，且 `tool_calls[0].arguments.generated_cypher` 可用于排查查询路径

## 7. 风险与未覆盖项

- 当前复杂 query 路径依赖 LLM + Neo4j 环境；若本地未配置对应依赖，只能验证单测与页面 mock 场景
- 当前 graph agent 路由是同步请求，页面未实现 SSE token 流式输出

## 8. 结论

- 结果：`pass`
- 结论一句话：智能问答主链路已切到 graph runtime agent，并具备复杂 query 走 cypher agent 后回填依据子图的验收能力
- 后续动作：多轮会话持久化、流式输出和更强来源选择策略
