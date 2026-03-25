# Graph Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `/graph` 重构为 protocol-first 的 Graph Workbench，在页面内落地 `Database information`、`Graph result view` 和 `Inspector` 三方联动，并补齐数据库级元数据接口。

**Architecture:** 采用 contract-first 垂直切片实现。先在 `packages/shared` 和 `packages/api/app/schemas` 中定义 Graph Workbench 协议，再在 `packages/api` 中补齐数据库元数据服务与图谱结果契约，最后在 `packages/web` 中建立新的数据层、交互 store 和 `/graph` 页面组件。运行时校验只发生在边界处一次，内部以共享类型和本地 view model 为主，不重复做多层 schema parse。

**Tech Stack:** TypeScript, React 18, React Router 6, Zustand, TanStack Query, Ant Design 5, `@ant-design/graphs`, FastAPI, Pydantic v2, Neo4j Python Driver, Vitest, Testing Library, Pytest, Ruff

**Status:** 已实施并补齐主链路验收（2026-03-25），更细的交互 parity 仍待后续扩展

**Implementation Summary:** `/graph` 已落地为三栏 Graph Workbench，后端补齐了 `/api/v1/graph/meta/*` 与 `scene` 信息，前端形成了 `Database information`、中央图谱结果区和右侧检查器闭环。实现阶段对中央图谱渲染做了进一步演进，已从计划中的图库方案切到仓库内自维护的 D3 结果视图。

**Implementation Evidence:**
- 提交：`c2850c4 feat(web): polish graph workbench interactions`
- 提交：`252f740 feat(web): replace graph canvases with d3 visualization`
- 提交：`76ed3af feat(tests): 重构图形可视化的模拟`
- 提交：`1ec000e test(web): align graph workspace hook expectations`
- 验收：`docs/acceptance/graph-workbench-mainline.md`

**Verification Result:**
- `uv run pytest tests/unit/kg/test_db.py tests/api/test_graph_routes.py -q`：`15 passed`
- `pnpm --dir packages/web test --run src/pages/GraphPage.test.tsx`：`3 passed`
- `pnpm --dir packages/web typecheck`：通过
- 本地 `curl` spot-check：`/graph/meta/*` 与 `/graph/herb/人参` 返回有效 JSON
- 页面事实检查：`/graph/人参` 同时呈现 `Database information`、图谱结果区与 `Overview`

---

## Scope Check

本计划覆盖单一可实现子系统，而不是多个独立项目：

- `/graph` 页面升级为 Graph Workbench
- 支撑该页面的数据库元数据接口与画布结果契约

不包含：

- 完整 Cypher workbench
- 聊天页复用
- 旧 `GraphWorkbenchPage` 独立路线的继续扩展

旧的“独立 Browser workbench 页”方向以及更早的 query workspace / canvas redesign 中间态计划，均已被本计划覆盖并删除。本计划以 [docs/superpowers/specs/2026-03-23-graph-workbench-design.md](/Users/ticoag/Documents/myws/BaiCao/docs/superpowers/specs/2026-03-23-graph-workbench-design.md) 为唯一设计真源。

## File Map

- Create: `packages/shared/types/graph-workbench.ts`
  - 定义 Graph Workbench 的共享协议，覆盖数据库元数据、图谱场景补充字段、检查器概览统计、交互枚举等跨端真源。
- Modify: `packages/shared/types/index.ts`
  - 导出新的 graph-workbench 类型，保持 SSOT 入口统一。
- Create: `packages/api/app/schemas/graph_workbench.py`
  - 定义与共享协议对齐的 Pydantic 模型，承担 API 边界校验。
- Modify: `packages/api/app/schemas/graph.py`
  - 补齐 GraphScene 需要的附加响应字段，避免前端只能从子图结果反推状态。
- Create: `packages/api/app/kg/graph_metadata_service.py`
  - 负责只读查询 labels、relationship types、property keys、indexes、constraints、全库计数等数据库元信息。
- Modify: `packages/api/app/kg/graph_service.py`
  - 为 `/graph` 当前结果视图补齐 scene 信息，例如 truncation、node limit、info message。
