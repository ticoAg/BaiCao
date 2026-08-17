# 白草知识数据集与下一波数据源 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把已入库的药典 2022 与苏子阳 v3 收成可重复发布的 private HF dataset，并让 Graph Workbench / 问答能按方剂、医案、穴位、治法查询。

**Architecture:** `datasets/baicao-knowledge/` 是 staging 与产量台账；`packages/knowledge_model/` 是图模型真源；`packages/data_ingestion/` 负责抽取与发布 CLI。图已用中文标签/属性键。本轮不再抽新源、不再扩 `NodeType`。

**Tech Stack:** Python 3.12, Pydantic, Hugging Face Hub, Parquet, Neo4j, React / Vite

**Status:** partial（catalog/publish CLI 与 Workbench 查询消费已落地。private HF 实际上传被 Infisical TLS 证书过期阻塞。）

**Spec:** `docs/superpowers/specs/2026-08-16-baicao-knowledge-dataset-design.md`

## Global Constraints

- HF dataset 默认 private；id 锁定 `ticoAg/baicao-knowledge`；苏子阳原文不上公开仓库、不进 git
- 不要重做苏子阳抽取，不要再开药典 LLM ingest
- 不要再扩 `NodeType` / `EdgeType`；方剂、医案、穴位、治法已经在 `packages/knowledge_model/`
- 数量以 `stats.json` / `ledger.json` 为准，禁止把 estimate 写成已导入
- 入图不要用会 `SET n += props` 的 `app.importers.cli --neo4j`；用 `data_ingestion.cli.import_dataset_neo4j`
- 图存储键用中文；VIEW / 验收 Cypher 必须写 `导入源` / `导入范围键`，不要写 `import_source_id`
- 下方「不要再执行」里的历史 checkbox 不是本轮任务

---

## 不要再执行（已落地）

这些工作已经完成。不要按旧 Task 5 重抽，也不要回退「先别扩模型」。

| 项 | 证据 |
|----|------|
| 药典 605/605 merge + 入图 | `ledger.json` `pharmacopoeia-extract-605` / `pharmacopoeia-merge-latest`；latest 约 3431 条，近重复并点后图约 3427 |
| 苏子阳收源 389 章 | `daoyi-suyang-collect` |
| 苏子阳 v3 抽取 + 入图 | `daoyi-suyang-extract-wave-1` 1687 条；`daoyi-suyang-neo4j-import` |
| 模型已含方剂/医案/穴位/治法 | `packages/knowledge_model/knowledge_model/constants.py` |
| 中文图存储 + 近重复合并 | commit `4e23546`；`merge_near_duplicates` / `recreate_graph_store` / `text_normalize` |
| 验收 | `docs/acceptance/baicao-knowledge-dataset.md` 为 `pass` |

产量真源：`datasets/baicao-knowledge/catalog.json`、`tasks/ledger.json`（当前整目录被 `/datasets` gitignore，本轮 Task 1 要改）。

---

## File Map（剩余）

- Create: `packages/data_ingestion/data_ingestion/dataset_catalog.py`
- Create: `packages/data_ingestion/data_ingestion/cli/dataset_publish.py`
- Test: `packages/data_ingestion/tests/test_dataset_catalog.py`
- Test: `packages/data_ingestion/tests/test_dataset_publish.py`
- Modify: `.gitignore` — 只忽略载荷，元数据进 git
- Modify: `packages/data_ingestion/data_ingestion/cli/compute_dataset_stats.py` — VIEW Cypher 改中文键
- Modify: `packages/data_ingestion/README.md` — catalog / stats / parquet / publish
- Modify: `packages/api/app/kg/graph_service.py` — `QUERY_LABEL_DISPLAY` / `QUERY_REL_TYPE_DISPLAY`
- Modify: `packages/web/src/types/graph.ts` — 查询枚举、颜色、样式
- Modify: `packages/web/src/components/graph/GraphQueryPanel.tsx` — 下拉选项
- Modify: `packages/api/app/services/chat_agent_runtime/system_prompt.py`
- Test: `packages/api/tests/api/test_graph_routes.py`
- Modify: `docs/acceptance/baicao-knowledge-dataset.md` — 补查询/发布证据

---

### Task 1: catalog 契约 + private publish CLI

