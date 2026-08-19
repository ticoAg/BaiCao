# Pipeline And Ingestion Closure Wave 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补齐数据处理工作台与共享知识模型/数据采集主线的剩余闭环，让 `pipeline` 工作台从“除 map 步骤外其余步骤仍为通用 summary 占位”升级为结构化 7 步预览流，并让 API、导入导出、数据采集边界真正消费 `packages/knowledge_model/`。

**Architecture:** 本轮按两条独立实施线推进。A 线负责共享知识模型消费者迁移：API graph schema、importers/exporters、`data_ingestion` 子项目与对应验收文档；B 线负责数据工作台剩余固定步骤与来源适配器，并补齐工作台验收与计划证据。两条线只通过 `knowledge_model` 共享边界和文档索引耦合，允许在独立 worktree 中并行实施，最后由主代理统一集成与验证。

**Tech Stack:** Python >=3.12（本地可用 3.13）, FastAPI, Pydantic v2, SQLAlchemy, React, Zustand, pnpm, uv, Markdown

---

## 实施状态更新（2026-03-25）

### 已完成

- 共享知识模型消费者迁移已经落地：API graph schema 复用共享 `NodeType` / `NodeStatus`，importer/exporter 切到共享 `GraphImportRecord`，见 `packages/api/app/models/enums.py`、`packages/api/app/schemas/graph.py`、`packages/api/app/importers/`、`packages/api/app/exporters/`
- `packages/data_ingestion/` 子项目骨架已经建立，并直接消费共享模型，见 `packages/data_ingestion/README.md`、`packages/data_ingestion/pyproject.toml`、`packages/data_ingestion/data_ingestion/models.py`
- 数据处理工作台剩余固定步骤与来源适配器已经补齐，七步预览不再停留在通用 summary 占位，见 `packages/api/app/pipeline/steps/`、`packages/api/app/pipeline/adapters/`、`packages/api/app/pipeline/service.py`
- 对应验收与历史计划回填已经落地，见 `docs/acceptance/data-ingestion-and-knowledge-model.md`、`docs/acceptance/data-pipeline-workbench-mainline.md`、`docs/superpowers/plans/2026-03-23-knowledge-model-and-data-ingestion.md`、`docs/superpowers/plans/2026-03-23-data-pipeline-workbench.md`
- 后续 Wave 2 已在此基础上继续把 review/export 从 preview-only 推进到真实持久化与显式执行，说明本 plan 的 Wave 1 主线已先行完成并成为后续迭代基础

### 验证结果

- `cd packages/api && uv run pytest tests/contract/test_graph_shared_model_contract.py tests/contract/test_import_record_contract.py tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py -q` → `30 passed`
- `cd packages/data_ingestion && uv run --with pytest pytest tests/test_models.py -q` → `1 passed`
- `pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx` → `5 passed`

### 风险与备注

- 本轮补齐的是 Wave 1 闭环，不代表已经覆盖完整浏览器 E2E、截图回归或全部真实外部来源接入
- `huggingface` 来源当前仍以 locator 校验与摘要预览为主；正式远端抓取与生产级任务编排不在本 plan 范围
- review/export 的真实持久化与显式执行已在后续 `2026-03-25-review-export-persistence-wave-2.md` 中继续推进，因此本计划应被视为后续 Wave 的已完成前置
- 历史步骤中的 checkbox 未逐项回填；本节作为当前实现事实与验证证据的聚合更新

### 当前结论

- 这份 plan 的 Wave 1 目标已完成，属于“实现先落地，计划状态后补记”的情况
- 它也是“checkbox 仍显示未开始，但相关代码、验收和后续 Wave 已经建立在其结果之上”的典型例子

## File Map

- Modify: `packages/api/app/models/enums.py`
  - 收缩本地图谱枚举，改为复用或对齐共享知识模型。
- Modify: `packages/api/app/models/__init__.py`
  - 保持 `app.models` 对外导出的图谱枚举别名稳定。
- Modify: `packages/api/app/schemas/graph.py`
  - 在不破坏 API 现有 edge superset 的前提下，对齐并复用共享模型定义。
- Modify: `packages/api/app/schemas/__init__.py`
  - 暴露更新后的 graph schema 入口。
- Modify: `packages/api/app/importers/base.py`
  - 把导入中间结构切到共享 `GraphImportRecord` / `GraphImportEdge`。
- Modify: `packages/api/app/importers/__init__.py`
  - 收敛或兼容导入器对外导出的记录类型。