- Modify: `packages/api/app/api/graph.py`
  - 增加 `/graph/meta/*` 路由，并把场景补充字段挂到现有图谱接口响应中。
- Create: `packages/api/tests/contract/test_graph_workbench_schema.py`
  - 锁定 Graph Workbench 协议形状，保证 schema 与共享类型一致。
- Modify: `packages/api/tests/api/test_graph_routes.py`
  - 锁定 `/graph/meta/*` 新路由和现有 `/graph` 场景响应。
- Modify: `packages/api/tests/kg/test_graph_service.py`
  - 锁定 graph scene 附加字段与元数据服务的只读查询行为。
- Create: `packages/web/src/types/graphWorkbench.ts`
  - 仅放前端 view model、store state 和组件专用 helper 类型；尽量引用 `@bai-cao/shared` 的协议类型，不重复定义 DTO。
- Create: `packages/web/src/services/graphWorkbenchApi.ts`
  - Graph Workbench 专用 API 封装，负责取数并在边界处做一次远端到 view model 的适配。
- Create: `packages/web/src/stores/graphWorkbenchStore.ts`
  - 统一保存 selected、hovered、highlighted label/relationship type、inspector mode、面板折叠态等交互状态。
- Create: `packages/web/src/hooks/useGraphWorkbenchPage.ts`
  - 统一编排 metadata query、graph scene query、selection/highlight 反向驱动和页面级派生数据。
- Modify: `packages/web/src/types/graph.ts`
  - 收敛本地重复 DTO，改为依赖 shared 协议和本地 view model，避免继续漂移。
- Modify: `packages/web/src/hooks/useGraphWorkspace.ts`
  - 限定为当前图谱场景取数与展开逻辑，不再承担整页工作台状态。
- Create: `packages/web/src/components/graph/GraphMetadataSidebar.tsx`
  - 落地 `Database information` 侧栏。
- Create: `packages/web/src/components/graph/GraphCanvasWorkspace.tsx`
  - 承接中央画布、缩放/平移/fit、空白点击、选中与弱化逻辑。
- Create: `packages/web/src/components/graph/GraphInspectorPanel.tsx`
  - 承接右侧 `Overview / Details` 检查器及反向高亮操作。
- Modify: `packages/web/src/components/graph/NodeDetail.tsx`
  - 适配新的检查器详情模式，支持系统字段与业务字段统一展示。
- Modify: `packages/web/src/components/graph/EdgeDetail.tsx`
  - 适配新的关系详情模式。
- Modify: `packages/web/src/pages/GraphPage.tsx`
  - 从“业务图谱页”升级为 Graph Workbench 页面壳。
- Create: `packages/web/src/components/graph/GraphMetadataSidebar.test.tsx`
  - 锁定 `Database information` 的渲染与点击行为。
- Create: `packages/web/src/components/graph/GraphInspectorPanel.test.tsx`
  - 锁定 `Overview / Details` 切换与反向高亮行为。
- Create: `packages/web/src/hooks/useGraphWorkbenchPage.test.tsx`
  - 锁定整页数据编排与交互 store 协调。
- Modify: `packages/web/src/pages/GraphPage.test.tsx`
  - 锁定 `/graph` 的三栏工作台主路径。
- Create: `docs/acceptance/graph-workbench-mainline.md`
  - 记录新的 `/graph` 主链路验收步骤与证据格式。
- Modify: `docs/acceptance/README.md`
  - 将新验收文档纳入入口。
- Delete: superseded graph workbench / graph workspace intermediate plans after acceptance and architecture graduation
  - 在文档头部补一条说明，标明 `/graph` 路径后续以新 plan 为准，避免执行者选错入口。

## Notes

- `packages/shared/types/workbench.ts` 已存在，且语义属于命令式 workbench，不应承载 `/graph` 的 Database information 协议。本计划新建 `graph-workbench.ts`，避免同名不同义继续膨胀。
- `packages/web/src/pages/GraphWorkbenchPage.tsx`、`packages/web/src/hooks/useGraphWorkbench.ts` 和 `packages/web/src/stores/workbenchStore.ts` 当前属于旧的独立 workbench 路线，本轮不继续扩展它们，除非执行中发现可以安全复用很小一部分通用能力。
- `protocol first` 在本轮的具体含义是：共享协议先行，前端本地 view model 只做展示态适配，不重新定义后端真源字段。
- “边界处只校验一次”在本轮意味着：Pydantic 校验 API 边界，web service adapter 只做一次远端响应适配，store / components 不再重复 `safeParse` 或字段兜底。

