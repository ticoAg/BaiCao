# Graph Runtime / Agent Wave 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地一个独立的 `packages/graph_runtime/` 包，提供 agent-first 的图谱 primitives、schema-aware planning、默认 graph exploration agent、渐进式发现 CLI 薄壳，以及 `packages/api/` 侧的最小接线能力。

**Architecture:** 核心逻辑放进 `packages/graph_runtime/`：`contracts -> service -> primitives -> planner -> agent -> cli`。`packages/api/` 仅负责用现有 `graph_service` / `graph_metadata_service` 适配 runtime 所需 backend，并提供最小 HTTP 接口或现有 chat service 集成点。CLI 只做 terminal tool 薄壳，遵循渐进式发现、help 分层和友好错误提示。默认 graph agent 采用“双轨输出 + 渐进式、自适应探索 + 必要时只读 Cypher fallback”。

**Tech Stack:** Python 3.12, Pydantic v2, asyncio, pytest, FastAPI, Neo4j, LangChain-compatible LLM adapter

---

### Task 1: 建立 `packages/graph_runtime/` 包与统一 contracts

**Files:**
- Create: `packages/graph_runtime/pyproject.toml`
- Create: `packages/graph_runtime/graph_runtime/__init__.py`
- Create: `packages/graph_runtime/graph_runtime/contracts/inputs.py`
- Create: `packages/graph_runtime/graph_runtime/contracts/outputs.py`
- Create: `packages/graph_runtime/graph_runtime/contracts/tool_calls.py`
- Create: `packages/graph_runtime/graph_runtime/contracts/__init__.py`
- Create: `packages/graph_runtime/tests/test_contracts.py`
- Modify: `packages/api/pyproject.toml`

- [ ] **Step 1: 先写失败测试，固定 graph runtime 的输入输出契约**

```python
# packages/graph_runtime/tests/test_contracts.py
from graph_runtime.contracts.inputs import GraphAskRequest, GraphExploreRequest
from graph_runtime.contracts.outputs import GraphAgentAnswer, GraphSubgraphMeta


def test_graph_ask_request_accepts_question_and_budget():
    request = GraphAskRequest(
        question="黄芩的功效和归经是什么？",
        max_depth=2,
        node_budget=30,
        allow_read_cypher=True,
    )

    assert request.question == "黄芩的功效和归经是什么？"
    assert request.max_depth == 2
    assert request.allow_read_cypher is True


def test_graph_agent_answer_exposes_dual_track_output():
    answer = GraphAgentAnswer(
        answer="黄芩味苦，性寒，归肺、胆、脾、胃、大肠、小肠经。",
        evidence=[{"node_id": "证据:1", "snippet": "【性味与归经】苦，寒。归肺、胆、脾、胃、大肠、小肠经。"}],
        related_nodes=[{"id": "药材:黄芩", "name": "黄芩"}],
        related_edges=[{"source": "药材:黄芩", "target": "归经:肺经", "type": "归于经脉"}],
        subgraph_meta=GraphSubgraphMeta(center_node_id="药材:黄芩", actual_depth=1, fallback_used=False),
        reasoning_trace=[{"kind": "planner", "summary": "命中 schema 语义：功效、归经"}],
        tool_calls=[{"tool_name": "search_nodes", "summary": "召回黄芩"}],
    )

    assert answer.subgraph_meta.center_node_id == "药材:黄芩"
    assert answer.related_nodes[0]["name"] == "黄芩"
```

- [ ] **Step 2: 运行测试确认当前包和 contracts 尚不存在**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_contracts.py -q
```

Expected:

- `packages/graph_runtime/` 不存在
- `graph_runtime.contracts` 无法导入

- [ ] **Step 3: 创建包和 contracts 模型**

```python
# packages/graph_runtime/graph_runtime/contracts/inputs.py
from pydantic import BaseModel, ConfigDict, Field