- Modify: `packages/api/app/importers/jsonl_importer.py`
  - 输出共享导入记录。
- Modify: `packages/api/app/importers/csv_importer.py`
  - 输出共享导入记录。
- Modify: `packages/api/app/exporters/base.py`
  - 以共享导入记录作为统一输入。
- Modify: `packages/api/app/exporters/jsonl_exporter.py`
  - 从共享导入记录导出 JSONL。
- Modify: `packages/api/app/exporters/csv_exporter.py`
  - 从共享导入记录导出 CSV。
- Create: `packages/api/tests/contract/test_graph_shared_model_contract.py`
  - 校验 API graph schema 与共享模型边界。
- Modify: `packages/api/tests/unit/kg/test_models.py`
  - 锁住 API 现有 KG edge superset 不被意外删除。
- Create: `packages/api/tests/contract/test_import_record_contract.py`
  - 校验导入导出链路使用共享导入记录。
- Create: `packages/data_ingestion/README.md`
  - 描述规则 + agent + 共享知识模型消费边界。
- Create: `packages/data_ingestion/pyproject.toml`
  - 数据采集子项目最小包配置。
- Create: `packages/data_ingestion/data_ingestion/__init__.py`
  - 子项目入口。
- Create: `packages/data_ingestion/data_ingestion/models.py`
  - 只承载来源适配与候选抽取辅助模型。
- Create: `packages/data_ingestion/tests/test_models.py`
  - 验证子项目直接消费共享知识模型。
- Create: `docs/acceptance/data-ingestion-and-knowledge-model.md`
  - 共享模型 -> API -> import/export -> data_ingestion 证据链。
- Create: `packages/api/app/pipeline/steps/base.py`
  - 固定步骤处理器协议与辅助上下文。
- Create: `packages/api/app/pipeline/steps/source_ingest.py`
  - 生成来源接入预览。
- Create: `packages/api/app/pipeline/steps/source_preview.py`
  - 生成原始内容预览。
- Create: `packages/api/app/pipeline/steps/normalize.py`
  - 生成规范化清洗预览。
- Create: `packages/api/app/pipeline/steps/extract.py`
  - 生成结构抽取预览。
- Modify: `packages/api/app/pipeline/steps/map_to_knowledge_model.py`
  - 改为消费前序提取结果并严格校验共享模型边界。
- Create: `packages/api/app/pipeline/steps/human_review.py`
  - 生成人工确认与修订预览。
- Create: `packages/api/app/pipeline/steps/export_step.py`
  - 生成导出 / 入库预览。
- Create: `packages/api/app/pipeline/adapters/__init__.py`
  - 来源适配器注册入口。
- Create: `packages/api/app/pipeline/adapters/base.py`
  - 来源适配器协议。
- Create: `packages/api/app/pipeline/adapters/manual.py`
  - 支持当前 `source_type=manual` 主路径。
- Create: `packages/api/app/pipeline/adapters/jsonl.py`
  - 支持当前 `source_type=jsonl` 的最小文件来源主路径。
- Create: `packages/api/app/pipeline/adapters/csv.py`
  - 支持当前 `source_type=csv` 的最小文件来源主路径。
- Create: `packages/api/app/pipeline/adapters/huggingface.py`
  - 支持当前 `source_type=huggingface` 的最小 locator 校验与预览摘要。
- Modify: `packages/api/app/pipeline/service.py`
  - 通过步骤注册表和适配器驱动 7 步预览，而不是只给 summary 占位。
- Modify: `packages/api/app/pipeline/steps/__init__.py`
  - 汇总步骤处理器。
- Modify: `packages/api/tests/unit/pipeline/test_service.py`
  - 覆盖 7 步固定模板、适配器分发、前后步骤数据衔接。
- Modify: `packages/api/tests/api/test_pipeline_routes.py`
  - 覆盖多步骤预览与 map step 边界校验。
- Create: `docs/acceptance/data-pipeline-workbench-mainline.md`
  - 数据工作台主链路验收。
- Modify: `docs/acceptance/README.md`
  - 由主代理统一收录新增验收文档入口。
- Modify: `docs/verification-matrix.md`
  - 由主代理统一对齐最终验证口径。
- Modify: `docs/superpowers/plans/2026-03-23-data-pipeline-workbench.md`
  - 由主代理统一回填已完成 / 本轮完成的实施证据与验证结果。
- Modify: `docs/superpowers/plans/2026-03-23-knowledge-model-and-data-ingestion.md`
  - 由主代理统一回填已完成 / 本轮完成的实施证据与验证结果。