**Files:**
- Create: `packages/data_ingestion/data_ingestion/dataset_catalog.py`
- Create: `packages/data_ingestion/data_ingestion/cli/dataset_publish.py`
- Test: `packages/data_ingestion/tests/test_dataset_catalog.py`
- Test: `packages/data_ingestion/tests/test_dataset_publish.py`
- Modify: `.gitignore`
- Modify: `packages/data_ingestion/data_ingestion/cli/compute_dataset_stats.py`
- Modify: `packages/data_ingestion/README.md`

**Interfaces:**
- Consumes: `datasets/baicao-knowledge/catalog.json`、`tasks/ledger.json`、各源 `processed/latest/*.parquet`
- Produces: `load_catalog(path) -> Catalog`；`dataset_publish --dry-run` 列出将上传文件且拒绝非 private

- [x] **Step 1: 写 catalog 失败测试**

`packages/data_ingestion/tests/test_dataset_catalog.py`：

```python
import json
from pathlib import Path

import pytest

from data_ingestion.dataset_catalog import CatalogError, load_catalog, load_ledger

REPO = Path(__file__).resolve().parents[3]


def write_catalog(path: Path, **overrides) -> Path:
    body = {
        "dataset_id": "ticoAg/baicao-knowledge",
        "visibility": "private",
        "knowledge_model": "packages/knowledge_model",
        "updated_at": "2026-08-17",
        "sources": [
            {
                "source_id": "national-standard-2022-pharmacopoeia",
                "title": "2022年中药药典",
                "status": "imported",
                "kind": "pharmacopoeia_entries",
                "filter": {
                    "source_provider": "huggingface",
                    "dataset_name": "ZJUFanLab/TCMChat-dataset-600k",
                    "file_path": "pretrain/train/books/national_standard/2022年中药药典.txt",
                    "import_scope_key": "huggingface|ZJUFanLab/TCMChat-dataset-600k|pretrain/train/books/national_standard/2022年中药药典.txt",
                },
                "planned": {"unit": "entries", "count": 605},
                "completed": {"unit": "entries", "count": 605},
                "paths": {
                    "source_doc": "sources/national-standard-2022-pharmacopoeia/SOURCE.md",
                    "view": "sources/national-standard-2022-pharmacopoeia/VIEW.md",
                },
            },
            {
                "source_id": "daoyi-suyang",
                "title": "道医苏子阳",
                "status": "imported",
                "kind": "narrative_medical_cases",
                "filter": {
                    "source_provider": "manual",
                    "dataset_name": "baicao-knowledge",
                    "file_path": "sources/daoyi-suyang/source/道医苏子阳.md",
                    "import_scope_key": "manual:baicao-knowledge:daoyi-suyang",
                },
                "planned": {"unit": "chapters", "count": 389},
                "completed": {"unit": "chapters", "count": 389},
                "paths": {
                    "source_doc": "sources/daoyi-suyang/SOURCE.md",
                    "view": "sources/daoyi-suyang/VIEW.md",
                },
            },
        ],
    }
    body.update(overrides)
    path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    return path


def test_load_catalog_locks_private_and_two_sources(tmp_path: Path):
    catalog = load_catalog(write_catalog(tmp_path / "catalog.json"))
    assert catalog.dataset_id == "ticoAg/baicao-knowledge"
    assert catalog.visibility == "private"
    assert {item.source_id for item in catalog.sources} == {
        "national-standard-2022-pharmacopoeia",
        "daoyi-suyang",
    }
    assert catalog.source("daoyi-suyang").filter.import_scope_key == (
        "manual:baicao-knowledge:daoyi-suyang"
    )


def test_reject_public_visibility(tmp_path: Path):
    path = write_catalog(tmp_path / "catalog.json", visibility="public")
    with pytest.raises(CatalogError, match="private"):
        load_catalog(path)


def test_ledger_tasks_must_reference_known_sources(tmp_path: Path):
    catalog = load_catalog(write_catalog(tmp_path / "catalog.json"))
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-08-17",
                "repo_plan": "docs/superpowers/plans/2026-08-16-baicao-knowledge-dataset.md",
                "tasks": [
                    {
                        "task_id": "ghost",
                        "source_id": "not-a-source",
                        "status": "done",
                        "unit": "entries",
                        "planned_units": 1,
                        "completed_units": 1,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogError, match="not-a-source"):
        load_ledger(ledger_path, catalog)


@pytest.mark.skipif(
    not (REPO / "datasets/baicao-knowledge/catalog.json").exists(),
    reason="local dataset staging missing",
)
def test_repo_catalog_matches_known_sources():
    catalog = load_catalog(REPO / "datasets/baicao-knowledge/catalog.json")
    assert catalog.visibility == "private"
    assert catalog.dataset_id == "ticoAg/baicao-knowledge"
```

