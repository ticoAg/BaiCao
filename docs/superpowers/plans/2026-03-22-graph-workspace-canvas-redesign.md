# Graph Workspace Canvas Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `/graph` 重构为“画布优先、查询按需唤出、详情与图例回到画布语义”的沉浸式知识图谱工作区，并在不改后端契约的前提下完成首轮前端落地。

**Architecture:** 保留 `useGraphWorkspace`、`graphApi` 与现有图谱数据结构不变，把主要变更集中在 `packages/web` 的页面布局、局部交互状态与详情展示层。页面从固定三栏切换为“单主画布 + 查询抽屉 + 右下详情浮卡 + 画布内图例与工具栏”，并通过页面级测试锁定新的主路径和关键控件职责。

**Tech Stack:** React 18, React Router 6, TanStack Query, Zustand, Ant Design 5, `@ant-design/graphs`, Vitest, Testing Library

---

## File Map

- Modify: `packages/web/src/pages/GraphPage.tsx`
  - 重构工作区主布局，移除顶部重复深度控件，引入查询入口卡、查询抽屉、详情浮卡、图例和画布工具栏。
- Modify: `packages/web/src/components/graph/GraphQueryPanel.tsx`
  - 适配抽屉形态，补充重置动作和默认折叠的开发者预览，明确“查询深度”语义。
- Modify: `packages/web/src/components/graph/NodeDetail.tsx`
  - 重新组织节点详情层级，加入长字段截断、Tooltip、复制动作。
- Modify: `packages/web/src/components/graph/EdgeDetail.tsx`
  - 对齐关系详情层级和长字段处理。
- Modify: `packages/web/src/pages/GraphPage.test.tsx`
  - 锁定新布局的核心交互和职责边界。
- Modify: `packages/web/src/components/graph/GraphQueryPanel.test.tsx`
  - 增加重置和开发者预览折叠行为测试。
- Modify: `packages/web/src/index.css`
  - 收敛页面级工作区样式，包括浮层、工具条、画布覆盖层和隐藏滚动条等基础样式。
- Optional Create: `packages/web/src/components/graph/GraphWorkspaceToolbar.tsx`
  - 若 `GraphPage.tsx` 过重，则拆出画布工具栏。
- Optional Create: `packages/web/src/components/graph/GraphWorkspaceLegend.tsx`
  - 若 `GraphPage.tsx` 过重，则拆出画布图例组件。
- Optional Create: `packages/web/src/components/graph/GraphSelectionCard.tsx`
  - 若 `NodeDetail` / `EdgeDetail` 需要统一卡片框架，则抽出浮卡壳层。

## Notes

- 目标文件当前已有未提交改动，本计划默认这些变更应保留并在其上继续演进，不允许回滚用户在途修改。
- 首轮实现不修改 `packages/web/src/hooks/useGraphWorkspace.ts` 的主状态结构，也不改后端契约。
- 如在执行时发现 `GraphPage.tsx` 体积或职责过重，可以进行小范围组件拆分，但不要演变为无关重构。

## Non-Goals

- 不修改任何 API 路由、Schema、共享 DTO 或 Neo4j 查询逻辑。
- 不引入新的全局状态容器。
- 不在本轮实现复杂动画编排或移动端专属重布局。
- 不把图谱页面改造成任意编辑器或路径设计器。

### Task 1: Lock the New Workspace Contract in Page Tests

**Files:**
- Modify: `packages/web/src/pages/GraphPage.test.tsx`

- [ ] **Step 1: Write failing tests for the new layout contract**

Add tests that assert:

```tsx
it("shows a query entry trigger instead of a permanent left query title in the main canvas flow", () => {
  // render /graph/人参
  // expect query entry CTA to exist
  // expect top bar depth selector to be absent
});

it("renders the legend inside the canvas workspace and not in the detail panel body", () => {
  // render with graph data
  // expect floating legend label to exist
});

it("shows an empty selection card prompt after clearing selection", () => {
  // render /graph with selected null
  // expect contextual empty-state copy
});
```

- [ ] **Step 2: Run the focused page tests and verify they fail**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphPage.test.tsx
```

Expected: FAIL because the current layout still contains the old permanent side panels and duplicated depth control.

- [ ] **Step 3: Update the test doubles to match the redesigned shell**

Adjust the mocked workspace result and selectors so tests look for:

- query entry trigger / drawer affordance
- absence of top-bar depth control
- floating legend
- floating detail empty state

- [ ] **Step 4: Re-run the focused page tests**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphPage.test.tsx
```

