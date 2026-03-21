# Graph Page Query Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `/graph` 从“固定 480px 的单药材图谱详情页”升级成“接近全屏的图谱工作区”，并支持按名称 / 属性 / 边条件查询后直接展示子图结果。

**Architecture:** 保留现有 `GET /graph/herb/{name}` 单药材入口，新增一个结构化的图谱条件查询接口，用单独的 query response 包装查询摘要与图数据，避免把“多结果查询模式”硬塞进现有单中心点 `GraphData`。前端将 `GraphPage` 重组为三栏工作区：左侧查询条件、中央全高图谱画布、右侧详情面板；当 URL 带 `:name` 时自动预填并拉取单药材图谱，当用户提交高级查询时切换为“查询结果图谱”模式。

**Tech Stack:** FastAPI, Neo4j Cypher, React 18, React Router 6, TanStack Query, Ant Design 5, `@ant-design/graphs`, Vitest, pytest

---

## File Map

- Modify: `packages/api/app/api/graph.py`
  - 新增图谱条件查询 route，保留现有单药材图谱 route 不变。
- Modify: `packages/api/app/schemas/graph.py`
  - 新增查询请求 / 响应 schema，定义 node filters、edge filters、summary 与 result graph 包装结构。
- Modify: `packages/api/app/kg/graph_service.py`
  - 新增 `query_graph(...)`，把名称 / 标签 / 属性 / 边条件翻译为 Cypher，并复用现有节点 / 边去重逻辑。
- Modify: `packages/api/tests/api/test_graph_routes.py`
  - 增加 query route 合约测试。
- Modify: `packages/api/tests/kg/test_graph_service.py`
  - 增加 query service 单元测试，锁定过滤行为和返回形状。
- Modify: `packages/web/src/App.tsx`
  - 图谱路由改为 `/graph/:name?`，允许无路径参数时进入高级查询模式。
- Modify: `packages/web/src/types/graph.ts`
  - 新增前端 query form、query response、summary 类型。
- Modify: `packages/web/src/services/api.ts`
  - 新增 `graphApi.queryGraph(...)`。
- Create: `packages/web/src/components/graph/GraphQueryPanel.tsx`
  - 查询表单，负责名称 / 标签 / 状态 / 属性键值 / 边类型 / 边状态 / 深度 / limit 输入。
- Create: `packages/web/src/components/graph/GraphQuerySummary.tsx`
  - 显示当前查询模式、命中节点数 / 边数 / 活跃筛选条件。
- Create: `packages/web/src/hooks/useGraphWorkspace.ts`
  - 统一管理“按名称加载图谱”和“提交条件查询”两种数据流，避免继续膨胀 `useGraph.ts`。
- Modify: `packages/web/src/pages/GraphPage.tsx`
  - 改成全屏工作区布局，接入 query panel / summary / graph data source。
- Modify: `packages/web/src/pages/GraphPage.test.tsx`
  - 增加 GraphPage 工作区与 query-mode 回归测试。
- Modify: `docs/acceptance/graph-query-mainline.md`
  - 补充高级查询主链路验收步骤与预期。

## Non-Goals

- 不做复杂路径可视化编辑器。
- 不做任意 Cypher 输入框。
- 不做结果分页和大图性能优化；P0 只做合理的 `limit` 限流与空态提示。
- 不改 `NodeDetail.tsx` / `EdgeDetail.tsx` 的视觉细节，只保证它们在新布局里继续工作。

## Query Contract Proposal

为避免把高级查询模式塞进现有 `GraphData.center` 语义，新增独立 contract：

```python
class GraphQueryNodeFilters(BaseModel):
    name_contains: str | None = None
    label: str | None = None
    status: str | None = None
    source_contains: str | None = None
    property_key: str | None = None
    property_value_contains: str | None = None

class GraphQueryEdgeFilters(BaseModel):
    rel_type: str | None = None
    status: str | None = None
    connected_name_contains: str | None = None

class GraphQueryRequest(BaseModel):
    node: GraphQueryNodeFilters = GraphQueryNodeFilters()
    edge: GraphQueryEdgeFilters = GraphQueryEdgeFilters()
    depth: int = 1
    limit: int = 30

class GraphQuerySummary(BaseModel):
    mode: Literal["advanced-query"]
    matched_nodes: int
    matched_edges: int
    truncated: bool
    active_filters: list[str]

class GraphQueryResponse(BaseModel):
    summary: GraphQuerySummary
    graph: dict
```

前端高级查询模式直接消费 `summary + graph`。单药材详情模式继续走现有 `GraphData`。

## Layout Proposal

