# Graph Agent Complex Query / LangChain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 graph agent 能处理“不直接命中实体”的复杂自然语言问题，基于 LangChain Neo4j 图查询能力完成工具调用循环，并继续输出可展开依据子图的最终答案。

**Architecture:** 保持 `/api/v1/graph-agent/ask` 与前端页面协议不变，直接重构 `packages/graph_runtime/` 内部：新增“问题意图分类 + 工具计划 + 图查询 loop”层，把实体型问题继续走 `search_nodes / expand_neighbors`，把抽象问题切到 LangChain-backed `graph_cypher_qa`。API 层负责把 Neo4j 连接与现有 LLM 配置接到 runtime 需要的 cypher agent；前端继续消费统一 `GraphAgentResponse`，但会展示更丰富的 `tool_calls.arguments / result_summary / generated_cypher`。

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, LangChain, `langchain-neo4j`, Neo4j, React 18, Vite, Vitest

---

## File Map

### Runtime (`packages/graph_runtime/`)

- Modify: `packages/graph_runtime/pyproject.toml` — 在实际接入 cypher agent 时增加 LangChain 能力所需依赖
- Create: `packages/graph_runtime/graph_runtime/planner/query_intent.py` — 问题意图分类（实体问句 / 抽象症状问句 / 治法问句 / fallback）
- Create: `packages/graph_runtime/graph_runtime/planner/tool_plan_builder.py` — 根据意图与问题构建初始工具调用计划
- Modify: `packages/graph_runtime/graph_runtime/planner/plan_builder.py` — 输出 `query_mode`、`entity_hints`、`target_node_types`、`target_edge_types`
- Modify: `packages/graph_runtime/graph_runtime/planner/__init__.py` — 导出新 planner API
- Create: `packages/graph_runtime/graph_runtime/service/cypher_agent.py` — runtime 侧 cypher agent 协议
- Modify: `packages/graph_runtime/graph_runtime/contracts/tool_calls.py` — 规范 `arguments`、`status`、`result_summary`
- Modify: `packages/graph_runtime/graph_runtime/contracts/outputs.py` — `GraphAgentAnswer.tool_calls` 使用结构化模型
- Modify: `packages/graph_runtime/graph_runtime/agent/graph_agent.py` — 重构为 question-router + tool loop + result hydration
- Create: `packages/graph_runtime/tests/test_query_intent.py` — 抽象 query 分类测试
- Create: `packages/graph_runtime/tests/test_tool_plan_builder.py` — 工具计划构建测试
- Modify: `packages/graph_runtime/tests/test_graph_agent.py` — loop、fallback、复杂 query 主路径测试

### API (`packages/api/`)

- Modify: `packages/api/pyproject.toml` — API 层增加 `langchain-neo4j`
- Create: `packages/api/app/services/graph_cypher_agent.py` — 基于 `Neo4jGraph + GraphCypherQAChain` 的 API 适配器
- Modify: `packages/api/app/services/graph_agent_service.py` — 注入 graph facade + cypher agent
- Modify: `packages/api/app/graph_runtime_backend.py` — 补 schema 摘要 / 搜索结果归一化辅助方法（如需要）
- Create: `packages/api/tests/services/test_graph_cypher_agent.py` — LangChain cypher adapter 单测
- Modify: `packages/api/tests/services/test_graph_agent_service.py` — 复杂 query 服务层测试
- Modify: `packages/api/tests/api/test_graph_agent_routes.py` — 抽象 query route payload 测试

### Web (`packages/web/`)

- Modify: `packages/web/src/types/chat.ts` — `tool_calls` 增加 `arguments`、`result_summary`、可选 `generated_cypher`
- Modify: `packages/web/src/hooks/useChat.ts` — 保持兼容但透传 richer tool call payload
- Modify: `packages/web/src/components/chat/GraphAgentBasisPanel.tsx` — 展示工具参数、cypher 摘要、结果摘要
- Modify: `packages/web/src/pages/ChatPage.test.tsx` — 复杂 query 页面主路径测试

### Docs

- Modify: `docs/acceptance/chat-mainline.md` — 把复杂 query 样例纳入验收
- Modify: `docs/architecture/system-overview.md` — 更新“问题分类 → graph tool loop → cypher agent”数据流

---

