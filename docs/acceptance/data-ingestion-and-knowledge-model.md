<!--
---
doc_kind: acceptance
status: stable
tags: ["acceptance", "knowledge-model", "data-ingestion", "import-export"]
summary: 共享知识模型到 API、导入导出与数据采集边界的主线验收
audience: developer
---
-->

# 共享知识模型与数据采集主链路验收

## 1. 概述

- 功能名称：共享图模型 / 导入记录 / 数据采集边界闭环
- 验收目标：验证 `packages/knowledge_model/` 已成为 API 图谱 schema、导入导出记录以及 `packages/data_ingestion/` 的共享真源
- 对应需求：让共享知识模型消费者迁移形成最小可验证闭环
- 对应计划：[../superpowers/plans/2026-03-25-pipeline-ingestion-closure-wave-1.md](../superpowers/plans/2026-03-25-pipeline-ingestion-closure-wave-1.md)
- 当前版本 / 日期：shared-model-ingestion-closure / 2026-03-25

## 2. 验收范围

### 包含

- API graph schema 直接复用共享 `NodeType` / `NodeStatus`
- API `EdgeType` 保持 superset，同时用 contract test 锁住共享子集
- importer / exporter 统一消费共享导入记录 `GraphImportRecord`
- `app.importers` 继续兼容导出 `GraphRecord` / `EdgeRecord`
- `packages/data_ingestion/` 直接消费共享图模型，而不是重新定义图谱枚举

### 不包含

- pipeline 七步预览链路
- `docs/acceptance/README.md` 索引更新
- 全量 API / web / integration 验证
- 非共享子集的 API-only edge 语义调整

## 3. 前置条件

### 环境

- 仓库 worktree：`/Users/ticoag/Documents/myws/BaiCao/.worktrees/shared-model-ingestion-closure`
- Python：`>=3.12`
- 依赖：`packages/api/` 与 `packages/data_ingestion/` 可通过 `uv` 解析本地 `packages/knowledge_model/`

### 启动命令

```bash
cd packages/api
uv run pytest tests/contract/test_graph_shared_model_contract.py tests/api/test_graph_routes.py tests/unit/kg/test_models.py -q

cd ../data_ingestion
uv run --with pytest pytest tests/test_models.py -q
```

## 4. 验收步骤

### Step 1

- 操作：验证 API graph schema 使用共享图模型枚举
- 命令：

```bash
cd packages/api
uv run pytest tests/contract/test_graph_shared_model_contract.py tests/unit/kg/test_models.py -q
```

### Step 2

- 操作：验证 importer / exporter 统一消费共享导入记录，并保持兼容导出
- 命令：

```bash
cd packages/api
uv run pytest tests/contract/test_import_record_contract.py -q
```

### Step 3

- 操作：验证数据采集边界直接消费共享图模型
- 命令：

```bash
cd packages/data_ingestion
uv run --with pytest pytest tests/test_models.py -q
```

## 5. 期望结果

### Step 1 预期

- `HerbNode.type` 字段注解直接指向共享 `NodeType`
- `BaseNode.status` 字段注解直接指向共享 `NodeStatus`
- API `EdgeType` 仍保留 `PARENT_OF` / `CHILD_OF`
- 共享图模型中的 edge 子集全部存在于 API `EdgeType`

### Step 2 预期

- `JSONLImporter` 返回共享 `GraphImportRecord`
- `JSONLExporter` 能直接导出共享导入记录
- `app.importers.GraphRecord` / `app.importers.EdgeRecord` 继续可用，并与共享类型保持同一对象

### Step 3 预期

- `ExtractionCandidate.node_type` 直接使用共享 `NodeType`
- 数据采集边界只定义来源适配 / 抽取候选模型，不复制图谱节点与边模型

## 6. 证据记录

### 实现证据

- `packages/knowledge_model/knowledge_model/constants.py`
- `packages/knowledge_model/knowledge_model/import_records.py`
- `packages/api/app/models/enums.py`
- `packages/api/app/schemas/graph.py`
- `packages/api/app/importers/base.py`
- `packages/api/app/importers/__init__.py`
- `packages/api/app/importers/jsonl_importer.py`
- `packages/api/app/importers/csv_importer.py`
- `packages/api/app/exporters/base.py`
- `packages/api/app/exporters/jsonl_exporter.py`
- `packages/api/app/exporters/csv_exporter.py`
- `packages/data_ingestion/data_ingestion/models.py`

### 运行证据

