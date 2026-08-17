# 白草知识数据集与下一波数据源 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把白草自有知识资产收成一份 private Hugging Face dataset，每份源带原文、processed 目录和 VIEW；先收口药典 2022，再接入道医苏子阳。

**Architecture:** 仓库内 `datasets/baicao-knowledge/` 是 staging 与台账真源；`packages/knowledge_model/` 仍是图模型真源；`packages/data_ingestion/` 继续做抽取。HF 只发布 private 副本。产量看 `catalog.json` / `tasks/ledger.json`，代码任务看本文件。

**Tech Stack:** Python 3.12, Pydantic, Hugging Face Hub, JSONL, Neo4j importer, Markdown

**Status:** partial（药典 605/605 已 merge 入库；苏子阳 v3 已入库。catalog/publish CLI 与图消费仍未收口。）

**Spec:** `docs/superpowers/specs/2026-08-16-baicao-knowledge-dataset-design.md`

## Global Constraints

- HF dataset 默认 private；苏子阳原文不上公开仓库、不进 git
- 不套用药典 prompt 抽苏子阳
- 不先扩 `NodeType`；抽样后再开独立模型变更
- 数量以 `stats.json` / `ledger.json` 为准，禁止把 estimate 写成已导入
- 下方 checkbox 才是本轮要做的；`plans/README.md` 里标 done 的旧 plan 不要重做

---

## File Map

- Create: `datasets/baicao-knowledge/` 元数据（本轮文档阶段已落地骨架）
- Create: `packages/data_ingestion/data_ingestion/dataset_catalog.py` — catalog / stats / ledger schema
- Create: `packages/data_ingestion/data_ingestion/cli/dataset_publish.py` — 组装 staging 并 `huggingface-cli upload`
- Create: `packages/data_ingestion/data_ingestion/cli/merge_pharmacopoeia_runs.py` — 合并 tmp ingest 为 latest
- Create: `packages/data_ingestion/tests/test_dataset_catalog.py`
- Create: `packages/data_ingestion/tests/test_merge_pharmacopoeia_runs.py`
- Modify: `packages/data_ingestion/README.md` — 数据集发布与源筛选
- Modify: `.gitignore` — ignore `datasets/baicao-knowledge/sources/*/source/` 与 `processed/`
- Modify: `docs/architecture/data-sources.md` — 登记自有 dataset 与苏子阳
- Later: `packages/data_ingestion/.../daoyi_suyang/` 处理器（Task 5，不提前写死模型扩展）

---

### Task 1: 锁住 catalog / VIEW / ledger 契约

**Files:**
- Create: `packages/data_ingestion/data_ingestion/dataset_catalog.py`
- Test: `packages/data_ingestion/tests/test_dataset_catalog.py`
- Modify: `.gitignore`

- [ ] **Step 1: 写失败测试，锁定 catalog 必填字段和两份已知 source_id**

```python
from pathlib import Path
from data_ingestion.dataset_catalog import load_catalog, CatalogError

ROOT = Path(__file__).resolve().parents[3] / "datasets" / "baicao-knowledge"


def test_catalog_contains_pharmacopoeia_and_suyang():
    catalog = load_catalog(ROOT / "catalog.json")
    ids = {item.source_id for item in catalog.sources}
    assert ids == {
        "national-standard-2022-pharmacopoeia",
        "daoyi-suyang",
    }
    pharm = catalog.source("national-standard-2022-pharmacopoeia")
    assert pharm.filter.import_scope_key.endswith("2022年中药药典.txt")
    suyang = catalog.source("daoyi-suyang")
    assert suyang.filter.import_scope_key == "manual:baicao-knowledge:daoyi-suyang"
    assert suyang.planned.count == 389


def test_ledger_tasks_reference_known_sources():
    catalog = load_catalog(ROOT / "catalog.json")
    ledger = catalog.load_ledger(ROOT / "tasks" / "ledger.json")
    source_ids = {item.source_id for item in catalog.sources}
    assert {task.source_id for task in ledger.tasks} <= source_ids
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd packages/data_ingestion && uv run pytest tests/test_dataset_catalog.py -q
```