### Task 1: 锁定复杂 query 契约

**Files:**
- Modify: `packages/graph_runtime/graph_runtime/contracts/tool_calls.py`
- Modify: `packages/graph_runtime/graph_runtime/contracts/outputs.py`
- Test: `packages/graph_runtime/tests/test_contracts.py`

- [ ] **Step 1: 先写失败测试，锁定 richer tool call 契约**

```python
# packages/graph_runtime/tests/test_contracts.py
from graph_runtime.contracts.outputs import GraphAgentAnswer, GraphSubgraphMeta


def test_graph_agent_answer_tool_calls_support_arguments_and_result_summary():
    answer = GraphAgentAnswer(
        answer="感冒相关中药包括桂枝、荆芥等。",
        evidence=[],
        related_nodes=[],
        related_edges=[],
        subgraph_meta=GraphSubgraphMeta(center_node_id=None, actual_depth=0, fallback_used=True),
        reasoning_trace=[{"kind": "planner", "summary": "识别为抽象症状问题"}],
        tool_calls=[
            {
                "tool_name": "graph_cypher_qa",
                "arguments": {
                    "question": "治感冒的中药都有哪些，怎么做",
                    "top_k": 8,
                },
                "summary": "使用 schema-aware cypher agent 查询图谱",
                "result_summary": "返回 6 个候选药材与 1 段结构化说明",
                "status": "completed",
            }
        ],
    )

    assert answer.tool_calls[0].tool_name == "graph_cypher_qa"
    assert answer.tool_calls[0].arguments["top_k"] == 8
    assert answer.tool_calls[0].result_summary.startswith("返回 6 个候选")
```

- [ ] **Step 2: 运行测试确认当前 contracts 还不完整**

Run:

```bash
cd packages/graph_runtime
uv run --with pytest pytest tests/test_contracts.py -q
```

Expected:

- 失败，提示 `GraphToolCall` 缺少 `arguments` / `result_summary` / `status`

- [ ] **Step 3: 最小实现 contracts 升级**

```python
# packages/graph_runtime/graph_runtime/contracts/tool_calls.py
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GraphToolCall(BaseModel):
    tool_name: str = Field(description="调用的工具名")
    arguments: dict[str, Any] = Field(default_factory=dict, description="工具调用参数")
    summary: str = Field(description="工具调用摘要")
    result_summary: str | None = Field(default=None, description="工具执行结果摘要")
    status: str = Field(default="completed", description="工具执行状态")

    model_config = ConfigDict(use_enum_values=False)
```

```python
# packages/graph_runtime/graph_runtime/contracts/outputs.py
from .tool_calls import GraphToolCall

tool_calls: list[GraphToolCall] = Field(default_factory=list, description="工具调用记录")
```

- [ ] **Step 4: 回跑 contracts 测试**

Run:

```bash
cd packages/graph_runtime
uv run --with pytest pytest tests/test_contracts.py -q
```

Expected:

- `tool_calls` 支持 richer payload

- [ ] **Step 5: Commit**

```bash
git add packages/graph_runtime/graph_runtime/contracts packages/graph_runtime/tests/test_contracts.py
git commit -m "feat(graph-runtime): extend tool call contracts"
```

### Task 2: 增加复杂 query 意图分类与工具计划构建

**Files:**
- Create: `packages/graph_runtime/graph_runtime/planner/query_intent.py`
- Create: `packages/graph_runtime/graph_runtime/planner/tool_plan_builder.py`
- Modify: `packages/graph_runtime/graph_runtime/planner/plan_builder.py`
- Modify: `packages/graph_runtime/graph_runtime/planner/__init__.py`
- Test: `packages/graph_runtime/tests/test_query_intent.py`
- Test: `packages/graph_runtime/tests/test_tool_plan_builder.py`

- [ ] **Step 1: 写失败测试，锁定抽象问题分类**

```python
# packages/graph_runtime/tests/test_query_intent.py
from graph_runtime.planner.query_intent import classify_query_intent


def test_classify_query_intent_marks_symptom_question_as_abstract_graph_query():
    intent = classify_query_intent("治感冒的中药都有哪些，怎么做")

    assert intent.query_mode == "abstract_graph_query"
    assert "病证" in intent.target_node_types
    assert "治疗病证" in intent.target_edge_types


def test_classify_query_intent_marks_external_cold_question_as_abstract_graph_query():
    intent = classify_query_intent("外寒入里怎么办")

    assert intent.query_mode == "abstract_graph_query"
    assert intent.requires_cypher_agent is True
```