- 页面外层高度由 viewport 驱动，而不是沿用 graph library 默认的 `480px`。
- 顶部只保留一行标题 / 深度 / 刷新 / 结果模式标识。
- 主体用三栏：
  - 左：`320px` 查询条件面板，可滚动。
  - 中：`minmax(0, 1fr)` 图谱画布，整列撑满剩余高度。
  - 右：`320px` 详情面板，可滚动。
- 中央图谱区在查询模式下顶部展示 `GraphQuerySummary`，其下方画布 `height: 100%` 占满剩余空间。
- 若图库仍回落到默认 480px，则通过容器明确传入高度，不能再依赖默认尺寸。

---

### Task 1: Add Graph Query Contract and Route Skeleton

**Files:**
- Modify: `packages/api/app/schemas/graph.py`
- Modify: `packages/api/app/api/graph.py`
- Modify: `packages/api/tests/api/test_graph_routes.py`

- [ ] **Step 1: Write the failing route contract test**

```python
@pytest.mark.asyncio
async def test_query_graph_returns_summary_and_graph(self, client):
    payload = {
        "node": {"name_contains": "人参", "label": "Herb"},
        "edge": {"rel_type": "HAS_EFFICACY"},
        "depth": 2,
        "limit": 20,
    }
    mocked = {
        "summary": {
            "mode": "advanced-query",
            "matched_nodes": 3,
            "matched_edges": 2,
            "truncated": False,
            "active_filters": ["名称包含: 人参", "关系类型: HAS_EFFICACY"],
        },
        "graph": {"center": None, "nodes": [], "edges": []},
    }

    with patch("app.api.graph.graph_service") as mock_svc:
        mock_svc.query_graph = AsyncMock(return_value=mocked)
        resp = await client.post("/api/v1/graph/query", json=payload)

    assert_status(resp, 200)
    assert_json_keys(resp.json(), {"summary", "graph"})
```

- [ ] **Step 2: Run the route test to verify it fails**

Run:

```bash
cd packages/api
uv run pytest tests/api/test_graph_routes.py::TestGraphQuery::test_query_graph_returns_summary_and_graph -v
```

Expected: FAIL with `404` or missing route / method.

- [ ] **Step 3: Add the request/response schema and route skeleton**

```python
@router.post("/query")
async def query_graph(payload: GraphQueryRequest):
    return await graph_service.query_graph(payload)
```

```python
class GraphQueryRequest(BaseModel):
    ...

class GraphQueryResponse(BaseModel):
    ...
```

- [ ] **Step 4: Run the route test to verify it passes**

Run:

```bash
cd packages/api
uv run pytest tests/api/test_graph_routes.py::TestGraphQuery::test_query_graph_returns_summary_and_graph -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/schemas/graph.py packages/api/app/api/graph.py packages/api/tests/api/test_graph_routes.py
git commit -m "feat(api): add graph query route contract"
```

### Task 2: Implement Neo4j Graph Query Filtering

**Files:**
- Modify: `packages/api/app/kg/graph_service.py`
- Modify: `packages/api/tests/kg/test_graph_service.py`

- [ ] **Step 1: Write the failing GraphService tests**

```python
@pytest.mark.unit
async def test_query_graph_filters_by_name_label_and_rel_type(graph_service):
    payload = {
        "node": {"name_contains": "人参", "label": "Herb"},
        "edge": {"rel_type": "HAS_EFFICACY"},
        "depth": 2,
        "limit": 20,
    }

    result = await graph_service.query_graph(payload)

    assert result["summary"]["mode"] == "advanced-query"
    assert "active_filters" in result["summary"]
    assert "graph" in result
```

```python
@pytest.mark.unit
async def test_query_graph_returns_empty_graph_when_no_match(graph_service):
    result = await graph_service.query_graph(
        {"node": {"name_contains": "不存在"}, "edge": {}, "depth": 1, "limit": 10}
    )

    assert result["summary"]["matched_nodes"] == 0
    assert result["graph"]["nodes"] == []
```

- [ ] **Step 2: Run the GraphService tests to verify they fail**

Run:

```bash
cd packages/api
uv run pytest tests/kg/test_graph_service.py -k query_graph -v
```

Expected: FAIL with `AttributeError: 'GraphService' object has no attribute 'query_graph'`.

- [ ] **Step 3: Implement `query_graph(...)` with bounded Cypher**

```python
async def query_graph(self, payload: dict) -> Dict[str, Any]:
    where_clauses = []
    params = {"limit": payload["limit"], "depth": payload["depth"]}

    if name := payload["node"].get("name_contains"):
        where_clauses.append("n.name CONTAINS $name_contains")
        params["name_contains"] = name

    if label := payload["node"].get("label"):
        label_clause = f":{label}"
    else:
        label_clause = ""

    # 只拼白名单允许的 label / rel_type / property_key，其他值走参数绑定
    ...
```