```bash
cd packages/api
uv run pytest tests/contract/test_graph_shared_model_contract.py tests/api/test_graph_routes.py tests/unit/kg/test_models.py -q
uv run pytest tests/contract/test_import_record_contract.py tests/api/test_graph_routes.py -q

cd ../data_ingestion
uv run --with pytest pytest tests/test_models.py -q
```

执行日期：`2026-03-25`

```bash
cd packages/api
uv run pytest tests/contract/test_graph_shared_model_contract.py \
  tests/contract/test_import_record_contract.py \
  tests/api/test_graph_routes.py \
  tests/unit/kg/test_models.py -q

cd ../knowledge_model
uv run --with pytest pytest tests -q
```

- 当前结果：API contract + route + unit 聚焦验证 `21 passed`；共享模型包测试 `8 passed`；`data_ingestion` 测试 `1 passed`

```bash
cd packages/api
uv run python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory

from app.importers.jsonl_importer import JSONLImporter
from app.exporters.jsonl_exporter import JSONLExporter
from knowledge_model.import_records import GraphImportRecord

source = Path("../db/import/herbs.jsonl")
records = list(JSONLImporter().load(str(source)))
print(type(records[0]).__name__, records[0].node_name, records[0].node_type)
with TemporaryDirectory() as tmpdir:
    output = Path(tmpdir) / "roundtrip.jsonl"
    JSONLExporter().export(records[:2], str(output))
    first = GraphImportRecord.model_validate_json(output.read_text(encoding="utf-8").splitlines()[0])
    print(type(first).__name__, first.node_name, len(first.edges))
PY
```

- 当前结果：样例 `packages/db/import/herbs.jsonl` 导入后直接得到 `GraphImportRecord`；导出到临时 JSONL 后可再次由共享 `GraphImportRecord` 成功回读

```bash
cd packages/data_ingestion
uv run python - <<'PY'
from data_ingestion.models import ExtractionCandidate
from knowledge_model.constants import NodeType

candidate = ExtractionCandidate(node_type=NodeType.HERB, node_name="陈皮", source_name="demo")
print(candidate.node_type is NodeType.HERB, candidate.node_type)
PY
```

- 当前结果：`ExtractionCandidate` 在真实运行中直接消费共享 `NodeType.HERB`

```bash
curl -sS http://127.0.0.1:8000/api/v1/graph/meta/schema
```

- 当前结果：API graph 元信息接口在本地集成环境可正常返回 schema 摘要，证明共享图模型迁移后的 graph 主路径仍可工作

### 结果证据

- `tests/contract/test_graph_shared_model_contract.py` 通过，锁住共享图模型枚举绑定与 edge 子集
- `tests/unit/kg/test_models.py` 通过，锁住 API-only `PARENT_OF` / `CHILD_OF` 未被删除
- `tests/contract/test_import_record_contract.py` 通过，锁住共享导入记录与 importer `__init__` 兼容导出
- `packages/data_ingestion/tests/test_models.py` 通过，证明数据采集边界直接复用共享图模型

## 7. 风险与未覆盖项

- 当前 importer / exporter 的手工 round-trip 主要覆盖 JSONL 主路径；CSV 仍依赖同一共享导入记录抽象，但未在本文单独展开样例
- 本轮没有补真实 Neo4j 导入执行，也没有补浏览器端人工验收；这条验收聚焦的是共享结构真源与消费者边界
- API `EdgeType` 仍保留 superset 策略；shared 与 API-only edge 的完全收敛不在本轮范围

## 8. 结论

- 结果：`pass`
- 结论一句话：共享知识模型已经成为 API schema、导入导出与数据采集边界的单一事实来源，并已补齐样例 round-trip 与本地集成环境复核
- 后续动作：后续只需在真实导入执行与更广覆盖的 CSV / integration 层补更多样例证据

## 9. 2026-03-31 药典条目图谱化补充证据

### 本轮新增范围

- 共享图模型新增 `饮片`、`证据` 节点及 `具有饮片`、`由证据支持` 关系
- `packages/data_ingestion/` 新增文件级路由、条目块协议、统一 bundle 输出
- `2022年中药药典.txt` 新增专属切段、章节解析、条目映射逻辑
- API pipeline 新增 `processor_runtime`，能把药典条目映射结果接入 `MAP_TO_KNOWLEDGE_MODEL` 预览

## 10. 2026-04-19 药典大批量导入与重置补充证据

### 本轮新增范围

