# Chat DeepAgents Graph Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 BaiCao 图谱问答收敛为唯一的 `/api/v1/chat/stream` 入口，内部接入 `deepagents` graph specialist agent，使用基础图工具自主决策，并把 provider 原生 reasoning、工具调用和依据子图流式展示到 chat 页面。

**Architecture:** 保留 chat 作为唯一对外主入口，新增 `chat_agent_runtime/` 作为 `deepagents` 真源，新增 `graph_tools/` 作为基础图工具注册层。前端沿用现有 chat 页面和 SSE 模式，但改为消费统一的 agent 事件流；旧 `graph-agent` 路径和规则 planner 退出主链，待新链路稳定后删除。

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, LangChain, `deepagents`, LangGraph, Neo4j, React 18, Vite, Vitest

**Status Snapshot (2026-04-20):** 当前主链已落地为 `/api/v1/chat/stream -> chat_agent_runtime -> deepagents`。会话上下文真源已收敛到 LangGraph `thread_id` + 进程内 `InMemorySaver`，并补了 30 分钟 TTL 回收与同 `session_id` 串行锁；原计划中的 `thread_store.py` 已被 `session_memory.py` 替代。

**Implementation Evidence:**

- `packages/api/app/services/chat_agent_runtime/runtime.py`
- `packages/api/app/services/chat_agent_runtime/event_adapter.py`
- `packages/api/app/services/chat_agent_runtime/session_memory.py`
- `packages/api/app/services/graph_tools/registry.py`
- `packages/api/tests/services/test_chat_agent_runtime.py`
- `packages/api/tests/services/test_session_memory.py`
- `docs/architecture/system-overview.md`
- `docs/acceptance/chat-mainline.md`

**Verification Evidence:**

- `cd packages/api && uv run ruff check app tests`
- `cd packages/api && uv run ty check`
- `cd packages/api && uv run pytest -m "not integration"`
- `corepack pnpm --dir packages/web test --run`
- `corepack pnpm --dir packages/web exec vp build`

---

> Historical note: 下方 task-by-task 拆解保留了当时的实施顺序，用于回溯过程；若与顶部 `Status Snapshot` 冲突，以顶部现状和稳定文档为准。与 `thread_store.py` 相关的步骤已由 `session_memory.py` + LangGraph `thread_id` / `InMemorySaver` 方案替代。

## File Map

### API Runtime (`packages/api/`)

- Create: `packages/api/app/services/chat_agent_runtime/__init__.py` — 导出 runtime 入口
- Create: `packages/api/app/services/chat_agent_runtime/runtime.py` — 创建和执行 deepagents graph specialist agent，暴露 `stream_turn(...)`
- Create: `packages/api/app/services/chat_agent_runtime/session_memory.py` — 进程内 memory checkpointer、30 分钟 TTL 回收与同 session 串行锁
- Create: `packages/api/app/services/chat_agent_runtime/system_prompt.py` — graph specialist 的 system prompt 与工具使用约束
- Create: `packages/api/app/services/chat_agent_runtime/event_adapter.py` — deepagents/langgraph 事件转 SSE 事件
- Create: `packages/api/app/services/chat_agent_runtime/provider_reasoning.py` — 只提取 provider 原生 reasoning，不生成替代文本
- Create: `packages/api/app/services/graph_tools/__init__.py` — 导出工具注册入口
- Create: `packages/api/app/services/graph_tools/registry.py` — 向 deepagents 注册基础图工具
- Create: `packages/api/app/services/graph_tools/search_nodes.py` — 节点模糊查询工具
- Create: `packages/api/app/services/graph_tools/search_edges.py` — 关系模糊查询工具
- Create: `packages/api/app/services/graph_tools/expand_neighbors.py` — 邻居展开工具
- Create: `packages/api/app/services/graph_tools/lookup_nodes.py` — 节点精确读取工具
- Create: `packages/api/app/services/graph_tools/read_cypher.py` — 受限只读 Cypher 工具
- Modify: `packages/api/app/api/chat.py` — `/chat/stream` 接入新 runtime；`/chat/question` 改为废弃路径或复用 stream 收束
- Modify: `packages/api/app/services/chat_service.py` — 删除主路径职责，保留兼容层或薄封装，避免继续走规则问答链
- Modify: `packages/api/app/graph_runtime_backend.py` — 补基础图工具所需的 schema-safe 读方法
- Modify: `packages/api/pyproject.toml` — 增加 `deepagents` / LangGraph 等运行时依赖

### API Tests (`packages/api/tests/`)