- [x] **Step 2: 跑测试确认失败**

```bash
cd packages/data_ingestion && uv run pytest tests/test_dataset_catalog.py -q
```

Expected: FAIL，`dataset_catalog` 不存在。

- [x] **Step 3: 实现 `dataset_catalog.py`**

最小形状：

```python
from pathlib import Path
from pydantic import BaseModel, Field

class CatalogError(ValueError):
    pass

class SourceFilter(BaseModel):
    source_provider: str
    dataset_name: str
    file_path: str
    import_scope_key: str

class CatalogSource(BaseModel):
    source_id: str
    title: str
    status: str
    kind: str
    filter: SourceFilter
    planned: dict
    completed: dict
    paths: dict

class Catalog(BaseModel):
    dataset_id: str
    visibility: str
    knowledge_model: str
    updated_at: str
    sources: list[CatalogSource] = Field(default_factory=list)

    def source(self, source_id: str) -> CatalogSource:
        ...

def load_catalog(path: Path) -> Catalog:
    # visibility 必须是 private；dataset_id 必须是 ticoAg/baicao-knowledge
    ...

def load_ledger(path: Path, catalog: Catalog):
    # 每个 task.source_id 必须在 catalog.sources 里
    ...
```

- [x] **Step 4: 收窄 `.gitignore`**

把根目录 `/datasets` 换成只忽略载荷：

```gitignore
/datasets/baicao-knowledge/sources/*/source/
/datasets/baicao-knowledge/sources/*/processed/
/datasets/baicao-knowledge/sources/*/work/
/datasets/baicao-knowledge/data/
/datasets/baicao-knowledge/exports/
```

然后只 add 元数据：

```bash
git add -f \
  datasets/baicao-knowledge/README.md \
  datasets/baicao-knowledge/catalog.json \
  datasets/baicao-knowledge/tasks/README.md \
  datasets/baicao-knowledge/tasks/ledger.json \
  datasets/baicao-knowledge/sources/national-standard-2022-pharmacopoeia/SOURCE.md \
  datasets/baicao-knowledge/sources/national-standard-2022-pharmacopoeia/VIEW.md \
  datasets/baicao-knowledge/sources/daoyi-suyang/SOURCE.md \
  datasets/baicao-knowledge/sources/daoyi-suyang/VIEW.md
```

`git status` 不得出现 `道医苏子阳.md`、`*.jsonl`、`*.parquet`、`exports/`。

- [x] **Step 5: VIEW Cypher 改中文键**

`compute_dataset_stats.render_view` 里的筛选段改成：

```cypher
MATCH (n)
WHERE n.导入源 = '<localized source>'
   OR '<localized source>' IN coalesce(n.导入源列表, [])
RETURN n
```

药典 localized source：`2022年中药药典`；苏子阳：`道医苏子阳`。scope key 用 `graph_i18n.SCOPE_VALUE_EN_TO_ZH`。加一个小测试锁住生成文本里没有 `import_source_id`。

对本机 latest 重跑一次 stats，覆盖两份 `VIEW.md`。

- [x] **Step 6: publish CLI 失败测试**

`packages/data_ingestion/tests/test_dataset_publish.py`：

```python
from pathlib import Path

import pytest

from data_ingestion.cli.dataset_publish import plan_upload, PublishError


def test_plan_upload_rejects_public(tmp_path: Path, monkeypatch):
    # 写一份 visibility=public 的 catalog，调用 plan_upload
    with pytest.raises(PublishError, match="private"):
        plan_upload(tmp_path)


def test_plan_upload_excludes_payloads(tmp_path: Path):
    # 建 README / catalog / VIEW / source md / records.jsonl / 道医苏子阳.md
    files = plan_upload(tmp_path)
    relative = {str(path.relative_to(tmp_path)) for path in files}
    assert "catalog.json" in relative
    assert "README.md" in relative
    assert not any(name.endswith(".jsonl") for name in relative)
    assert not any("source/" in name and name.endswith(".md") and "SOURCE.md" not in name for name in relative)
```