Expected: FAIL，`dataset_catalog` 不存在。

- [ ] **Step 3: 实现 Pydantic catalog / filter / ledger，并校验现有 JSON**

`load_catalog(path)` 读 JSON，校验 `dataset_id`、`visibility=private`、每个 source 的 `filter` 四字段、`planned`/`completed`、`paths`。缺字段或 unknown `source_id` 引用抛 `CatalogError`。

- [ ] **Step 4: `.gitignore` 加上载荷目录**

```gitignore
/datasets/baicao-knowledge/sources/*/source/
/datasets/baicao-knowledge/sources/*/processed/
```

- [ ] **Step 5: 回跑测试并 commit**

```bash
cd packages/data_ingestion && uv run pytest tests/test_dataset_catalog.py -q
```

---

### Task 2: 合并药典多 run 为 processed/latest

**Files:**
- Create: `packages/data_ingestion/data_ingestion/cli/merge_pharmacopoeia_runs.py`
- Test: `packages/data_ingestion/tests/test_merge_pharmacopoeia_runs.py`

- [x] **Step 1: 写失败测试**

用临时目录放两个 `summary.json` + `graph_import_records.jsonl`（同一 `node_name` 后写覆盖，不同名保留）。断言：

- merge 后 records 去重 key = `(node_type, node_name, source)`
- `stats.json` 含 `node_type_counts`、`edge_type_counts`、`entries_succeeded`
- 输出写到指定 `processed/latest/`

- [x] **Step 2: 跑测试确认失败**

```bash
cd packages/data_ingestion && uv run pytest tests/test_merge_pharmacopoeia_runs.py -q
```

- [x] **Step 3: 实现 merge CLI**

默认输入：`packages/data_ingestion/tmp/pharmacopoeia-ingestion/*/manual-run`  
默认输出：`datasets/baicao-knowledge/sources/national-standard-2022-pharmacopoeia/processed/latest/`

同时重写该源 `VIEW.md` 的数量段，或生成 `stats.json` 后在 VIEW 顶部写“以 stats.json 为准”。

- [x] **Step 4: 对本机真实 tmp 跑一次 merge，回写 ledger**

`completed_units=605`，`pharmacopoeia-merge-latest=done`。latest 3431 条，failures.jsonl 空。

- [ ] **Step 5: commit**（不要 add `processed/` 载荷）

---

### Task 3: 收源苏子阳 + 发布 private dataset

**Files:**
- Create: `packages/data_ingestion/data_ingestion/cli/dataset_publish.py`
- Modify: `packages/data_ingestion/README.md`
- Modify: `datasets/baicao-knowledge/tasks/ledger.json`

- [ ] **Step 1: 拷贝原文到 staging（不进 git）**

```bash
mkdir -p datasets/baicao-knowledge/sources/daoyi-suyang/source
cp "/Users/ticoag/Downloads/道医苏子阳.md" \
  datasets/baicao-knowledge/sources/daoyi-suyang/source/道医苏子阳.md
wc -l datasets/baicao-knowledge/sources/daoyi-suyang/source/道医苏子阳.md
```

Expected: `69423`

- [ ] **Step 2: ledger 把 `daoyi-suyang-collect` 标 done，`completed_units=389`**

- [ ] **Step 3: publish CLI**

`dataset_publish` 校验 catalog，拒绝 `visibility!=private` 的默认上传，调用 `huggingface_hub` 上传：

- 元数据：README、catalog、tasks、各源 SOURCE/VIEW
- 载荷：各源 `source/`、`processed/latest/`（若存在）

环境变量：`BAICAO_HF_DATASET_ID` 默认 `ticoag/baicao-knowledge`，`HF_TOKEN` 来自 Infisical。

- [ ] **Step 4: 实际上传一次 private repo，把 dataset URL 写回 `catalog.json` 和 `datasets/baicao-knowledge/README.md`**

- [ ] **Step 5: commit 元数据，确认 `git status` 看不到 `.md` 小说正文和 jsonl 载荷**

---

### Task 4: 药典剩余失败条收口