Implementation requirements:

- 仅允许白名单 label / rel_type / property_key，避免字符串注入。
- 查询命中的 node 之后，按 `depth` 扩展子图，并复用现有 `_dedupe_nodes` / `_dedupe_edges`。
- `summary.active_filters` 必须返回前端可直接展示的中文文案。
- 结果为空时返回空图而不是抛错。

- [ ] **Step 4: Run the focused GraphService tests to verify they pass**

Run:

```bash
cd packages/api
uv run pytest tests/kg/test_graph_service.py -k query_graph -v
```

Expected: PASS.

- [ ] **Step 5: Run route + service tests together**

Run:

```bash
cd packages/api
uv run pytest tests/api/test_graph_routes.py tests/kg/test_graph_service.py -k "query_graph or TestGraphQuery" -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/api/app/kg/graph_service.py packages/api/tests/kg/test_graph_service.py packages/api/tests/api/test_graph_routes.py
git commit -m "feat(api): implement graph query filtering"
```

### Task 3: Rework Graph Route and Data Layer for Workspace Mode

**Files:**
- Modify: `packages/web/src/App.tsx`
- Modify: `packages/web/src/types/graph.ts`
- Modify: `packages/web/src/services/api.ts`
- Create: `packages/web/src/hooks/useGraphWorkspace.ts`

- [ ] **Step 1: Write the failing frontend data-layer test**

Extend `packages/web/src/pages/GraphPage.test.tsx` with a case that verifies:

```tsx
it("submits advanced query filters and renders summary mode", async () => {
  vi.spyOn(graphApi, "queryGraph").mockResolvedValue({
    summary: {
      mode: "advanced-query",
      matched_nodes: 4,
      matched_edges: 3,
      truncated: false,
      active_filters: ["名称包含: 人参"],
    },
    graph: { center: null, nodes: [], edges: [] },
  });

  // render /graph, submit the query panel, then assert summary text is visible
});
```

- [ ] **Step 2: Run the focused frontend test to verify it fails**

Run:

```bash
cd packages/web
pnpm test --run src/pages/GraphPage.test.tsx
```

Expected: FAIL because `queryGraph` / summary mode / optional route do not exist.

- [ ] **Step 3: Add route + data types + hook skeleton**

```tsx
<Route path="/graph/:name?" element={<GraphPage />} />
```

```ts
export interface GraphQueryRequest {
  node: {...};
  edge: {...};
  depth: number;
  limit: number;
}

export interface GraphQueryResponse {
  summary: {...};
  graph: GraphData;
}
```

```ts
export function useGraphWorkspace(name?: string) {
  // load by route param or submit advanced query
}
```

- [ ] **Step 4: Run the focused frontend test to verify the data-layer pieces compile but still fail on UI**

Run:

```bash
cd packages/web
pnpm test --run src/pages/GraphPage.test.tsx
```

Expected: FAIL later in rendering / interactions, not on missing imports.

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/App.tsx packages/web/src/types/graph.ts packages/web/src/services/api.ts packages/web/src/hooks/useGraphWorkspace.ts packages/web/src/pages/GraphPage.test.tsx
git commit -m "feat(web): add graph workspace query data flow"
```

### Task 4: Build the Full-Height Graph Workspace UI

**Files:**
- Create: `packages/web/src/components/graph/GraphQueryPanel.tsx`
- Create: `packages/web/src/components/graph/GraphQuerySummary.tsx`
- Modify: `packages/web/src/pages/GraphPage.tsx`
- Modify: `packages/web/src/pages/GraphPage.test.tsx`

- [ ] **Step 1: Write the failing layout and interaction assertions**

Add or extend tests so they verify:

```tsx
expect(screen.getByText("图谱条件查询")).toBeInTheDocument();
expect(screen.getByText("查询结果")).toBeInTheDocument();
expect(screen.getByTestId("graph-workspace")).toHaveStyle({ height: "calc(100vh - 56px)" });
```

And after submitting filters:

```tsx
expect(await screen.findByText("命中 4 个节点")).toBeInTheDocument();
```

- [ ] **Step 2: Run the GraphPage test to verify it fails**

Run:

```bash
cd packages/web
pnpm test --run src/pages/GraphPage.test.tsx
```

Expected: FAIL because the new panel / summary / workspace layout are not rendered yet.

- [ ] **Step 3: Implement the workspace UI with explicit full-height graph pane**

```tsx
<div
  data-testid="graph-workspace"
  style={{
    height: "calc(100vh - 56px)",
    display: "grid",
    gridTemplateColumns: "320px minmax(0, 1fr) 320px",
  }}