class GraphAskRequest(BaseModel):
    question: str = Field(description="用户自然语言问题")
    max_depth: int = Field(default=2, ge=1, le=5, description="默认探索深度预算")
    node_budget: int = Field(default=30, ge=1, le=500, description="节点预算")
    edge_budget: int = Field(default=60, ge=1, le=1000, description="边预算")
    tool_call_budget: int = Field(default=8, ge=1, le=30, description="工具调用预算")
    allow_read_cypher: bool = Field(default=True, description="是否允许只读 Cypher fallback")

    model_config = ConfigDict(use_enum_values=False)


class GraphExploreRequest(BaseModel):
    query: str = Field(description="探索起点查询")
    mode: str = Field(default="adaptive", description="探索模式：adaptive / bfs / dfs")
    max_depth: int = Field(default=2, ge=1, le=5)
    node_budget: int = Field(default=30, ge=1, le=500)

    model_config = ConfigDict(use_enum_values=False)
```

```python
# packages/graph_runtime/graph_runtime/contracts/outputs.py
from pydantic import BaseModel, ConfigDict, Field


class GraphSubgraphMeta(BaseModel):
    center_node_id: str | None = Field(default=None, description="中心节点 ID")
    actual_depth: int = Field(default=0, description="实际探索深度")
    fallback_used: bool = Field(default=False, description="是否使用只读 Cypher fallback")
    node_count: int = Field(default=0, description="返回节点数量")
    edge_count: int = Field(default=0, description="返回边数量")

    model_config = ConfigDict(use_enum_values=False)


class GraphAgentAnswer(BaseModel):
    answer: str = Field(description="自然语言回答")
    evidence: list[dict] = Field(default_factory=list, description="证据摘要列表")
    related_nodes: list[dict] = Field(default_factory=list, description="相关节点")
    related_edges: list[dict] = Field(default_factory=list, description="相关边")
    subgraph_meta: GraphSubgraphMeta = Field(description="子图元信息")
    reasoning_trace: list[dict] = Field(default_factory=list, description="推理轨迹摘要")
    tool_calls: list[dict] = Field(default_factory=list, description="工具调用记录")

    model_config = ConfigDict(use_enum_values=False)
```

- [ ] **Step 4: 在 `packages/api/pyproject.toml` 里接入本地 source**

```toml
# packages/api/pyproject.toml
dependencies = [
  "bai-cao-graph-runtime",
  "bai-cao-data-ingestion",
  "bai-cao-knowledge-model",
]

[tool.uv.sources]
bai-cao-graph-runtime = { path = "../graph_runtime", editable = true }
bai-cao-data-ingestion = { path = "../data_ingestion", editable = true }
bai-cao-knowledge-model = { path = "../knowledge_model", editable = true }
```

- [ ] **Step 5: 回跑 contracts 测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_contracts.py -q
```

Expected:

- `GraphAskRequest`、`GraphExploreRequest`、`GraphAgentAnswer` 可正常构造
- 双轨输出字段被稳定锁定

- [ ] **Step 6: Commit**

```bash
git add packages/graph_runtime packages/api/pyproject.toml
git commit -m "feat(graph-runtime): add runtime contracts package"
```

### Task 2: 定义 backend 协议与 service facade

**Files:**
- Create: `packages/graph_runtime/graph_runtime/service/backend.py`
- Create: `packages/graph_runtime/graph_runtime/service/graph_facade.py`
- Create: `packages/graph_runtime/graph_runtime/service/cypher_readonly.py`
- Create: `packages/graph_runtime/graph_runtime/service/__init__.py`
- Create: `packages/graph_runtime/tests/test_graph_facade.py`

- [ ] **Step 1: 写失败测试，锁定 facade 的稳定能力面**