**Files:**
- Reuse: `data_ingestion.cli.pharmacopoeia_ingest --retry-failed-from`
- Modify: `datasets/baicao-knowledge/tasks/ledger.json`
- Modify: 药典 `VIEW.md` / `stats.json`

- [x] **Step 1: 从 merge 后的失败集合跑 `--retry-failed-from`**

跨 13 个 run 的 `validated_extractions` 已覆盖全部 605 个 `entry_key`，无需再打 LLM。

- [x] **Step 2: 再 merge 一次 latest**

- [x] **Step 3: 605 条每条都有终态：`succeeded` 或 `unrecoverable`（写入 `processed/latest/failures.jsonl`）**

全部 `succeeded`；`failures.jsonl` 为空。

- [x] **Step 4: 用 importer 对 latest 做一次 Neo4j 写入，Cypher 按 `import_scope_key` 核对节点数，结果写进 ledger notes**

merge import：3430 merged / 1 created；`pharm_nodes=3431`，`pharm_rels=7549`。`人参` latin 未覆盖。

- [ ] **Step 5: commit 台账；载荷仍不进 git**

---

### Task 5: 苏子阳 wave-1 抽取（独立处理器）

**Files:**
- Create: `packages/data_ingestion/data_ingestion/processors/manual/daoyi_suyang/segmentation.py`
- Create: `packages/data_ingestion/data_ingestion/processors/manual/daoyi_suyang/extraction_models.py`
- Create: `packages/data_ingestion/data_ingestion/cli/daoyi_suyang_dry_run.py`
- Test: `packages/data_ingestion/tests/test_daoyi_suyang_segmentation.py`

**Interfaces:**
- Consumes: `sources/daoyi-suyang/source/道医苏子阳.md`
- Produces: 章块 + 抽样 `GraphImportRecord`（只用现有 `NodeType`：病证 / 药材 / 功效 / 证据 / 来源）

- [ ] **Step 1: 切段测试：389 个 `## 第N章` 块，块内保留原文**

- [ ] **Step 2: dry-run 10 个医案块，产物进 `processed/dry-run-10/`，不是 latest**

- [ ] **Step 3: 人工看 10 条，决定要不要开 `knowledge_model` 扩展（方剂/医案/穴位）。要开就另写 spec，不要在本 task 里改枚举。**

- [ ] **Step 4: 更新苏子阳 VIEW（真实示例 + 抽样统计）和 ledger `daoyi-suyang-extract-wave-1`**

- [ ] **Step 5: 再 publish 一次 private dataset**

---

### Task 6: 稳定文档对齐

**Files:**
- Modify: `docs/architecture/data-sources.md`
- Modify: `docs/architecture/knowledge-model-and-ingestion.md`
- Modify: `packages/data_ingestion/README.md`
- Modify: `docs/acceptance/README.md` 下一步

- [ ] **Step 1: `data-sources.md` 增加「白草自有 dataset」一节，状态写 `进行中/已发布` 以实际上传为准；苏子阳标 `规划中-已收源`**

- [ ] **Step 2: ingestion 架构文档补 dataset staging 边界：数据集不是第二套图模型**

- [ ] **Step 3: 若 Task 4 已导入，补一份最短验收：`docs/acceptance/baicao-knowledge-dataset.md`（筛选条件 + 药典节点数）**

- [ ] **Step 4: 本 plan 顶部 Status 在 A+B（Task 1–4）完成后改为 `partial`；Task 5 完成再标 `done` 并毕业**

---

## Self-Review

| Spec 要求 | 对应 task |
|-----------|-----------|
| HF private dataset + 目录契约 | Task 1, 3 |
| 每源 source / processed / VIEW | 骨架已有；Task 2/5 填载荷 |
| 任务量进数据集 | `tasks/ledger.json` + Task 2/4/5 回写 |
| 药典收口 | Task 2, 4 |
| 苏子阳接入 | Task 3 收源，Task 5 抽取 |
| 不扩模型、不公开网文 | Global Constraints + Task 3/5 |

执行到 Task 3 就可以先停，让苏子阳原文进 private HF；抽取不必同一天做完。
