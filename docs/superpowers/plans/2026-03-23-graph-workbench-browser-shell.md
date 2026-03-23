# Graph Workbench Browser Shell Implementation Plan

> Superseded note: `/graph` 路径上的 Graph Workbench 改造以后以 `docs/superpowers/plans/2026-03-23-graph-workbench.md` 为准。本计划仅保留给独立命令式 workbench 路线参考。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个独立的 Neo4j Browser 风格图谱工作台页，连同可复用的命令/语义查询/Cypher 校验与只读执行能力，并让聊天页能够复用同一后端能力层。

**Architecture:** 采用 contract-first 垂直切片实现：先定义 workbench 命令与 frame 共享契约，再在 `packages/api` 中实现只读工作台执行层和路由，最后在 `packages/web` 中落地 Browser 风格 shell、stream frames 和聊天页复用入口。图谱工作台与聊天页共享同一套后端 workbench service，但前端展示保留各自主路径，避免直接把 Browser 壳层塞进现有 `/graph` 页面。

**Tech Stack:** React 18, React Router 6, Zustand, TanStack Query, Ant Design 5, `@ant-design/graphs`, FastAPI, Pydantic v2, Neo4j Python Driver, Vitest, Testing Library, Pytest, Ruff

---

## Scope Check

本计划覆盖一个垂直闭环能力，而不是两个独立子系统：

- Browser 风格 workbench 壳层
- 其背后的统一命令执行 / 语义查询 / Cypher 校验与只读执行能力

它们必须一起落地才具备可验收价值，因此保持在同一计划中；但任务会按 `shared -> api -> web -> chat reuse -> docs` 的顺序拆开，避免前后端互相阻塞。

## File Map

- Create: `packages/shared/types/workbench.ts`
  - 定义 workbench 命令、frame、执行请求/响应、Cypher 校验结果、语义查询模式等跨端契约。
- Modify: `packages/shared/types/index.ts`
  - 导出新的 workbench 共享类型，保持单一真源。
- Create: `packages/api/app/schemas/workbench.py`
  - 定义 FastAPI / Pydantic 版本的 workbench 请求响应模型。
- Create: `packages/api/app/services/workbench_service.py`
  - 统一命令解析、UI 命令处理、语义查询分发、Cypher 校验、只读执行和 frame 组装。
- Create: `packages/api/app/api/workbench.py`
  - 暴露 `/workbench/execute`、`/workbench/validate-cypher` 等路由。
- Modify: `packages/api/app/main.py`
  - 注册 workbench router。
- Modify: `packages/api/app/services/chat_service.py`
  - 让聊天链路可以调用 workbench service 生成结构化工具结果，而不是未来再做第二套。
- Modify: `packages/api/app/api/chat.py`
  - 如响应体字段需要扩展，保持 chat route 与新结构一致。
- Create: `packages/api/tests/services/test_workbench_service.py`
  - 覆盖命令分类、语义查询路由、Cypher 安全校验、frame 组装。
- Create: `packages/api/tests/api/test_workbench_routes.py`
  - 覆盖 workbench API 契约和错误响应。
- Modify: `packages/api/tests/services/test_chat_service.py`
  - 增加聊天页复用 workbench service 的服务级断言。
- Create: `packages/web/src/types/workbench.ts`
  - Web 端友好模型与 UI state 辅助类型；尽量从 shared 契约适配，而不是重新发明字段。
- Create: `packages/web/src/services/workbenchApi.ts`
  - workbench 相关前端请求封装。
- Create: `packages/web/src/stores/workbenchStore.ts`
  - 保存 editor 内容、frame stream、sidebar 状态、command history、favorites。
- Create: `packages/web/src/hooks/useGraphWorkbench.ts`
  - 封装命令执行、frame 写入、历史回填、命令来源标记。
- Create: `packages/web/src/pages/GraphWorkbenchPage.tsx`
  - Browser 风格工作台主页面。
- Create: `packages/web/src/components/workbench/WorkbenchShell.tsx`
  - 组合 rail / drawer / editor / stream。
- Create: `packages/web/src/components/workbench/WorkbenchSidebarRail.tsx`
  - 最左侧 icon rail。
- Create: `packages/web/src/components/workbench/WorkbenchDrawer.tsx`
  - 左侧 drawer 容器，承载 guides / history / favorites / settings。
- Create: `packages/web/src/components/workbench/CommandEditor.tsx`
  - Browser 风格命令编辑器与运行/清空/历史回填入口。
