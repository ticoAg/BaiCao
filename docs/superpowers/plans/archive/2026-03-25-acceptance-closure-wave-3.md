# Acceptance Closure Wave 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把当前仍停留在 `risk` 的主链路验收项收口为 `pass`，并把顶层 README / 架构文档中的状态表述对齐到当前代码事实。

**Architecture:** 本轮不新增新的产品子系统，只做“证据闭环”和“口径对齐”。优先复用现有 API / Web 测试、集成脚本、浏览器手工验收与 `curl` spot-check；只有在验收过程中暴露真实缺口时，才补最小回归测试和最小实现修复。任何超过当前 wave 范围的能力缺口，都拆到后续独立计划，而不是在本轮顺手扩张。

**Tech Stack:** FastAPI, React, Vitest, Pytest, curl, Docker Compose, Neo4j, Markdown, `@agent-browser`

---

## 实施状态更新（2026-03-25）

### 已完成

- Graph Workbench 已补齐本地浏览器页面事实检查与 API spot-check，验收文档已从 `risk` 提升为 `pass`
- 在 Graph Workbench 验收过程中发现 `neomodel.adb.url` 漂移风险，已在 `packages/api/app/kg/db.py` 补 `ensure_kg_db()` 并用单测锁住
- 数据处理工作台 Wave 1 已补齐四类来源分发、七步 preview、map 门禁、confirm / rollback 与页面恢复的 fresh 证据，验收文档已从 `risk` 提升为 `pass`
- 共享知识模型 / 数据采集主线已补齐 JSONL importer/exporter round-trip、本地 graph schema spot-check 与 package-level 运行证据，验收文档已从 `risk` 提升为 `pass`
- `README.md`、`docs/architecture/system-overview.md` 与 `docs/acceptance/README.md` 已对齐当前仓库事实，移除了对已落地能力的过时表述

### 验证结果

- `cd packages/api && uv run pytest tests/unit/kg/test_db.py tests/api/test_graph_routes.py tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py tests/contract/test_graph_shared_model_contract.py tests/contract/test_import_record_contract.py tests/unit/kg/test_models.py -q` → `48 passed`
- `cd packages/knowledge_model && uv run --with pytest pytest tests -q` → `8 passed`
- `cd packages/data_ingestion && uv run --with pytest pytest tests/test_models.py -q` → `1 passed`
- `pnpm --dir packages/web test --run src/pages/GraphPage.test.tsx src/pages/DataPipelinePage.test.tsx` → `8 passed`
- `pnpm --dir packages/web typecheck` → `passed`
- `./scripts/test_integration.sh` → `3 passed, 230 deselected`
- 本地浏览器 / curl spot-check 已覆盖 `/graph`、`/graph/:name`、`/data/pipeline` 与 `graph/meta/*`

### 风险

- 本轮补的是“主链路验收闭环”，不是完整浏览器 E2E / 截图回归体系
- `huggingface` 在数据处理工作台里仍是 locator 校验与摘要预览，不代表远端抓取已接入
- 真实导入执行、权限 / 审计 / 关系级治理、完整溯源链路、事件驱动 / 监控仍在后续范围

### 当前结论

- 这轮 plan 的目标已完成：此前停留在 `risk` 的三条主链路验收现均已提升为 `pass`

## Scope Notes

- 本计划只覆盖：
  - Graph Workbench 验收补证据
  - 数据处理工作台 Wave 1 验收补证据
  - 共享知识模型 / 数据采集主链路补高层验证
  - README / 架构文档状态口径对齐
- 本计划明确不覆盖以下独立子系统；这些应在后续拆成单独计划：
  - 专家权限 / 审计日志 / 关系级审核
  - 聊天多轮会话持久化与更强来源选择
  - 事件驱动、缓存策略、监控与追踪

## File Map

- Modify: `docs/acceptance/graph-workbench-mainline.md`
  - 把 Graph Workbench 从 `risk` 提升到 `pass`，写入浏览器人工验收和本地接口 spot-check 的 fresh 证据。
- Modify: `packages/web/src/pages/GraphPage.test.tsx`
  - 若人工验收发现当前测试未锁住关键 UI 状态，补最小回归。