```python
# packages/graph_runtime/tests/test_graph_facade.py
import pytest

from graph_runtime.service.graph_facade import GraphFacade


class FakeBackend:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        return [{"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]}]

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        return {
            "center": {"id": node_id, "name": "黄芩", "labels": ["药材"]},
            "nodes": [{"id": node_id, "name": "黄芩", "labels": ["药材"]}],
            "edges": [],
        }

    async def execute_readonly_cypher(self, query: str):
        return [{"name": "黄芩"}]


@pytest.mark.asyncio
async def test_graph_facade_delegates_search_and_expand():
    facade = GraphFacade(FakeBackend())

    matches = await facade.search_nodes("黄芩")
    subgraph = await facade.expand_neighbors("药材:黄芩", depth=1)

    assert matches[0]["name"] == "黄芩"
    assert subgraph["center"]["id"] == "药材:黄芩"


@pytest.mark.asyncio
async def test_graph_facade_exposes_readonly_cypher():
    facade = GraphFacade(FakeBackend())

    rows = await facade.read_cypher("MATCH (n) RETURN n.name AS name LIMIT 1")

    assert rows == [{"name": "黄芩"}]
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_graph_facade.py -q
```

Expected:

- `graph_runtime.service` 模块不存在
- `GraphFacade` 未定义

- [ ] **Step 3: 定义 backend 协议和 facade**

```python
# packages/graph_runtime/graph_runtime/service/backend.py
from typing import Protocol, Any


class GraphRuntimeBackend(Protocol):
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20) -> list[dict]: ...
    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20) -> dict[str, Any]: ...
    async def get_node(self, node_id: str) -> dict[str, Any] | None: ...
    async def find_path(self, from_name: str, to_name: str, max_depth: int = 4) -> list[dict]: ...
    async def execute_readonly_cypher(self, query: str) -> list[dict[str, Any]]: ...
    async def get_schema_summary(self) -> dict[str, Any]: ...
```

```python
# packages/graph_runtime/graph_runtime/service/graph_facade.py
from .backend import GraphRuntimeBackend
from .cypher_readonly import ensure_readonly_cypher


class GraphFacade:
    def __init__(self, backend: GraphRuntimeBackend) -> None:
        self.backend = backend

    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20) -> list[dict]:
        return await self.backend.search_nodes(query=query, label=label, limit=limit)

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20) -> dict:
        return await self.backend.expand_neighbors(node_id=node_id, depth=depth, limit=limit)

    async def read_cypher(self, query: str) -> list[dict]:
        normalized = ensure_readonly_cypher(query)
        return await self.backend.execute_readonly_cypher(normalized)
```

- [ ] **Step 4: 为只读 Cypher 加校验器**

```python
# packages/graph_runtime/graph_runtime/service/cypher_readonly.py
FORBIDDEN = {"CREATE", "MERGE", "DELETE", "SET", "REMOVE", "DROP", "LOAD CSV", "FOREACH", "APOC"}


def ensure_readonly_cypher(query: str) -> str:
    normalized = " ".join(query.strip().split())
    upper = normalized.upper()
    if ";" in normalized:
        raise ValueError("只允许单条只读 Cypher 语句")
    for keyword in FORBIDDEN:
        if keyword in upper:
            raise ValueError("只允许执行只读 Cypher")
    return normalized
```

- [ ] **Step 5: 回跑 facade 测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_graph_facade.py -q
```

Expected:

- `search_nodes` / `expand_neighbors` / `read_cypher` 主路径通过
- 只读 Cypher 校验器能阻断写操作

- [ ] **Step 6: Commit**

```bash
git add packages/graph_runtime/graph_runtime/service packages/graph_runtime/tests/test_graph_facade.py
git commit -m "feat(graph-runtime): add backend protocol and graph facade"
```

### Task 3: 实现底层 primitives 与 BFS / DFS

**Files:**
- Create: `packages/graph_runtime/graph_runtime/primitives/search.py`
- Create: `packages/graph_runtime/graph_runtime/primitives/expand.py`
- Create: `packages/graph_runtime/graph_runtime/primitives/bfs.py`
- Create: `packages/graph_runtime/graph_runtime/primitives/dfs.py`
- Create: `packages/graph_runtime/graph_runtime/primitives/evidence.py`
- Create: `packages/graph_runtime/graph_runtime/primitives/__init__.py`
- Create: `packages/graph_runtime/tests/test_graph_primitives.py`

- [ ] **Step 1: 写失败测试，锁定遍历预算与返回形态**

```python
# packages/graph_runtime/tests/test_graph_primitives.py
import pytest