- Create: `packages/web/src/components/workbench/FrameStream.tsx`
  - frame 流容器。
- Create: `packages/web/src/components/workbench/frames/GraphResultFrame.tsx`
  - Browser 风格 graph frame，内部复用已有图谱交互和 inspector。
- Create: `packages/web/src/components/workbench/frames/TableResultFrame.tsx`
  - 结构化表格 frame。
- Create: `packages/web/src/components/workbench/frames/TextResultFrame.tsx`
  - help / guide / summary 文本 frame。
- Create: `packages/web/src/components/workbench/frames/ErrorResultFrame.tsx`
  - error / warning frame。
- Create: `packages/web/src/components/workbench/frames/FrameChrome.tsx`
  - 统一的 frame 头部、命令回显、状态标签和 rerun 控件。
- Modify: `packages/web/src/App.tsx`
  - 添加 workbench 路由。
- Modify: `packages/web/src/services/api.ts`
  - 若仍保留聚合导出，补 workbench 入口；否则导出到独立 `workbenchApi.ts` 并按现有模式接入。
- Modify: `packages/web/src/types/chat.ts`
  - 为聊天消息增加可选 workbench frames / command trace。
- Modify: `packages/web/src/hooks/useChat.ts`
  - 接收新增 workbench 结果并写入消息。
- Modify: `packages/web/src/components/chat/MessageList.tsx`
  - 在 assistant 消息中渲染简化版 workbench tool results / graph frame 入口。
- Create: `packages/web/src/pages/GraphWorkbenchPage.test.tsx`
  - 锁定 Browser 风格 shell 主路径。
- Create: `packages/web/src/hooks/useGraphWorkbench.test.tsx`
  - 锁定命令执行到 frame stream 的状态流。
- Modify: `packages/web/src/pages/ChatPage.test.tsx`
  - 锁定聊天页对 workbench 结果的消费。
- Modify: `packages/web/src/index.css`
  - 添加 workbench 专属样式，避免污染现有 `/graph`。
- Create: `docs/acceptance/graph-workbench-browser-mainline.md`
  - 记录主链路验收步骤和证据。

## Notes

- 设计参考来自本轮已确认的终端讨论，以及只读参考仓库 [`.tmp/neo4j-browser/README.md`](/Users/ticoag/Documents/myws/BaiCao/.tmp/neo4j-browser/README.md)。由于该项目为 GPL-3.0，本计划默认只复刻交互与信息架构，不直接复制其源码实现。
- 第一阶段只支持 **只读 Cypher**。任何写操作、DDL、导入、删除、更新类命令都必须在校验阶段被拒绝，并以 error frame 返回。
- 语义查询优先支持三种模式：`exact`、`fuzzy`、`path`。更多高级策略（例如 ranking、hybrid search、multi-hop planner）不在本轮。
- 聊天页复用同一后端能力层，但不把完整 Browser 壳层塞进 `/chat`；仅消费结构化工具结果和 frame 摘要。

## Non-Goals

- 不在第一阶段实现完整 Neo4j Browser 的数据库管理、项目文件、认证配置、写 Cypher、事务控制等开发者功能。
- 不把现有 `/graph` 页面直接替换为 Browser 壳层。
- 不在本轮实现完整 Monaco 级编辑器特性；如现有依赖不足，可先用高质量 textarea / code-like editor 壳层占位。
- 不引入第二套图谱查询后端；统一复用 `graph_service` 与新增 workbench service。

### Task 1: Lock the Workbench Contract Before UI Work Starts

**Files:**
- Create: `packages/shared/types/workbench.ts`
- Modify: `packages/shared/types/index.ts`
- Create: `packages/api/app/schemas/workbench.py`
- Create: `packages/api/tests/services/test_workbench_service.py`

- [ ] **Step 1: Write the failing contract tests for command and frame shapes**

Add focused service/schema tests that assert payloads like:

```python
def test_validate_cypher_response_rejects_write_queries():
    result = CypherValidationResult.model_validate({
        "valid": False,
        "normalized_query": "MATCH (n) DELETE n",
        "errors": ["Write operations are not allowed."],
        "warnings": [],
    })
    assert result.valid is False


def test_workbench_execute_response_supports_graph_and_error_frames():
    response = WorkbenchExecuteResponse.model_validate({
        "command": ":help",
        "frames": [
            {"id": "f-1", "type": "text", "title": "Commands", "status": "ok", "payload": {"markdown": "help"}},
            {"id": "f-2", "type": "error", "title": "Unknown", "status": "error", "payload": {"message": "bad command"}},
        ],
        "history_item": {"command": ":help", "source": "workbench"},
    })
    assert len(response.frames) == 2
```

