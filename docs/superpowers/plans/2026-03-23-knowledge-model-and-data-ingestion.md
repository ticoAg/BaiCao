# Knowledge Model And Data Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 BaiCao 建立仓库级图模型唯一真源，并把数据采集明确为依赖该真源的二级子项目，为后续规则 + agent 的非结构化知识处理链路打下共享结构基础。

**Architecture:** 新增一个独立共享 Python 包承载节点类型、关系类型、知识结构定义、导入中间模型和中文映射；API、导入器与后续数据采集子项目逐步迁移为消费该共享包。稳定架构文档只负责解释边界与术语，不再承担可执行真源角色。

**Tech Stack:** Python 3.12, Pydantic v2, StrEnum, Literal, FastAPI, TypeScript, Markdown, Mermaid

---

## 实施状态更新（2026-03-25）

### 已完成

- 共享知识模型包已经落地并作为仓库内结构真源使用，见 `packages/knowledge_model/knowledge_model/constants.py`、`packages/knowledge_model/knowledge_model/import_records.py`、`packages/knowledge_model/knowledge_model/schema.py`
- API graph schema 已直接复用共享 `NodeType` / `NodeStatus`，同时保留 API `EdgeType` superset，见 `packages/api/app/models/enums.py`、`packages/api/app/schemas/graph.py`
- importer / exporter 已统一切到共享 `GraphImportRecord`，并保留 `app.importers` 的兼容导出，见 `packages/api/app/importers/` 与 `packages/api/app/exporters/`
- `packages/data_ingestion/` 子项目骨架已建立，并直接消费共享 `NodeType`，见 `packages/data_ingestion/data_ingestion/models.py`
- 本轮新增共享模型主链路验收文档，见 `docs/acceptance/data-ingestion-and-knowledge-model.md`

### 验证结果

- `cd packages/api && uv run pytest tests/contract/test_graph_shared_model_contract.py tests/api/test_graph_routes.py tests/unit/kg/test_models.py -q` → `18 passed`
- `cd packages/api && uv run pytest tests/contract/test_import_record_contract.py tests/api/test_graph_routes.py -q` → `15 passed`
- `cd packages/api && uv run pytest tests/contract/test_graph_shared_model_contract.py tests/contract/test_import_record_contract.py tests/api/test_graph_routes.py tests/unit/kg/test_models.py -q` → `21 passed`
- `cd packages/data_ingestion && uv run --with pytest pytest tests/test_models.py -q` → `1 passed`

### 风险

- 当前验收主要覆盖 contract / unit 层，未补充更高层 API 全量验证、真实导入执行与浏览器端人工验收
- API `EdgeType` 仍保留 superset 策略；shared 与 API edge 的完全收敛不在本轮范围
- 历史步骤中的 checkbox 未逐项回填；本节作为当前已实现事实与验证证据的聚合更新

## File Map

- Create: `packages/knowledge_model/pyproject.toml`
  - 定义共享图模型包的最小 Python 包配置。
- Create: `packages/knowledge_model/knowledge_model/__init__.py`
  - 对外导出节点类型、关系类型、结构定义与导入模型。
- Create: `packages/knowledge_model/knowledge_model/constants.py`
  - 承载 `StrEnum`、`Literal` 值域、字段键集合。
- Create: `packages/knowledge_model/knowledge_model/node_models.py`
  - 定义节点类型与节点属性 `pydantic` 模型。
- Create: `packages/knowledge_model/knowledge_model/edge_models.py`
  - 定义关系类型与关系属性 `pydantic` 模型。
- Create: `packages/knowledge_model/knowledge_model/schema.py`
  - 定义联合类型、注册表、校验入口与结构元数据。
- Create: `packages/knowledge_model/knowledge_model/import_records.py`
  - 定义面向采集与导入的统一中间格式。
- Create: `packages/knowledge_model/knowledge_model/labels.py`
  - 定义中文主称、展示名、技术标识映射。
- Create: `packages/knowledge_model/tests/test_constants.py`
  - 覆盖节点、关系、中文映射和值域约束。
