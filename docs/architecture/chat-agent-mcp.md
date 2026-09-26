<!--
---
doc_kind: architecture
status: stable
tags: ["qa", "mcp", "agent", "knowledge-graph"]
summary: 问答与 Cursor 共用一套官方 mcp v2 知识 server；检索仍由 pydantic-ai 循环完成，执行中的判定走 TypeSafe system_one
audience: developer
---
-->

# 问答 Agent 检索与 MCP 边界

## Overview

BaiCao 的产品问答 agent 不是通用研究助手，也不是本机 coding agent。它只负责一件事：用图里已经入库的知识回答问题，并带上可核验的出处。

因此检索面必须轻：模型走网络调用，知识走数据库（当前是 Neo4j 结构化工具）。本机文件、向量库、原始 Cypher、多 agent 编排都不进入这条主链。Web 搜索最多作为后续可选补强，不能替代图谱证据。

执行过程中的判定（要不要检索、证据够不够、草稿能不能发布）不是再一次自由生成，也不是第五个图 tool。这类问题都是有限选项、是/否或分档评分，和 TypeSafe 的 `system_one` 同一形状：事实放在 `state`，问题和标准放在 `questions`。问答循环里用一个 `judge` 工具调用它。

**产品 chat 必须是我们自己的 Knowledge MCP 的客户端。** 四个图 tool 和 `graph://schema` 只在这一套 server 上出现一次：问答、Cursor、stdio 调试都走它。pydantic-ai 只做 agent loop 和 SSE 流，不再另写一份 `graph_agent_tools`。

上一轮为了躲开 stdio 子进程、以及 `pydantic-ai-slim[mcp]` 与 `mcp>=1.29,<2` 的依赖冲突，把 chat 改成了进程内 Function Tool 直调 handler。那是权宜之计，不是产品边界。正确收口是：把官方 Python MCP SDK 升到 **v2 / 协议 `2026-07-28`**，chat 用同进程 `mcp.client.Client(server)` 连这台 server，不再绕开 MCP。

```mermaid
flowchart LR
    User[用户问题] --> Runtime[pydantic-ai Agent]
    Runtime --> LLM[网络 LLM]
    Runtime --> Client["mcp Client(server)"]
    Client --> Server[Knowledge MCPServer]
    Cursor[Cursor /mcp] --> Server
    Server --> Neo4j[(Neo4j 图谱)]
    Runtime --> Judge[judge]
    Judge --> SystemOne[TypeSafe system_one]
    LLM --> Answer[Markdown 结论]
    Client --> Cite[结构化 citation]
```

## Key Concepts

| 术语 | 含义 |
|------|------|
| 产品 agent | `/api/v1/chat/stream` 上的 Graph Specialist，面向终端用户问答 |
| 轻量检索 | 只暴露少量、有界、只读的图操作；模型自己决定何时调用 |
| system_one | TypeSafe 的一次判定请求：一份 `state`，多道具名问题，每道是 Choice、Noul 或 Score |
| Noul | 是/否。返回值 `noul` 是「是」的概率，0 到 1，不是布尔值 |
| judge | 问答循环里的判定工具。模型只选场景和关注点；问题和标准由代码固定 |
| Knowledge MCP | 官方 `mcp` v2 的 `MCPServer`：四个图 tool + `graph://schema` |
| 同进程客户端 | `mcp.client.Client(knowledge_mcp)`，DirectDispatcher，不走 HTTP、不拉子进程 |
| Streamable HTTP | 同一台 server 挂在 FastAPI `/mcp`，给 Cursor 等外部客户端 |
| MCP Tools | `search_nodes` / `search_edges` / `expand_neighbors` / `lookup_nodes` |
| MCP Resources | 应用控制的只读上下文：`graph://schema`。chat 开场 `read_resource`，不要旁路 `build_graph_schema()` 再塞进 prompt |