- [ ] **Step 2: Run the focused API service tests and verify they fail**

Run:

```bash
uv run pytest tests/services/test_workbench_service.py -v
```

Expected: FAIL because the schema/service files do not exist yet.

- [ ] **Step 3: Add the shared cross-end contract and matching Pydantic schemas**

Create the smallest useful shared contract, for example:

```ts
export type WorkbenchCommandSource = "workbench" | "chat";
export type WorkbenchFrameType = "graph" | "table" | "text" | "error";

export interface WorkbenchExecuteRequest {
  command: string;
  source: WorkbenchCommandSource;
  sessionId?: string;
}
```

and the matching Pydantic models in `packages/api/app/schemas/workbench.py`.

- [ ] **Step 4: Run the focused service test again**

Run:

```bash
uv run pytest tests/services/test_workbench_service.py -v
```

Expected: FAIL moves from import/schema errors to unimplemented service behavior.

- [ ] **Step 5: Run shared typecheck**

Run:

```bash
pnpm --dir packages/shared typecheck
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packages/shared/types/workbench.ts packages/shared/types/index.ts packages/api/app/schemas/workbench.py packages/api/tests/services/test_workbench_service.py
git commit -m "feat(shared): define workbench execution contract"
```

### Task 2: Build the Read-Only Workbench Execution Service

**Files:**
- Create: `packages/api/app/services/workbench_service.py`
- Modify: `packages/api/app/kg/graph_service.py`
- Modify: `packages/api/tests/services/test_workbench_service.py`

- [ ] **Step 1: Write the failing service tests for command routing**

Add tests for these behaviors:

```python
async def test_execute_routes_help_command_to_text_frame():
    response = await service.execute(":help", source="workbench")
    assert response.frames[0].type == "text"


async def test_execute_routes_exact_semantic_query_to_graph_frame():
    response = await service.execute("查人参的功效", source="workbench")
    assert response.frames[0].type == "graph"


async def test_validate_cypher_rejects_delete_keyword():
    result = await service.validate_cypher("MATCH (n) DELETE n")
    assert result.valid is False
```

- [ ] **Step 2: Run the focused service test and verify it fails**

Run:

```bash
uv run pytest tests/services/test_workbench_service.py -v
```

Expected: FAIL because `WorkbenchService` has not been implemented.

- [ ] **Step 3: Implement minimal command classification and UI command handlers**

Start with a narrow command router:

```python
if command.startswith(":help"):
    return self._help_frames(command)
if command.startswith(":clear"):
    return self._clear_frames()
if command.startswith(":history"):
    return self._history_frames(history)
```

Do not add every Browser command in phase one.

- [ ] **Step 4: Implement semantic query tools on top of `graph_service`**

Add three service methods only:

```python
async def run_exact_query(self, text: str) -> WorkbenchFrame: ...
async def run_fuzzy_query(self, text: str) -> WorkbenchFrame: ...
async def run_path_query(self, text: str) -> WorkbenchFrame: ...
```

Prefer reusing `get_herb_graph`, `query_graph`, `search_nodes`, and `find_path` rather than inventing a second graph API.

- [ ] **Step 5: Implement read-only Cypher validation and execution**

Add a guarded validator such as:

```python
FORBIDDEN_KEYWORDS = {"CREATE", "MERGE", "DELETE", "SET", "REMOVE", "DROP", "CALL"}
```

and reject any query containing write / admin operations before execution. Only after validation passes should the service call a read-only execution helper.

- [ ] **Step 6: Add minimal graph-service support for raw read-only Cypher**

Introduce one clearly named method in `graph_service`, for example:

```python
async def execute_readonly_cypher(self, query: str, params: dict | None = None) -> list[dict]:
    ...
```

Keep it explicitly read-only and private to the service boundary.

- [ ] **Step 7: Re-run the focused service test**

Run:

```bash
uv run pytest tests/services/test_workbench_service.py -v
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add packages/api/app/services/workbench_service.py packages/api/app/kg/graph_service.py packages/api/tests/services/test_workbench_service.py
git commit -m "feat(api): add read-only workbench execution service"
```

### Task 3: Expose Workbench Routes and Make Chat Reuse the Same Backend Capability