- Create: `packages/knowledge_model/tests/test_schema.py`
  - 覆盖联合类型、模型校验、导入中间格式。
- Modify: `packages/api/app/models/enums.py`
  - 改为从共享包消费或至少与共享包对齐，逐步收缩本地枚举。
- Modify: `packages/api/app/schemas/graph.py`
  - 改为复用共享图模型中的节点、关系和导入记录结构。
- Modify: `packages/api/app/importers/base.py`
  - 改为消费共享导入中间模型，而不是继续维护本地平行结构。
- Modify: `packages/api/app/importers/jsonl_importer.py`
  - 改为把 JSONL 解析为共享导入记录。
- Modify: `packages/api/app/importers/csv_importer.py`
  - 改为把 CSV 解析为共享导入记录。
- Create: `packages/data_ingestion/README.md`
  - 建立数据采集二级子项目入口和边界说明。
- Create: `packages/data_ingestion/pyproject.toml`
  - 建立数据采集子项目最小包配置。
- Create: `packages/data_ingestion/data_ingestion/__init__.py`
  - 建立数据采集包入口。
- Create: `packages/data_ingestion/data_ingestion/models.py`
  - 定义来源适配与采集任务侧的辅助模型，依赖共享图模型。
- Create: `packages/data_ingestion/tests/test_models.py`
  - 验证数据采集子项目对共享模型的消费边界。
- Modify: `docs/architecture/README.md`
  - 收录新的稳定架构文档。
- Modify: `docs/README.md`
  - 收录新的稳定架构文档与数据采集主线入口。
- Modify: `docs/architecture/data-model.md`
  - 增补“唯一真源与共享知识结构定义”的引用说明。
- Create: `docs/acceptance/data-ingestion-and-knowledge-model.md`
  - 建立共享图模型与数据采集主链路验收文档。

## Non-Goals

- 不在本计划内完成全部外部数据源接入。
- 不在本计划内完成 Hugging Face 数据集的正式导入。
- 不在本计划内做前端全面迁移。
- 不在本计划内实现所有 agent 抽取策略，只先建立共享边界和最小骨架。

## Implementation Notes

- 文档主叙述使用中文术语，但代码中的技术值保持英文稳定标识。
- 共享图模型包是唯一结构真源；其他模块只消费，不再定义长期平行模型。
- 若中文文件名对工具链兼容性不佳，实施时允许改用 ASCII 文件名，但中文语义必须保留在模型元数据与文档中。

---

### Task 1: Add the Stable Architecture Entry for the Shared Knowledge Model

**Files:**
- Modify: `docs/architecture/knowledge-model-and-ingestion.md`
- Modify: `docs/architecture/README.md`
- Modify: `docs/README.md`
- Modify: `docs/architecture/data-model.md`

- [ ] **Step 1: Write the failing docs consistency checklist**

在本任务开始前，先列出应满足的文档一致性检查：

- `docs/architecture/README.md` 能索引到新文档
- `docs/README.md` 能索引到新文档
- `docs/architecture/data-model.md` 至少有一处引用共享图模型唯一真源的新口径
- 新文档中明确“代码优先”“数据采集是消费者”“规则 + agent 混合模式”

- [ ] **Step 2: Run a docs grep check to verify the new entry is missing**

Run:

```bash
rg -n "图模型唯一真源|数据采集架构|知识结构定义" docs/architecture docs/README.md
```

Expected: 新口径尚未完整出现，或没有形成稳定入口。

- [ ] **Step 3: Write the architecture documentation**

实现要求：

- 在 `docs/architecture/knowledge-model-and-ingestion.md` 中说明共享图模型真源、中文语义、数据采集边界与处理流
- 在 `docs/architecture/README.md` 和 `docs/README.md` 中补索引
- 在 `docs/architecture/data-model.md` 中增补到新文档的引用说明

- [ ] **Step 4: Run the docs grep check to verify the new entry exists**

Run:

```bash
rg -n "图模型唯一真源|数据采集架构|知识结构定义" docs/architecture docs/README.md
```

Expected: 能看到新文档和引用入口。