Expected: still FAIL on assertions until implementation lands, but test names and expectations should now describe the new design correctly.

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/pages/GraphPage.test.tsx
git commit -m "test(web): lock graph workspace canvas redesign contract"
```

### Task 2: Rebuild GraphPage as a Canvas-First Workspace Shell

**Files:**
- Modify: `packages/web/src/pages/GraphPage.tsx`
- Optional Create: `packages/web/src/components/graph/GraphWorkspaceToolbar.tsx`
- Optional Create: `packages/web/src/components/graph/GraphWorkspaceLegend.tsx`

- [ ] **Step 1: Write the minimal shell state needed by the redesign**

Add page-local state for:

```tsx
const [isQueryDrawerOpen, setIsQueryDrawerOpen] = useState(false);
```

Keep `selected`, `mode`, `depth`, `querySummary`, and `graphData` sourced from `useGraphWorkspace`.

- [ ] **Step 2: Replace the fixed three-column layout with canvas + overlays**

Implement the page shell so it renders:

- one full-height canvas container
- one top status strip with mode, counts, truncation marker, refresh only
- one left-top query summary card with open / reset actions
- one left drawer containing `GraphQueryPanel`
- one floating legend inside the canvas
- one floating action toolbar inside the canvas
- one floating detail card anchored away from the toolbar

- [ ] **Step 3: Remove the duplicated top-bar depth control**

Delete the `Select` used for depth in the top floating area, and ensure depth remains controlled only through the query UI.

- [ ] **Step 4: Add explicit canvas controls backed by the graph instance**

Capture the graph instance in `onReady` and wire actions for:

- zoom in
- zoom out
- fit view
- focus center node

If the graph instance API needs guarding, no-op safely when the graph is not ready.

- [ ] **Step 5: Ensure selection can return to empty state**

Add a canvas blank-click handler or equivalent fallback so clicking outside nodes/edges clears the selection and reveals the empty-state detail card.

- [ ] **Step 6: Run the page tests**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphPage.test.tsx
```

Expected: page tests move to PASS or only fail on downstream detail/query panel assertions not yet updated.

- [ ] **Step 7: Commit**

```bash
git add packages/web/src/pages/GraphPage.tsx packages/web/src/components/graph/GraphWorkspaceToolbar.tsx packages/web/src/components/graph/GraphWorkspaceLegend.tsx
git commit -m "feat(web): rebuild graph page as canvas-first workspace"
```

### Task 3: Convert the Query Builder into an On-Demand Drawer Panel

**Files:**
- Modify: `packages/web/src/components/graph/GraphQueryPanel.tsx`
- Modify: `packages/web/src/components/graph/GraphQueryPanel.test.tsx`

- [ ] **Step 1: Write failing tests for reset and collapsed developer preview**

Add tests that assert:

```tsx
it("resets all query fields and keeps depth in sync with the workspace default", async () => {
  // fill fields, click reset, assert fields cleared
});

it("hides developer payload preview by default and expands it on demand", async () => {
  // expect preview body absent initially
  // expand dev section and assert payload renders
});
```

- [ ] **Step 2: Run the focused query panel tests and verify they fail**

Run:

```bash
pnpm --dir packages/web exec vp test run src/components/graph/GraphQueryPanel.test.tsx
```

Expected: FAIL because reset and collapsed developer preview do not exist yet.

- [ ] **Step 3: Add query-panel props and UX for drawer usage**

Introduce the smallest API necessary, for example:

```tsx
type GraphQueryPanelProps = {
  depth: number;
  loading?: boolean;
  onSubmit: (request: GraphQueryRequest) => void | Promise<unknown>;
  onDepthChange?: (depth: number) => void;
  onReset?: () => void;
};
```

Implement:

- button text “执行图谱查询”
- secondary reset / clear action
- label rename from `深度` to `查询深度`
- developer preview inside a `Collapse` or similar, default closed

- [ ] **Step 4: Keep the submit payload behavior stable**

Verify the refactor still trims empty filters and preserves the existing `GraphQueryRequest` shape before submission.

- [ ] **Step 5: Re-run the query panel tests**

Run:

```bash
pnpm --dir packages/web exec vp test run src/components/graph/GraphQueryPanel.test.tsx
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/web/src/components/graph/GraphQueryPanel.tsx packages/web/src/components/graph/GraphQueryPanel.test.tsx
git commit -m "feat(web): adapt graph query panel for drawer workflow"
```

### Task 4: Redesign the Selection Detail Card for Readability

**Files:**
- Modify: `packages/web/src/components/graph/NodeDetail.tsx`
- Modify: `packages/web/src/components/graph/EdgeDetail.tsx`

- [ ] **Step 1: Write or extend tests for long-field rendering if coverage is missing**

If component-level tests exist, extend them. If not, cover the behavior via page-level tests plus a small new component test:

```tsx
it("renders long verification identifiers in truncated form with copy affordance", () => {
  // render node detail with a long verification_id
  // assert copy button exists
  // assert full raw id is not dumped as a wrapped paragraph
});
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphPage.test.tsx
```

Expected: FAIL on missing copy affordance or updated empty-state structure.

- [ ] **Step 3: Refactor node and edge detail hierarchy**

Implement:

- a stronger title block
- softer key styling, stronger value styling
- long-field rendering helper with truncation + tooltip + copy
- consistent status / type tag styling

Keep action behavior such as “查看完整详情” intact for herb nodes.

- [ ] **Step 4: Re-run the affected tests**

Run:

```bash
pnpm --dir packages/web exec vp test run src/pages/GraphPage.test.tsx
```

Expected: PASS on detail-card assertions.

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/components/graph/NodeDetail.tsx packages/web/src/components/graph/EdgeDetail.tsx packages/web/src/pages/GraphPage.test.tsx
git commit -m "feat(web): redesign graph selection detail cards"
```

### Task 5: Apply Shared Workspace Styling and Visual Polish

**Files:**
- Modify: `packages/web/src/index.css`
- Modify: `packages/web/src/pages/GraphPage.tsx`

- [ ] **Step 1: Add failing assertions only if style hooks are missing**

Prefer testing through semantic hooks already added in page tests. If a new stable class or `data-testid` is required for overlays, add it with intention rather than snapshotting styles.

- [ ] **Step 2: Implement shared workspace surface styles**

Add or refine CSS for:

- workspace background
- floating card surfaces
- canvas legend shell
- canvas toolbar shell
- hidden scrollbars where needed
- drawer-compatible spacing

Keep CSS names specific to the graph workspace to avoid leaking styles across the app.

- [ ] **Step 3: Refine graph label presentation in the page config**

Within `GraphPage.tsx`, keep:

- improved node label legibility
- relation pill label background
- tooltip readability

Avoid changing graph data semantics while polishing display.

- [ ] **Step 4: Run the full web test suite**

Run:

```bash
pnpm run test:web
```

Expected: PASS.

- [ ] **Step 5: Run a production build for the web package**

Run:

```bash
pnpm --dir packages/web exec vp build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/web/src/index.css packages/web/src/pages/GraphPage.tsx
git commit -m "style(web): polish graph workspace canvas surfaces"
```

### Task 6: Final Verification and Handoff Notes

**Files:**
- Modify: `docs/superpowers/plans/2026-03-22-graph-workspace-canvas-redesign.md`
- Optional Modify: `docs/acceptance/graph-query-mainline.md`

- [ ] **Step 1: Verify the main user-visible flows manually**

Check:

1. `/graph/人参` loads with canvas-first layout and visible query entry card
2. `/graph` shows empty workspace guidance and can open the query drawer
3. Running a query updates summary state without reintroducing duplicate depth controls
4. Clicking a node or edge opens the detail float card
5. Clicking blank canvas clears the selection
6. Long IDs show copy affordance instead of hard wrapping

- [ ] **Step 2: Update acceptance docs only if the changed flow is already documented there**

If `docs/acceptance/graph-query-mainline.md` already describes the old permanent three-column flow, update it to match the new canvas-first interaction.

- [ ] **Step 3: Record executed verification commands in the final handoff**

Include:

```bash
pnpm run test:web
pnpm --dir packages/web exec vp build
```

Also note any unverified item if graph-instance toolbar behavior cannot be fully covered by automated tests.

- [ ] **Step 4: Commit**

```bash
git add docs/acceptance/graph-query-mainline.md docs/superpowers/plans/2026-03-22-graph-workspace-canvas-redesign.md
git commit -m "docs: record graph workspace canvas redesign verification"
```