**Files:**
- Create: `packages/api/app/api/workbench.py`
- Modify: `packages/api/app/main.py`
- Modify: `packages/api/app/services/chat_service.py`
- Modify: `packages/api/app/api/chat.py`
- Create: `packages/api/tests/api/test_workbench_routes.py`
- Modify: `packages/api/tests/api/test_chat_routes.py`
- Modify: `packages/api/tests/services/test_chat_service.py`

- [ ] **Step 1: Write the failing route tests**

Add API tests that assert:

```python
async def test_execute_workbench_command_returns_frames(client):
    response = client.post("/api/v1/workbench/execute", json={"command": ":help", "source": "workbench"})
    assert response.status_code == 200
    assert response.json()["frames"][0]["type"] == "text"


async def test_validate_cypher_returns_422_for_missing_query(client):
    response = client.post("/api/v1/workbench/validate-cypher", json={})
    assert response.status_code == 422
```

- [ ] **Step 2: Run the focused route tests and verify they fail**

Run:

```bash
uv run pytest tests/api/test_workbench_routes.py tests/api/test_chat_routes.py -v
```

Expected: FAIL because router is not registered and chat responses do not expose workbench results yet.

- [ ] **Step 3: Add the new workbench router and register it**

Create `packages/api/app/api/workbench.py` with endpoints like:

```python
@router.post("/execute", response_model=WorkbenchExecuteResponse)
async def execute_command(payload: WorkbenchExecuteRequest): ...

@router.post("/validate-cypher", response_model=CypherValidationResult)
async def validate_cypher(payload: CypherValidationRequest): ...
```

and include the router from `packages/api/app/main.py`.

- [ ] **Step 4: Extend chat service to optionally return structured workbench results**

Do the smallest additive change:

```python
response["workbench_frames"] = await self._maybe_build_workbench_frames(question, graph_data)
```

Keep existing chat fields backward compatible.

- [ ] **Step 5: Update chat API models only as needed**

If `chat.py` needs a request/response model to reflect the new optional field, add it there or in a dedicated schema file. Do not break existing callers.

- [ ] **Step 6: Re-run the focused API tests**

Run:

```bash
uv run pytest tests/api/test_workbench_routes.py tests/api/test_chat_routes.py tests/services/test_chat_service.py -v
```

Expected: PASS

- [ ] **Step 7: Run API lint for touched files**

Run:

```bash
uv run ruff check app tests
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add packages/api/app/api/workbench.py packages/api/app/main.py packages/api/app/services/chat_service.py packages/api/app/api/chat.py packages/api/tests/api/test_workbench_routes.py packages/api/tests/api/test_chat_routes.py packages/api/tests/services/test_chat_service.py
git commit -m "feat(api): expose workbench routes and chat reuse"
```

### Task 4: Add the Frontend Workbench Service Layer and Route Entry

**Files:**
- Create: `packages/web/src/types/workbench.ts`
- Create: `packages/web/src/services/workbenchApi.ts`
- Create: `packages/web/src/stores/workbenchStore.ts`
- Create: `packages/web/src/hooks/useGraphWorkbench.ts`
- Modify: `packages/web/src/App.tsx`
- Create: `packages/web/src/hooks/useGraphWorkbench.test.tsx`

- [ ] **Step 1: Write the failing hook test**

Add a focused state-flow test like:

```tsx
it("appends returned frames to the stream when a command succeeds", async () => {
  // mock executeCommand -> one text frame
  // call runCommand(":help")
  // expect stream length === 1
});
```

- [ ] **Step 2: Run the focused hook test and verify it fails**

Run:

```bash
pnpm --dir packages/web exec vp test run src/hooks/useGraphWorkbench.test.tsx
```

Expected: FAIL because the hook/store/files do not exist yet.

- [ ] **Step 3: Add web-side workbench types and API client**

Model the minimal client boundary:

```ts
export const workbenchApi = {
  execute: async (payload: WorkbenchExecuteRequest) => { ... },
  validateCypher: async (payload: CypherValidationRequest) => { ... },
};
```

- [ ] **Step 4: Add the workbench store and hook**

Store only the state needed by the shell:

```ts
type WorkbenchState = {
  editorValue: string;
  frames: WorkbenchFrame[];
  history: HistoryItem[];
  selectedDrawer: "guides" | "history" | "favorites" | null;
}
```

- [ ] **Step 5: Add the route entry without building the full page yet**

Register a new page route in `packages/web/src/App.tsx`, for example:

```tsx
<Route path="/graph/workbench" element={<GraphWorkbenchPage />} />
```

If the page file is still a placeholder at this step, make it explicit and minimal.