- Modify: `packages/api/tests/api/test_graph_routes.py`
  - 若 spot-check 暴露未锁住的接口形状，补最小 route 回归。
- Modify: `docs/architecture/graph-workbench.md`
  - 更新“已完成 / 仍未完成边界”，移除已补齐的人工验收缺口。
- Modify: `docs/superpowers/plans/2026-03-23-graph-workbench.md`
  - 将 plan 状态从“仍待补人工验收”收口到当前完成事实。

- Modify: `docs/acceptance/data-pipeline-workbench-mainline.md`
  - 为 Wave 1 补页面级人工验收与 fresh 证据，若范围内主链路均通过则改为 `pass`。
- Modify: `packages/web/src/pages/DataPipelinePage.test.tsx`
  - 若当前页面测试没锁住 review/export 操作入口，则补最小回归。
- Modify: `packages/api/tests/api/test_pipeline_routes.py`
  - 若 curl/API spot-check 暴露未锁住的 step / preview / confirm 形状，则补 route 回归。
- Modify: `packages/web/src/components/pipeline/PipelineActionPanel.tsx`
  - 仅在页面验收发现 CTA 文案 / 可见性与当前主路径不一致时做最小修复。
- Modify: `packages/web/src/components/pipeline/PipelinePreviewPanel.tsx`
  - 仅在页面验收发现 review/export 信息展示缺口时做最小修复。

- Modify: `docs/acceptance/data-ingestion-and-knowledge-model.md`
  - 追加更高层 contract / CLI / package-level fresh 证据，并在覆盖足够时改为 `pass`。
- Modify: `packages/api/tests/contract/test_import_record_contract.py`
  - 补 CSV 主路径共享导入记录断言，避免验收只靠 JSONL。
- Modify: `packages/data_ingestion/tests/test_models.py`
  - 若 package-level 边界校验还不够，补一条更高层消费断言。
- Modify: `packages/api/tests/api/test_graph_routes.py`
  - 若需要增加一条 API 侧 shared model smoke 断言，在现有文件补最小回归。

- Modify: `README.md`
  - 更新当前状态表与一页看懂，避免继续把 SSE / 数据管道当前事实写成“规划中”。
- Modify: `docs/architecture/system-overview.md`
  - 对齐“已实现 / 进行中 / 规划中”的分层口径。
- Modify: `docs/acceptance/README.md`
  - 如状态统计或文档摘要需要同步，补入口页说明。

## Non-Goals

- 不在本轮接入新的业务能力。
- 不在本轮重做 Graph Workbench 或 Data Pipeline 的视觉设计。
- 不在本轮补完整 E2E 套件；只做足以把 `risk` 提升到 `pass` 的最小主链路证据。

---

### Task 1: Promote Graph Workbench Acceptance from `risk` to `pass`

**Files:**
- Modify: `docs/acceptance/graph-workbench-mainline.md`
- Modify: `packages/web/src/pages/GraphPage.test.tsx`
- Modify: `packages/api/tests/api/test_graph_routes.py`
- Modify: `docs/architecture/graph-workbench.md`
- Modify: `docs/superpowers/plans/2026-03-23-graph-workbench.md`

- [ ] **Step 1: Add the narrowest missing regression only if acceptance reveals an uncovered behavior**

优先目标不是“多写测试”，而是给浏览器验收发现的真实缺口补一条最小锁定。

候选示例：

```tsx
it("keeps the inspector visible when graph data is loaded from /graph/:name", () => {
  mockedUseGraphWorkbenchPage.mockReturnValue(createHookResult());

  renderWithProviders(
    <Routes>
      <Route path="/graph/:name?" element={<GraphPage />} />
    </Routes>,
    "/graph/人参",
  );

  expect(screen.getByText("Database information")).toBeInTheDocument();
  expect(screen.getByTestId("graph-canvas-workspace")).toBeInTheDocument();
  expect(screen.getByTestId("graph-inspector-panel")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run current Graph Workbench checks before touching implementation**

Run:

```bash
cd packages/api
uv run pytest tests/api/test_graph_routes.py -q

