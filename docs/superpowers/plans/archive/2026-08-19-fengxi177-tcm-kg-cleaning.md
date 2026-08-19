# fengxi177 中医药图谱清洗 Implementation Plan

**Goal:** 把 `fengxi177/Knowlegde_Graph_TCM` 的药材与方剂关系清洗为 BaiCao `DatasetRecord`，在不扩共享图模型、不改原始数据的前提下完成质量验收、Neo4j smoke 与发布决策。

**Architecture:** `tmp/qibo-datasets/Knowlegde_Graph_TCM/` 只读；清洗器位于 `packages/data_ingestion/`，输出进入 `datasets/baicao-knowledge/sources/fengxi177-knowledge-graph-tcm/processed/latest/`。节点/关系只复用 `packages/knowledge_model/` 真源。Codex 负责集成和验证，多个 Grok 分别承担隔离实现、契约审查与数据质量审查。

**Status:** done（2026-08-19）

## Scope

- 中药材：131 个药材入口、3,335 条关系
- 方剂：266 个方名、742 个处方变体、16,588 条原始关系
- `composition` 后的 `dose` 折叠为 `组成药材.dosage`
- 生成确定性 JSONL、统计、SOURCE/VIEW、catalog/ledger 记录
- 运行 importer dry-run 与隔离 Neo4j smoke
- 只有源许可允许再发布时才加入 public Hugging Face；许可不明时保留本地 staging 并记录阻塞

## Non-Goals

- 不修改或删除 `tmp/` 原始数据
- 不新增 `NodeType` / `EdgeType`
- 不把剂量建模为全局 `药材 -> 剂量` 关系
- 不伪造证据节点或证据原文
- 不因数据已在公开 GitHub 而推断其具有再发布许可

## Done Definition

1. 解析器对坏端点、未知关系和 composition/dose 错配显式失败
2. 方名与处方变体不误合并；6,521 条组成边保留，其中 5,784 条带 dosage
3. 所有边 target 都有同批 `DatasetRecord`，全部记录通过 `validate_types()`
4. 全量清洗统计可重复，定向/全包测试、Ruff 与 diff check 通过
5. Neo4j dry-run 与隔离 scope smoke 无 dangling edge
6. catalog、ledger、SOURCE/VIEW、架构与验收文档同步
7. 许可已确认则重新发布并验收 Viewer；否则明确保持本地、不上传该源

## Tasks

### Task 0: 关闭旧计划并建立单一入口

- [x] 将 public HF Viewer 的 200 验收写入稳定文档
- [x] 把 dataset predecessor/spec 与可信问答收口 plan 标记 done 并归档
- [x] plans 根索引只保留本计划为 active

### Task 1: Grok 并行清洗设计与实现

- [x] 派发隔离实现 Grok，只允许修改 parser/CLI/test 三个文件
- [x] 派发只读契约审查 Grok，检查实体合并、边目标和关系语义
- [x] 派发只读质量审查 Grok，检查原始计数、剂量配对与许可
- [x] Codex 审查三个结果并只集成可验证结论

### Task 2: 集成清洗器并锁住契约

- [x] 集成纯解析/映射模块与 CLI，不新增依赖
- [x] 测试剂量上下文、处方隔离、别名/分布属性、未知输入失败
- [x] 全量运行并校验关键计数、稳定排序与重复率

### Task 3: 产物与 Neo4j 验收

- [x] 写入新源 `processed/latest/records.jsonl` 与 `stats.json`
- [x] 生成 VIEW 并执行 importer dry-run
- [x] 在临时无 volume Neo4j 容器导入，验证节点、边与 target label 后删除容器，不修改现有图库

### Task 4: 文档、许可与发布决策

- [x] 新增 SOURCE/VIEW，更新 catalog 与 ledger
- [x] 把稳定映射与验收结果同步到 architecture/acceptance
- [x] 核实上游 LICENSE；不明确时不把该源加入 public 发布 Parquet
- [x] 上游无许可证：保持 `publish: false`；public Parquet 重导仍为 5,118 / 11,202

## Verification

```bash
cd packages/data_ingestion
uv run --with pytest pytest tests/test_qibo_tcm_kg.py -q
uvx ruff check data_ingestion/qibo_tcm_kg.py \
  data_ingestion/cli/qibo_tcm_kg_clean.py tests/test_qibo_tcm_kg.py
uv run python -m data_ingestion.cli.qibo_tcm_kg_clean \
  --input-root ../../tmp/qibo-datasets/Knowlegde_Graph_TCM \
  --out-dir ../../datasets/baicao-knowledge/sources/fengxi177-knowledge-graph-tcm/processed/latest
uv run --with neo4j python -m data_ingestion.cli.import_dataset_neo4j \
  --records ../../datasets/baicao-knowledge/sources/fengxi177-knowledge-graph-tcm/processed/latest/records.jsonl \
  --dry-run
```

## Evidence

- public 基线发布：10 个允许文件 + `.gitattributes`；`records=5,118`、`edges=11,202`
- public 脱敏：`evidence_text` 全空，properties 五个原文字段均不存在
- public Viewer：匿名 `/is-valid`、`/splits`、records/edges rows 均为 200
- 原始数据预检：药材 3,335 条且无重复；方剂 16,588 条，其中 2,796 个全局 dose 重复；端点均可解析
- Grok 三路：隔离实现 `13 passed, 1 skipped` + Ruff；契约/质量审查结论已进入 Live UI
- 主工作区：相关测试 `21 passed`；全量输出 4,996 records / 11,445 edges
- 临时 Neo4j：4,996 created / 11,445 edges；6,521 composition、5,784 dosage、436 source；错误 target label 为 0
- 发布门禁：第三源 `publish: false` 后重导仍为 5,118 / 11,202
- data ingestion 全量：`89 passed`；本次涉及文件 Ruff 通过，`git diff --check` 通过
- 最终 public Viewer：匿名 `/is-valid`、`/splits`、records/edges rows 均为 200，pending/failed 为空，行数 5,118 / 11,202

## Residual Risks

- 737 条组成关系没有可绑定剂量，另有疑似截断词、剂量混入药名和一对多别名；因此全部记录保持 `pending`，本计划只声明结构清洗完成。
- 全包 Ruff 仍报告 3 个既有错误，位于未修改的 `migrate_graph_chinese.py`、药典 `dry_run.py` 与 `protocols.py`；未为本任务顺手修复。
- 上游没有许可证；除非取得明确授权，`fengxi177-knowledge-graph-tcm.publish` 必须保持 false。