```python
# packages/graph_runtime/tests/test_tool_plan_builder.py
from graph_runtime.planner.plan_builder import build_graph_plan
from graph_runtime.planner.tool_plan_builder import build_initial_tool_plan


def test_tool_plan_builder_prefers_graph_cypher_for_abstract_query():
    plan = build_graph_plan("治感冒的中药都有哪些，怎么做")
    tool_plan = build_initial_tool_plan(plan)

    assert tool_plan[0].tool_name == "graph_cypher_qa"
    assert tool_plan[0].arguments["question"] == "治感冒的中药都有哪些，怎么做"


def test_tool_plan_builder_keeps_search_first_for_entity_query():
    plan = build_graph_plan("黄芩归什么经？")
    tool_plan = build_initial_tool_plan(plan)

    assert tool_plan[0].tool_name == "search_nodes"
    assert tool_plan[0].arguments["query"] == "黄芩"
```

- [ ] **Step 2: 运行测试确认分类器和工具计划器不存在**

Run:

```bash
cd packages/graph_runtime
uv run --with pytest pytest tests/test_query_intent.py tests/test_tool_plan_builder.py -q
```

Expected:

- 失败，提示 `query_intent` / `tool_plan_builder` 不存在

- [ ] **Step 3: 实现最小意图分类器**

```python
# packages/graph_runtime/graph_runtime/planner/query_intent.py
from dataclasses import dataclass, field


ABSTRACT_QUERY_KEYWORDS = [
    "哪些",
    "都有哪些",
    "怎么办",
    "怎么做",
    "治",
]


@dataclass
class QueryIntent:
    query_mode: str
    target_node_types: list[str] = field(default_factory=list)
    target_edge_types: list[str] = field(default_factory=list)
    requires_cypher_agent: bool = False


def classify_query_intent(question: str) -> QueryIntent:
    normalized = question.replace("？", "").replace("?", "").strip()
    if any(keyword in normalized for keyword in ABSTRACT_QUERY_KEYWORDS):
        return QueryIntent(
            query_mode="abstract_graph_query",
            target_node_types=["病证", "功效", "药材"],
            target_edge_types=["治疗病证", "具有功效"],
            requires_cypher_agent=True,
        )
    return QueryIntent(query_mode="entity_lookup")
```

- [ ] **Step 4: 实现工具计划构建器**

```python
# packages/graph_runtime/graph_runtime/planner/tool_plan_builder.py
from dataclasses import dataclass


@dataclass
class PlannedToolCall:
    tool_name: str
    arguments: dict
    summary: str


def build_initial_tool_plan(plan: dict) -> list[PlannedToolCall]:
    if plan["query_mode"] == "abstract_graph_query":
        return [
            PlannedToolCall(
                tool_name="graph_cypher_qa",
                arguments={"question": plan["question"], "top_k": 8},
                summary="对抽象问题使用 schema-aware graph cypher agent",
            )
        ]
    return [
        PlannedToolCall(
            tool_name="search_nodes",
            arguments={"query": plan["entity_hints"][0], "limit": 5},
            summary="根据实体 hint 搜索图谱节点",
        )
    ]
```

```python
# packages/graph_runtime/graph_runtime/planner/plan_builder.py
from .entity_fuzzy_recall import normalize_question, recall_entity_keywords
from .query_intent import classify_query_intent


def build_graph_plan(question: str) -> dict:
    normalized_question = normalize_question(question)
    intent = classify_query_intent(question)
    return {
        "question": question,
        "normalized_question": normalized_question,
        "query_mode": intent.query_mode,
        "entity_hints": recall_entity_keywords(question),
        "target_node_types": list(intent.target_node_types),
        "target_edge_types": list(intent.target_edge_types),
        "requires_cypher_agent": intent.requires_cypher_agent,
        "search_mode": "adaptive",
    }
```

- [ ] **Step 5: 回跑 planner 测试**

Run:

```bash
cd packages/graph_runtime
uv run --with pytest pytest tests/test_query_intent.py tests/test_tool_plan_builder.py -q
```