cd ../..
pnpm --dir packages/web test --run src/pages/GraphPage.test.tsx
```

Expected:
- 现有自动化检查全部通过；如果失败，先记录失败点，再决定是否进入最小修复。

- [ ] **Step 3: Perform the missing browser and local API spot-checks**

使用 `@agent-browser` 或等价浏览器自动化执行：

1. 打开 `/graph`
2. 打开 `/graph/人参`
3. 验证左侧 `Database information`
4. 验证中央画布结果区
5. 验证右侧 `Overview`
6. 尝试一次查询器打开/关闭
7. 点击一个节点类型按钮，确认不会清空图

同时执行本地接口 spot-check：

```bash
curl -sS http://localhost:8000/api/v1/graph/meta/summary | python3 -m json.tool
curl -sS 'http://localhost:8000/api/v1/graph/meta/labels?limit=20' | python3 -m json.tool
curl -sS http://localhost:8000/api/v1/graph/meta/schema | python3 -m json.tool
curl -sS 'http://localhost:8000/api/v1/graph/herb/%E4%BA%BA%E5%8F%82?depth=1' | python3 -m json.tool
```

Expected:
- 页面主路径与文档描述一致
- meta / herb graph 接口返回形状与当前验收文档一致

- [ ] **Step 4: If a mismatch is found, apply the smallest possible fix in the owning module**

可能的最小修复归属：
- 页面布局 / inspector 丢失：`packages/web/src/pages/GraphPage.tsx`
- 左侧 metadata 展示异常：`packages/web/src/components/graph/GraphMetadataSidebar.tsx`
- 路由响应形状不一致：`packages/api/app/api/graph.py`
- graph scene / meta 数据缺口：`packages/api/app/kg/graph_service.py`、`packages/api/app/kg/graph_metadata_service.py`

要求：
- 先补对应最小回归，再修代码
- 不顺手扩张到 Cypher workbench 或更细 Neo4j Browser parity

- [ ] **Step 5: Re-run checks and update the docs to `pass`**

Run:

```bash
cd packages/api
uv run pytest tests/api/test_graph_routes.py -q

cd ../..
pnpm --dir packages/web test --run src/pages/GraphPage.test.tsx
pnpm --dir packages/web typecheck
```

然后更新：
- `docs/acceptance/graph-workbench-mainline.md`
- `docs/architecture/graph-workbench.md`
- `docs/superpowers/plans/2026-03-23-graph-workbench.md`

Expected:
- 验收文档改为 `结果：pass`
- 架构文档不再把“浏览器人工验收”列为未完成
- 历史 plan 状态口径与新证据一致

- [ ] **Step 6: Commit**

```bash
git add docs/acceptance/graph-workbench-mainline.md docs/architecture/graph-workbench.md docs/superpowers/plans/2026-03-23-graph-workbench.md packages/web/src/pages/GraphPage.test.tsx packages/api/tests/api/test_graph_routes.py packages/web/src/pages/GraphPage.tsx packages/web/src/components/graph/GraphMetadataSidebar.tsx packages/api/app/api/graph.py packages/api/app/kg/graph_service.py packages/api/app/kg/graph_metadata_service.py
git commit -m "docs(acceptance): close graph workbench evidence gaps"
```

### Task 2: Promote Data Pipeline Workbench Acceptance from `risk` to `pass`

**Files:**
- Modify: `docs/acceptance/data-pipeline-workbench-mainline.md`
- Modify: `packages/web/src/pages/DataPipelinePage.test.tsx`
- Modify: `packages/api/tests/api/test_pipeline_routes.py`
- Modify: `packages/web/src/components/pipeline/PipelineActionPanel.tsx`
- Modify: `packages/web/src/components/pipeline/PipelinePreviewPanel.tsx`
- Modify: `packages/web/src/hooks/usePipelineRun.ts`

- [ ] **Step 1: Lock the current review/export UI entrypoints with one focused page regression**

候选最小测试：

```tsx
it("shows review and export step actions on the workbench", async () => {
  renderWithProviders(<App />, "/data/pipeline?runId=pipeline-restore");

  expect(await screen.findByText("当前步骤：原始内容预览")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "回退到上一步" })).toBeInTheDocument();
});
```

如果现有测试已经足够，扩成更有针对性的断言：
- `锁定人工审阅`
- `确认允许执行`
- `执行导出`

- [ ] **Step 2: Run the existing pipeline checks first**

Run:

```bash
cd packages/api
uv run pytest tests/api/test_pipeline_routes.py -q