## Parallelization Layout

- **Worktree A / shared-model-lane**
  - 只负责 `packages/knowledge_model/`、`packages/data_ingestion/`、`packages/api/app/models/enums.py`、`packages/api/app/models/__init__.py`、`packages/api/app/schemas/graph.py`、`packages/api/app/importers/**`、`packages/api/app/exporters/**`、`docs/acceptance/data-ingestion-and-knowledge-model.md`。
- **Worktree B / pipeline-lane**
  - 只负责 `packages/api/app/pipeline/**`、`packages/api/tests/unit/pipeline/**`、`packages/api/tests/api/test_pipeline_routes.py`、`docs/acceptance/data-pipeline-workbench-mainline.md`。
- **Main agent**
  - 负责计划审阅、worktree 创建、分发、集成、冲突处理、`docs/acceptance/README.md`、`docs/verification-matrix.md`、两份历史计划回填、统一验证和最终交付。
- **Ownership hard rule**
  - 凡是需要改 `packages/knowledge_model/` 公共枚举/模型的变更，一律归 Worktree A。
  - 凡是需要改 `source_type` 读取逻辑与 pipeline 来源兼容层的变更，一律归 Worktree B；不要两边同时碰来源契约。

## Non-Goals

- 不在本轮接入生产级批量调度、任务队列或异步作业系统。
- 不在本轮做前端页面大改版；工作台页面只消费已经暴露的预览结构。
- 不在本轮把全部 graph schema 都彻底替换为共享模型的判别联合；优先保证 API 主契约与导入记录边界一致。
- 不在本轮做全部外部数据源接入；`data_ingestion` 只建立最小可验证骨架。

---

### Task 1: Migrate API Graph Contract to the Shared Knowledge Model

**Files:**
- Modify: `packages/api/app/models/enums.py`
- Modify: `packages/api/app/models/__init__.py`
- Modify: `packages/api/app/schemas/graph.py`
- Modify: `packages/api/app/schemas/__init__.py`
- Create: `packages/api/tests/contract/test_graph_shared_model_contract.py`
- Modify: `packages/api/tests/api/test_graph_routes.py`
- Modify: `packages/api/tests/unit/kg/test_models.py`

- [ ] **Step 1: Write the failing contract test**

```python
from knowledge_model.constants import NodeType
from app.schemas.graph import HerbNode


def test_herb_node_annotation_uses_shared_node_type():
    assert HerbNode.model_fields["type"].annotation is NodeType
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/contract/test_graph_shared_model_contract.py -q
```

Workdir: `packages/api`

Expected: FAIL，因为当前字段注解仍来自 API 本地枚举别名，而不是共享包对象。

- [ ] **Step 3: Write minimal implementation**

实现要求：

- `packages/api/app/schemas/graph.py` 直接从 `knowledge_model` 复用 `NodeType` / `NodeStatus` 与能复用的节点模型
- 只保留 API 响应必须的包装层，不再维护平行值域
- `EdgeType` 先保持 API superset；`PARENT_OF` / `CHILD_OF` 等 API-only edge 不能被意外删除
- shared contract test 只锁共享子集一致性，不要求 API edge 立刻与共享包完全同构
- `app.models.enums` 与 `app.models` 继续稳定 re-export `NodeType` / `EdgeType` / `NodeStatus`
- 保证现有 `test_graph_routes.py` 主链路不回归

- [ ] **Step 4: Run targeted tests to verify they pass**

Run:

```bash
uv run pytest tests/contract/test_graph_shared_model_contract.py tests/api/test_graph_routes.py tests/unit/kg/test_models.py -q
```

Workdir: `packages/api`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/models/enums.py packages/api/app/models/__init__.py packages/api/app/schemas/graph.py packages/api/app/schemas/__init__.py packages/api/tests/contract/test_graph_shared_model_contract.py packages/api/tests/api/test_graph_routes.py packages/api/tests/unit/kg/test_models.py
git commit -m "refactor(api): align graph contract with shared knowledge model"
```

### Task 2: Migrate Importers and Exporters to Shared Import Records

**Files:**
- Modify: `packages/api/app/importers/base.py`
- Modify: `packages/api/app/importers/__init__.py`
- Modify: `packages/api/app/importers/jsonl_importer.py`
- Modify: `packages/api/app/importers/csv_importer.py`
- Modify: `packages/api/app/exporters/base.py`
- Modify: `packages/api/app/exporters/jsonl_exporter.py`
- Modify: `packages/api/app/exporters/csv_exporter.py`
- Create: `packages/api/tests/contract/test_import_record_contract.py`

- [ ] **Step 1: Write the failing importer/exporter contract test**

```python
from app.importers.jsonl_importer import JSONLImporter
from knowledge_model.import_records import GraphImportRecord