Expected:

- 抽象 query 被标成 `abstract_graph_query`
- 实体 query 继续走 `search_nodes`

- [ ] **Step 6: Commit**

```bash
git add packages/graph_runtime/graph_runtime/planner packages/graph_runtime/tests/test_query_intent.py packages/graph_runtime/tests/test_tool_plan_builder.py
git commit -m "feat(graph-runtime): classify complex graph queries"
```

### Task 3: 增加 LangChain Neo4j cypher agent 适配器

**Files:**
- Modify: `packages/graph_runtime/pyproject.toml`
- Modify: `packages/api/pyproject.toml`
- Create: `packages/graph_runtime/graph_runtime/service/cypher_agent.py`
- Create: `packages/api/app/services/graph_cypher_agent.py`
- Test: `packages/api/tests/services/test_graph_cypher_agent.py`

- [ ] **Step 1: 写失败测试，锁定 cypher agent 返回中间步骤**

```python
# packages/api/tests/services/test_graph_cypher_agent.py
import pytest


class FakeChain:
    def invoke(self, payload):
        assert payload["query"] == "治感冒的中药都有哪些，怎么做"
        return {
            "result": "可考虑桂枝、荆芥、防风等。",
            "intermediate_steps": [
                {"query": "MATCH (h:Herb)-[:TREATS]->(d:Disease {name: '感冒'}) RETURN h.name LIMIT 8"},
                {"context": [{"name": "桂枝"}, {"name": "荆芥"}]},
            ],
        }


@pytest.mark.asyncio
async def test_graph_cypher_agent_returns_generated_cypher_and_candidates():
    from app.services.graph_cypher_agent import GraphCypherAgentService

    service = GraphCypherAgentService(chain=FakeChain())
    result = await service.answer("治感冒的中药都有哪些，怎么做")

    assert result["answer"].startswith("可考虑桂枝")
    assert "MATCH (h:Herb)" in result["generated_cypher"]
    assert result["node_names"] == ["桂枝", "荆芥"]
```

- [ ] **Step 2: 运行测试确认 adapter 尚不存在**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/services/test_graph_cypher_agent.py -q
```

Expected:

- 失败，提示 `GraphCypherAgentService` 不存在

- [ ] **Step 3: 定义 runtime 侧 cypher agent 协议**

```toml
# packages/graph_runtime/pyproject.toml
dependencies = [
    "pydantic>=2.10.0",
    "langchain>=0.3.0",
    "langchain-core>=0.3.0",
]
```

```toml
# packages/api/pyproject.toml
"langchain>=0.3.0",
"langchain-openai>=0.2.0",
"langchain-anthropic>=1.4.0",
"langchain-neo4j>=0.2.0",
```

```python
# packages/graph_runtime/graph_runtime/service/cypher_agent.py
from typing import Any, Protocol


class GraphCypherAgent(Protocol):
    async def answer(self, question: str, top_k: int = 8) -> dict[str, Any]:
        raise NotImplementedError
```

- [ ] **Step 4: 实现 API 层 LangChain Neo4j adapter**

```python
# packages/api/app/services/graph_cypher_agent.py
from anyio import to_thread
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph

from ..core.config import get_settings
from .llm_client import get_chat_model


class GraphCypherAgentService:
    def __init__(self, chain=None) -> None:
        if chain is not None:
            self.chain = chain
            return

        settings = get_settings()
        graph = Neo4jGraph(
            url=settings.neo4j_uri,
            username=settings.neo4j_user,
            password=settings.neo4j_password,
            refresh_schema=False,
        )
        llm = get_chat_model()
        if llm is None:
            raise RuntimeError("Graph cypher agent requires configured LLM")
        self.chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=False,
            allow_dangerous_requests=False,
            return_intermediate_steps=True,
            validate_cypher=True,
            top_k=8,
            use_function_response=True,
        )

    async def answer(self, question: str, top_k: int = 8) -> dict:
        result = await to_thread.run_sync(self.chain.invoke, {"query": question, "top_k": top_k})
        steps = result.get("intermediate_steps", [])
        generated_cypher = steps[0].get("query") if steps else None
        context_rows = steps[1].get("context", []) if len(steps) > 1 else []
        node_names = [row["name"] for row in context_rows if isinstance(row, dict) and row.get("name")]
        return {
            "answer": result.get("result", ""),
            "generated_cypher": generated_cypher,
            "node_names": node_names,
            "intermediate_steps": steps,
        }
