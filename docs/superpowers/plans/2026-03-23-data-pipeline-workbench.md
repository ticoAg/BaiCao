# Data Pipeline Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 BaiCao 建立一个固定步骤、可预览、可人工放行、可恢复的数据处理工作台页面，用来承接多来源数据的处理、抽取、图模型映射与导出 / 入库主链路。

**Architecture:** 新增 `pipeline` 后端模块和 `/data/pipeline` 前端页面，使用持久化 `PipelineRun` 驱动 7 个固定步骤。步骤之间默认人工确认放行，第 5 步统一映射到共享图模型唯一真源，第 7 步才允许正式导出 / 入库。

**Tech Stack:** React, Ant Design, Zustand, React Query, FastAPI, Pydantic v2, PostgreSQL, Markdown, Mermaid

---

## 实施状态更新（2026-03-25）

### 已完成

- 后端 `pipeline` 路由、持久化 `PipelineRun`、预览快照 / 历史版本、确认 / 重跑 / 回退主链路已经落地，见 `packages/api/app/api/pipeline.py`、`packages/api/app/pipeline/service.py`、`packages/api/app/pipeline/storage.py`
- 前端 `/data/pipeline` 页面、路由与导航入口已经落地，见 `packages/web/src/pages/DataPipelinePage.tsx`、`packages/web/src/App.tsx`、`packages/web/src/components/Header.tsx`
- 第 5 步共享模型映射门禁已经接入，且空白来源无法绕过确认进入下一步，见 `packages/api/app/pipeline/steps/map_to_knowledge_model.py`
- 本轮补齐了七步固定 handler 与来源 adapter，`source_ingest`、`source_preview`、`normalize`、`extract`、`map_to_knowledge_model`、`human_review`、`export` 不再统一返回通用 summary 占位，见 `packages/api/app/pipeline/steps/` 与 `packages/api/app/pipeline/adapters/`
- 本轮新增工作台主链路验收文档，见 `docs/acceptance/data-pipeline-workbench-mainline.md`

### 验证结果

- `cd packages/api && uv run pytest tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py -q` → `24 passed`
- `cd packages/api && uv run ruff check app/pipeline tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py` → `All checks passed!`
- `pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx` → `5 passed`
- `pnpm --dir packages/web typecheck` → `passed`
- 本地 API spot-check 复核了四类来源分发、七步 preview kind、map 门禁与 confirm / rollback 主路径
- 本地浏览器页面事实检查复核了 `/data/pipeline` 与 `/data/pipeline?runId=<id>` 的固定七步、最近任务、当前步骤恢复与预览内容展示

### 风险

- 本轮已经补齐页面级人工验收与真实来源分发的本地复核，但未扩展到完整截图回归或 E2E 套件
- `huggingface` 来源目前仅做 locator 校验与摘要预览，不代表远端数据抓取已接入
- 历史步骤中的 checkbox 未逐项回填；本节作为当前已实现事实与验证证据的聚合更新

## File Map

- Create: `packages/api/app/api/pipeline.py`
  - 暴露处理任务、步骤预览、确认、重跑、回退等接口。
- Create: `packages/api/app/pipeline/models.py`
  - 定义处理任务、步骤运行、产物与人工确认的领域模型。
- Create: `packages/api/app/pipeline/schemas.py`
  - 定义 API 输入输出 schema。
- Create: `packages/api/app/pipeline/service.py`
  - 管理任务流转与步骤推进。
- Create: `packages/api/app/pipeline/storage.py`
  - 管理预览快照、产物引用和中间结果持久化。
- Create: `packages/api/app/pipeline/steps/base.py`
  - 固定步骤处理器协议。
- Create: `packages/api/app/pipeline/steps/*.py`
  - 实现 7 个固定步骤处理器。
- Create: `packages/api/app/pipeline/adapters/*.py`
  - 实现来源适配器。
- Create: `packages/api/tests/**`
  - 覆盖任务创建、步骤预览、确认与回退。
- Create: `packages/web/src/pages/DataPipelinePage.tsx`
  - 数据处理工作台页面入口。
- Create: `packages/web/src/components/pipeline/*.tsx`
  - 步骤轨、操作区、预览区和预览组件。
- Create: `packages/web/src/hooks/usePipelineRun.ts`
  - 页面数据与操作 hook。
- Create: `packages/web/src/services/pipelineApi.ts`
  - 前端 API 封装。
- Create: `packages/web/src/stores/pipelineStore.ts`
  - 工作台局部状态。
- Create: `packages/web/src/types/pipeline.ts`
  - 前端类型定义。
- Modify: `packages/web/src/App.tsx`
  - 注册新页面路由。
- Modify: `packages/web/src/components/Header.tsx`
  - 增加数据处理工作台入口。
- Modify: `docs/architecture/README.md`
  - 收录新的稳定架构文档。