- Create: `packages/api/tests/services/test_provider_reasoning.py` — provider reasoning 提取测试
- Create: `packages/api/tests/services/test_session_memory.py` — session memory TTL 与同 session 串行锁测试
- Create: `packages/api/tests/services/test_graph_tools.py` — 基础图工具单测
- Create: `packages/api/tests/services/test_chat_agent_runtime.py` — runtime 装配、事件适配、thread 绑定测试
- Modify: `packages/api/tests/api/test_chat_routes.py` — `/chat/stream` 新 SSE 事件 contract 测试
- Modify: `packages/api/tests/services/test_chat_service.py` — 更新 chat service / runtime 主路径测试
- Delete: `packages/api/tests/services/test_graph_agent_service.py` — 旧 graph-agent service 测试退役
- Delete: `packages/api/tests/api/test_graph_agent_routes.py` — 旧 graph-agent route 测试退役

### Web (`packages/web/`)

- Modify: `packages/web/src/types/chat.ts` — 定义 agent SSE 事件、provider reasoning、tool timeline、subgraph patch、final payload
- Modify: `packages/web/src/services/api.ts` — `chatApi.stream()` 解析新的 agent SSE 事件
- Modify: `packages/web/src/hooks/useChat.ts` — 用流式草稿态驱动单条 assistant message，替换 `graphAgentApi.ask`
- Modify: `packages/web/src/components/chat/GraphAgentBasisPanel.tsx` — 展示 provider reasoning、工具时间线、流式子图与最终结果
- Modify: `packages/web/src/components/chat/MessageList.tsx` — 适配新的 message 结构与 reasoning / tools 渲染条件
- Modify: `packages/web/src/pages/ChatPage.tsx` — 页面文案与唯一 chat 入口说明
- Modify: `packages/web/src/pages/ChatPage.test.tsx` — agent stream 主路径与 reasoning 有/无两种场景测试

### Graph Runtime / Legacy Cleanup

- Delete: `packages/api/app/services/graph_agent_service.py` — 旧独立 graph-agent service 退役
- Delete: `packages/api/app/services/graph_cypher_agent.py` — 高阶黑盒 graph QA 工具退役
- Delete: `packages/graph_runtime/graph_runtime/planner/query_intent.py` — 旧规则分类退役
- Delete: `packages/graph_runtime/graph_runtime/planner/tool_plan_builder.py` — 旧初始工具计划退役
- Delete: `packages/graph_runtime/graph_runtime/agent/graph_agent.py` — 旧 graph runtime agent 主链退役

### Docs

- Modify: `docs/architecture/system-overview.md` — 更新为 chat 单入口 + deepagents graph specialist 架构
- Modify: `docs/acceptance/chat-mainline.md` — 更新唯一 chat 主入口和 agent 过程流验收

---

### Task 1: 锁定 `/chat/stream` 的新 agent SSE 协议

**Files:**
- Modify: `packages/web/src/types/chat.ts`
- Modify: `packages/api/tests/api/test_chat_routes.py`

- [ ] **Step 1: 先写失败测试，锁定 `/chat/stream` 会输出 agent 事件而不是旧的 `reasoning/sources/token` 三段式**

```python
# packages/api/tests/api/test_chat_routes.py
import json
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_chat_stream_emits_agent_event_types(client):
    async def fake_stream_turn(question: str, session_id: str | None = None):
        yield {"type": "session", "data": {"session_id": "sid-1", "turn_id": "turn-1"}}
        yield {
            "type": "tool_start",
            "data": {
                "call_id": "call-1",
                "tool_name": "search_nodes",
                "arguments": {"query": "感冒", "limit": 5},
            },
        }
        yield {
            "type": "tool_result",
            "data": {
                "call_id": "call-1",
                "tool_name": "search_nodes",
                "result_summary": "返回 2 个候选节点",
            },
        }
        yield {"type": "answer_chunk", "data": {"text": "可考虑桂枝、荆芥。"}}
        yield {
            "type": "final",
            "data": {
                "answer": "可考虑桂枝、荆芥。",
                "provider_reasoning": [],
                "tool_calls": [],
                "related_nodes": [],
                "related_edges": [],
                "subgraph_meta": {
                    "center_node_id": None,
                    "actual_depth": 0,
                    "fallback_used": False,
                    "node_count": 0,
                    "edge_count": 0,
                },
                "evidence": [],
                "reasoning_trace": [],
                "session_id": "sid-1",
            },
        }

    with patch("app.api.chat.stream_chat_turn", side_effect=fake_stream_turn):
        response = await client.post("/api/v1/chat/stream", json={"question": "治感冒的中药有哪些"})

    assert response.status_code == 200
    body = response.text
    assert "event: session" in body
    assert "event: tool_start" in body
    assert "event: tool_result" in body
    assert "event: answer_chunk" in body
    assert "event: final" in body
    assert "event: reasoning" not in body
    assert "event: sources" not in body
```

- [ ] **Step 2: 运行测试确认当前 `/chat/stream` 还是旧事件模型**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/api/test_chat_routes.py::test_chat_stream_emits_agent_event_types -q
```

Expected:

- 失败，提示 `stream_chat_turn` 不存在，或返回的仍是旧 `reasoning/sources/token/done`

- [ ] **Step 3: 先更新前端类型，锁定新的 SSE 事件与最终消息结构**

```ts
// packages/web/src/types/chat.ts
export interface ChatAgentProviderReasoningChunk {
  id?: string;
  text: string;
}