from graph_runtime.primitives.bfs import bfs_walk
from graph_runtime.primitives.dfs import dfs_walk


class WalkBackend:
    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        graph = {
            "药材:黄芩": {
                "center": {"id": "药材:黄芩", "name": "黄芩"},
                "nodes": [{"id": "功效:清热燥湿", "name": "清热燥湿"}, {"id": "归经:肺经", "name": "肺经"}],
                "edges": [
                    {"source": {"id": "药材:黄芩"}, "target": {"id": "功效:清热燥湿"}, "type": "具有功效"},
                    {"source": {"id": "药材:黄芩"}, "target": {"id": "归经:肺经"}, "type": "归于经脉"},
                ],
            }
        }
        return graph[node_id]


@pytest.mark.asyncio
async def test_bfs_walk_respects_node_budget():
    result = await bfs_walk(WalkBackend(), seed_node_id="药材:黄芩", max_depth=2, node_budget=2)
    assert len(result["nodes"]) <= 2


@pytest.mark.asyncio
async def test_dfs_walk_returns_trace():
    result = await dfs_walk(WalkBackend(), seed_node_id="药材:黄芩", max_depth=2, node_budget=4)
    assert result["trace"][0]["strategy"] == "dfs"
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_graph_primitives.py -q
```

Expected:

- `graph_runtime.primitives` 不存在

- [ ] **Step 3: 实现 search / expand / bfs / dfs / evidence primitives**

```python
# packages/graph_runtime/graph_runtime/primitives/bfs.py
async def bfs_walk(backend, seed_node_id: str, max_depth: int, node_budget: int) -> dict:
    visited = set()
    queue = [(seed_node_id, 0)]
    nodes: list[dict] = []
    edges: list[dict] = []
    trace: list[dict] = []

    while queue and len(nodes) < node_budget:
        current_id, depth = queue.pop(0)
        if current_id in visited or depth > max_depth:
            continue
        visited.add(current_id)
        expanded = await backend.expand_neighbors(current_id, depth=1, limit=node_budget)
        for node in expanded.get("nodes", []):
            if len(nodes) >= node_budget:
                break
            nodes.append(node)
            next_id = node.get("id")
            if next_id and next_id not in visited:
                queue.append((next_id, depth + 1))
        edges.extend(expanded.get("edges", []))
        trace.append({"strategy": "bfs", "node_id": current_id, "depth": depth})

    return {"nodes": nodes, "edges": edges, "trace": trace}
```

```python
# packages/graph_runtime/graph_runtime/primitives/dfs.py
async def dfs_walk(backend, seed_node_id: str, max_depth: int, node_budget: int) -> dict:
    visited = set()
    stack = [(seed_node_id, 0)]
    nodes: list[dict] = []
    edges: list[dict] = []
    trace: list[dict] = []

    while stack and len(nodes) < node_budget:
        current_id, depth = stack.pop()
        if current_id in visited or depth > max_depth:
            continue
        visited.add(current_id)
        expanded = await backend.expand_neighbors(current_id, depth=1, limit=node_budget)
        for node in expanded.get("nodes", []):
            if len(nodes) >= node_budget:
                break
            nodes.append(node)
            next_id = node.get("id")
            if next_id and next_id not in visited:
                stack.append((next_id, depth + 1))
        edges.extend(expanded.get("edges", []))
        trace.append({"strategy": "dfs", "node_id": current_id, "depth": depth})

    return {"nodes": nodes, "edges": edges, "trace": trace}
```

- [ ] **Step 4: 回跑 primitives 测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_graph_primitives.py -q
```

Expected:

- BFS / DFS 都能输出子图与 trace
- `node_budget` 能限制返回规模

- [ ] **Step 5: Commit**

```bash
git add packages/graph_runtime/graph_runtime/primitives packages/graph_runtime/tests/test_graph_primitives.py
git commit -m "feat(graph-runtime): add graph traversal primitives"
```