规范里 Tools / Resources / Prompts 的控制权划分以 [MCP server concepts](https://modelcontextprotocol.io/docs/2026-07-28/learn/server-concepts.md) 为准。轻量 agent 只用 Tools + Resources。

## Architecture

### 当前代码

产品 chat 用 `mcp.client.Client(knowledge_mcp)` 同进程调用官方 mcp v2 `MCPServer`。`/mcp` 与 stdio 是同一台 server 的外部入口。pydantic-ai 只做 loop；MCP tools 经 `mcp_agent_tools.tools_from_mcp_client` 暴露，不再复制 handler。配了 TypeSafe 时，同一个 agent 再挂 `judge`。

### 目标拓扑

```mermaid
flowchart TB
    subgraph App[产品问答]
        Runtime[pydantic-ai-slim Agent]
        Prompt[政策型 system prompt]
        McpClient["mcp.client.Client(server)"]
        Judge[judge / system_one]
    end

    subgraph OneServer[唯一 Knowledge MCP]
        Server["MCPServer baicao-knowledge"]
        Handlers[KnowledgeMcpHandlers]
    end

    subgraph External[外部]
        HttpMount["/mcp Streamable HTTP"]
        Stdio[stdio 调试]
    end

    subgraph Data[数据]
        Neo4j[(Neo4j)]
        Meta[graph_metadata_service]
        KM[knowledge_model 枚举]
    end

    Runtime --> McpClient
    Runtime --> Judge
    McpClient --> Server
    Prompt --> Runtime
    HttpMount --> Server
    Stdio --> Server
    Server --> Handlers
    Handlers --> Neo4j
    Server --> KM
    Server --> Meta
```

一套 server，三条入口（同进程 Client、`/mcp`、stdio）。不要再为 chat 复制 tool 实现，也不要为 pydantic-ai 再装 FastMCP / `pydantic-ai-slim[mcp]`。

### 为什么不用 pydantic-ai MCP extra

`pydantic-ai` 的 `MCPToolset` / `MCP` capability 包的是 **FastMCP Client**（`pydantic-ai-slim[mcp]`）。文档示例仍 `from mcp.server.fastmcp import FastMCP`，而官方 SDK **v2 已删除该模块**，改名为 `MCPServer`。再装 extra 会引入第二套 MCP 客户端，和「升官方 mcp」打架。

同进程 `Client(server)` 是官方 v2 给「测试与单进程部署」的入口，正好覆盖产品 chat 与 FastAPI 同进程的事实。外部 Cursor 继续走 Streamable HTTP，不必让 chat 再 HTTP 打自己。

## How It Works

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户
    participant R as ChatAgentRuntime
    participant A as pydantic-ai Agent
    participant C as mcp Client
    participant S as Knowledge MCPServer
    participant G as Neo4j

    U->>R: 问题
    R->>C: Client(server)
    C->>S: read_resource graph://schema
    S-->>C: 标签 / 关系 / 标识规则
    R->>A: 政策 prompt + schema + 用户问题
    A->>C: tools/call search_nodes
    C->>S: search_nodes
    S->>G: 名称或标识检索
    G-->>S: 候选节点
    A->>C: tools/call expand_neighbors
    S->>G: depth 1或2 邻居
    G-->>S: 子图
    A-->>R: Markdown 结论
    R-->>U: SSE + citation
```

SSE 事件形状不变：`session` / `tool_start` / `tool_result` / `subgraph_patch` / `answer_chunk` / `final`。`judge` 走同一套工具事件，不另加事件类型。只保留一份 pydantic-ai → SSE 映射；LangGraph 那份删掉。

### 四个 tool 的推荐用法

| 工具 | 何时用 | 不要用来 |
|------|--------|----------|
| `search_nodes` | 问题里的实体还没变成节点标识 | 猜 Cypher；在已有 `标识` 时重复模糊搜 |
| `search_edges` | 已知关系类型、还没锁定锚点 | 代替邻居展开 |
| `expand_neighbors` | 已有锚点，要组方 / 功效 / 证据邻居 | 无界全图遍历 |
| `lookup_nodes` | 已有 `标识`，回看属性 | 当搜索用 |

不要再给 agent 加第五个图 tool。结构化判定只走下面的 `judge`，不要再把「够不够、算不算、该不该发布」写回自由生成。

## 执行中的判定

检索和写结论仍由 pydantic-ai 循环完成。循环里每一次要在有限标准下做决定时，调用 `judge`，由 TypeSafe `system_one` 一次答完该场景的全部问题。模型不编写 `criteria`，也不把判定拆成另一段自由文本。

```mermaid
sequenceDiagram
    autonumber
    participant A as pydantic-ai Agent
    participant J as judge
    participant T as TypeSafe system_one

    A->>J: profile、focus、draft
    Note right of J: state 只取本轮问题和已返回的图工具结果
    J->>T: state + 该 profile 的固定 questions
    T-->>J: Choice / Noul / Score
    J-->>A: answers + follow
    Note right of A: 按 follow 检索、追问或写结论
```

`judge` 标成顺序屏障：同一步里排在它前面的图工具先返回，判定看到的是已经落地的结果，而不是和检索并行的空状态。

### state 和 questions

`state` 是这一次要判断的事实，字段有名字。`questions` 是问题名到 Choice / Noul / Score 的映射，标准留在问题里，不塞进 state。一次请求答完该场景的全部问题。

| state 字段 | 谁填写 | 内容 |
|---|---|---|
| `用户问题` | 运行时 | 当前这轮用户输入 |
| `关注点` | 模型的 `focus`，可空 | 这一次具体在决定什么 |
| `待核对结论` | 模型的 `draft`，仅 `claim` | 准备给用户看的全文 |
| `图工具记录` | 运行时 | 最近的 `search_nodes` / `search_edges` / `expand_neighbors` / `lookup_nodes` 参数和结果 |

图工具记录有上限：最近 6 次，单次结果序列化后超过 8000 字会截断。判定请求必须有界；截断后的结果不能再当成完整子图。`judge` 自己的返回不写进 state，避免把上一次判定当成图谱证据。

### 三个 profile

问题和标准写在 `chat_agent_runtime/turn_judgment.py`。增加场景时加一套 questions，不要让模型临时组题。

| profile | 何时调用 | 问题 |
|---|---|---|
| `intake` | 第一次图工具之前 | 任务（Choice：图谱检索 / 需要澄清 / 超出图谱问答）、需要检索（Noul）、问题具体程度（Score） |
| `evidence` | 每次图工具返回后，决定继续检索还是作答之前 | 锚点已定位（Noul）、证据足够作答（Noul）、下一步（Choice：继续检索 / 可以作答 / 说明没有图谱证据）、证据充分度（Score） |
| `claim` | 写出给用户的结论之前 | 超出已检索子图（Noul）、编造剂量或出处（Noul）、可以发布（Noul）。`draft` 必填 |

Noul 的 `true` / `false` 是协议字段，标准正文用中文。Choice 的选项名就是模型必须服从的标签。Score 从 0 分起，按条目顺序升档。

### follow

工具返回里的 `follow` 是运行时根据答案算出的下一步，不是模型再解释一遍。

- Noul：`noul >= 0.7` 视为是，`<= 0.3` 视为否，中间视为不确定。
- Choice：`confidence < 0.5` 视为不确定，不采用那个标签。
- `claim` 里，只要「超出已检索子图」或「编造剂量或出处」不是明确的否，或「可以发布」不是明确的是，`follow` 就要求改草稿后重判。
- 答案缺字段时，`follow` 要求不要据此发布。

未配置 `TYPESAFE_API_KEY` 和 `TYPESAFE_BASE_URL` 时不注册 `judge`，问答仍只走四个图工具。配了之后，政策 prompt 要求在上面三个时点调用它，并按 `follow` 行动。判定失败必须可见，不能当成已经判定过。

文本一旦经 `answer_chunk` 流出，不再用判定把 SSE 回滚。`follow` 约束的是模型下一步怎么做。citation 仍只从已查询子图提取，不从判定文本里取。

同一套 `SystemOneJudge.ask(state, questions)` 可供以后的审查预筛复用：另写一份 questions，不要再包一个判定客户端。数据采集里的实体归类仍按来源计划，不用模型猜测类型。

## 检索工具评估

四个只读图 tool 的契约（structured dict、空结果 hint、depth 1..2、名称+标识检索、`graph://schema`）已经收口，本轮不要重做。缺口变成：**chat 没走 MCP、SDK 停在 1.x、旁边还有第二套 LangChain 包装。**

仍不做：别名 / 拼音检索。

## Prompt 评估

政策 + 失败协议留在 `build_graph_specialist_system_prompt()`。标签、关系、标识格式只来自 `graph://schema`（chat 经 MCP Resource 读取）。不要再旁路 `build_graph_schema()` 拼进 instructions。

## MCP 规范对齐

对照 [Understanding MCP servers (2026-07-28)](https://modelcontextprotocol.io/docs/2026-07-28/learn/server-concepts.md) 与官方 [v1 → v2 迁移指南](https://py.sdk.modelcontextprotocol.io/migration/)。

| 规范能力 | 谁控制 | 目标仓库 | 轻量问答是否需要 |
|----------|--------|----------|------------------|
| `tools/list` + `tools/call` | 模型 | 四个图 tool | 需要 |
| Streamable HTTP | 传输 | FastAPI `/mcp` | 外部客户端需要 |
| 同进程 `Client(server)` | 传输 | 产品 chat | 需要，避免子进程与自连 HTTP |
| stdio | 传输 | `python -m app.services.knowledge_mcp` | 只留给 Cursor / 本机调试 |
| HTTP+SSE | 传输 | 删除 `--transport sse` | Deprecated，不要 |
| Resources | 应用 | `graph://schema`；chat 经 Client 读 | 需要 |
| Prompts / subscriptions / Apps / Tasks | — | 不实现 | 不需要 |

依赖目标：`mcp>=2,<3`。机械改动以迁移指南为准：`FastMCP` → `MCPServer`，传输参数从构造器挪到 `streamable_http_app()` / `run()`，测试用 `Client(server)` 替代已删除的 `create_connected_server_and_client_session`。

## Agent Runtime SDK

| 选项 | 结论 |
|------|------|
| pydantic-ai 进程内 Function Tool 复制 MCP 面 | 上一轮权宜之计，删 |
| `pydantic-ai-slim[mcp]` / FastMCP Client | 第二套 MCP 栈，且与官方 v2 模块路径冲突，不要 |
| pydantic-ai Harness | 过重，不要 |
| **官方 mcp v2 `MCPServer` + `Client(server)` + pydantic-ai-slim[openai] loop** | 推荐。一套协议，两种入口（同进程 / HTTP） |
| TypeSafe `system_one` | 执行中的 Choice / Noul / Score。不替代检索循环，也不要换成让问答模型自己打分 |

pydantic-ai 只替代 agent loop 与流式事件。MCP 客户端用官方 SDK，不要再包一层 FastMCP。判定客户端用 `typesafe-sdk` 的 `AsyncTypeSafeClient`，不要把 `system_one` 再包成一套自有提示词。

## 轻量边界

只做：

- 网络 LLM（OpenAI 兼容 provider）
- 官方 mcp v2 知识 server（四个只读图 tool + `graph://schema`）
- 产品 chat：同进程 MCP 客户端
- `/mcp` 与 stdio：同一台 server 的外部入口
- agent loop：`pydantic-ai-slim[openai]`，不要 Harness、不要 pydantic-ai MCP extra
- 执行中判定：可选的 `judge` → TypeSafe `system_one`。未配置密钥时不注册

明确不做：

- 原始 Cypher 给模型；顺手删掉仅给 LangChain 用的 `read_cypher` handler
- 本机文件 / 向量 RAG / 第二套知识库
- LangGraph / LangChain `graph_tools` 回流 chat
- 把已删除的 `packages/graph_runtime` 接回 chat
- MCP Prompts、Apps、Tasks、subscriptions
- pydantic-ai Harness、WebSearch、第二套 FastMCP 客户端
- 为「更聪明」继续堆图 tool，或让问答模型自己编写判定标准
- chat 再拉 stdio 子进程，或 HTTP 打本机 `/mcp`

pipeline 抽取仍可用 LangChain Chat 模型；那不是问答检索面。不要把 pipeline 用的 `langchain` / `langchain-openai` 从仓库卸掉。问答侧不要再装 `langgraph` 或 `langchain-neo4j`。

## Data Model

Agent 看见的节点必须能回到图主键。

```mermaid
erDiagram
    NODE ||--o{ EDGE : connects
    NODE {
        string 标识 PK
        string 名称
        string labels
    }
    EDGE {
        string rel_type
        string source_id
        string target_id
    }
    NODE ||--o{ EVIDENCE : 由证据支持
    EVIDENCE ||--o{ SOURCE : 来源于
```

`标识` 是 `expand_neighbors` / `lookup_nodes` 的输入。`名称` 只用于 `search_nodes`。活图默认不写入 `来源于` 与原文片段；citation 优先用已查询子图的「由证据支持」，出处回落到节点 `导入源`。若图上仍有「来源于」边则继续用。见 `chat_agent_runtime/citations.py`。

## Configuration

| 项 | 当前事实 |
|----|----------|
| Agent loop | `pydantic-ai-slim[openai]` |
| MCP 依赖 | `mcp>=2,<3` |
| Chat 客户端 | `mcp.client.Client(knowledge_mcp)` 同进程 |
| HTTP 挂载 | FastAPI `/mcp` → 同一 `MCPServer.streamable_http_app()` |
| 独立进程 | `python -m app.services.knowledge_mcp --transport stdio` 或 `streamable-http` |
| System prompt | `chat_agent_runtime/system_prompt.py`（政策；配了 TypeSafe 才附加 judge 说明） |
| Schema | MCP Resource `graph://schema` |
| 判定 | `TYPESAFE_API_KEY`、`TYPESAFE_BASE_URL`、`TYPESAFE_MODEL`（默认 `decision-model-preview`） |
| 判定实现 | `app/services/system_one.py`、`chat_agent_runtime/turn_judgment.py` |

## Troubleshooting

| 现象 | 更可能的原因 |
|------|----------------|
| 模型说图里没有，Workbench 里有 | `search_nodes` 只匹配名称/标识，或 limit 截断 |
| 有实体、没有出处 | 未把 `expand_neighbors` 的 depth 设为 2 |
| 展开失败 | 传入的是名称不是 `标识` |
| `ModuleNotFoundError: mcp.server.fastmcp` | 仍按 v1 导入；应 `mcp.server.mcpserver.MCPServer` |
| chat 又拉起 knowledge_mcp 子进程 | 错误地用了 stdio 客户端；应 `Client(server)` |
| 装了 `pydantic-ai-slim[mcp]` 后解析失败 | extra 与官方 mcp v2 冲突；不要装 |
| 工具列表里没有 `judge` | 未配置 `TYPESAFE_API_KEY` / `TYPESAFE_BASE_URL`，或密钥仍是占位符 |
| `judge` 报认证或模型错误 | 密钥、`TYPESAFE_BASE_URL` 或 `TYPESAFE_MODEL` 与账号不一致 |

## 相关文档

- [system-overview.md](system-overview.md#61-问答链路) — 问答 SSE 主链
- [knowledge-model-and-ingestion.md](knowledge-model-and-ingestion.md#51-graph-runtime--agent-运行边界) — runtime 边界与中文图模型
- [graph-workbench.md](graph-workbench.md) — 人看的 metadata / 展开；agent 应复用同一份图事实
- [../acceptance/chat-mainline.md](../acceptance/chat-mainline.md) — 问答验收