- [ ] **Step 6: Re-run the focused hook test**

Run:

```bash
pnpm --dir packages/web exec vp test run src/hooks/useGraphWorkbench.test.tsx
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add packages/web/src/types/workbench.ts packages/web/src/services/workbenchApi.ts packages/web/src/stores/workbenchStore.ts packages/web/src/hooks/useGraphWorkbench.ts packages/web/src/hooks/useGraphWorkbench.test.tsx packages/web/src/App.tsx
git commit -m "feat(web): add graph workbench client state layer"
```

### Task 5: Build the Browser-Style Workbench Shell

**Files:**
- Create: `packages/web/src/pages/GraphWorkbenchPage.tsx`
- Create: `packages/web/src/components/workbench/WorkbenchShell.tsx`
- Create: `packages/web/src/components/workbench/WorkbenchSidebarRail.tsx`
- Create: `packages/web/src/components/workbench/WorkbenchDrawer.tsx`
- Create: `packages/web/src/components/workbench/CommandEditor.tsx`
- Create: `packages/web/src/components/workbench/FrameStream.tsx`
- Create: `packages/web/src/components/workbench/frames/FrameChrome.tsx`
- Create: `packages/web/src/pages/GraphWorkbenchPage.test.tsx`
- Modify: `packages/web/src/index.css`

- [ ] **Step 1: Write the failing page tests for the Browser shell contract**

Add tests that assert:

```tsx
it("renders a left icon rail, command editor, and frame stream on the workbench route", () => {
  // render /graph/workbench
  // expect rail buttons
  // expect command editor
  // expect frame stream region
});

it("opens the history drawer from the rail", async () => {
  // click history icon
  // expect drawer content
});
```

- [ ] **Step 2: Run the focused page tests and verify they fail**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphWorkbenchPage.test.tsx
```

Expected: FAIL because the page and components do not exist yet.

- [ ] **Step 3: Implement the shell frame, not the final frame renderers**

Build the high-level structure first:

```tsx
<WorkbenchShell>
  <WorkbenchSidebarRail />
  <WorkbenchDrawer />
  <CommandEditor />
  <FrameStream />
</WorkbenchShell>
```

Do not overbuild editor internals before the shell hierarchy is visible.

- [ ] **Step 4: Give the editor Browser-like command ergonomics**

Support:

- run current command
- clear editor
- recall selected history item
- starter commands such as `:help` and one semantic query example

Keep the editor implementation dependency-light unless the repo already carries a preferred code editor.

- [ ] **Step 5: Style the shell as a distinct workbench**

Add workbench-specific CSS scopes in `packages/web/src/index.css`:

- left icon rail
- drawer surface
- code/editor surface
- stream spacing
- frame chrome

Avoid regressing current `/graph`.

- [ ] **Step 6: Re-run the focused page tests**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphWorkbenchPage.test.tsx
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add packages/web/src/pages/GraphWorkbenchPage.tsx packages/web/src/components/workbench packages/web/src/pages/GraphWorkbenchPage.test.tsx packages/web/src/index.css
git commit -m "feat(web): build browser-style graph workbench shell"
```

### Task 6: Add Graph/Table/Text/Error Frames and Reuse the Existing Graph Interaction Layer

**Files:**
- Create: `packages/web/src/components/workbench/frames/GraphResultFrame.tsx`
- Create: `packages/web/src/components/workbench/frames/TableResultFrame.tsx`
- Create: `packages/web/src/components/workbench/frames/TextResultFrame.tsx`
- Create: `packages/web/src/components/workbench/frames/ErrorResultFrame.tsx`
- Modify: `packages/web/src/components/graph/NodeDetail.tsx`
- Modify: `packages/web/src/components/graph/EdgeDetail.tsx`
- Modify: `packages/web/src/pages/GraphWorkbenchPage.test.tsx`

- [ ] **Step 1: Write the failing frame rendering tests**

Add tests that assert:

```tsx
it("renders graph frames with inspector behavior inside the stream", () => {
  // seed one graph frame
  // expect graph frame chrome + inspector
});

it("renders error frames for invalid cypher", () => {
  // seed one error frame
  // expect error title + message
});
```