export interface ChatAgentToolStartEvent {
  call_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
}

export interface ChatAgentToolResultEvent {
  call_id: string;
  tool_name: string;
  result_summary: string;
  payload_preview?: Record<string, unknown> | null;
}

export interface ChatAgentSubgraphPatchEvent {
  nodes?: Array<Partial<GraphNode> & { id?: string; name?: string }>;
  edges?: Array<Partial<GraphEdge>>;
  center_node_id?: string | null;
}

export interface ChatAgentFinalPayload extends GraphAgentResponse {
  provider_reasoning: ChatAgentProviderReasoningChunk[];
  session_id: string;
}

export interface ChatAgentSSECallbacks {
  onSession?: (sessionId: string, turnId?: string) => void;
  onProviderReasoning?: (chunk: ChatAgentProviderReasoningChunk) => void;
  onToolStart?: (event: ChatAgentToolStartEvent) => void;
  onToolResult?: (event: ChatAgentToolResultEvent) => void;
  onSubgraphPatch?: (patch: ChatAgentSubgraphPatchEvent) => void;
  onAnswerChunk?: (text: string) => void;
  onFinal?: (payload: ChatAgentFinalPayload) => void;
  onError?: (message: string) => void;
}
```

- [ ] **Step 4: 回到 API 测试文件，给后续主链留出 `stream_chat_turn` 导入位**

```python
# packages/api/tests/api/test_chat_routes.py
with patch("app.api.chat.stream_chat_turn", side_effect=fake_stream_turn):
    response = await client.post("/api/v1/chat/stream", json={"question": "治感冒的中药有哪些"})
```

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/types/chat.ts packages/api/tests/api/test_chat_routes.py
git commit -m "test(chat): lock deepagents stream event contract"
```

### Task 2: 搭起 `chat_agent_runtime` 骨架与 provider reasoning 提取

**Files:**
- Create: `packages/api/app/services/chat_agent_runtime/__init__.py`
- Create: `packages/api/app/services/chat_agent_runtime/runtime.py`
- Create: `packages/api/app/services/chat_agent_runtime/thread_store.py`
- Create: `packages/api/app/services/chat_agent_runtime/system_prompt.py`
- Create: `packages/api/app/services/chat_agent_runtime/event_adapter.py`
- Create: `packages/api/app/services/chat_agent_runtime/provider_reasoning.py`
- Create: `packages/api/tests/services/test_provider_reasoning.py`
- Create: `packages/api/tests/services/test_thread_store.py`
- Create: `packages/api/tests/services/test_chat_agent_runtime.py`
- Modify: `packages/api/pyproject.toml`

- [ ] **Step 1: 先写失败测试，锁定 provider reasoning “有则透传、无则为空”**

```python
# packages/api/tests/services/test_provider_reasoning.py
from app.services.chat_agent_runtime.provider_reasoning import extract_provider_reasoning_chunks


def test_extract_provider_reasoning_chunks_returns_empty_when_provider_has_no_reasoning():
    chunks = extract_provider_reasoning_chunks({"output": [{"type": "message", "content": []}]})

    assert chunks == []


def test_extract_provider_reasoning_chunks_preserves_native_reasoning_text():
    chunks = extract_provider_reasoning_chunks(
        {
            "output": [
                {
                    "type": "reasoning",
                    "id": "rs-1",
                    "summary": [{"type": "summary_text", "text": "先定位病证锚点，再查药材关系"}],
                }
            ]
        }
    )

    assert chunks == [{"id": "rs-1", "text": "先定位病证锚点，再查药材关系"}]
```

```python
# packages/api/tests/services/test_thread_store.py
from app.services.chat_agent_runtime.thread_store import InMemoryThreadStore


def test_thread_store_appends_messages_and_tool_outputs_in_original_order():
    store = InMemoryThreadStore()
    store.append_event("sid-1", {"type": "user", "content": "感冒怎么办"})
    store.append_event("sid-1", {"type": "tool", "name": "search_nodes", "output": {"items": ["感冒"]}})

    history = store.get_thread("sid-1")

    assert history[0]["type"] == "user"
    assert history[1]["type"] == "tool"
```

- [ ] **Step 2: 运行测试确认 runtime 骨架尚不存在**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/services/test_provider_reasoning.py tests/services/test_thread_store.py -q
```

Expected:

- 失败，提示 `chat_agent_runtime` 模块不存在

- [ ] **Step 3: 实现最小 runtime 骨架与 thread store**

```python
# packages/api/app/services/chat_agent_runtime/thread_store.py
from collections import defaultdict
from typing import Any


class InMemoryThreadStore:
    def __init__(self) -> None:
        self._threads: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def get_thread(self, session_id: str) -> list[dict[str, Any]]:
        return list(self._threads[session_id])

    def append_event(self, session_id: str, event: dict[str, Any]) -> None:
        self._threads[session_id].append(event)