### Task 4: 实现 schema-aware planner 与探索策略

**Files:**
- Create: `packages/graph_runtime/graph_runtime/planner/schema_semantic_mapping.py`
- Create: `packages/graph_runtime/graph_runtime/planner/entity_fuzzy_recall.py`
- Create: `packages/graph_runtime/graph_runtime/planner/plan_builder.py`
- Create: `packages/graph_runtime/graph_runtime/planner/__init__.py`
- Create: `packages/graph_runtime/tests/test_graph_planner.py`

- [ ] **Step 1: 写失败测试，固定 schema 语义映射**

```python
# packages/graph_runtime/tests/test_graph_planner.py
from graph_runtime.planner.plan_builder import build_graph_plan


def test_plan_builder_maps_meridian_question_to_schema_targets():
    plan = build_graph_plan("黄芩归什么经？")

    assert "归经" in plan["target_node_types"]
    assert "归于经脉" in plan["target_edge_types"]


def test_plan_builder_maps_evidence_question_to_supported_by():
    plan = build_graph_plan("给我黄芩的原文证据")

    assert "证据" in plan["target_node_types"]
    assert "由证据支持" in plan["target_edge_types"]
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_graph_planner.py -q
```

Expected:

- `build_graph_plan` 不存在

- [ ] **Step 3: 用表驱动规则实现 Phase 1 schema 语义模糊增强**

```python
# packages/graph_runtime/graph_runtime/planner/schema_semantic_mapping.py
SCHEMA_SEMANTIC_RULES = [
    {
        "keywords": ["功效", "主治", "作用"],
        "target_node_types": ["功效", "病证"],
        "target_edge_types": ["具有功效", "治疗病证"],
    },
    {
        "keywords": ["归经", "归什么经", "走什么经"],
        "target_node_types": ["归经"],
        "target_edge_types": ["归于经脉"],
    },
    {
        "keywords": ["饮片", "炮制", "切片后"],
        "target_node_types": ["饮片"],
        "target_edge_types": ["具有饮片"],
    },
    {
        "keywords": ["证据", "原文", "出处"],
        "target_node_types": ["证据"],
        "target_edge_types": ["由证据支持"],
    },
]
```

```python
# packages/graph_runtime/graph_runtime/planner/plan_builder.py
from .schema_semantic_mapping import SCHEMA_SEMANTIC_RULES


def build_graph_plan(question: str) -> dict:
    plan = {
        "question": question,
        "target_node_types": [],
        "target_edge_types": [],
        "search_mode": "adaptive",
    }
    for rule in SCHEMA_SEMANTIC_RULES:
        if any(keyword in question for keyword in rule["keywords"]):
            plan["target_node_types"].extend(rule["target_node_types"])
            plan["target_edge_types"].extend(rule["target_edge_types"])
    plan["target_node_types"] = list(dict.fromkeys(plan["target_node_types"]))
    plan["target_edge_types"] = list(dict.fromkeys(plan["target_edge_types"]))
    return plan
```

- [ ] **Step 4: 回跑 planner 测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_graph_planner.py -q
```

Expected:

- “归经 / 证据” 类型问题能正确命中 schema 语义映射

- [ ] **Step 5: Commit**

```bash
git add packages/graph_runtime/graph_runtime/planner packages/graph_runtime/tests/test_graph_planner.py
git commit -m "feat(graph-runtime): add schema-aware graph planner"
```

### Task 5: 实现默认 graph exploration agent

**Files:**
- Create: `packages/graph_runtime/graph_runtime/agent/exploration_policy.py`
- Create: `packages/graph_runtime/graph_runtime/agent/answer_synthesis.py`
- Create: `packages/graph_runtime/graph_runtime/agent/graph_agent.py`
- Create: `packages/graph_runtime/graph_runtime/agent/__init__.py`
- Create: `packages/graph_runtime/tests/test_graph_agent.py`

- [ ] **Step 1: 写失败测试，锁定双轨输出与自适应探索**

```python
# packages/graph_runtime/tests/test_graph_agent.py
import pytest