```

- [ ] **Step 5: 回跑 cypher agent 测试**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/services/test_graph_cypher_agent.py -q
```

Expected:

- adapter 能返回自然语言结果、生成的 cypher 和候选节点名

- [ ] **Step 6: Commit**

```bash
git add packages/graph_runtime/pyproject.toml packages/api/pyproject.toml packages/graph_runtime/graph_runtime/service/cypher_agent.py packages/api/app/services/graph_cypher_agent.py packages/api/tests/services/test_graph_cypher_agent.py
git commit -m "feat(api): add langchain neo4j cypher agent adapter"
```

### Task 4: 重构 graph runtime agent 为复杂问题工具循环

**Files:**
- Modify: `packages/graph_runtime/graph_runtime/agent/graph_agent.py`
- Modify: `packages/graph_runtime/tests/test_graph_agent.py`

- [ ] **Step 1: 写失败测试，锁定抽象问题走 cypher agent + subgraph hydration**

```python
# packages/graph_runtime/tests/test_graph_agent.py
import asyncio

from graph_runtime.agent.graph_agent import GraphExplorationAgent
from graph_runtime.contracts.inputs import GraphAskRequest


class ComplexFacade:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        return [{"id": f"药材:{query}", "name": query, "labels": ["药材"]}] if query in {"桂枝", "荆芥"} else []

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        return {
            "center": {"id": node_id, "name": node_id.split(':', 1)[1], "labels": ["药材"]},
            "nodes": [{"id": node_id, "name": node_id.split(':', 1)[1], "labels": ["药材"]}],
            "edges": [],
        }

    async def read_cypher(self, query: str):
        return []


class FakeCypherAgent:
    async def answer(self, question: str, top_k: int = 8):
        return {
            "answer": "可考虑桂枝、荆芥，并结合发汗解表思路处理。",
            "generated_cypher": "MATCH (h)-[:TREATS]->(d {name:'感冒'}) RETURN h.name LIMIT 8",
            "node_names": ["桂枝", "荆芥"],
            "intermediate_steps": [],
        }


async def _run_graph_agent_uses_graph_cypher_qa_for_abstract_query():
    agent = GraphExplorationAgent(graph_facade=ComplexFacade(), cypher_agent=FakeCypherAgent())

    result = await agent.ask(GraphAskRequest(question="治感冒的中药都有哪些，怎么做", tool_call_budget=8))

    assert result.tool_calls[0].tool_name == "graph_cypher_qa"
    assert "generated_cypher" in result.tool_calls[0].arguments
    assert result.related_nodes[0]["name"] == "桂枝"
    assert "桂枝" in result.answer


def test_graph_agent_uses_graph_cypher_qa_for_abstract_query():
    asyncio.run(_run_graph_agent_uses_graph_cypher_qa_for_abstract_query())
```

- [ ] **Step 2: 运行测试确认当前 runtime agent 还不会走 cypher agent**

Run:

```bash
cd packages/graph_runtime
uv run --with pytest pytest tests/test_graph_agent.py -q
```

Expected:

- 失败，提示 `GraphExplorationAgent.__init__` 不接受 `cypher_agent`
- 或 `tool_calls[0].tool_name` 仍是 `search_nodes`

- [ ] **Step 3: 最小重构 graph agent**