```

```python
# packages/api/app/services/chat_agent_runtime/provider_reasoning.py
from typing import Any


def extract_provider_reasoning_chunks(payload: dict[str, Any]) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "reasoning":
            continue
        item_id = item.get("id")
        for summary in item.get("summary", []):
            if isinstance(summary, dict) and isinstance(summary.get("text"), str):
                chunk = {"text": summary["text"]}
                if isinstance(item_id, str):
                    chunk["id"] = item_id
                chunks.append(chunk)
    return chunks
```

```python
# packages/api/app/services/chat_agent_runtime/runtime.py
from typing import AsyncIterator
from uuid import uuid4

from .thread_store import InMemoryThreadStore


_STORE = InMemoryThreadStore()


async def stream_turn(question: str, session_id: str | None = None) -> AsyncIterator[dict]:
    sid = session_id or str(uuid4())
    turn_id = str(uuid4())
    _STORE.append_event(sid, {"type": "user", "content": question})
    yield {"type": "session", "data": {"session_id": sid, "turn_id": turn_id}}
    yield {
        "type": "final",
        "data": {
            "answer": "",
            "provider_reasoning": [],
            "tool_calls": [],
            "related_nodes": [],
            "related_edges": [],
            "subgraph_meta": {
                "center_node_id": None,
                "actual_depth": 0,
                "fallback_used": False,
                "node_count": 0,
                "edge_count": 0,
            },
            "evidence": [],
            "reasoning_trace": [],
            "session_id": sid,
        },
    }
```

```python
# packages/api/app/services/chat_agent_runtime/__init__.py
from .runtime import stream_turn

__all__ = ["stream_turn"]
```

```toml
# packages/api/pyproject.toml
"deepagents>=0.0.7",
"langgraph>=1.1.3",
```

- [ ] **Step 4: 回跑 provider reasoning / thread store 测试**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/services/test_provider_reasoning.py tests/services/test_thread_store.py -q
```

Expected:

- 通过，证明 runtime 骨架与 reasoning 提取行为已锁定

- [ ] **Step 5: 增加一个失败测试，锁定 `stream_turn` 会保存完整 thread 历史而不是人工摘要**

```python
# packages/api/tests/services/test_chat_agent_runtime.py
import pytest


@pytest.mark.asyncio
async def test_stream_turn_preserves_original_user_messages_in_thread():
    from app.services.chat_agent_runtime.runtime import stream_turn, _STORE

    async for _ in stream_turn("第一问", session_id="sid-keep-all"):
        pass
    async for _ in stream_turn("第二问", session_id="sid-keep-all"):
        pass

    history = _STORE.get_thread("sid-keep-all")
    assert history[0]["content"] == "第一问"
    assert history[1]["content"] == "第二问"
```

- [ ] **Step 6: 回跑 runtime 测试**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/services/test_chat_agent_runtime.py -q
```

Expected:

- 通过，证明 thread 历史以原始顺序保存

- [ ] **Step 7: Commit**

```bash
git add packages/api/app/services/chat_agent_runtime packages/api/tests/services/test_provider_reasoning.py packages/api/tests/services/test_thread_store.py packages/api/tests/services/test_chat_agent_runtime.py packages/api/pyproject.toml
git commit -m "feat(chat): scaffold deepagents runtime shell"
```

### Task 3: 把基础图能力整理为 `graph_tools` 注册层

**Files:**
- Create: `packages/api/app/services/graph_tools/__init__.py`
- Create: `packages/api/app/services/graph_tools/registry.py`
- Create: `packages/api/app/services/graph_tools/search_nodes.py`
- Create: `packages/api/app/services/graph_tools/search_edges.py`
- Create: `packages/api/app/services/graph_tools/expand_neighbors.py`
- Create: `packages/api/app/services/graph_tools/lookup_nodes.py`
- Create: `packages/api/app/services/graph_tools/read_cypher.py`
- Modify: `packages/api/app/graph_runtime_backend.py`
- Create: `packages/api/tests/services/test_graph_tools.py`

- [ ] **Step 1: 先写失败测试，锁定首批只暴露 5 个基础图工具**

```python
# packages/api/tests/services/test_graph_tools.py
from app.services.graph_tools.registry import build_graph_tools


def test_build_graph_tools_registers_only_foundational_graph_tools():
    tools = build_graph_tools()
    names = [tool.name for tool in tools]

    assert names == [
        "search_nodes",
        "search_edges",
        "expand_neighbors",
        "lookup_nodes",
        "read_cypher",
    ]
    assert "graph_cypher_qa" not in names
```

```python
def test_search_nodes_tool_description_guides_agent_to_anchor_first():
    tools = build_graph_tools()
    tool = next(tool for tool in tools if tool.name == "search_nodes")

    assert "锚点" in tool.description
    assert "模糊" in tool.description
```

- [ ] **Step 2: 运行测试确认 `graph_tools` 层尚不存在**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/services/test_graph_tools.py -q
```