- `packages/data_ingestion/` 新增通用异步批量执行器
- 药典 ingest 支持真实 LLM 大批量执行、失败条目筛选重跑、`GraphImportRecord` 快照落盘
- `packages/api/` 的导入 CLI 支持把 JSONL 快照真实写入 Neo4j
- 新增数据集级重置能力，支持按 scope 清理新版导入关系，也支持按历史快照精确清理旧关系

### 运行证据

```bash
cd packages/data_ingestion
uv run --with pytest pytest \
  tests/test_async_batch.py \
  tests/test_record_snapshots.py \
  tests/test_pharmacopoeia_ingestion.py \
  tests/test_pharmacopoeia_dry_run.py \
  tests/test_pharmacopoeia_llm_extraction.py \
  tests/test_pharmacopoeia_mapping.py -q
```

- 当前结果：相关数据采集测试通过

```bash
cd packages/api
uv run --extra dev pytest \
  tests/unit/importers/test_neo4j_import.py \
  tests/unit/importers/test_dataset_reset.py \
  tests/unit/export/test_neo4j_graph_writer.py \
  tests/contract/test_import_record_contract.py -q
```

- 当前结果：导入、重置、Neo4j 关系 scope 与导入记录契约测试通过

### 真实运行证据

- Infisical 注入确认：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`、`NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD` 均已注入
- `2022年中药药典.txt` 切分条目数：`605`
- 第一次真实全量尝试：
  - `entries_attempted=605`
  - `entries_succeeded=287`
  - `entries_failed=318`
  - 主要失败原因：上游 `429 rate limit`
  - `records_generated=3225`
- 切换新版 provider 后的失败重跑：
  - `10` 条窗口：`10 / 10` 成功
  - `50` 条窗口：`50 / 50` 成功
  - `100` 条窗口 A：`99 / 100` 成功
  - `100` 条窗口 B：`97 / 100` 成功
  - `62` 条最终窗口：`62 / 62` 成功
  - 总计重跑成功：`318 / 318`
- 当前完成状态：
  - 全文件 `605 / 605` 条目已成功完成结构化抽取与映射
  - 重跑阶段残留的 `4` 次失败已在后续窗口中全部清空
- 累计导入快照：
  - 首次成功批次：`3225` 记录
  - 重跑 `10` 条样本：`159` 记录
  - 重跑 `50` 条窗口：`726` 记录
  - 重跑 `100` 条窗口 A：`1346` 记录
  - 重跑 `100` 条窗口 B：`1320` 记录
  - 重跑最终 `62` 条窗口：`867` 记录
- 当前图内按数据集属性统计：
  - `Herb=309`
  - `PreparedHerb=250`
  - `Evidence=314`
  - `Disease=860`
  - `Efficacy=409`
  - `Meridian=11`
  - `Flavor=11`

### 风险与未覆盖项

- 初版 provider `openrouter/elephant-alpha` 在运行时触发上游限流，已通过切换 provider 完成剩余失败条目回填
- 新 provider `https://ark.cn-beijing.volces.com/api/v3` 需要保持原始版本路径，且不支持 `enable_thinking` 扩展字段；当前代码已兼容自动降级
- 历史已导入但不带 `import_scope_key` 的关系，需要通过 `--snapshot-jsonl` 做一次精确清理

### 对应实现

- `packages/knowledge_model/knowledge_model/constants.py`
- `packages/knowledge_model/knowledge_model/node_models.py`
- `packages/knowledge_model/knowledge_model/import_records.py`
- `packages/data_ingestion/data_ingestion/source_models.py`
- `packages/data_ingestion/data_ingestion/routing.py`
- `packages/data_ingestion/data_ingestion/bundles.py`
- `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/segmentation.py`
- `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/parsing.py`
- `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/mapping.py`
- `packages/api/app/pipeline/processor_runtime.py`
- `packages/api/app/pipeline/service.py`
- `packages/api/app/pipeline/steps/map_to_knowledge_model.py`

### 补充验证命令

```bash
cd packages/knowledge_model
uv run --with pytest pytest tests/test_constants.py tests/test_schema.py -q

cd ../data_ingestion
uv run --with pytest pytest tests -q

cd ../api
uv run --extra dev pytest tests/unit/pipeline/test_processor_runtime.py tests/unit/pipeline/test_service.py tests/contract/test_import_record_contract.py -q
```

### 预期闭环

- `一枝黄花` 这类药典条目能被切成单个 `证据` 节点
- `饮片` 以独立节点形式进入 bundle，而不是作为 `药材` 附属字段
- `MAP_TO_KNOWLEDGE_MODEL` 预览可返回 `药材 / 饮片 / 证据 / 性味 / 归经 / 功效` 及中文关系