## Non-Goals

- 不把 `.tmp/neo4j-browser` 的 GPL 源码直接带入产品代码。
- 不把 `/graph` 扩展成完整 Cypher 编辑器、命令历史、结果流系统。
- 不把聊天页、独立 `GraphWorkbenchPage` 或旧 workbench API 一起并入本轮。
- 不做无关的全仓类型迁移或风格重写。

### Task 1: Lock the Graph Workbench Protocol Before Any UI Refactor

**Files:**
- Create: `packages/shared/types/graph-workbench.ts`
- Modify: `packages/shared/types/index.ts`
- Create: `packages/api/app/schemas/graph_workbench.py`
- Create: `packages/api/tests/contract/test_graph_workbench_schema.py`

- [ ] **Step 1: Write the failing schema and contract tests**

Add focused tests that assert payload shapes like:

```python
def test_graph_workbench_meta_summary_requires_database_counts():
    summary = GraphWorkbenchMetaSummary.model_validate({
        "node_count": 12,
        "relationship_count": 18,
        "label_count": 4,
        "relationship_type_count": 6,
        "property_key_count": 11,
        "index_count": 2,
        "constraint_count": 1,
        "truncated": False,
        "generated_at": "2026-03-23T10:00:00Z",
    })
    assert summary.node_count == 12


def test_graph_workbench_label_meta_requires_property_keys():
    item = GraphWorkbenchLabelMetaItem.model_validate({
        "name": "Herb",
        "count": 3,
        "property_keys": ["name", "category"],
    })
    assert item.property_keys == ["name", "category"]
```

- [ ] **Step 2: Run the focused contract test and verify it fails**

Run:

```bash
uv run pytest tests/contract/test_graph_workbench_schema.py -v
```

Expected: FAIL because the graph-workbench shared / schema files do not exist yet.

- [ ] **Step 3: Add the shared protocol file with Graph Workbench-specific names**

Create a new shared contract file with names that do not collide with the existing command workbench types, for example:

```ts
export interface GraphWorkbenchMetaSummary { ... }
export interface GraphWorkbenchLabelMetaItem { ... }
export interface GraphWorkbenchRelationshipTypeMetaItem { ... }
export interface GraphWorkbenchPropertyKeyMetaItem { ... }
export interface GraphWorkbenchSchemaIndexItem { ... }
export interface GraphWorkbenchSchemaConstraintItem { ... }
export interface GraphSceneInfo { ... }
```

Use `graph-workbench.ts`, not `workbench.ts`.

- [ ] **Step 4: Add matching Pydantic schemas with API field naming aligned to current backend style**

Create `packages/api/app/schemas/graph_workbench.py` with snake_case fields and explicit response models that mirror the shared protocol semantics.

- [ ] **Step 5: Export the new shared contract**

Update `packages/shared/types/index.ts` to export the new file while keeping the existing `workbench.ts` export intact.

- [ ] **Step 6: Re-run the focused contract test**

Run:

```bash
uv run pytest tests/contract/test_graph_workbench_schema.py -v
```

Expected: PASS

- [ ] **Step 7: Run shared typecheck**

Run:

```bash
pnpm --dir packages/shared typecheck
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add packages/shared/types/graph-workbench.ts packages/shared/types/index.ts packages/api/app/schemas/graph_workbench.py packages/api/tests/contract/test_graph_workbench_schema.py
git commit -m "feat(shared): define graph workbench protocol"
```

### Task 2: Add Read-Only Database Metadata Endpoints for `/graph`

**Files:**
- Create: `packages/api/app/kg/graph_metadata_service.py`
- Modify: `packages/api/app/api/graph.py`
- Modify: `packages/api/tests/api/test_graph_routes.py`
- Modify: `packages/api/tests/kg/test_graph_service.py`

- [ ] **Step 1: Write failing API tests for the metadata routes**