Expected:

- 失败，提示 `graph_tools` 模块不存在

- [ ] **Step 3: 先补 backend 所需的只读图查询方法**

```python
# packages/api/app/graph_runtime_backend.py
class ApiGraphRuntimeBackend:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20) -> list[dict]:
        ...

    async def search_edges(
        self,
        rel_query: str,
        source_label: str | None = None,
        target_label: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        rows = await graph_service.query_relationships(
            rel_query=rel_query,
            source_label=source_label,
            target_label=target_label,
            limit=limit,
        )
        return rows

    async def lookup_nodes(self, node_ids: list[str]) -> list[dict]:
        rows = []
        for node_id in node_ids:
            row = await graph_service.get_node_by_id(node_id)
            if row:
                rows.append(row)
        return rows
```

- [ ] **Step 4: 实现工具文件与 registry**

```python
# packages/api/app/services/graph_tools/search_nodes.py
from pydantic import BaseModel, Field


class SearchNodesArgs(BaseModel):
    query: str = Field(description="节点关键词，优先用于定位锚点")
    label: str | None = Field(default=None, description="可选节点类型过滤")
    limit: int = Field(default=5, ge=1, le=20, description="返回候选上限")
```

```python
# packages/api/app/services/graph_tools/registry.py
from app.services.graph_tools.search_nodes import build_search_nodes_tool
from app.services.graph_tools.search_edges import build_search_edges_tool
from app.services.graph_tools.expand_neighbors import build_expand_neighbors_tool
from app.services.graph_tools.lookup_nodes import build_lookup_nodes_tool
from app.services.graph_tools.read_cypher import build_read_cypher_tool


def build_graph_tools():
    return [
        build_search_nodes_tool(),
        build_search_edges_tool(),
        build_expand_neighbors_tool(),
        build_lookup_nodes_tool(),
        build_read_cypher_tool(),
    ]
```

- [ ] **Step 5: 回跑 `graph_tools` 测试**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/services/test_graph_tools.py -q
```

Expected:

- 通过，证明只注册了 5 个基础图工具，且描述里明确“先锚点、再游走”的建议

- [ ] **Step 6: Commit**

```bash
git add packages/api/app/services/graph_tools packages/api/app/graph_runtime_backend.py packages/api/tests/services/test_graph_tools.py
git commit -m "feat(chat): register foundational graph tools"
```

### Task 4: 把 `/chat/stream` 接到 `deepagents` runtime，并输出新 SSE 事件

**Files:**
- Modify: `packages/api/app/api/chat.py`
- Modify: `packages/api/app/services/chat_agent_runtime/runtime.py`
- Modify: `packages/api/app/services/chat_agent_runtime/event_adapter.py`
- Modify: `packages/api/tests/api/test_chat_routes.py`
- Modify: `packages/api/tests/services/test_chat_agent_runtime.py`

- [ ] **Step 1: 写失败测试，锁定 `/chat/stream` 调用的是 `stream_turn` 而不是旧 `ChatService.answer_question_stream`**

```python
# packages/api/tests/api/test_chat_routes.py
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_chat_stream_delegates_to_chat_agent_runtime(client):
    async def fake_stream_turn(question: str, session_id: str | None = None):
        yield {"type": "session", "data": {"session_id": "sid-1", "turn_id": "turn-1"}}
        yield {"type": "final", "data": {"answer": "done", "provider_reasoning": [], "tool_calls": [], "related_nodes": [], "related_edges": [], "subgraph_meta": {"center_node_id": None, "actual_depth": 0, "fallback_used": False, "node_count": 0, "edge_count": 0}, "evidence": [], "reasoning_trace": [], "session_id": "sid-1"}}

    with patch("app.api.chat.stream_chat_turn", side_effect=fake_stream_turn) as stream_mock:
        response = await client.post("/api/v1/chat/stream", json={"question": "外寒入里怎么办", "session_id": "sid-1"})

    assert response.status_code == 200
    stream_mock.assert_called_once_with("外寒入里怎么办", "sid-1")
```

- [ ] **Step 2: 运行测试确认 route 仍在实例化旧 `ChatService`**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/api/test_chat_routes.py::test_chat_stream_delegates_to_chat_agent_runtime -q
```

Expected:

- 失败，提示 route 未调用 `stream_chat_turn`

- [ ] **Step 3: 改造 route，接入新 runtime**

```python
# packages/api/app/api/chat.py
from ..services.chat_agent_runtime import stream_turn as stream_chat_turn


@router.post("/stream")
async def stream_answer(payload: AskQuestionRequest):
    async def event_generator():
        async for event in stream_chat_turn(payload.question, payload.session_id):
            event_type = event["type"]
            event_data = json.dumps(event["data"], ensure_ascii=False)
            yield f"event: {event_type}\ndata: {event_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 4: 在 runtime 中补最小事件链，接入 graph tools 和 system prompt**

```python
# packages/api/app/services/chat_agent_runtime/runtime.py
from app.services.graph_tools.registry import build_graph_tools
from .system_prompt import build_graph_specialist_system_prompt