>
  <GraphQueryPanel ... />
  <main style={{ minWidth: 0, minHeight: 0 }}>
    <GraphQuerySummary ... />
    <div style={{ height: "100%", minHeight: 0 }}>
      <NetworkGraph {...graphOptions} />
    </div>
  </main>
  <aside>...</aside>
</div>
```

Implementation requirements:

- 保留现有视觉升级：`nodeStyleMap`、tooltip、背景、grid-line、动画。
- 查询表单字段至少包含：
  - 节点名称包含
  - 节点类型 label
  - 节点状态
  - 来源包含
  - 属性键
  - 属性值包含
  - 关系类型
  - 关系状态
  - 深度
  - limit
- 提交后结果摘要必须展示命中节点数 / 边数 / 当前 active filters。
- URL 带 `name` 时，左侧表单自动填充“节点名称包含 = name”，并提供“恢复药材默认图谱”按钮。

- [ ] **Step 4: Run the GraphPage test to verify it passes**

Run:

```bash
cd packages/web
pnpm test --run src/pages/GraphPage.test.tsx
```

Expected: PASS.

- [ ] **Step 5: Run frontend typecheck**

Run:

```bash
cd packages/web
pnpm typecheck
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/web/src/components/graph/GraphQueryPanel.tsx packages/web/src/components/graph/GraphQuerySummary.tsx packages/web/src/pages/GraphPage.tsx packages/web/src/pages/GraphPage.test.tsx
git commit -m "feat(web): turn graph page into full-height query workspace"
```

### Task 5: Acceptance and End-to-End Verification

**Files:**
- Modify: `docs/acceptance/graph-query-mainline.md`

- [ ] **Step 1: Add acceptance steps for advanced query mode**

Update the acceptance doc so it covers:

- `/graph` 直接进入查询工作区
- 输入名称 / 属性 / 边过滤条件后返回图谱结果
- `/graph/人参` 仍能进入预填模式
- 查询摘要显示命中数量与 active filters

- [ ] **Step 2: Verify API route locally**

Run:

```bash
curl -sS 'http://localhost:8000/api/v1/graph/herb/%E4%BA%BA%E5%8F%82?depth=1' | python3 -m json.tool
curl -sS -X POST 'http://localhost:8000/api/v1/graph/query' \
  -H 'Content-Type: application/json' \
  -d '{"node":{"name_contains":"人参","label":"Herb"},"edge":{"rel_type":"HAS_EFFICACY"},"depth":2,"limit":20}' \
  | python3 -m json.tool
```

Expected:

- 第一个接口仍返回 `center / nodes / edges`
- 第二个接口返回 `summary / graph`

- [ ] **Step 3: Verify the graph workspace in browser**

Run:

```bash
cd packages/web
pnpm vp dev
```

Then verify:

1. 打开 `http://localhost:3000/graph`
2. 左侧可见“图谱条件查询”
3. 中间图谱区高度接近整屏，不再固定为 480px
4. 输入“名称包含 = 人参”并提交，可看到查询结果图谱
5. 再加“关系类型 = HAS_EFFICACY”后，摘要变化且图谱收敛
6. 打开 `http://localhost:3000/graph/人参` 仍能看到默认药材图谱

- [ ] **Step 4: Run the repo-minimum verification commands**

Run:

```bash
pnpm run test:web
cd packages/web && pnpm typecheck
cd ../../packages/api && uv run pytest tests/api/test_graph_routes.py tests/kg/test_graph_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/acceptance/graph-query-mainline.md
git commit -m "docs: update graph workspace acceptance"
```

## Final Verification Checklist

- [ ] `/graph` 可作为高级查询入口访问
- [ ] `/graph/:name` 仍兼容既有入口
- [ ] 图谱画布高度由工作区驱动，不再固定 480px
- [ ] 名称 / 属性 / 边条件查询可返回图谱结果
- [ ] 查询摘要显示命中数和 active filters
- [ ] 节点视觉升级、tooltip、背景、网格、动画未回退
- [ ] API route、GraphService、Web tests 和 typecheck 全部通过

## Notes for the Implementer

- 这是跨模块变更，顺序必须是：API contract -> GraphService -> Web data flow -> GraphPage UI -> acceptance。
- 不要为了赶进度把高级查询塞回 `GET /graph/search`；该接口继续承担轻量节点搜索，不承担子图返回。
- 不要把任意用户输入直接拼进 label / rel_type / property key；这些必须白名单化。
- 如果 demo 数据里没有足够多的 `pending` 边，不要伪造视觉验收结论；如实记录“查询分支代码存在，但当前 demo 数据无法覆盖”。
- 没有独立 spec 文档时，以本计划文件和本轮用户需求为准执行。