Add focused route tests for:

```python
async def test_get_graph_meta_summary(client):
    response = await client.get("/api/v1/graph/meta/summary")
    assert response.status_code == 200
    assert "node_count" in response.json()


async def test_get_graph_meta_labels_supports_limit(client):
    response = await client.get("/api/v1/graph/meta/labels?limit=20")
    assert response.status_code == 200
    assert "items" in response.json()
```

- [ ] **Step 2: Run the focused graph route test and verify it fails**

Run:

```bash
uv run pytest tests/api/test_graph_routes.py -v
```

Expected: FAIL because `/graph/meta/*` routes do not exist.

- [ ] **Step 3: Write failing service tests for metadata aggregation**

Add tests that assert the new metadata service can normalize:

- labels with counts and property keys
- relationship types with counts and property keys
- property keys with usage summaries
- indexes and constraints in a UI-friendly shape

- [ ] **Step 4: Implement `graph_metadata_service.py` as a separate read-only service**

Keep database metadata querying out of `graph_service.py` so the two responsibilities stay separate:

```python
class GraphMetadataService:
    async def get_summary(self) -> GraphWorkbenchMetaSummary: ...
    async def list_labels(self, q: str | None, limit: int, offset: int): ...
    async def list_relationship_types(self, q: str | None, limit: int, offset: int): ...
    async def list_property_keys(self, q: str | None, limit: int, offset: int): ...
    async def get_schema(self): ...
```

- [ ] **Step 5: Add `/graph/meta/*` routes using explicit response models**

Add:

- `GET /api/v1/graph/meta/summary`
- `GET /api/v1/graph/meta/labels`
- `GET /api/v1/graph/meta/relationship-types`
- `GET /api/v1/graph/meta/property-keys`
- `GET /api/v1/graph/meta/schema`

- [ ] **Step 6: Re-run the focused metadata tests**

Run:

```bash
uv run pytest tests/api/test_graph_routes.py tests/kg/test_graph_service.py -v
```

Expected: PASS for the new metadata routes and service behaviors.

- [ ] **Step 7: Commit**

```bash
git add packages/api/app/kg/graph_metadata_service.py packages/api/app/api/graph.py packages/api/tests/api/test_graph_routes.py packages/api/tests/kg/test_graph_service.py
git commit -m "feat(api): expose graph metadata endpoints"
```

### Task 3: Enrich the Existing Graph Scene Contract Without Mixing It With Database Meta

**Files:**
- Modify: `packages/api/app/schemas/graph.py`
- Modify: `packages/api/app/kg/graph_service.py`
- Modify: `packages/api/tests/api/test_graph_routes.py`
- Modify: `packages/api/tests/kg/test_graph_service.py`

- [ ] **Step 1: Write failing tests for GraphScene info fields**

Add tests that assert herb graph and advanced query responses can expose scene metadata such as:

- `truncated`
- `node_limit_hit`
- `relationship_limit_hit`
- `info_message`

Example:

```python
async def test_query_graph_includes_scene_info(client):
    response = await client.post("/api/v1/graph/query", json={"depth": 1, "limit": 20})
    body = response.json()
    assert "scene" in body
    assert "truncated" in body["scene"]
```

- [ ] **Step 2: Run the focused graph contract tests and verify they fail**

Run:

```bash
uv run pytest tests/api/test_graph_routes.py tests/kg/test_graph_service.py -v
```

Expected: FAIL because current graph responses do not expose scene information.

- [ ] **Step 3: Extend `packages/api/app/schemas/graph.py` with explicit scene models**

Add models such as:

```python
class GraphSceneInfo(BaseModel):
    truncated: bool = False
    node_limit_hit: bool = False
    relationship_limit_hit: bool = False
    info_message: str | None = None
```

and attach them to the advanced-query response shape without folding database metadata into the same object.

- [ ] **Step 4: Update `graph_service.py` to populate scene metadata**

Keep the scene info derived from the current result only. Do not call metadata service from here.

- [ ] **Step 5: Re-run the focused graph tests**

Run:

```bash
uv run pytest tests/api/test_graph_routes.py tests/kg/test_graph_service.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packages/api/app/schemas/graph.py packages/api/app/kg/graph_service.py packages/api/tests/api/test_graph_routes.py packages/api/tests/kg/test_graph_service.py
git commit -m "feat(api): enrich graph scene response for workbench"
```

### Task 4: Build the Web Data Layer Around the Shared Graph Workbench Protocol

**Files:**
- Create: `packages/web/src/types/graphWorkbench.ts`
- Create: `packages/web/src/services/graphWorkbenchApi.ts`
- Create: `packages/web/src/stores/graphWorkbenchStore.ts`
- Create: `packages/web/src/hooks/useGraphWorkbenchPage.ts`
- Modify: `packages/web/src/types/graph.ts`
- Modify: `packages/web/src/hooks/useGraphWorkspace.ts`
- Create: `packages/web/src/hooks/useGraphWorkbenchPage.test.tsx`

- [ ] **Step 1: Write failing hook tests for independent metadata and graph-scene loading**

Add tests that assert:

- metadata can load even if graph scene errors
- selecting a node switches inspector mode to `details`
- clicking a label intent updates `highlightedLabel` without losing current scene data

- [ ] **Step 2: Run the focused hook test and verify it fails**

Run:

```bash
pnpm --dir packages/web exec vp test run src/hooks/useGraphWorkbenchPage.test.tsx
```

Expected: FAIL because the hook and store do not exist yet.

- [ ] **Step 3: Add the web-only view model types**

Create `packages/web/src/types/graphWorkbench.ts` for local-only types such as:

```ts
export type GraphWorkbenchInspectorMode = "overview" | "details";

export interface GraphWorkbenchSelectionState { ... }
export interface GraphWorkbenchHighlightState { ... }
export interface GraphWorkbenchOverviewViewModel { ... }
```

Import protocol DTOs from `@bai-cao/shared` instead of redefining them.

- [ ] **Step 4: Add `graphWorkbenchApi.ts` with one boundary adaptation layer**

Implement functions like:

```ts
getMetaSummary()
getMetaLabels(params)
getMetaRelationshipTypes(params)
getMetaPropertyKeys(params)
getMetaSchema()
```

Do the remote-to-view-model normalization here, once.

- [ ] **Step 5: Add a dedicated Graph Workbench store**

Create a new store to hold:

- selected node / relationship
- hovered node / relationship
- highlighted label / relationship type
- inspector mode
- sidebar and inspector collapsed state

Do not overload the old command `workbenchStore.ts`.

- [ ] **Step 6: Refactor `useGraphWorkspace.ts` into a narrower scene-data helper**

Keep it focused on graph scene fetching and expansion; let the new page hook own metadata + selection orchestration.

- [ ] **Step 7: Re-run the focused hook tests and typecheck**

Run:

```bash
pnpm --dir packages/web exec vp test run src/hooks/useGraphWorkbenchPage.test.tsx
pnpm --dir packages/web typecheck
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add packages/web/src/types/graphWorkbench.ts packages/web/src/services/graphWorkbenchApi.ts packages/web/src/stores/graphWorkbenchStore.ts packages/web/src/hooks/useGraphWorkbenchPage.ts packages/web/src/types/graph.ts packages/web/src/hooks/useGraphWorkspace.ts packages/web/src/hooks/useGraphWorkbenchPage.test.tsx
git commit -m "feat(web): add graph workbench data layer"
```

### Task 5: Rebuild `/graph` as a Three-Pane Graph Workbench Shell

**Files:**
- Create: `packages/web/src/components/graph/GraphMetadataSidebar.tsx`
- Create: `packages/web/src/components/graph/GraphCanvasWorkspace.tsx`
- Create: `packages/web/src/components/graph/GraphInspectorPanel.tsx`
- Modify: `packages/web/src/pages/GraphPage.tsx`
- Modify: `packages/web/src/pages/GraphPage.test.tsx`
- Create: `packages/web/src/components/graph/GraphMetadataSidebar.test.tsx`
- Create: `packages/web/src/components/graph/GraphInspectorPanel.test.tsx`

- [ ] **Step 1: Write failing page and component tests for the new three-pane layout**

Add tests that assert:

- `/graph` renders `Database information`, canvas, and inspector at the same time
- metadata loading state is separate from scene loading state
- overview is the default inspector mode on first render

Example:

```tsx
it("renders database information, graph result view, and inspector together", () => {
  render(<GraphPage />);
  expect(screen.getByText("Database information")).toBeInTheDocument();
  expect(screen.getByTestId("graph-canvas-workspace")).toBeInTheDocument();
  expect(screen.getByText("Overview")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the focused web tests and verify they fail**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphPage.test.tsx src/components/graph/GraphMetadataSidebar.test.tsx src/components/graph/GraphInspectorPanel.test.tsx
```

Expected: FAIL because the new components and layout do not exist yet.

- [ ] **Step 3: Build `GraphMetadataSidebar.tsx`**

Implement grouped sections for:

- Summary
- Labels
- Relationship types
- Property keys
- Indexes
- Constraints

Add search and `show more / show all` interactions where required.

- [ ] **Step 4: Build `GraphInspectorPanel.tsx` with `overview` and `details` modes**

Keep overview and details rendering inside a single panel component, with explicit props for click handlers on labels and relationship types.

- [ ] **Step 5: Build `GraphCanvasWorkspace.tsx` as the canvas-only component**

Move graph rendering concerns out of `GraphPage.tsx` so page layout and canvas interaction stay separate.

- [ ] **Step 6: Rebuild `GraphPage.tsx` around the new shell**

Compose:

- left metadata sidebar
- central canvas
- right inspector

Make sure `GraphPage.tsx` only orchestrates data and layout, not every interaction detail.

- [ ] **Step 7: Re-run the focused component and page tests**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphPage.test.tsx src/components/graph/GraphMetadataSidebar.test.tsx src/components/graph/GraphInspectorPanel.test.tsx
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add packages/web/src/components/graph/GraphMetadataSidebar.tsx packages/web/src/components/graph/GraphCanvasWorkspace.tsx packages/web/src/components/graph/GraphInspectorPanel.tsx packages/web/src/pages/GraphPage.tsx packages/web/src/pages/GraphPage.test.tsx packages/web/src/components/graph/GraphMetadataSidebar.test.tsx packages/web/src/components/graph/GraphInspectorPanel.test.tsx
git commit -m "feat(web): rebuild graph page as graph workbench shell"
```

### Task 6: Implement Graph Interaction Parity and Reverse Highlighting

**Files:**
- Modify: `packages/web/src/components/graph/GraphCanvasWorkspace.tsx`
- Modify: `packages/web/src/components/graph/GraphInspectorPanel.tsx`
- Modify: `packages/web/src/components/graph/GraphMetadataSidebar.tsx`
- Modify: `packages/web/src/components/graph/NodeDetail.tsx`
- Modify: `packages/web/src/components/graph/EdgeDetail.tsx`
- Modify: `packages/web/src/pages/GraphPage.test.tsx`
- Modify: `packages/web/src/components/graph/GraphMetadataSidebar.test.tsx`
- Modify: `packages/web/src/components/graph/GraphInspectorPanel.test.tsx`

- [ ] **Step 1: Write failing interaction tests for highlight and selection parity**

Cover:

- clicking a sidebar label highlights matching nodes
- clicking a sidebar relationship type highlights matching edges
- clicking a node switches inspector to `details`
- clicking blank canvas returns inspector to `overview`
- clicking a label in the inspector drives the same highlight behavior as the sidebar

- [ ] **Step 2: Run the focused interaction tests and verify they fail**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphPage.test.tsx src/components/graph/GraphMetadataSidebar.test.tsx src/components/graph/GraphInspectorPanel.test.tsx
```

Expected: FAIL because reverse-highlighting and blank-canvas reset are not implemented yet.

- [ ] **Step 3: Add stable highlight and dimming rules in `GraphCanvasWorkspace.tsx`**

Implement one visual pipeline for:

- hovered item
- selected item
- highlighted label
- highlighted relationship type
- dimmed non-focus elements

Keep label and relationship type colors stable across canvas and legend.

- [ ] **Step 4: Add reverse highlight handlers in sidebar and inspector**

Do not let components mutate canvas state directly. Route all highlight actions through the page hook/store.