cd ../..
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
```

Expected:
- 现有 route / page 回归全部通过；若失败，先记录失败点。

- [ ] **Step 3: Perform the missing page-level acceptance and API spot-check**

使用 `@agent-browser` 或等价浏览器自动化执行：

1. 打开 `/data/pipeline`
2. 创建或恢复一条 run
3. 验证固定七步 rail
4. 运行预览
5. 进入 `human_review`
6. 验证 review/export 相关 CTA 是否可见

补充 API spot-check：

```bash
curl -sS -X POST http://localhost:8000/api/v1/pipeline/runs \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"manual","source_locator":"候选实体：陈皮（药材）"}' | python3 -m json.tool
curl -sS -X POST http://localhost:8000/api/v1/pipeline/runs/<RUN_ID>/steps/source_ingest/preview | python3 -m json.tool
curl -sS -X POST http://localhost:8000/api/v1/pipeline/runs/<RUN_ID>/steps/map_to_knowledge_model/preview | python3 -m json.tool
curl -sS -X POST http://localhost:8000/api/v1/pipeline/runs/<RUN_ID>/steps/human_review/preview | python3 -m json.tool
curl -sS -X POST http://localhost:8000/api/v1/pipeline/runs/<RUN_ID>/steps/export/preview | python3 -m json.tool
```

Expected:
- 页面主路径与 Wave 1 验收范围一致
- API 返回仍与固定七步预览口径一致

- [ ] **Step 4: If a mismatch is found, patch the smallest owning file**

可能归属：
- CTA 文案 / 可见性：`packages/web/src/components/pipeline/PipelineActionPanel.tsx`
- review/export 展示：`packages/web/src/components/pipeline/PipelinePreviewPanel.tsx`
- 页面级编排：`packages/web/src/hooks/usePipelineRun.ts`
- route 返回形状：`packages/api/tests/api/test_pipeline_routes.py` 对应的实现文件

要求：
- 不把这一步扩张成新的 pipeline 功能设计
- 不把真正远端 HuggingFace 抓取塞进本 wave

- [ ] **Step 5: Re-run checks and update the acceptance doc to `pass`**

Run:

```bash
cd packages/api
uv run pytest tests/api/test_pipeline_routes.py -q

cd ../..
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
pnpm --dir packages/web exec vp build
```

然后更新 `docs/acceptance/data-pipeline-workbench-mainline.md`

Expected:
- 验收文档改为 `结果：pass`
- `风险与未覆盖项` 只保留当前 scope 外的明确边界，而不是本轮应补却未补的证据

- [ ] **Step 6: Commit**

```bash
git add docs/acceptance/data-pipeline-workbench-mainline.md packages/web/src/pages/DataPipelinePage.test.tsx packages/api/tests/api/test_pipeline_routes.py packages/web/src/components/pipeline/PipelineActionPanel.tsx packages/web/src/components/pipeline/PipelinePreviewPanel.tsx packages/web/src/hooks/usePipelineRun.ts
git commit -m "docs(acceptance): close data pipeline workbench evidence gaps"
```

### Task 3: Promote Shared-Model / Data-Ingestion Acceptance from `risk` to `pass`

**Files:**
- Modify: `docs/acceptance/data-ingestion-and-knowledge-model.md`
- Modify: `packages/api/tests/contract/test_import_record_contract.py`
- Modify: `packages/data_ingestion/tests/test_models.py`
- Modify: `packages/api/tests/api/test_graph_routes.py`

- [ ] **Step 1: Add one higher-layer regression that the current acceptance doc is missing**

优先补“CSV 主路径”而不是再重复 JSONL：

```python
def test_csv_importer_returns_shared_record(tmp_path):
    path = tmp_path / "records.csv"
    path.write_text("node_type,node_name,source\nHerb,陈皮,中国药典\n", encoding="utf-8")

    record = next(CSVImporter().load(str(path)))

    assert isinstance(record, GraphImportRecord)
    assert record.node_name == "陈皮"
```

- [ ] **Step 2: Run targeted shared-model / ingestion checks**

Run:

```bash
cd packages/api
uv run pytest tests/contract/test_import_record_contract.py tests/api/test_graph_routes.py -q