- [x] **Step 7: 实现 `dataset_publish.py`**

```python
def plan_upload(dataset_root: Path) -> list[Path]:
    catalog = load_catalog(dataset_root / "catalog.json")
    if catalog.visibility != "private":
        raise PublishError("refusing to publish non-private dataset")
    # 收录：README、catalog、tasks、各源 SOURCE.md / VIEW.md、data/*.parquet
    # 排除：sources/*/source/**、sources/*/work/**、exports/**、**/*.jsonl

def main() -> None:
    # --dry-run 只打印文件列表
    # 实际上传：huggingface_hub.HfApi.upload_folder
    # repo_id 默认 catalog.dataset_id，可用 BAICAO_HF_DATASET_ID 覆盖
    # 必须 private=True
```

`huggingface_hub` 用 `uv run --with huggingface_hub`，不要先加进 `pyproject.toml` 常驻依赖。

- [x] **Step 8: dry-run + 实际上传一次**（dry-run 通过；实际上传因 Infisical `infisical.ticoag.fun` 证书过期未完成）

```bash
cd packages/data_ingestion
uv run pytest tests/test_dataset_catalog.py tests/test_dataset_publish.py -q
uv run python -m data_ingestion.cli.export_dataset_parquet \
  --dataset-root ../../datasets/baicao-knowledge
uv run --with huggingface_hub python -m data_ingestion.cli.dataset_publish \
  --dataset-root ../../datasets/baicao-knowledge \
  --dry-run
infisical run --project-config-dir="$PWD/../.." -- \
  uv run --with huggingface_hub python -m data_ingestion.cli.dataset_publish \
  --dataset-root ../../datasets/baicao-knowledge
```

Expected：dry-run 无原文、无 jsonl；实际上传后 Viewer `is-valid` 为 true（private 带 `HF_TOKEN`）。

把 dataset URL 写回 `catalog.json` 与 `datasets/baicao-knowledge/README.md`。`data_ingestion/README.md` 补 catalog / stats / parquet / publish 命令。

- [x] **Step 9: commit**

```bash
git add packages/data_ingestion .gitignore datasets/baicao-knowledge
git status   # 确认没有 source 正文 / jsonl / parquet / exports
git commit -m "feat(data-ingestion): add catalog validation and private dataset publish"
```

---

### Task 2: Workbench / 问答消费方剂、医案、穴位、治法

**Files:**
- Modify: `packages/web/src/types/graph.ts`
- Modify: `packages/web/src/components/graph/GraphQueryPanel.tsx`
- Modify: `packages/api/app/kg/graph_service.py`
- Modify: `packages/api/app/services/chat_agent_runtime/system_prompt.py`
- Test: `packages/api/tests/api/test_graph_routes.py`
- Modify: `docs/acceptance/baicao-knowledge-dataset.md`

**Interfaces:**
- Consumes: `knowledge_model.constants.NodeType` / `EdgeType`（已含新类型）；`POST /api/v1/graph/query` 的 `label` 已是 `NodeType`
- Produces: 查询面板能选新类型；过滤摘要显示中文；问答 system prompt 点名这些类型

- [x] **Step 1: 写 API 失败测试，锁住新类型能进 query schema**

在 `packages/api/tests/api/test_graph_routes.py` 的 `TestGraphQuery` 增加：

```python
@pytest.mark.asyncio
async def test_query_graph_accepts_formula_and_case_filters(self, client):
    payload = {
        "node": {"label": "方剂", "name_contains": "止嗽散"},
        "edge": {"rel_type": "使用方剂"},
        "depth": 1,
        "limit": 10,
    }
    with patch("app.api.graph.graph_service") as mock_svc:
        mock_svc.query_graph = AsyncMock(
            return_value={
                "summary": {
                    "mode": "advanced-query",
                    "matched_nodes": 0,
                    "matched_edges": 0,
                    "truncated": False,
                    "active_filters": [],
                },
                "graph": {"center": None, "nodes": [], "edges": []},
                "scene": {
                    "truncated": False,
                    "node_limit_hit": False,
                    "relationship_limit_hit": False,
                    "info_message": None,
                },
            }
        )
        resp = await client.post("/api/v1/graph/query", json=payload)
    assert resp.status_code == 200
    forwarded = mock_svc.query_graph.await_args.args[0]
    assert forwarded.node.label == NodeType.FORMULA
    assert forwarded.edge.rel_type == EdgeType.USES_FORMULA
```