- [ ] **Step 2: Run the focused page tests and verify they fail**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphWorkbenchPage.test.tsx
```

Expected: FAIL because the shell has no frame implementations yet.

- [ ] **Step 3: Implement a reusable frame chrome**

Create a common wrapper that displays:

- original command
- source tag (`workbench` / `chat`)
- status tag
- rerun button placeholder
- close/dismiss affordance if the UX needs it

- [ ] **Step 4: Implement graph frame by reusing existing graph interaction patterns**

Do not duplicate the entire current `/graph` page. Reuse the graph rendering + inspector logic in a focused frame component, even if that requires extracting small reusable pieces from the existing graph components.

- [ ] **Step 5: Implement table/text/error frames minimally**

Each frame should do one thing clearly:

```tsx
switch (frame.type) {
  case "table": return <TableResultFrame ... />
  case "text": return <TextResultFrame ... />
  case "error": return <ErrorResultFrame ... />
}
```

- [ ] **Step 6: Re-run the focused page tests**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphWorkbenchPage.test.tsx
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add packages/web/src/components/workbench/frames packages/web/src/components/graph/NodeDetail.tsx packages/web/src/components/graph/EdgeDetail.tsx packages/web/src/pages/GraphWorkbenchPage.test.tsx
git commit -m "feat(web): add graph and result frames to workbench stream"
```

### Task 7: Surface Reusable Workbench Results in the Chat UI

**Files:**
- Modify: `packages/web/src/types/chat.ts`
- Modify: `packages/web/src/hooks/useChat.ts`
- Modify: `packages/web/src/components/chat/MessageList.tsx`
- Modify: `packages/web/src/pages/ChatPage.test.tsx`

- [ ] **Step 1: Write the failing chat-page tests**

Add tests that assert an assistant message can render a compact workbench result preview:

```tsx
it("renders workbench result cards returned from chat responses", () => {
  // seed assistant message with workbenchFrames
  // expect command label and frame summary
});
```

- [ ] **Step 2: Run the focused chat tests and verify they fail**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/ChatPage.test.tsx
```

Expected: FAIL because chat types and message rendering do not know about workbench frames yet.

- [ ] **Step 3: Extend chat response mapping in the smallest additive way**

Update `ChatResponse` and message shaping to include optional frame payloads:

```ts
export interface ChatResponse {
  ...
  workbench_frames?: WorkbenchFrame[];
}
```

- [ ] **Step 4: Render a compact reusable result card in assistant messages**

Keep it intentionally lighter than the full workbench:

- command summary
- frame type badges
- graph frame deep-link to `/graph/workbench`
- existing graph preview can remain for backward compatibility

- [ ] **Step 5: Re-run the focused chat tests**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/ChatPage.test.tsx
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packages/web/src/types/chat.ts packages/web/src/hooks/useChat.ts packages/web/src/components/chat/MessageList.tsx packages/web/src/pages/ChatPage.test.tsx
git commit -m "feat(web): surface workbench results in chat messages"
```

### Task 8: Acceptance Docs and Full Verification

**Files:**
- Create: `docs/acceptance/graph-workbench-browser-mainline.md`
- Modify: `docs/acceptance/README.md` (only if a new entry is needed)
- Modify: `docs/superpowers/plans/2026-03-23-graph-workbench-browser-shell.md`

- [ ] **Step 1: Write the acceptance checklist**

Document at least these user-visible flows:

- open `/graph/workbench`
- run `:help`
- run one semantic graph query
- run one invalid Cypher and see an error frame
- see graph frame + inspector
- see chat message consume workbench results

- [ ] **Step 2: Run shared verification**

Run:

```bash
pnpm --dir packages/shared typecheck
```

Expected: PASS

- [ ] **Step 3: Run API verification**

Run from `packages/api`:

```bash
uv run ruff check .
uv run pytest
```

Expected: PASS

- [ ] **Step 4: Run web verification**

Run:

```bash
pnpm run test:web
pnpm --dir packages/web exec vp build
```

Expected: PASS

- [ ] **Step 5: Update the plan with actual evidence**

Mark completed items only after commands pass and record any residual warning, such as large frontend chunks.

- [ ] **Step 6: Commit**

```bash
git add docs/acceptance/graph-workbench-browser-mainline.md docs/acceptance/README.md docs/superpowers/plans/2026-03-23-graph-workbench-browser-shell.md
git commit -m "docs: add graph workbench acceptance evidence"
```

## Self-Review Note

- 本次按 `writing-plans` 产出了完整计划文档。
- 按 skill 原流程应再派发 plan reviewer 子代理做 review loop，但当前会话没有得到你对代理协作的明确授权；因此这一步我只做了主线程自检，没有启动 reviewer agent。
- 若你后续希望我严格按该 skill 的 reviewer 流程补一轮，可以直接明确说“允许你用子代理 review plan”。
