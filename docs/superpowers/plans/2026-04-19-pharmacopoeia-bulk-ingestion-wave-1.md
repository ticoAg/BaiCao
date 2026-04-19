# 药典条目大批量入图 Wave 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `2022年中药药典.txt` 建立一条可复用的“LLM 初始化 → 异步批量抽取 → 统一记录快照 → Neo4j 写入”主链路，并能在注入真实 Infisical 环境后执行大批量或全量入图。

**Architecture:** 复用药典现有的切段、section 解析、LLM 抽取和 bundle 映射，把通用能力上收到 `packages/data_ingestion/`：统一的 LLM transport 初始化、通用异步批量执行器、bundle 记录扁平化与 JSONL 快照产物。数据库写入继续放在 `packages/api/` 下游边界，复用现有 `Neo4jGraphWriter` 完成 `GraphImportRecord` 到图谱的真实写入。

**Tech Stack:** Python 3.12, Pydantic v2, OpenAI compatible Responses API, asyncio, pytest, Neo4j

---

### Task 1: 抽出通用异步批量执行与记录快照能力

**Files:**
- Create: `packages/data_ingestion/data_ingestion/async_batch.py`
- Create: `packages/data_ingestion/data_ingestion/record_snapshots.py`
- Modify: `packages/data_ingestion/data_ingestion/__init__.py`
- Test: `packages/data_ingestion/tests/test_async_batch.py`
- Test: `packages/data_ingestion/tests/test_record_snapshots.py`

- [ ] 定义保序异步批量执行器，支持 `concurrency`、逐条回调和结果聚合
- [ ] 定义 bundle / record 扁平化与 JSONL 快照写入能力
- [ ] 跑 `cd packages/data_ingestion && uv run pytest tests/test_async_batch.py tests/test_record_snapshots.py -q`

### Task 2: 抽出通用 LLM transport 初始化与药典批处理编排

**Files:**
- Modify: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/llm_extraction.py`
- Create: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/ingestion.py`
- Modify: `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/dry_run.py`
- Create: `packages/data_ingestion/data_ingestion/cli/pharmacopoeia_ingest.py`
- Test: `packages/data_ingestion/tests/test_pharmacopoeia_ingestion.py`

- [ ] 先写测试锁定：可从环境构造真实 transport、批量编排会产出 `graph_import_records.jsonl`
- [ ] 将 dry-run 的并发逻辑迁移到通用批量执行器
- [ ] 新增药典大批量 ingest CLI，支持 `--limit`、`--entry-offset`、`--concurrency`、`--timeout-seconds`
- [ ] 跑 `cd packages/data_ingestion && uv run pytest tests/test_pharmacopoeia_llm_extraction.py tests/test_pharmacopoeia_dry_run.py tests/test_pharmacopoeia_ingestion.py -q`

### Task 3: 打通 JSONL 记录到 Neo4j 的真实写入

**Files:**
- Create: `packages/api/app/importers/neo4j_import.py`
- Modify: `packages/api/app/importers/cli.py`
- Test: `packages/api/tests/unit/importers/test_neo4j_import.py`

- [ ] 先写测试锁定：合法 `GraphImportRecord` 会被交给 `Neo4jGraphWriter`，统计节点和边数量
- [ ] CLI 的 `--neo4j` 从“待实现”变成真实写入
- [ ] 跑 `cd packages/api && uv run --extra dev pytest tests/unit/importers/test_neo4j_import.py tests/contract/test_import_record_contract.py -q`

### Task 4: 文档与实跑验证

**Files:**
- Modify: `packages/data_ingestion/README.md`

- [ ] 补充大批量 ingest 与 Neo4j 导入命令
- [ ] 跑 `cd packages/data_ingestion && uv run python -m data_ingestion.cli.pharmacopoeia_ingest ...`
- [ ] 跑 `cd packages/api && uv run python -m app.importers.cli ... --neo4j`
- [ ] 用 Cypher 核对导入节点/关系数量与示例节点存在性