- [ ] **Step 5: Commit**

```bash
git add docs/architecture/knowledge-model-and-ingestion.md docs/architecture/README.md docs/README.md docs/architecture/data-model.md
git commit -m "docs(architecture): define shared knowledge model and ingestion architecture"
```

### Task 2: Bootstrap the Shared Knowledge Model Package

**Files:**
- Create: `packages/knowledge_model/pyproject.toml`
- Create: `packages/knowledge_model/knowledge_model/__init__.py`
- Create: `packages/knowledge_model/knowledge_model/constants.py`
- Create: `packages/knowledge_model/knowledge_model/node_models.py`
- Create: `packages/knowledge_model/knowledge_model/edge_models.py`
- Create: `packages/knowledge_model/knowledge_model/schema.py`
- Create: `packages/knowledge_model/knowledge_model/import_records.py`
- Create: `packages/knowledge_model/knowledge_model/labels.py`
- Create: `packages/knowledge_model/tests/test_constants.py`
- Create: `packages/knowledge_model/tests/test_schema.py`

- [ ] **Step 1: Write the failing tests for the shared package**

```python
from knowledge_model.constants import NodeType, EdgeType
from knowledge_model.labels import NODE_TYPE_LABELS
from knowledge_model.import_records import GraphImportRecord


def test_node_type_has_herb():
    assert NodeType.HERB == "Herb"


def test_labels_expose_chinese_name():
    assert NODE_TYPE_LABELS[NodeType.HERB] == "药材"


def test_import_record_accepts_known_node_type():
    record = GraphImportRecord(node_type=NodeType.HERB, node_name="陈皮", source="中国药典")
    assert record.node_name == "陈皮"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest packages/knowledge_model/tests -q
```

Expected: FAIL because the shared package does not exist yet.

- [ ] **Step 3: Implement the shared knowledge model package**

实现要求：