- Modify: `docs/README.md`
  - 收录新的稳定架构文档入口。
- Modify: `docs/architecture/knowledge-model-and-ingestion.md`
  - 增补数据处理工作台作为共享图模型消费者的说明。

## Non-Goals

- 不在本计划内实现用户自定义步骤模板。
- 不在本计划内实现完整批处理调度系统。
- 不在本计划内接入全部数据来源。
- 不在本计划内实现最终图谱入库的全量生产级能力。

## Fixed Step Template

1. 接入来源
2. 原始内容预览
3. 规范化清洗
4. 结构抽取
5. 映射到共享图模型
6. 人工确认与修订
7. 导出 / 入库

---

### Task 1: Add Stable Architecture Coverage for the Data Pipeline Workbench

**Files:**
- Create: `docs/architecture/data-pipeline-workbench.md`
- Modify: `docs/architecture/README.md`
- Modify: `docs/README.md`
- Modify: `docs/architecture/knowledge-model-and-ingestion.md`

- [ ] **Step 1: Write the docs consistency checklist**

检查点：

- 架构目录能索引到数据处理工作台文档
- 文档入口能索引到新文档
- 共享图模型架构文档能引用该工作台作为消费者

- [ ] **Step 2: Verify the new document is not yet indexed**

Run:

```bash
rg -n "data-pipeline-workbench|数据处理工作台" docs/architecture docs/README.md
```

Expected: 新文档或入口尚不存在。

- [ ] **Step 3: Write the stable architecture documentation**

实现要求：

- 写明固定步骤模板
- 写明任务持久化与人工放行
- 写明和共享图模型的关系

- [ ] **Step 4: Verify the new document is indexed**

Run:

```bash
rg -n "data-pipeline-workbench|数据处理工作台" docs/architecture docs/README.md
```

Expected: 新文档与入口已出现。

- [ ] **Step 5: Commit**

```bash
git add docs/architecture/data-pipeline-workbench.md docs/architecture/README.md docs/README.md docs/architecture/knowledge-model-and-ingestion.md
git commit -m "docs(architecture): define data pipeline workbench"
```

### Task 2: Define Pipeline Domain Models and API Schemas

**Files:**
- Create: `packages/api/app/pipeline/models.py`
- Create: `packages/api/app/pipeline/schemas.py`
- Create: `packages/api/tests/test_pipeline_models.py`

- [ ] **Step 1: Write the failing tests for pipeline task and step models**

```python
from app.pipeline.models import PipelineRunStatus, PipelineStepKey


def test_pipeline_has_fixed_step_keys():
    assert PipelineStepKey.SOURCE_INGEST == "source_ingest"


def test_pipeline_run_status_has_pending_review():
    assert PipelineRunStatus.PENDING_REVIEW == "pending_review"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest packages/api/tests/test_pipeline_models.py -q
```

Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Implement the pipeline domain models and schemas**

实现要求：