async def stream_turn(question: str, session_id: str | None = None):
    sid = session_id or str(uuid4())
    turn_id = str(uuid4())
    history = _STORE.get_thread(sid)
    _STORE.append_event(sid, {"type": "user", "content": question})

    yield {"type": "session", "data": {"session_id": sid, "turn_id": turn_id}}

    # 第一版先通过 fake adapter 把 deepagents 接线位打通，后续任务再补 provider reasoning / tool / final 细节
    agent = build_graph_specialist_agent(
        system_prompt=build_graph_specialist_system_prompt(),
        tools=build_graph_tools(),
        history=history + [{"type": "user", "content": question}],
    )
    async for event in adapt_agent_events(agent, session_id=sid, turn_id=turn_id):
        yield event
```

- [ ] **Step 5: 回跑 chat route 定向测试**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/api/test_chat_routes.py::test_chat_stream_delegates_to_chat_agent_runtime -q
```

Expected:

- 通过，证明唯一 chat 入口已经接到新 runtime

- [ ] **Step 6: Commit**

```bash
git add packages/api/app/api/chat.py packages/api/app/services/chat_agent_runtime/runtime.py packages/api/app/services/chat_agent_runtime/event_adapter.py packages/api/tests/api/test_chat_routes.py packages/api/tests/services/test_chat_agent_runtime.py
git commit -m "feat(chat): route chat stream through deepagents runtime"
```

### Task 5: 让前端 chat 页面消费 agent SSE 并展示流式过程

**Files:**
- Modify: `packages/web/src/services/api.ts`
- Modify: `packages/web/src/hooks/useChat.ts`
- Modify: `packages/web/src/components/chat/GraphAgentBasisPanel.tsx`
- Modify: `packages/web/src/components/chat/MessageList.tsx`
- Modify: `packages/web/src/pages/ChatPage.tsx`
- Modify: `packages/web/src/pages/ChatPage.test.tsx`

- [ ] **Step 1: 写失败测试，锁定 ChatPage 会渲染流式工具事件与 provider reasoning**

```tsx
// packages/web/src/pages/ChatPage.test.tsx
it("renders provider reasoning only when stream emits native reasoning chunks", async () => {
  const user = userEvent.setup();
  vi.spyOn(chatApi, "stream").mockImplementation((_question, _sessionId, callbacks) => {
    callbacks?.onSession?.("sid-1", "turn-1");
    callbacks?.onProviderReasoning?.({ id: "rs-1", text: "先定位病证锚点，再查药材关系" });
    callbacks?.onToolStart?.({
      call_id: "call-1",
      tool_name: "search_nodes",
      arguments: { query: "感冒", limit: 5 },
    });
    callbacks?.onToolResult?.({
      call_id: "call-1",
      tool_name: "search_nodes",
      result_summary: "返回 2 个候选节点",
    });
    callbacks?.onAnswerChunk?.("可考虑桂枝。");
    callbacks?.onFinal?.({
      answer: "可考虑桂枝。",
      provider_reasoning: [{ id: "rs-1", text: "先定位病证锚点，再查药材关系" }],
      evidence: [],
      related_nodes: [],
      related_edges: [],
      subgraph_meta: {
        center_node_id: null,
        actual_depth: 0,
        fallback_used: false,
        node_count: 0,
        edge_count: 0,
      },
      reasoning_trace: [],
      tool_calls: [],
      session_id: "sid-1",
    });
    return new AbortController();
  });

  renderWithProviders(<ChatPage />);
  await user.type(screen.getByPlaceholderText("输入您的问题，例如：陈皮有什么功效？"), "感冒怎么办");
  await user.click(screen.getByRole("button", { name: /发送/ }));

  expect(await screen.findByText("先定位病证锚点，再查药材关系")).toBeInTheDocument();
  expect(screen.getByText("search_nodes")).toBeInTheDocument();
  expect(screen.getByText(/"query": "感冒"/)).toBeInTheDocument();
  expect(screen.getByText("返回 2 个候选节点")).toBeInTheDocument();
  expect(screen.getByText("可考虑桂枝。")).toBeInTheDocument();
});
```

```tsx
it("does not render reasoning panel when provider reasoning is absent", async () => {
  const user = userEvent.setup();
  vi.spyOn(chatApi, "stream").mockImplementation((_question, _sessionId, callbacks) => {
    callbacks?.onSession?.("sid-2", "turn-2");
    callbacks?.onAnswerChunk?.("暂无足够图谱证据。");
    callbacks?.onFinal?.({
      answer: "暂无足够图谱证据。",
      provider_reasoning: [],
      evidence: [],
      related_nodes: [],
      related_edges: [],
      subgraph_meta: {
        center_node_id: null,
        actual_depth: 0,
        fallback_used: false,
        node_count: 0,
        edge_count: 0,
      },
      reasoning_trace: [],
      tool_calls: [],
      session_id: "sid-2",
    });
    return new AbortController();
  });

  renderWithProviders(<ChatPage />);
  await user.type(screen.getByPlaceholderText("输入您的问题，例如：陈皮有什么功效？"), "外寒入里怎么办");
  await user.click(screen.getByRole("button", { name: /发送/ }));

  expect(await screen.findByText("暂无足够图谱证据。")).toBeInTheDocument();
  expect(screen.queryByText("provider_reasoning")).not.toBeInTheDocument();
});
```

