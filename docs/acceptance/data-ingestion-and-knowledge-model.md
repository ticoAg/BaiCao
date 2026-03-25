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

### 结果证据

- `tests/contract/test_graph_shared_model_contract.py` 通过，锁住共享图模型枚举绑定与 edge 子集
- `tests/unit/kg/test_models.py` 通过，锁住 API-only `PARENT_OF` / `CHILD_OF` 未被删除
- `tests/contract/test_import_record_contract.py` 通过，锁住共享导入记录与 importer `__init__` 兼容导出
- `packages/data_ingestion/tests/test_models.py` 通过，证明数据采集边界直接复用共享图模型

## 7. 风险与未覆盖项

- 本验收只覆盖共享图模型、导入记录与数据采集边界的最小主线，没有补充全量 API 测试、lint、type check
- 当前 importer / exporter 只验证了 JSONL 主路径；CSV 行为依赖同一共享导入记录抽象，但未在本验收文档中单独展开样例
- 未补充真实 Neo4j 导入或浏览器端人工验收，因此结果更偏向 contract / unit 证据

## 8. 结论

- 结果：`risk`
- 结论一句话：共享图模型已经成为 API schema、导入记录与数据采集边界的单一事实来源，但更高层联调与人工验收仍待补充
- 后续动作：由主代理在集成阶段决定是否追加更高层 API / acceptance 验证