- 定义任务状态与步骤状态
- 定义固定步骤键
- 定义预览响应结构
- 定义确认与回退请求结构

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest packages/api/tests/test_pipeline_models.py -q
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/pipeline/models.py packages/api/app/pipeline/schemas.py packages/api/tests/test_pipeline_models.py
git commit -m "feat(pipeline): add pipeline domain models"
```

### Task 3: Implement the Pipeline Service Skeleton and Fixed Step Contract

**Files:**
- Create: `packages/api/app/pipeline/service.py`
- Create: `packages/api/app/pipeline/storage.py`
- Create: `packages/api/app/pipeline/steps/base.py`
- Create: `packages/api/app/pipeline/steps/*.py`
- Create: `packages/api/tests/test_pipeline_service.py`

- [ ] **Step 1: Write failing tests for preview and confirmation flow**

```python
def test_preview_does_not_auto_advance():
    ...


def test_confirm_advances_to_next_step():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest packages/api/tests/test_pipeline_service.py -q
```

Expected: FAIL because the service and steps are not implemented yet.

- [ ] **Step 3: Implement the service skeleton**

实现要求：

- 任务创建
- 当前步骤预览
- 步骤确认
- 步骤重跑
- 步骤回退
- 固定 7 步模板注册

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest packages/api/tests/test_pipeline_service.py -q
```

Expected: PASS，并证明 preview 不会自动推进，confirm 才会推进。

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/pipeline/service.py packages/api/app/pipeline/storage.py packages/api/app/pipeline/steps packages/api/tests/test_pipeline_service.py
git commit -m "feat(pipeline): add fixed-step pipeline service skeleton"
```

### Task 4: Expose the Pipeline API

**Files:**
- Create: `packages/api/app/api/pipeline.py`
- Modify: `packages/api/app/api/__init__.py`
- Modify: `packages/api/app/main.py`
- Create: `packages/api/tests/test_pipeline_api.py`

- [ ] **Step 1: Write failing API tests for task creation and step preview**

```python
def test_create_pipeline_run(client):
    ...


def test_preview_step_returns_preview_payload(client):
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest packages/api/tests/test_pipeline_api.py -q
```

Expected: FAIL because the API is not wired yet.

- [ ] **Step 3: Implement the API routes**

实现要求：

- 创建任务
- 查询任务列表与详情
- 运行步骤预览
- 确认步骤
- 重跑步骤
- 回退步骤

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest packages/api/tests/test_pipeline_api.py -q
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/api/pipeline.py packages/api/app/api/__init__.py packages/api/app/main.py packages/api/tests/test_pipeline_api.py
git commit -m "feat(api): add pipeline workbench endpoints"
```

### Task 5: Build the Web Pipeline Workbench Shell

**Files:**
- Create: `packages/web/src/pages/DataPipelinePage.tsx`
- Create: `packages/web/src/components/pipeline/PipelineShell.tsx`
- Create: `packages/web/src/components/pipeline/PipelineStepRail.tsx`
- Create: `packages/web/src/components/pipeline/PipelineActionPanel.tsx`
- Create: `packages/web/src/components/pipeline/PipelinePreviewPanel.tsx`
- Create: `packages/web/src/types/pipeline.ts`
- Create: `packages/web/src/services/pipelineApi.ts`
- Create: `packages/web/src/hooks/usePipelineRun.ts`
- Create: `packages/web/src/stores/pipelineStore.ts`
- Create: `packages/web/src/pages/DataPipelinePage.test.tsx`

- [ ] **Step 1: Write the failing page test**

```tsx
it("renders the fixed pipeline steps and action buttons", async () => {
  ...
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pnpm --dir packages/web test -- DataPipelinePage
```

Expected: FAIL because the page does not exist yet.

- [ ] **Step 3: Implement the workbench shell**

实现要求：

- 左侧步骤轨
- 中部操作区
- 右侧预览区
- 固定步骤名称与状态展示
- `运行预览` 与 `确认进入下一步` 主操作

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pnpm --dir packages/web test -- DataPipelinePage
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/pages/DataPipelinePage.tsx packages/web/src/components/pipeline packages/web/src/types/pipeline.ts packages/web/src/services/pipelineApi.ts packages/web/src/hooks/usePipelineRun.ts packages/web/src/stores/pipelineStore.ts packages/web/src/pages/DataPipelinePage.test.tsx
git commit -m "feat(web): add data pipeline workbench shell"
```

### Task 6: Wire Navigation and Shared Workbench Entry

**Files:**
- Modify: `packages/web/src/App.tsx`
- Modify: `packages/web/src/components/Header.tsx`
- Modify: `packages/web/src/pages/HomePage.tsx`
- Modify: `packages/web/src/pages/HomePage.test.tsx`

- [ ] **Step 1: Write failing navigation tests**

```tsx
it("shows a nav entry to the data pipeline workbench", () => {
  ...
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pnpm --dir packages/web test -- Header HomePage
```

Expected: FAIL because the route and nav entry are not added yet.

- [ ] **Step 3: Register the route and navigation**

实现要求：

- 注册 `/data/pipeline`
- 在顶部导航增加入口
- 在首页或合适入口增加工作台跳转

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pnpm --dir packages/web test -- Header HomePage
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/App.tsx packages/web/src/components/Header.tsx packages/web/src/pages/HomePage.tsx packages/web/src/pages/HomePage.test.tsx
git commit -m "feat(web): add navigation for data pipeline workbench"
```

### Task 7: Connect Step 5 to the Shared Knowledge Model Boundary

**Files:**
- Modify: `packages/api/app/pipeline/steps/map_to_knowledge_model.py`
- Modify: `packages/api/tests/test_pipeline_service.py`
- Modify: `packages/api/tests/test_pipeline_api.py`

- [ ] **Step 1: Write failing tests for shared knowledge model mapping**

```python
def test_mapping_step_returns_shared_model_preview():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest packages/api/tests/test_pipeline_service.py packages/api/tests/test_pipeline_api.py -q
```

Expected: FAIL because step 5 is not yet wired to the shared model boundary.

- [ ] **Step 3: Implement the mapping boundary**

实现要求：

- 第 5 步把候选结果转换成共享图模型实例或等价预览结构
- 返回校验通过 / 不通过项
- 不允许绕过共享真源进入后续步骤

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest packages/api/tests/test_pipeline_service.py packages/api/tests/test_pipeline_api.py -q
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/pipeline/steps/map_to_knowledge_model.py packages/api/tests/test_pipeline_service.py packages/api/tests/test_pipeline_api.py
git commit -m "feat(pipeline): map candidates to shared knowledge model"
```