- [ ] **Step 2: 运行测试确认当前 `useChat` 仍走 `graphAgentApi.ask()`**

Run:

```bash
cd packages/web
corepack pnpm test --run src/pages/ChatPage.test.tsx
```

Expected:

- 失败，提示 `chatApi.stream` 未被调用，或 provider reasoning/tool stream 不会实时渲染

- [ ] **Step 3: 改造 `chatApi.stream()`，解析新的 agent SSE 事件**

```ts
// packages/web/src/services/api.ts
switch (eventType) {
  case "session":
    callbacks?.onSession?.(payload.session_id, payload.turn_id);
    break;
  case "provider_reasoning":
    callbacks?.onProviderReasoning?.(payload);
    break;
  case "tool_start":
    callbacks?.onToolStart?.(payload);
    break;
  case "tool_result":
    callbacks?.onToolResult?.(payload);
    break;
  case "subgraph_patch":
    callbacks?.onSubgraphPatch?.(payload);
    break;
  case "answer_chunk":
    callbacks?.onAnswerChunk?.(payload.text);
    break;
  case "final":
    callbacks?.onFinal?.(payload);
    break;
  case "error":
    callbacks?.onError?.(payload.message);
    break;
}
```

- [ ] **Step 4: 改造 `useChat.ts`，用单条 assistant 草稿消息承接流式过程**

```ts
// packages/web/src/hooks/useChat.ts
const assistantId = (Date.now() + 1).toString();
addMessage({ id: assistantId, role: "assistant", content: "", providerReasoning: [], toolCalls: [] });

const controller = chatApi.stream(question.trim(), sessionId, {
  onSession: (sid) => setSessionId(sid),
  onProviderReasoning: (chunk) => updateMessage(assistantId, (msg) => ({
    ...msg,
    providerReasoning: [...(msg.providerReasoning ?? []), chunk],
  })),
  onToolStart: (event) => updateMessage(assistantId, (msg) => ({
    ...msg,
    toolCalls: [
      ...(msg.toolCalls ?? []),
      {
        tool_name: event.tool_name,
        arguments: event.arguments,
        summary: "工具调用开始",
        status: "running",
        call_id: event.call_id,
      },
    ],
  })),
  onToolResult: (event) => updateMessage(assistantId, (msg) => ({
    ...msg,
    toolCalls: (msg.toolCalls ?? []).map((tool) =>
      tool.call_id === event.call_id
        ? { ...tool, result_summary: event.result_summary, status: "completed" }
        : tool,
    ),
  })),
  onAnswerChunk: (text) => updateMessage(assistantId, (msg) => ({
    ...msg,
    content: `${msg.content}${text}`,
  })),
  onFinal: (payload) => updateMessage(assistantId, () => buildAssistantMessageFromFinal(payload)),
  onError: (message) => showErrorMessage(message, assistantId),
});
```

- [ ] **Step 5: 改造 `GraphAgentBasisPanel.tsx`，只有 provider reasoning 存在时才显示该区块**

```tsx
// packages/web/src/components/chat/GraphAgentBasisPanel.tsx
{providerReasoning.length ? (
  <List
    size="small"
    header={<Text strong>provider_reasoning</Text>}
    dataSource={providerReasoning}
    renderItem={(item) => (
      <List.Item style={{ padding: "4px 0" }}>
        <Text>{item.text}</Text>
      </List.Item>
    )}
  />
) : null}
```

- [ ] **Step 6: 回跑前端定向测试**

Run:

```bash
cd packages/web
corepack pnpm test --run src/pages/ChatPage.test.tsx
corepack pnpm exec vp build
```

Expected:

- ChatPage 定向测试通过
- provider reasoning 有/无两种路径都符合预期
- 构建通过

- [ ] **Step 7: Commit**

```bash
git add packages/web/src/services/api.ts packages/web/src/hooks/useChat.ts packages/web/src/components/chat/GraphAgentBasisPanel.tsx packages/web/src/components/chat/MessageList.tsx packages/web/src/pages/ChatPage.tsx packages/web/src/pages/ChatPage.test.tsx
git commit -m "feat(chat): stream graph agent process in chat UI"
```

### Task 6: 退役旧 `graph-agent` 主路径与规则 planner