```python
# packages/graph_runtime/graph_runtime/agent/graph_agent.py
from collections import deque


class GraphExplorationAgent:
    def __init__(self, graph_facade, cypher_agent=None) -> None:
        self.graph_facade = graph_facade
        self.cypher_agent = cypher_agent

    async def ask(self, request) -> GraphAgentAnswer:
        plan = build_graph_plan(request.question)
        pending_calls = deque(build_initial_tool_plan(plan))
        tool_calls: list[GraphToolCall] = []
        related_nodes: list[dict] = []
        related_edges: list[dict] = []
        draft_answer: str | None = None
        if planned_call.tool_name == "graph_cypher_qa":
            if self.cypher_agent is None:
                raise RuntimeError("graph_cypher_qa requested but no cypher agent configured")
            result = await self.cypher_agent.answer(
                planned_call.arguments["question"],
                top_k=int(planned_call.arguments.get("top_k", 8)),
            )
            tool_calls.append(
                GraphToolCall(
                    tool_name="graph_cypher_qa",
                    arguments={
                        **planned_call.arguments,
                        "generated_cypher": result.get("generated_cypher"),
                    },
                    summary=planned_call.summary,
                    result_summary=result["answer"][:120],
                )
            )
            for node_name in result.get("node_names", []):
                pending_calls.append(
                    PlannedToolCall(
                        tool_name="search_nodes",
                        arguments={"query": node_name, "limit": 5},
                        summary="根据 cypher 结果回查图谱节点",
                    )
                )
            draft_answer = result["answer"]
        if planned_call.tool_name == "search_nodes":
            matches = await self.graph_facade.search_nodes(planned_call.arguments["query"], limit=5)
            if matches:
                center = matches[0]
                expanded = await self.graph_facade.expand_neighbors(center["id"], depth=1, limit=request.node_budget)
                related_nodes = expanded.get("nodes", [])
                related_edges = expanded.get("edges", [])
        answer = draft_answer or synthesize_answer(request.question, None, related_nodes, related_edges, plan)
```

- [ ] **Step 4: 回跑 runtime agent 测试**

Run:

```bash
cd packages/graph_runtime
uv run --with pytest pytest tests/test_graph_agent.py -q
```

Expected:

- 抽象 query 首先走 `graph_cypher_qa`
- `tool_calls.arguments.generated_cypher` 可见
- 结果能继续回查节点并补出依据子图

- [ ] **Step 5: Commit**

```bash
git add packages/graph_runtime/graph_runtime/agent/graph_agent.py packages/graph_runtime/tests/test_graph_agent.py
git commit -m "feat(graph-runtime): route abstract queries through cypher loop"
```

### Task 5: 在 API 层接线复杂 query 能力

**Files:**
- Modify: `packages/api/app/services/graph_agent_service.py`
- Modify: `packages/api/tests/services/test_graph_agent_service.py`
- Modify: `packages/api/tests/api/test_graph_agent_routes.py`

- [ ] **Step 1: 写失败测试，锁定 service 会注入 cypher agent**

```python
# packages/api/tests/services/test_graph_agent_service.py
import pytest


class FakeGraphFacade:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        return [{"id": "药材:桂枝", "name": "桂枝", "labels": ["药材"]}]

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        return {"center": {"id": node_id, "name": "桂枝", "labels": ["药材"]}, "nodes": [{"id": node_id, "name": "桂枝", "labels": ["药材"]}], "edges": []}


class FakeCypherAgent:
    async def answer(self, question: str, top_k: int = 8):
        return {
            "answer": "可考虑桂枝。",
            "generated_cypher": "MATCH (h:Herb)-[:TREATS]->(d:Disease {name:'感冒'}) RETURN h.name LIMIT 8",
            "node_names": ["桂枝"],
            "intermediate_steps": [],
        }


@pytest.mark.asyncio
async def test_graph_agent_service_supports_abstract_query_payload():
    from app.services.graph_agent_service import GraphAgentService

    service = GraphAgentService(graph_facade=FakeGraphFacade(), cypher_agent=FakeCypherAgent())
    payload = await service.ask("治感冒的中药都有哪些，怎么做")

    assert payload["tool_calls"][0]["tool_name"] == "graph_cypher_qa"
    assert payload["tool_calls"][0]["arguments"]["generated_cypher"].startswith("MATCH (h:Herb)")
    assert payload["related_nodes"][0]["name"] == "桂枝"
```

- [ ] **Step 2: 运行测试确认 service 构造器还未接 `cypher_agent`**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/services/test_graph_agent_service.py tests/api/test_graph_agent_routes.py -q
```

Expected:

- 失败，提示 `GraphAgentService.__init__` 不接受 `cypher_agent`

- [ ] **Step 3: 最小实现 API service 接线**

```python
# packages/api/app/services/graph_agent_service.py
from .graph_cypher_agent import GraphCypherAgentService


class GraphAgentService:
    def __init__(self, graph_facade: Any | None = None, cypher_agent: Any | None = None) -> None:
        self.agent = GraphExplorationAgent(
            graph_facade=graph_facade or GraphFacade(ApiGraphRuntimeBackend()),
            cypher_agent=cypher_agent or GraphCypherAgentService(),
        )