cd ../data_ingestion
uv run --with pytest pytest tests/test_models.py -q
```

Expected:
- contract、API 和 package-level 测试全部通过。

- [ ] **Step 3: Add one CLI-level smoke check so acceptance is not only unit/contract evidence**

Run:

```bash
cd packages/api
uv run python -m app.importers.cli packages/db/import/herbs.jsonl --dry-run
uv run python -m app.importers.cli packages/db/import/herbs.csv --dry-run
```

Expected:
- JSONL / CSV dry-run 都能输出统计信息
- 不出现共享记录类型漂移或 importer 入口报错

- [ ] **Step 4: If any smoke check fails, patch only the shared-boundary owner**

可能归属：
- importer / exporter 真源：`packages/api/app/importers/**`、`packages/api/app/exporters/**`
- API graph shared-boundary：`packages/api/app/schemas/graph.py`
- data_ingestion package-level 边界：`packages/data_ingestion/data_ingestion/models.py`

要求：
- 不扩张到 pipeline 七步或前端展示
- 只修共享真源和它的直接消费者

- [ ] **Step 5: Re-run checks and update the acceptance doc to `pass`**

Run:

```bash
cd packages/api
uv run pytest tests/contract/test_import_record_contract.py tests/api/test_graph_routes.py -q

cd ../data_ingestion
uv run --with pytest pytest tests/test_models.py -q
```

然后更新 `docs/acceptance/data-ingestion-and-knowledge-model.md`

Expected:
- 验收文档改为 `结果：pass`
- 风险说明不再把“缺少更高层验证”作为未完成项

- [ ] **Step 6: Commit**

```bash
git add docs/acceptance/data-ingestion-and-knowledge-model.md packages/api/tests/contract/test_import_record_contract.py packages/data_ingestion/tests/test_models.py packages/api/tests/api/test_graph_routes.py packages/api/app/importers packages/api/app/exporters packages/api/app/schemas/graph.py packages/data_ingestion/data_ingestion/models.py
git commit -m "docs(acceptance): close shared model and ingestion evidence gaps"
```

### Task 4: Align README and Architecture Docs with Current Repo Facts

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture/system-overview.md`
- Modify: `docs/acceptance/README.md`

- [ ] **Step 1: Reproduce the current wording drift with grep**

Run:

```bash
rg -n "规划中|进行中|SSE|事件驱动|缓存" README.md docs/architecture/system-overview.md
```

Expected:
- 能定位当前仍把已实现事实写成“规划中 / 进行中”的条目。

- [ ] **Step 2: Write the smallest doc diff that matches current code facts**

重点对齐：
- `README.md` 中的当前状态表
- `docs/architecture/system-overview.md` 中的“已实现 / 进行中 / 规划中”
- 不要把未做完的权限、多轮会话、事件驱动误写成已完成

候选替换示例：

```md
- 进行中：更完整的溯源链路、专家审查闭环、问答质量提升、图谱可视化增强
- 规划中：事件驱动集成、缓存策略、监控与追踪完善
```

说明：
- SSE 若已有实现和验收，不应继续列在“规划中”

- [ ] **Step 3: Validate doc consistency**

Run:

```bash
rg -n "SSE 流式输出|规划中：事件驱动" README.md docs/architecture/system-overview.md docs/acceptance
```

Expected:
- 顶层文档口径与当前验收事实不再冲突。

- [ ] **Step 4: Commit**

```bash
git add README.md docs/architecture/system-overview.md docs/acceptance/README.md
git commit -m "docs: align top-level status with current implementation"
```

## Follow-On Plans (Separate Scope, Do Not Fold Into This Wave)

以下仍是未完成任务，但应拆成独立计划：

1. **Governance / Permissions Wave**
   - 目标：补专家权限、审计日志、关系级审核
   - 证据来源：`docs/acceptance/verification-workflow.md`

2. **Chat Persistence Wave**
   - 目标：补多轮会话持久化、来源选择策略
   - 证据来源：`docs/acceptance/chat-mainline.md`

3. **Platform Hardening Wave**
   - 目标：补事件驱动、缓存策略、监控与追踪
   - 证据来源：`README.md`、`docs/architecture/system-overview.md`
