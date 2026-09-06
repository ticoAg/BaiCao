---
type: Plan
title: 问答 chat 走最新 MCP 并清适配
description: 升官方 mcp v2；产品 chat 改同进程 MCP 客户端；删问答侧遗留适配。
resource: docs/plans/2026/09-06/问答-chat-走最新-mcp-并清适配-b042.md
tags: [计划]
generated: { by: plan-docs/v2, at: "2026-09-06T05:11:25-04:00" }
status: draft
sources:
  - id: mcp-arch
    resource: docs/architecture/chat-agent-mcp.md
    title: 问答 Agent 检索与 MCP 边界
  - id: overview
    resource: docs/architecture/system-overview.md
    title: 系统架构概览
  - id: ingest
    resource: docs/architecture/knowledge-model-and-ingestion.md
    title: 图模型与数据采集
  - id: accept
    resource: docs/acceptance/chat-mainline.md
    title: 智能问答主链路验收
---

# 问答 chat 走最新 MCP 并清适配

设计与取舍在 [问答 Agent 检索与 MCP 边界](../../../architecture/chat-agent-mcp.md#overview)，这篇只回答**怎么落、按什么顺序、验收什么**。[^mcp-arch]
问答主链以 [系统架构概览 · 问答链路](../../../architecture/system-overview.md#61-问答链路) 为准。[^overview]

本计划取代同日 [问答 agent MCP 检索收口](问答-agent-mcp-检索收口-8eca.md) 里「chat 不走 MCP / 不升 mcp v2 / 进程内 Function Tool」的口径。工具契约、depth=2、`graph://schema`、pydantic-ai loop 继续沿用，不要重做。

## Context

产品内部 chat 绕开 Knowledge MCP，是为了躲开 stdio 子进程和 `pydantic-ai-slim[mcp]` 与 mcp 1.x 的依赖冲突。现在要把官方 SDK 升到 v2，让问答和 Cursor 共用同一台 server，并删掉问答侧那些平行包装。

## Approach

按 [目标拓扑](../../../architecture/chat-agent-mcp.md#目标拓扑) 与 [Agent Runtime SDK](../../../architecture/chat-agent-mcp.md#agent-runtime-sdk)：先把 server 迁到 `MCPServer`，再用同进程 `Client(server)` 接 chat，最后删 LangChain `graph_tools`、LangGraph SSE 适配、复制的 `graph_agent_tools`。不要装 pydantic-ai MCP extra。[^mcp-arch]

## Key Decisions

见 [为什么不用 pydantic-ai MCP extra](../../../architecture/chat-agent-mcp.md#为什么不用-pydantic-ai-mcp-extra) 与 [轻量边界](../../../architecture/chat-agent-mcp.md#轻量边界)。[^mcp-arch]

## Scope

- In: `mcp>=2,<3`；Knowledge MCP 迁 v2；chat 同进程 MCP 客户端；schema 经 Resource 读取；删除问答遗留适配
- Out: pydantic-ai Harness / MCP extra、websearch、Cypher 给模型、卸掉 pipeline 用的 LangChain、升 mcp 之外的无关大版本

## Files

- [`packages/api/pyproject.toml`](../../../../packages/api/pyproject.toml) — `mcp>=2,<3`，不加 `pydantic-ai-slim[mcp]`
- [`packages/api/app/services/knowledge_mcp/server.py`](../../../../packages/api/app/services/knowledge_mcp/server.py) — `FastMCP` → `MCPServer`，传输参数按 v2 迁移指南挪走
- [`packages/api/app/services/chat_agent_runtime/runtime.py`](../../../../packages/api/app/services/chat_agent_runtime/runtime.py) — 用 `Client(server)` 接 tool / resource，删 `graph_agent_tools`
- [`packages/api/app/main.py`](../../../../packages/api/app/main.py) — 继续 `app.mount("/mcp", ...)`，对齐 v2 `streamable_http_app()` 签名
- [`packages/api/app/services/graph_tools/`](../../../../packages/api/app/services/graph_tools/) — 整包删除（仅问答遗留 LangChain 包装）

## Reuse

- [`packages/api/app/services/knowledge_mcp/handlers.py`](../../../../packages/api/app/services/knowledge_mcp/handlers.py) `KnowledgeMcpHandlers` — 仍是 tool 唯一实现
- [`packages/api/app/services/knowledge_mcp/payloads.py`](../../../../packages/api/app/services/knowledge_mcp/payloads.py) — 空结果信封不变
- [`packages/api/app/services/knowledge_mcp/schema.py`](../../../../packages/api/app/services/knowledge_mcp/schema.py) `build_graph_schema` — 只给 MCP Resource，chat 不要旁路调用
- [`packages/api/app/services/chat_agent_runtime/pydantic_event_adapter.py`](../../../../packages/api/app/services/chat_agent_runtime/pydantic_event_adapter.py) `adapt_pydantic_stream` — 唯一 SSE 映射
- [`packages/api/app/services/chat_agent_runtime/citations.py`](../../../../packages/api/app/services/chat_agent_runtime/citations.py) `citations_from_graph_state` — citation 仍只从图状态生成
- 官方 [v1 → v2 迁移指南](https://py.sdk.modelcontextprotocol.io/migration/) — `MCPServer` 导入、构造器、`Client(server)` 测试替身

## 依赖

```mermaid
flowchart LR
    P0["PR0 文档"] --> P1["PR1 mcp v2 server"]
    P1 --> P2["PR2 chat 同进程客户端"]
    P2 --> P3["PR3 删遗留适配"]
    P3 --> P4["PR4 验证"]
```

P1 不绿之前不要接 chat 客户端。P3 必须在 P2 能跑通之后再删，避免 chat 无工具可用。

待办三态：`- [ ]` 未完成，`- [x]` 完成，`- [-]` 废弃。完成或废弃一项就改那一行。

## PR0 文档

- [x] [chat-agent-mcp.md](../../../architecture/chat-agent-mcp.md) 改为「一套 mcp v2 + 同进程 Client」
- [x] [system-overview.md · 问答链路](../../../architecture/system-overview.md#61-问答链路) 与 [knowledge-model 5.1](../../../architecture/knowledge-model-and-ingestion.md#51-graph-runtime--agent-运行边界) 指向同一目标，并标明当前仍直调 handler
- [x] `docs/plans/` 与年索引能点到本计划

验收：frontmatter 可解析；引用的章节存在。无业务代码。

## PR1 mcp v2 server

- [ ] `packages/api` 依赖改为 `mcp>=2,<3` 并 `uv lock`；不要加 `pydantic-ai-slim[mcp]`。
- [ ] `server.py` / `stdio.py` / `main.py` 按迁移指南改：`MCPServer`、传输参数离开构造器、挂载 `/mcp` 仍可用。删除 `--transport sse`。
- [ ] `tests/services/test_knowledge_mcp.py` 用 `Client(server)` 覆盖 `list_tools`、空结果信封、`graph://schema`；不再依赖 v1 `FastMCP` 测试 API。
- [ ] 删除 `handlers.read_cypher`（仅 LangChain `graph_tools` 在用）；MCP 面本来就没有这个 tool。

验收：`cd packages/api && uv run pytest tests/services/test_knowledge_mcp.py -q` 通过。`from mcp.server.fastmcp` 在 `packages/api/app` 为零命中。stdio 与 `/mcp` 仍是同一 `knowledge_mcp` 实例。

## PR2 chat 同进程客户端

- [ ] `runtime.py`：`async with Client(knowledge_mcp)`（或进程内长生命周期 Client）把 MCP tools 交给 pydantic-ai Agent；开场 `read_resource("graph://schema")`，不要再 `dumps(build_graph_schema())`。
- [ ] 删除 `graph_agent_tools.py` 及其引用。允许一份极薄的「list_tools → pydantic-ai Tool」胶水，禁止再实现 search/expand/lookup。
- [ ] 重写 `tests/services/test_chat_agent_runtime.py`：断言走 MCP Client（可用假 Client / 录制 list_tools），覆盖历史续接、TTL、shutdown；SSE 形状对照 [chat-mainline](../../../acceptance/chat-mainline.md)。[^accept]

验收：一次 `/chat/stream` 进程列表里没有新的 `python -m app.services.knowledge_mcp`。模型可见的 tool 名仍是四个图 tool。schema 来自 Resource。

## PR3 删遗留适配

- [ ] 删除 `packages/api/app/services/graph_tools/` 与 `tests/services/test_graph_tools.py`；清掉 `test_knowledge_mcp.py` 对 `build_read_cypher_tool` 的引用。
- [ ] 删除 `event_adapter.adapt_agent_events` 及 LangGraph/LangChain message 依赖。把 pydantic SSE 仍需要的 helper 留在 `pydantic_event_adapter.py`（或同目录一个无 LangChain 的小模块）。
- [ ] 删除 `close_all_openai_sessions` 别名、空的 `agent_client.close_knowledge_mcp_server` 若已无调用。pipeline 的 LangChain Chat 调用不动。

验收：`rg "adapt_agent_events|graph_agent_tools|close_all_openai_sessions|build_graph_tools" packages/api` 无业务命中。`cd packages/api && uv run pytest -m "not integration" -q` 通过。

## PR4 验证

- [ ] `cd packages/api && uv run ruff check app tests && uv run ty check && uv run pytest -m "not integration" -q`
- [ ] 若有 Fireworks + Neo4j：同一条「组方 + 出处」问题看 tool 名来自 MCP、depth=2 能否接到「来源于」。没有真实环境则在回复里标未验证。

验收：结构化工具、citation、SSE 不回退。真实 smoke 缺环境不算本计划失败，但必须写明。

## Verification

- `cd packages/api && uv run ruff check app tests && uv run ty check && uv run pytest -m "not integration" -q`
- 问答页走一条需要出处的问题：SSE `tool_start.tool_name` 为 MCP 四个名字之一；`final.evidence` 只来自子图
- 失败时看是否又拉起了 stdio 子进程，以及 `expand_neighbors` 的 `depth`

图模型中文标签仍以 [中文图模型口径](../../../architecture/knowledge-model-and-ingestion.md#7-中文图模型口径) 为准。[^ingest]

## 不做

见 [轻量边界](../../../architecture/chat-agent-mcp.md#轻量边界)。[^mcp-arch] 本轮尤其不要：装 `pydantic-ai-slim[mcp]`、chat HTTP 打本机 `/mcp`、chat 再开 stdio 子进程、把 Cypher 还给模型、卸 pipeline LangChain。

[^mcp-arch]: 问答 Agent 检索与 MCP 边界
[^overview]: 系统架构概览
[^accept]: 智能问答主链路验收
[^ingest]: 图模型与数据采集