```

```python
# packages/api/tests/api/test_graph_agent_routes.py
from unittest.mock import AsyncMock, patch
import pytest


@pytest.mark.asyncio
async def test_graph_agent_route_returns_abstract_query_payload(client):
    with patch("app.api.graph_agent.GraphAgentService") as service_cls:
        service_cls.return_value.ask = AsyncMock(
            return_value={
                "answer": "可考虑桂枝、荆芥。",
                "related_nodes": [{"id": "药材:桂枝", "name": "桂枝"}],
                "related_edges": [],
                "subgraph_meta": {
                    "center_node_id": "药材:桂枝",
                    "actual_depth": 1,
                    "fallback_used": False,
                    "node_count": 1,
                    "edge_count": 0,
                },
                "evidence": [],
                "reasoning_trace": [{"kind": "planner", "summary": "识别为抽象病证问题"}],
                "tool_calls": [
                    {
                        "tool_name": "graph_cypher_qa",
                        "arguments": {
                            "question": "治感冒的中药都有哪些，怎么做",
                            "generated_cypher": "MATCH (h:Herb)-[:TREATS]->(d:Disease {name:'感冒'}) RETURN h.name LIMIT 8",
                        },
                        "summary": "使用 schema-aware graph cypher agent 查询图谱",
                        "result_summary": "返回 2 个药材候选",
                        "status": "completed",
                    }
                ],
            }
        )
        response = await client.post("/api/v1/graph-agent/ask", json={"question": "治感冒的中药都有哪些，怎么做"})

    assert response.status_code == 200
```

- [ ] **Step 4: 回跑 API 接线测试**

Run:

```bash
cd packages/api
uv run --extra dev pytest tests/services/test_graph_agent_service.py tests/api/test_graph_agent_routes.py -q
```

Expected:

- 复杂 query 服务层与 route payload 都通过

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/services/graph_agent_service.py packages/api/tests/services/test_graph_agent_service.py packages/api/tests/api/test_graph_agent_routes.py
git commit -m "feat(api): wire complex graph queries into graph agent service"
```

### Task 6: 前端展示复杂 query 工具循环与更新验收

**Files:**
- Modify: `packages/web/src/types/chat.ts`
- Modify: `packages/web/src/hooks/useChat.ts`
- Modify: `packages/web/src/components/chat/GraphAgentBasisPanel.tsx`
- Modify: `packages/web/src/pages/ChatPage.test.tsx`
- Modify: `docs/acceptance/chat-mainline.md`
- Modify: `docs/architecture/system-overview.md`

- [ ] **Step 1: 写失败测试，锁定页面显示 generated cypher 与复杂 query 回答**

```tsx
// packages/web/src/pages/ChatPage.test.tsx
it("renders generated cypher and graph tool result for abstract query", async () => {
  const user = userEvent.setup();
  vi.spyOn(graphAgentApi, "ask").mockResolvedValue({
    answer: "可考虑桂枝、荆芥，并结合发汗解表思路处理。",
    evidence: [],
    related_nodes: [{ id: "药材:桂枝", name: "桂枝", status: "verified", labels: ["Herb"] }],
    related_edges: [],
    subgraph_meta: {
      center_node_id: "药材:桂枝",
      actual_depth: 1,
      fallback_used: false,
      node_count: 1,
      edge_count: 0,
    },
    reasoning_trace: [{ kind: "planner", summary: "识别为抽象病证问题" }],
    tool_calls: [
      {
        tool_name: "graph_cypher_qa",
        arguments: {
          question: "治感冒的中药都有哪些，怎么做",
          generated_cypher: "MATCH (h)-[:TREATS]->(d {name:'感冒'}) RETURN h.name LIMIT 8",
        },
        summary: "使用 schema-aware graph cypher agent 查询图谱",
        result_summary: "返回 2 个药材候选",
        status: "completed",
      },
    ],
  });

  renderWithProviders(<ChatPage />);
  await user.type(screen.getByPlaceholderText("输入您的问题，例如：陈皮有什么功效？"), "治感冒的中药都有哪些，怎么做");
  await user.click(screen.getByRole("button", { name: /发送/ }));

  expect(await screen.findByText("graph_cypher_qa")).toBeInTheDocument();
  expect(screen.getByText(/MATCH \(h\)-\[:TREATS\]->/)).toBeInTheDocument();
  expect(screen.getByText("返回 2 个药材候选")).toBeInTheDocument();
});
```