def test_jsonl_importer_returns_shared_record(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text('{"node_type":"Herb","node_name":"陈皮","source":"中国药典"}\n', encoding="utf-8")
    record = next(JSONLImporter().load(str(path)))
    assert isinstance(record, GraphImportRecord)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/contract/test_import_record_contract.py -q
```

Workdir: `packages/api`

Expected: FAIL，因为导入器仍输出本地 `GraphRecord`。

- [ ] **Step 3: Write minimal implementation**

实现要求：

- 导入器统一输出 `GraphImportRecord`
- 导出器统一消费 `GraphImportRecord`
- `packages/api/app/importers/__init__.py` 保持对外导出兼容，不让调用方悬空
- 保持当前 CSV / JSONL 样例格式兼容；必要时在 base 层做字段转换

- [ ] **Step 4: Run targeted tests to verify they pass**

Run:

```bash
uv run pytest tests/contract/test_import_record_contract.py tests/api/test_graph_routes.py -q
```

Workdir: `packages/api`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/importers/base.py packages/api/app/importers/__init__.py packages/api/app/importers/jsonl_importer.py packages/api/app/importers/csv_importer.py packages/api/app/exporters/base.py packages/api/app/exporters/jsonl_exporter.py packages/api/app/exporters/csv_exporter.py packages/api/tests/contract/test_import_record_contract.py
git commit -m "refactor(import): use shared graph import records"
```

### Task 3: Bootstrap the `data_ingestion` Subproject Boundary

**Files:**
- Create: `packages/data_ingestion/README.md`
- Create: `packages/data_ingestion/pyproject.toml`
- Create: `packages/data_ingestion/data_ingestion/__init__.py`
- Create: `packages/data_ingestion/data_ingestion/models.py`
- Create: `packages/data_ingestion/tests/test_models.py`

- [ ] **Step 1: Write the failing boundary test**

```python
from data_ingestion.models import ExtractionCandidate
from knowledge_model.constants import NodeType


def test_extraction_candidate_targets_shared_node_type():
    candidate = ExtractionCandidate(
        node_type=NodeType.HERB,
        node_name="陈皮",
        source_name="中国药典",
    )
    assert candidate.node_type == NodeType.HERB
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run --with pytest pytest tests/test_models.py -q
```

Workdir: `packages/data_ingestion`

Expected: FAIL，因为子项目尚不存在。

- [ ] **Step 3: Write minimal implementation**

实现要求：

- `README` 明确“规则 + agent + 统一中间格式 + 共享图模型”的边界
- `models.py` 只定义来源适配 / 候选抽取模型，不重新定义图模型
- `pyproject.toml` 至少能本地跑通 `pytest`

- [ ] **Step 4: Run targeted tests to verify they pass**

Run:

```bash
uv run --with pytest pytest tests/test_models.py -q
```

Workdir: `packages/data_ingestion`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add packages/data_ingestion
git commit -m "feat(ingestion): add data ingestion subproject scaffold"
```

### Task 4: Replace Pipeline Placeholder Steps with Registered Step Handlers

**Files:**
- Create: `packages/api/app/pipeline/steps/base.py`
- Create: `packages/api/app/pipeline/steps/source_ingest.py`
- Create: `packages/api/app/pipeline/steps/source_preview.py`
- Create: `packages/api/app/pipeline/steps/normalize.py`
- Create: `packages/api/app/pipeline/steps/extract.py`
- Modify: `packages/api/app/pipeline/steps/map_to_knowledge_model.py`
- Create: `packages/api/app/pipeline/steps/human_review.py`
- Create: `packages/api/app/pipeline/steps/export_step.py`
- Modify: `packages/api/app/pipeline/steps/__init__.py`
- Modify: `packages/api/app/pipeline/service.py`
- Modify: `packages/api/tests/unit/pipeline/test_service.py`
- Modify: `packages/api/tests/api/test_pipeline_routes.py`

- [ ] **Step 1: Write the failing multi-step preview tests**

```python
def test_preview_returns_step_specific_payloads():
    ...


def test_extract_step_feeds_map_step_validation():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py -q
```

Workdir: `packages/api`

Expected: FAIL，因为除映射步骤外其余步骤仍使用通用 summary 占位。

- [ ] **Step 3: Write minimal implementation**

实现要求：

- 用步骤注册表替代 `service.py` 里的单一 if/else 分支
- `source_ingest` / `source_preview` / `normalize` / `extract` / `human_review` / `export` 都返回各自的 `preview_kind` 与结构化 `preview_payload`
- `extract` 必须为 `map_to_knowledge_model` 提供稳定候选输入
- `map_to_knowledge_model` 继续禁止绕过共享模型校验进入下一步

- [ ] **Step 4: Run targeted tests to verify they pass**

Run:

```bash
uv run pytest tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py -q
```

Workdir: `packages/api`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/pipeline/steps/base.py packages/api/app/pipeline/steps/source_ingest.py packages/api/app/pipeline/steps/source_preview.py packages/api/app/pipeline/steps/normalize.py packages/api/app/pipeline/steps/extract.py packages/api/app/pipeline/steps/map_to_knowledge_model.py packages/api/app/pipeline/steps/human_review.py packages/api/app/pipeline/steps/export_step.py packages/api/app/pipeline/steps/__init__.py packages/api/app/pipeline/service.py packages/api/tests/unit/pipeline/test_service.py packages/api/tests/api/test_pipeline_routes.py
git commit -m "feat(pipeline): register fixed step handlers"
```

### Task 5: Add Source Adapters for the Pipeline Entry Step

**Files:**
- Create: `packages/api/app/pipeline/adapters/__init__.py`
- Create: `packages/api/app/pipeline/adapters/base.py`
- Create: `packages/api/app/pipeline/adapters/manual.py`
- Create: `packages/api/app/pipeline/adapters/jsonl.py`
- Create: `packages/api/app/pipeline/adapters/csv.py`
- Create: `packages/api/app/pipeline/adapters/huggingface.py`
- Modify: `packages/api/app/pipeline/service.py`
- Modify: `packages/api/tests/unit/pipeline/test_service.py`
- Modify: `packages/api/tests/api/test_pipeline_routes.py`

- [ ] **Step 1: Write the failing adapter dispatch tests**

```python
def test_manual_source_builds_text_preview():
    ...


def test_jsonl_source_reads_local_file_preview(tmp_path):
    ...


def test_csv_source_builds_file_preview(tmp_path):
    ...


def test_huggingface_source_builds_locator_preview():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/unit/pipeline/test_service.py -q
```

Workdir: `packages/api`

Expected: FAIL，因为当前 `source_type` 还没有适配器分发。

- [ ] **Step 3: Write minimal implementation**

实现要求：

- 保持现有外部 contract，不收窄 `source_type`；至少覆盖 `manual` / `jsonl` / `csv` / `huggingface`
- `manual` 适配器直接把 `source_locator` 当作原始文本来源
- `jsonl` / `csv` 适配器只做本地文件存在性与前几行预览，不做批量导入
- `huggingface` 适配器只做 locator 格式校验与预览摘要，不做真实远端抓取
- service 在 `source_ingest` / `source_preview` 阶段通过适配器读取来源，不在步骤里直接猜测来源类型

- [ ] **Step 4: Run targeted tests to verify they pass**

Run:

```bash
uv run pytest tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py -q
```

Workdir: `packages/api`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/pipeline/adapters/__init__.py packages/api/app/pipeline/adapters/base.py packages/api/app/pipeline/adapters/manual.py packages/api/app/pipeline/adapters/jsonl.py packages/api/app/pipeline/adapters/csv.py packages/api/app/pipeline/adapters/huggingface.py packages/api/app/pipeline/service.py packages/api/tests/unit/pipeline/test_service.py packages/api/tests/api/test_pipeline_routes.py
git commit -m "feat(pipeline): add source adapters for preview flow"
```

### Task 6: Add Acceptance Coverage for the Shared-Model Mainline

**Files:**
- Create: `docs/acceptance/data-ingestion-and-knowledge-model.md`

- [ ] **Step 1: Write the acceptance outline before implementation**

检查点：

- 共享知识模型包可导入并被 API 使用
- 导入器 / 导出器消费共享导入记录
- `data_ingestion` 子项目直接消费共享模型

- [ ] **Step 2: Verify docs are missing or incomplete**

Run:

```bash
test -f docs/acceptance/data-ingestion-and-knowledge-model.md
```

Expected: non-zero exit code，或文档尚未覆盖完整证据链。

- [ ] **Step 3: Write minimal documentation updates**

实现要求：

- 验收文档明确前置条件、步骤、期望结果、证据、风险
- 只写共享模型主线，不改目录索引、验证矩阵和历史计划

- [ ] **Step 4: Run docs verification**

Run:

```bash
test -f docs/acceptance/data-ingestion-and-knowledge-model.md
rg -n "共享图模型|数据采集|导入记录" docs/acceptance/data-ingestion-and-knowledge-model.md
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add docs/acceptance/data-ingestion-and-knowledge-model.md
git commit -m "docs(acceptance): add shared model mainline coverage"
```

### Task 7: Add Acceptance Coverage for the Data Pipeline Workbench

**Files:**
- Create: `docs/acceptance/data-pipeline-workbench-mainline.md`

- [ ] **Step 1: Write the acceptance outline before implementation**

检查点：

- `pipeline` 七步预览、人工放行、回退主路径可复现
- 第 5 步共享模型映射未通过时不能确认进入下一步

- [ ] **Step 2: Verify doc is missing or incomplete**

Run:

```bash
test -f docs/acceptance/data-pipeline-workbench-mainline.md
```

Expected: non-zero exit code，或文档尚未覆盖完整工作台主链路。

- [ ] **Step 3: Write minimal documentation update**

实现要求：

- 只写工作台主线，不改目录索引、验证矩阵和历史计划
- 明确前置条件、步骤、期望结果、证据、风险

- [ ] **Step 4: Run docs verification**

Run:

```bash
test -f docs/acceptance/data-pipeline-workbench-mainline.md
rg -n "数据处理工作台|七步|人工放行" docs/acceptance/data-pipeline-workbench-mainline.md
```

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add docs/acceptance/data-pipeline-workbench-mainline.md
git commit -m "docs(acceptance): add pipeline workbench mainline coverage"
```

### Task 8: Main-Agent Integration for Docs Indexes, Verification Matrix, and Historical Plan Backfill

**Files:**
- Modify: `docs/acceptance/README.md`
- Modify: `docs/verification-matrix.md`
- Modify: `docs/superpowers/plans/2026-03-23-data-pipeline-workbench.md`
- Modify: `docs/superpowers/plans/2026-03-23-knowledge-model-and-data-ingestion.md`

- [ ] **Step 1: Wait for lane outputs and list evidence paths**

检查点：

- Lane A 已产出共享模型验收文档与相关验证结果
- Lane B 已产出工作台验收文档与相关验证结果
- 两条线的最终验证命令和结果都可追溯

- [ ] **Step 2: Write the integration updates**

实现要求：

- `docs/acceptance/README.md` 只追加入口索引，不重写既有结构
- `docs/verification-matrix.md` 对齐本轮实际验证命令：API 最低验证、web 定向测试与构建、文档校验
- 两份历史计划文档回填“已完成 / 验证结果 / 风险”，不把未完成项写成 done

- [ ] **Step 3: Run docs verification**

Run:

```bash
rg -n "data-ingestion-and-knowledge-model|data-pipeline-workbench-mainline" docs/acceptance/README.md
rg -n "ruff check app tests|ty check|pytest -m \"not integration\"|DataPipelinePage.test.tsx|vp build" docs/verification-matrix.md
rg -n "已完成|验证结果|风险" docs/superpowers/plans/2026-03-23-data-pipeline-workbench.md docs/superpowers/plans/2026-03-23-knowledge-model-and-data-ingestion.md
```

Expected: PASS。

- [ ] **Step 4: Commit**

```bash
git add docs/acceptance/README.md docs/verification-matrix.md docs/superpowers/plans/2026-03-23-data-pipeline-workbench.md docs/superpowers/plans/2026-03-23-knowledge-model-and-data-ingestion.md
git commit -m "docs(plans): backfill pipeline and ingestion evidence"
```

## Verification Bundle

所有任务完成后，统一执行：

```bash
uv run ruff check app tests
```

Workdir: `packages/api`

```bash
uv run ty check
```

Workdir: `packages/api`

```bash
uv run pytest -m "not integration"
```

Workdir: `packages/api`

```bash
uv run --with pytest pytest tests -q
```

Workdir: `packages/knowledge_model`

```bash
uv run --with pytest pytest tests -q
```

Workdir: `packages/data_ingestion`

```bash
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
```

```bash
pnpm --dir packages/web exec vp build
```

```bash
rg -n "pass|fail|risk" docs/acceptance --type md
rg -n "data-ingestion-and-knowledge-model|data-pipeline-workbench-mainline" docs/acceptance/README.md
```