API schema 已用 `NodeType` / `EdgeType`，这一步现在就应通过。若 422，先修 schema 再往下。

- [x] **Step 2: 跑测试**

```bash
cd packages/api && uv run pytest tests/api/test_graph_routes.py::TestGraphQuery -q
```

Expected: PASS（或先修 schema 再 PASS）。

- [x] **Step 3: 前端查询枚举与下拉**

`packages/web/src/types/graph.ts` 的 `GraphNodeLabel` 补：

```ts
| "饮片" | "方剂" | "医案" | "穴位" | "治法" | "来源" | "证据"
```

`GraphEdgeRelType` 补：

```ts
| "组成药材" | "使用方剂" | "取用穴位" | "采用治法" | "记载于医案"
```

`GraphQueryPanel.tsx` 的 `nodeLabelOptions` / `relationTypeOptions` 同步加上这些值。

`labelTagColors` 补方剂/医案/穴位/治法/饮片/证据；`nodeStyleMap` 同样补，避免新类型掉进默认灰。

- [x] **Step 4: 后端过滤摘要**

`packages/api/app/kg/graph_service.py` 的 `QUERY_LABEL_DISPLAY` 补齐全部 `NodeType`；`QUERY_REL_TYPE_DISPLAY` 补 `组成药材` `使用方剂` `取用穴位` `采用治法` `记载于医案`。不要只改文档。

- [x] **Step 5: 问答 prompt**

`packages/api/app/services/chat_agent_runtime/system_prompt.py` 改成明确点名：

```python
def build_graph_specialist_system_prompt() -> str:
    return (
        "你是中药知识图谱专家。优先使用图工具定位锚点、查询关系并做子图游走。"
        "图里除了药材/功效/性味/归经/病证，还有方剂、医案、穴位、治法、饮片、证据。"
        "问组方、医案、取穴或治法时，按这些标签和关系查：组成药材、使用方剂、取用穴位、采用治法、记载于医案。"
        "不要编造结论；如果 provider 没有返回 reasoning，就不要生成 reasoning。"
    )
```

若已有 prompt 单测，锁住这几个词出现；没有就不要为了测字符串新开大文件。

- [x] **Step 6: 前端验证**

```bash
pnpm --dir packages/web exec vp test --run src/components/graph/GraphQueryPanel.tsx
pnpm --dir packages/shared typecheck
```

若 `GraphQueryPanel` 没有现成测试，至少跑 `pnpm --dir packages/web exec vp build`，并在浏览器打开 `/graph`：查询类型能选「方剂」，关系能选「使用方剂」，点一个苏子阳方剂节点颜色不是默认灰。

- [x] **Step 7: 回写验收**

`docs/acceptance/baicao-knowledge-dataset.md` 增加一节「查询消费」：

```text
POST /api/v1/graph/query
{"node":{"label":"方剂"},"limit":5}
```

期望：200，节点 `labels` 含 `方剂`。Workbench 下拉含方剂/医案/穴位/治法。

- [x] **Step 8: commit**

```bash
git add packages/web/src/types/graph.ts \
  packages/web/src/components/graph/GraphQueryPanel.tsx \
  packages/api/app/kg/graph_service.py \
  packages/api/app/services/chat_agent_runtime/system_prompt.py \
  packages/api/tests/api/test_graph_routes.py \
  docs/acceptance/baicao-knowledge-dataset.md
git commit -m "feat(graph): expose formula and case types in query and chat"
```

---

## Self-Review

| Spec 剩余要求 | 对应 task |
|---------------|-----------|
| HF private 可重复发布 | Task 1 |
| catalog / ledger 进 git，载荷不进 git | Task 1 Step 4 |
| VIEW 数量可从 stats 再生，Cypher 用生产键 | Task 1 Step 5 |
| 图消费方剂/医案/穴位/治法 | Task 2 |
| 不重抽、不扩模型、不公开原文 | Global Constraints |

本 plan 完成后：顶部 Status 改为 `done`，在 `plans/README.md` 毕业；稳定口径已在 `docs/architecture/knowledge-dataset.md`。