- [ ] **Step 2: 运行测试确认页面还没锁定 generated cypher**

Run:

```bash
pnpm --dir packages/web test --run src/pages/ChatPage.test.tsx
```

Expected:

- 若当前 UI 未展示 generated cypher / result summary，则失败

- [ ] **Step 3: 最小实现前端展示与文档更新**

```ts
// packages/web/src/types/chat.ts
export interface GraphAgentToolCall {
  tool_name: string;
  arguments?: Record<string, unknown>;
  summary: string;
  result_summary?: string | null;
  status?: string;
}
```

```tsx
// packages/web/src/components/chat/GraphAgentBasisPanel.tsx
{item.result_summary ? (
  <Text type="secondary" style={{ fontSize: 12 }}>
    {item.result_summary}
  </Text>
) : null}
{formatToolArguments(item.arguments) ? (
  <Paragraph code style={{ marginBottom: 0, whiteSpace: "pre-wrap", fontSize: 12 }}>
    {formatToolArguments(item.arguments)}
  </Paragraph>
) : null}
```

```text
# docs/acceptance/chat-mainline.md
### Step 4

- 操作：输入“治感冒的中药都有哪些，怎么做”或“外寒入里怎么办”
- 预期：页面能展示 `graph_cypher_qa`、generated cypher、结果摘要，以及回填后的依据子图
```

- [ ] **Step 4: 回跑前端定向测试**

Run:

```bash
pnpm --dir packages/web test --run src/pages/ChatPage.test.tsx
pnpm --dir packages/web exec vp build
```

Expected:

- Chat 页面定向测试通过
- 生产构建通过

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/types/chat.ts packages/web/src/hooks/useChat.ts packages/web/src/components/chat/GraphAgentBasisPanel.tsx packages/web/src/pages/ChatPage.test.tsx docs/acceptance/chat-mainline.md docs/architecture/system-overview.md
git commit -m "feat(web): show complex graph query tool traces"
```

### Task 7: 全链路验收与复杂样例回归

**Files:**
- Modify: `docs/acceptance/chat-mainline.md`

- [ ] **Step 1: 运行 graph runtime 全量测试**

Run:

```bash
cd packages/graph_runtime
uv run --with pytest pytest tests -q
```

Expected:

- 全量 runtime tests 通过

- [ ] **Step 2: 运行 API 最低验证**

Run:

```bash
cd packages/api
uv run ruff check app tests
uv run ty check
uv run pytest -m "not integration"
```

Expected:

- API 最低验证通过

- [ ] **Step 3: 运行 Web 最低验证**

Run:

```bash
pnpm run test:web
pnpm --dir packages/web exec vp build
```

Expected:

- Web tests 通过
- 构建通过

- [ ] **Step 4: 追加复杂 query 的人工 smoke 命令到验收文档**

```text
# docs/acceptance/chat-mainline.md
curl -sS -X POST http://localhost:8000/api/v1/graph-agent/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"治感冒的中药都有哪些，怎么做"}' | python3 -m json.tool

curl -sS -X POST http://localhost:8000/api/v1/graph-agent/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"外寒入里怎么办"}' | python3 -m json.tool
```

- [ ] **Step 5: Commit**

```bash
git add docs/acceptance/chat-mainline.md
git commit -m "docs(chat): add complex graph query acceptance"
```

## Self-Review

- **Spec coverage:** 已覆盖复杂 query 分类、LangChain Neo4j 接入、runtime tool loop、API 接线、前端展示、验收与 smoke。没有遗漏用户要求中的“复杂 query / 解析工具及参数 / 基于 graph 完成循环 / 最终输出结果”。
- **Placeholder scan:** 计划中没有 `TODO` / `TBD` / “自行处理” 之类占位项；每个任务都给了具体文件、测试、命令和实现代码片段。
- **Type consistency:** `GraphToolCall.arguments/result_summary/status`、`query_mode`、`graph_cypher_qa`、`generated_cypher` 在 runtime / API / web / tests 中名称保持一致。