from graph_runtime.agent.graph_agent import GraphExplorationAgent
from graph_runtime.contracts.inputs import GraphAskRequest


class StubFacade:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        return [{"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]}]

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        return {
            "center": {"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]},
            "nodes": [{"id": "归经:肺经", "name": "肺经", "labels": ["归经"]}],
            "edges": [{"source": {"id": "药材:黄芩"}, "target": {"id": "归经:肺经"}, "type": "归于经脉"}],
        }

    async def read_cypher(self, query: str):
        return [{"name": "黄芩"}]


@pytest.mark.asyncio
async def test_graph_agent_returns_dual_track_output():
    agent = GraphExplorationAgent(graph_facade=StubFacade())

    result = await agent.ask(GraphAskRequest(question="黄芩归什么经？"))

    assert "肺经" in result.answer
    assert result.related_nodes[0]["name"] == "肺经"
    assert result.subgraph_meta.actual_depth >= 1


@pytest.mark.asyncio
async def test_graph_agent_records_tool_calls():
    agent = GraphExplorationAgent(graph_facade=StubFacade())

    result = await agent.ask(GraphAskRequest(question="黄芩归什么经？"))

    assert result.tool_calls[0]["tool_name"] == "search_nodes"
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_graph_agent.py -q
```

Expected:

- `GraphExplorationAgent` 不存在

- [ ] **Step 3: 实现默认 graph agent**

```python
# packages/graph_runtime/graph_runtime/agent/graph_agent.py
from graph_runtime.contracts.outputs import GraphAgentAnswer, GraphSubgraphMeta
from graph_runtime.planner.plan_builder import build_graph_plan


class GraphExplorationAgent:
    def __init__(self, graph_facade) -> None:
        self.graph_facade = graph_facade

    async def ask(self, request) -> GraphAgentAnswer:
        plan = build_graph_plan(request.question)
        tool_calls = []
        matches = await self.graph_facade.search_nodes(request.question, limit=5)
        tool_calls.append({"tool_name": "search_nodes", "summary": f"召回 {len(matches)} 个候选"})

        center = matches[0] if matches else None
        subgraph = (
            await self.graph_facade.expand_neighbors(center["id"], depth=1, limit=request.node_budget)
            if center
            else {"center": None, "nodes": [], "edges": []}
        )
        tool_calls.append({"tool_name": "expand_neighbors", "summary": "展开中心节点一跳邻居"})

        related_nodes = subgraph.get("nodes", [])
        related_edges = subgraph.get("edges", [])
        answer = self._synthesize_answer(request.question, center, related_nodes, related_edges, plan)
        evidence = self._collect_evidence_snippets(related_nodes)

        return GraphAgentAnswer(
            answer=answer,
            evidence=evidence,
            related_nodes=related_nodes,
            related_edges=related_edges,
            subgraph_meta=GraphSubgraphMeta(
                center_node_id=center["id"] if center else None,
                actual_depth=1 if center else 0,
                fallback_used=False,
                node_count=len(related_nodes),
                edge_count=len(related_edges),
            ),
            reasoning_trace=[
                {"kind": "planner", "summary": f"schema targets: {plan['target_node_types']} / {plan['target_edge_types']}"}
            ],
            tool_calls=tool_calls,
        )
```

- [ ] **Step 4: 回跑 graph agent 测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_graph_agent.py -q
```

Expected:

- `ask()` 返回双轨输出
- `tool_calls` 与 `reasoning_trace` 主路径稳定

- [ ] **Step 5: Commit**

```bash
git add packages/graph_runtime/graph_runtime/agent packages/graph_runtime/tests/test_graph_agent.py
git commit -m "feat(graph-runtime): add default graph exploration agent"
```

### Task 6: 交付渐进式发现 CLI 薄壳

**Files:**
- Create: `packages/graph_runtime/graph_runtime/cli/main.py`
- Create: `packages/graph_runtime/graph_runtime/cli/help.py`
- Create: `packages/graph_runtime/graph_runtime/cli/formatters.py`
- Create: `packages/graph_runtime/tests/test_graph_cli.py`

- [ ] **Step 1: 写失败测试，锁定 help 与友好错误提示**

```python
# packages/graph_runtime/tests/test_graph_cli.py
from graph_runtime.cli.main import run_cli


def test_root_help_lists_progressive_commands(capsys):
    exit_code = run_cli(["help"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "ask" in captured.out
    assert "search" in captured.out
    assert "explore" in captured.out


def test_ask_without_question_suggests_next_step(capsys):
    exit_code = run_cli(["ask"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "graph ask --help" in captured.out
    assert "graph ask \"黄芩的功效是什么？\"" in captured.out
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_graph_cli.py -q
```

Expected:

- `run_cli()` 不存在

- [ ] **Step 3: 实现 CLI 主入口与 help**

```python
# packages/graph_runtime/graph_runtime/cli/main.py
from .help import ROOT_HELP, ASK_HELP


def run_cli(argv: list[str]) -> int:
    command = argv[0] if argv else "help"

    if command in {"help", "--help", "-h"}:
        print(ROOT_HELP)
        return 0

    if command == "ask":
        if len(argv) < 2:
            print("缺少问题内容。可以试试：")
            print('  graph ask "黄芩的功效是什么？"')
            print("  graph ask --help")
            return 2
        return 0

    print(f"未知命令: {command}")
    print("可以试试 `graph help` 查看可用命令。")
    return 2
```

```python
# packages/graph_runtime/graph_runtime/cli/help.py
ROOT_HELP = \"\"\"graph 命令面

常用命令:
  graph ask <question>      提问并返回双轨图谱回答
  graph search <query>      搜索节点
  graph explore <query>     探索相关子图
  graph walk <seed>         执行 BFS / DFS 游走
  graph cypher <query>      执行只读 Cypher

更多帮助:
  graph <command> --help
\"\"\"

ASK_HELP = \"\"\"graph ask

用法:
  graph ask \"黄芩归什么经？\"
\"\"\"
```

- [ ] **Step 4: 回跑 CLI 测试**

Run:

```bash
cd packages/graph_runtime && uv run --with pytest pytest tests/test_graph_cli.py -q
```

Expected:

- `graph help` 能展示渐进式命令面
- 参数缺失时有友好错误和下一步建议

- [ ] **Step 5: Commit**

```bash
git add packages/graph_runtime/graph_runtime/cli packages/graph_runtime/tests/test_graph_cli.py
git commit -m "feat(graph-runtime): add progressive-discovery graph cli"
```

### Task 7: 在 `packages/api/` 接入 runtime backend

**Files:**
- Create: `packages/api/app/graph_runtime_backend.py`
- Create: `packages/api/app/services/graph_agent_service.py`
- Create: `packages/api/app/api/graph_agent.py`
- Modify: `packages/api/app/api/__init__.py`
- Modify: `packages/api/app/main.py`
- Create: `packages/api/tests/services/test_graph_agent_service.py`
- Create: `packages/api/tests/api/test_graph_agent_routes.py`

- [ ] **Step 1: 写失败测试，锁定 API 接线点**

```python
# packages/api/tests/services/test_graph_agent_service.py
import pytest


@pytest.mark.asyncio
async def test_graph_agent_service_returns_dual_track_payload():
    from app.services.graph_agent_service import GraphAgentService

    service = GraphAgentService()
    result = await service.ask("黄芩归什么经？")

    assert "answer" in result
    assert "related_nodes" in result
    assert "subgraph_meta" in result
```

```python
# packages/api/tests/api/test_graph_agent_routes.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_graph_agent_route_returns_answer_payload(async_client: AsyncClient):
    response = await async_client.post("/api/v1/graph-agent/ask", json={"question": "黄芩归什么经？"})
    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert "related_nodes" in payload
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd packages/api && uv run --extra dev pytest tests/services/test_graph_agent_service.py tests/api/test_graph_agent_routes.py -q
```

Expected:

- `GraphAgentService` / `/graph-agent/ask` 尚不存在

- [ ] **Step 3: 创建 backend adapter 与 API service**

```python
# packages/api/app/graph_runtime_backend.py
from graph_runtime.service.graph_facade import GraphFacade

from .kg.graph_metadata_service import graph_metadata_service
from .kg.graph_service import graph_service


class ApiGraphRuntimeBackend:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        return await graph_service.search_nodes(query, label=label, limit=limit)

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        return await graph_service.expand_node_graph(node_id, depth=depth, limit=limit)

    async def get_node(self, node_id: str):
        return await graph_service.get_node(node_id)

    async def find_path(self, from_name: str, to_name: str, max_depth: int = 4):
        return await graph_service.find_path(from_name, to_name, max_depth=max_depth)

    async def execute_readonly_cypher(self, query: str):
        return await graph_service.execute_readonly_cypher(query)

    async def get_schema_summary(self):
        return await graph_metadata_service.get_summary()
```

```python
# packages/api/app/services/graph_agent_service.py
from graph_runtime.agent.graph_agent import GraphExplorationAgent
from graph_runtime.contracts.inputs import GraphAskRequest

from ..graph_runtime_backend import ApiGraphRuntimeBackend


class GraphAgentService:
    def __init__(self) -> None:
        self.agent = GraphExplorationAgent(graph_facade=ApiGraphRuntimeBackend())

    async def ask(self, question: str) -> dict:
        result = await self.agent.ask(GraphAskRequest(question=question))
        return result.model_dump(mode="json")
```

- [ ] **Step 4: 暴露最小 HTTP route**

```python
# packages/api/app/api/graph_agent.py
from fastapi import APIRouter
from pydantic import BaseModel

from ..services.graph_agent_service import GraphAgentService

router = APIRouter(prefix="/graph-agent", tags=["graph-agent"])


class GraphAgentAskPayload(BaseModel):
    question: str


@router.post("/ask")
async def ask_graph_agent(payload: GraphAgentAskPayload):
    return await GraphAgentService().ask(payload.question)
```

- [ ] **Step 5: 回跑 API 接线测试**

Run:

```bash
cd packages/api && uv run --extra dev pytest tests/services/test_graph_agent_service.py tests/api/test_graph_agent_routes.py -q
```

Expected:

- `GraphAgentService` 能返回双轨 payload
- `/api/v1/graph-agent/ask` 可正常工作

- [ ] **Step 6: Commit**

```bash
git add packages/api/app/graph_runtime_backend.py packages/api/app/services/graph_agent_service.py packages/api/app/api/graph_agent.py packages/api/app/main.py packages/api/tests/services/test_graph_agent_service.py packages/api/tests/api/test_graph_agent_routes.py
git commit -m "feat(api): wire graph runtime agent into api"
```

### Task 8: 文档与验收收口

**Files:**
- Modify: `docs/architecture/knowledge-model-and-ingestion.md`
- Modify: `docs/acceptance/data-ingestion-and-knowledge-model.md`
- Modify: `docs/README.md`
- Modify: `docs/agent-skill-routing.md`

- [ ] **Step 1: 更新文档入口，补 graph runtime / graph agent 的位置与边界**

```markdown
## 新增系统入口

- `packages/graph_runtime/`：agent-first 图谱 runtime 真源
- `packages/api/`：runtime 的 HTTP 接线层
- CLI：runtime 的 terminal 薄壳，不承载核心逻辑
```

- [ ] **Step 2: 追加验收命令**

Run:

```bash
cd packages/graph_runtime
uv run --with pytest pytest tests -q

cd ../api
uv run --extra dev pytest tests/services/test_graph_agent_service.py tests/api/test_graph_agent_routes.py -q
```

Expected:

- graph runtime 包内 tests 通过
- API 接线 tests 通过

- [ ] **Step 3: Commit**

```bash
git add docs/architecture/knowledge-model-and-ingestion.md docs/acceptance/data-ingestion-and-knowledge-model.md docs/README.md docs/agent-skill-routing.md
git commit -m "docs(graph-runtime): document runtime and agent integration"
```