**Files:**
- Delete: `packages/api/app/services/graph_agent_service.py`
- Delete: `packages/api/app/services/graph_cypher_agent.py`
- Delete: `packages/api/tests/services/test_graph_agent_service.py`
- Delete: `packages/api/tests/api/test_graph_agent_routes.py`
- Delete: `packages/graph_runtime/graph_runtime/planner/query_intent.py`
- Delete: `packages/graph_runtime/graph_runtime/planner/tool_plan_builder.py`
- Delete: `packages/graph_runtime/graph_runtime/agent/graph_agent.py`
- Modify: `packages/api/app/main.py`
- Modify: `packages/api/app/api/__init__.py` 或相关 router 接线文件

- [ ] **Step 1: 写失败测试，锁定主应用不再挂载 `/graph-agent` 路由**

```python
# packages/api/tests/api/test_chat_routes.py
import pytest


@pytest.mark.asyncio
async def test_graph_agent_route_is_no_longer_available(client):
    response = await client.post("/api/v1/graph-agent/ask", json={"question": "黄芩归什么经？"})

    assert response.status_code == 404
```

- [ ] **Step 2: 运行测试确认旧 route 仍存在**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/api/test_chat_routes.py::test_graph_agent_route_is_no_longer_available -q
```

Expected:

- 失败，说明旧 `graph-agent` route 仍被挂载

- [ ] **Step 3: 移除应用接线，删除旧 service / route 测试文件**

```python
# packages/api/app/main.py
# 删除:
# from .api.graph_agent import router as graph_agent_router
# app.include_router(graph_agent_router, prefix=settings.api_prefix)
```

```bash
git rm packages/api/app/services/graph_agent_service.py
git rm packages/api/app/services/graph_cypher_agent.py
git rm packages/api/tests/services/test_graph_agent_service.py
git rm packages/api/tests/api/test_graph_agent_routes.py
git rm packages/graph_runtime/graph_runtime/planner/query_intent.py
git rm packages/graph_runtime/graph_runtime/planner/tool_plan_builder.py
git rm packages/graph_runtime/graph_runtime/agent/graph_agent.py
```

- [ ] **Step 4: 回跑 route 退役测试**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/api/test_chat_routes.py::test_graph_agent_route_is_no_longer_available -q
```

Expected:

- 通过，证明旧 graph-agent 主路径已经退出

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/main.py packages/api/tests/api/test_chat_routes.py
git commit -m "refactor(chat): retire legacy graph agent entrypoints"
```

### Task 7: 文档与全量验证

**Files:**
- Modify: `docs/architecture/system-overview.md`
- Modify: `docs/acceptance/chat-mainline.md`

- [ ] **Step 1: 更新架构文档，明确 chat 单入口 + deepagents graph specialist**

```md
<!-- docs/architecture/system-overview.md -->
- 对外图谱问答主入口已收敛到 `/api/v1/chat/stream`
- `deepagents` graph specialist agent 负责工具决策与过程流
- 基础图工具包括：`search_nodes`、`search_edges`、`expand_neighbors`、`lookup_nodes`、`read_cypher`
- provider 原生 reasoning 有则透传，无则不显示
```

- [ ] **Step 2: 更新验收文档，补唯一 chat 入口和 agent 事件流 smoke**

```md
<!-- docs/acceptance/chat-mainline.md -->
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"question":"治感冒的中药都有哪些，怎么做","session_id":"acceptance-chat-1"}'

预期事件：
- `session`
- `tool_start`
- `tool_result`
- `answer_chunk`
- `final`

可选事件：
- `provider_reasoning`
```

- [ ] **Step 3: 运行 API 最低验证**

Run:

```bash
cd packages/api
uv run ruff check app tests
uv run ty check
uv run pytest -m "not integration"
```

Expected:

- API 最低验证通过

- [ ] **Step 4: 运行 Web 最低验证**

Run:

```bash
corepack pnpm --dir packages/web test --run
corepack pnpm --dir packages/web exec vp build
```

Expected:

- Web tests 通过
- 构建通过

- [ ] **Step 5: Commit**

```bash
git add docs/architecture/system-overview.md docs/acceptance/chat-mainline.md
git commit -m "docs(chat): document deepagents graph chat flow"
```

## Self-Review

- **Spec coverage:** 已覆盖单入口 `/chat/stream`、`deepagents` runtime、LangGraph `thread_id` + 进程内 `InMemorySaver` 会话续接、30 分钟 TTL 回收、同 session 串行锁、基础图工具注册、provider 原生 reasoning 透传、前端流式展示、旧 `graph-agent` 路径退役和文档更新。
- **Placeholder scan:** 计划中没有 `TODO`、`TBD`、"类似 Task N" 或“自行处理”类占位项；每个任务都包含明确文件、测试和命令。
- **Type consistency:** 统一使用 `provider_reasoning`、`tool_start`、`tool_result`、`subgraph_patch`、`answer_chunk`、`final` 这套事件名；统一使用 `search_nodes`、`search_edges`、`expand_neighbors`、`lookup_nodes`、`read_cypher` 作为基础图工具名；不再在后续任务中引入 `graph_cypher_qa`。
