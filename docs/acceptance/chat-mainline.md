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
- 验收目标：验证问答页面、问答接口、推理链和来源展示形成完整闭环
- 对应需求：图谱增强智能问答
- 对应计划：历史能力，迁移前未沉淀独立 `plans/*.md`；后续续改时请补对应计划文档
- 当前版本 / 日期：MVP / 2026-03-20

## 2. 验收范围

### 包含

- 问答页面提问
- 后端问答接口响应
- 推理链展示
- 来源标签展示
- 图谱预览跳转

### 不包含

- 多轮会话持久化

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
curl -sS -X POST http://localhost:8000/api/v1/chat/question \
  -H 'Content-Type: application/json' \
  -d '{"question":"人参有什么功效？"}' | python3 -m json.tool
```

## 5. 期望结果

### Step 1 预期

- 页面显示”智能问答”

### Step 2 预期

- 页面出现关于”人参”的回答
- 页面能看到”推理链”和来源标签

### Step 3 预期

- 响应内有 `answer`、`reasoning_chain`、`sources`、`graph_data`、`session_id`
- `answer` 提到”补气药”或”主要功效”

### Step 4: SSE 流式验收

- 操作：验证 SSE 流式端点

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{“question”:”陈皮有什么功效？”}'
```

- 预期：
  - 返回 `text/event-stream` MIME 类型
  - 依次收到 `event: session`、`event: reasoning`、`event: sources`、`event: token`（多次）、`event: done`
  - 每个 event 的 data 为合法 JSON
  - 当配置了 LLM API key 时，token 事件逐字流出；未配置时一次性返回规则引擎结果

## 6. 证据记录

### 实现证据

- `packages/api/app/api/chat.py` — 同步 + SSE 流式端点
- `packages/api/app/services/chat_service.py` — answer_question + answer_question_stream
- `packages/api/app/services/llm_client.py` — LangChain 双后端 LLM 抽象
- `packages/web/src/pages/ChatPage.tsx` — useChat hook 消费
- `packages/web/src/hooks/useChat.ts` — SSE 流式调用逻辑
- `packages/web/src/services/api.ts` — chatApi.stream() SSE 客户端

### 运行证据

```bash
pnpm run test:web
curl -sS -X POST http://localhost:8000/api/v1/chat/question -H 'Content-Type: application/json' -d '{"question":"人参有什么功效？"}'
```

### 结果证据

- 页面可见结果：回答、推理链、来源同时出现
- 接口返回摘要：`session_id` 存在，`reasoning_chain` 为列表

## 7. 风险与未覆盖项

- 当前回答生成仍偏规则化，不代表最终 LLM 质量

## 8. 结论

- 结果：`pass`
- 结论一句话：智能问答主链路在当前 demo 形态下已具备可执行验收能力
- 后续动作：多轮会话持久化和更强来源选择策略