- 使用 `StrEnum` 定义 `NodeType`、`EdgeType`、`NodeStatus` 等
- 使用 `Literal` 或判别联合约束关键值域
- 使用 `pydantic` 定义节点、关系、导入记录
- 提供中文名称映射
- 在 `__init__.py` 中导出主要模型与常量

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest packages/knowledge_model/tests -q
```

Expected: PASS，并能验证中文语义映射与导入中间格式。

- [ ] **Step 5: Commit**

```bash
git add packages/knowledge_model
git commit -m "feat(model): add shared knowledge model package"
```

### Task 3: Migrate API Graph Enums and Schemas to the Shared Package

**Files:**
- Modify: `packages/api/app/models/enums.py`
- Modify: `packages/api/app/schemas/graph.py`
- Modify: `packages/api/app/schemas/__init__.py`
- Modify: `packages/api/tests/**`

- [ ] **Step 1: Write failing API contract tests against the shared package**

```python
from knowledge_model.constants import NodeType
from app.schemas.graph import GraphRecord


def test_graph_record_uses_shared_node_type():
    record = GraphRecord(node_type=NodeType.HERB, node_name="陈皮", source="中国药典")
    assert record.node_type == NodeType.HERB
```

- [ ] **Step 2: Run the API tests to verify they fail**

Run:

```bash
pytest packages/api/tests -q
```

Expected: FAIL because API still uses local graph definitions.

- [ ] **Step 3: Replace local graph definitions with shared-package usage**

实现要求：

- 减少 `packages/api/app/models/enums.py` 中图谱相关本地定义
- 在 `packages/api/app/schemas/graph.py` 中复用共享图模型
- 保持现有 API 响应语义不意外回归

- [ ] **Step 4: Run the API tests to verify they pass**

Run:

```bash
pytest packages/api/tests -q
```

Expected: PASS，且 API 图谱结构改为消费共享包。

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/models/enums.py packages/api/app/schemas/graph.py packages/api/app/schemas/__init__.py packages/api/tests
git commit -m "refactor(api): consume shared knowledge model"
```

### Task 4: Migrate Importers to the Shared Import Record

**Files:**
- Modify: `packages/api/app/importers/base.py`
- Modify: `packages/api/app/importers/jsonl_importer.py`
- Modify: `packages/api/app/importers/csv_importer.py`
- Modify: `packages/api/app/exporters/base.py`
- Modify: `packages/api/app/exporters/jsonl_exporter.py`
- Modify: `packages/api/app/exporters/csv_exporter.py`
- Modify: `packages/api/tests/**`

- [ ] **Step 1: Write failing importer tests for the shared import record**

```python
from app.importers.jsonl_importer import JSONLImporter


def test_jsonl_importer_returns_shared_graph_import_record(tmp_path):
    ...
```

- [ ] **Step 2: Run importer tests to verify they fail**

Run:

```bash
pytest packages/api/tests -q
```

Expected: FAIL because importers still emit local record structures.

- [ ] **Step 3: Migrate importers and exporters**

实现要求：

- 导入器输出共享 `GraphImportRecord`
- 导出器消费共享 `GraphImportRecord`
- 保持现有 CSV / JSONL 样例格式的兼容性，必要时补转换层

- [ ] **Step 4: Run importer tests to verify they pass**

Run:

```bash
pytest packages/api/tests -q
```

Expected: PASS，并验证 CSV / JSONL 主路径未回归。

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/importers packages/api/app/exporters packages/api/tests
git commit -m "refactor(import): use shared graph import records"
```

### Task 5: Bootstrap the Data Ingestion Subproject Boundary

**Files:**
- Create: `packages/data_ingestion/README.md`
- Create: `packages/data_ingestion/pyproject.toml`
- Create: `packages/data_ingestion/data_ingestion/__init__.py`
- Create: `packages/data_ingestion/data_ingestion/models.py`
- Create: `packages/data_ingestion/tests/test_models.py`

- [ ] **Step 1: Write failing tests for the ingestion boundary**

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

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest packages/data_ingestion/tests -q
```

Expected: FAIL because the data ingestion package does not exist yet.

- [ ] **Step 3: Add the ingestion subproject skeleton**

实现要求：

- 在 README 中明确“规则 + agent + 统一中间格式 + 共享图模型”的边界
- 采集包中的模型只负责来源适配与候选抽取，不重新定义图模型

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest packages/data_ingestion/tests -q
```

Expected: PASS，并证明数据采集子项目直接消费共享图模型。

- [ ] **Step 5: Commit**

```bash
git add packages/data_ingestion
git commit -m "feat(ingestion): add data ingestion subproject scaffold"
```

### Task 6: Add Acceptance Coverage for the Shared-Model Mainline

**Files:**
- Create: `docs/acceptance/data-ingestion-and-knowledge-model.md`
- Modify: `docs/acceptance/README.md`
- Modify: `docs/verification-matrix.md`

- [ ] **Step 1: Write the acceptance outline before implementation**

列出以下主链路：

- 共享图模型包能被导入
- API 能消费共享图模型
- 导入器能输出共享导入记录
- 数据采集子项目能消费共享图模型

- [ ] **Step 2: Verify the acceptance doc does not yet exist**

Run:

```bash
test -f docs/acceptance/data-ingestion-and-knowledge-model.md
```

Expected: non-zero exit code because the doc is not created yet.

- [ ] **Step 3: Write the acceptance and verification docs**

实现要求：

- 在验收文档中写清楚共享模型、API、导入器、数据采集四段证据链
- 在 `docs/acceptance/README.md` 中补入口
- 在 `docs/verification-matrix.md` 中补该类改动的最低验证要求

- [ ] **Step 4: Verify the acceptance doc exists and is indexed**

Run:

```bash
test -f docs/acceptance/data-ingestion-and-knowledge-model.md
rg -n "data-ingestion-and-knowledge-model|知识模型" docs/acceptance/README.md docs/verification-matrix.md
```

Expected: PASS，并能看到入口索引。

- [ ] **Step 5: Commit**

```bash
git add docs/acceptance/data-ingestion-and-knowledge-model.md docs/acceptance/README.md docs/verification-matrix.md
git commit -m "docs(acceptance): add shared knowledge model mainline coverage"
```