- [ ] **Step 5: Update `NodeDetail.tsx` and `EdgeDetail.tsx` for inspector mode**

Ensure details show:

- system fields like id
- labels / relationship types
- property tables suitable for right-side inspection

- [ ] **Step 6: Re-run the focused interaction tests, then typecheck and build**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphPage.test.tsx src/components/graph/GraphMetadataSidebar.test.tsx src/components/graph/GraphInspectorPanel.test.tsx
pnpm --dir packages/web typecheck
pnpm --dir packages/web exec vp build
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add packages/web/src/components/graph/GraphCanvasWorkspace.tsx packages/web/src/components/graph/GraphInspectorPanel.tsx packages/web/src/components/graph/GraphMetadataSidebar.tsx packages/web/src/components/graph/NodeDetail.tsx packages/web/src/components/graph/EdgeDetail.tsx packages/web/src/pages/GraphPage.test.tsx packages/web/src/components/graph/GraphMetadataSidebar.test.tsx packages/web/src/components/graph/GraphInspectorPanel.test.tsx
git commit -m "feat(web): add graph workbench interaction parity"
```

### Task 7: Update Acceptance Docs and Mark the Old `/graph` Plan Assumption as Superseded

**Files:**
- Create: `docs/acceptance/graph-workbench-mainline.md`
- Modify: `docs/acceptance/README.md`
- Delete: superseded graph workbench / graph workspace intermediate plans after acceptance and architecture graduation

- [ ] **Step 1: Write the new acceptance doc for `/graph`**

Document the mainline around:

- loading `/graph`
- showing `Database information`
- clicking labels / relationship types
- selecting nodes / relationships
- returning to overview
- validating `/graph/meta/*` routes

- [ ] **Step 2: Add the new acceptance doc to the docs index**

Update `docs/acceptance/README.md` so the new Graph Workbench acceptance path is discoverable.

- [ ] **Step 3: Add a supersession note to the old browser-shell plan**

Delete superseded graph workbench intermediate docs so `/graph` only保留一条 requirement lineage。

- [ ] **Step 4: Run a lightweight doc sanity check**

Run:

```bash
rg -n "graph-workbench" docs/acceptance docs/superpowers/plans
```

Expected: the new plan and acceptance references are visible and not contradictory.

- [ ] **Step 5: Commit**

```bash
git add docs/acceptance/graph-workbench-mainline.md docs/acceptance/README.md docs/architecture/graph-workbench.md
git commit -m "docs: document graph workbench mainline"
```

### Task 8: Run End-to-End Verification for the New `/graph` Mainline

**Files:**
- No code changes required

- [ ] **Step 1: Run focused API verification**

Run:

```bash
uv run pytest tests/contract/test_graph_workbench_schema.py tests/api/test_graph_routes.py tests/kg/test_graph_service.py -v
```

Expected: PASS

- [ ] **Step 2: Run focused web verification**

Run:

```bash
pnpm --dir packages/web exec vp test run src/hooks/useGraphWorkbenchPage.test.tsx src/pages/GraphPage.test.tsx src/components/graph/GraphMetadataSidebar.test.tsx src/components/graph/GraphInspectorPanel.test.tsx
```

Expected: PASS

- [ ] **Step 3: Run web typecheck and build**

Run:

```bash
pnpm --dir packages/web typecheck
pnpm --dir packages/web exec vp build
```

Expected: PASS

- [ ] **Step 4: Run live route spot checks against the dev stack**

Run:

```bash
curl -sS http://localhost:8000/api/v1/graph/meta/summary | python3 -m json.tool
curl -sS 'http://localhost:8000/api/v1/graph/meta/labels?limit=20' | python3 -m json.tool
curl -sS 'http://localhost:8000/api/v1/graph/herb/%E4%BA%BA%E5%8F%82?depth=1' | python3 -m json.tool
```

Expected: all commands exit `0`, and the first two responses include metadata fields while the herb graph response includes scene information for the current graph result.

- [ ] **Step 5: Commit any final doc or test-only cleanup**

```bash
git status --short
```

Expected: empty worktree or only intentionally uncommitted changes outside this plan.
