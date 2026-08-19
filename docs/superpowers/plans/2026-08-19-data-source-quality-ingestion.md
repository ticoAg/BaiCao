---
type: Implementation Plan
title: 数据源逐源质量清洗与入图计划
description: 逐个核实、清洗和验收 BaiCao 已持有候选数据源，统一处理许可、实体消歧、图模型映射与发布门禁。
resource: docs/superpowers/plans/2026-08-19-data-source-quality-ingestion.md
tags: [data-sources, data-ingestion, entity-resolution, knowledge-graph]
timestamp: 2026-08-19T00:00:00+08:00
status: active
---

# 数据源逐源质量清洗与入图计划

**Goal:** 逐个把已持有候选源转成可追溯、可复核、符合 BaiCao 中医药图模型的本地结构化数据；许可允许时才进入 public dataset。

**Architecture:** 原始文件保留在 `tmp/qibo-datasets/` 且只读。每个源单独完成许可核实、契约映射、实体消歧、清洗、测试和隔离 Neo4j smoke，再更新 `docs/architecture/data-sources.md` 与 dataset 台账。不同源不共用未经验证的别名字典或启发式分类结果。

**Status:** active（当前源：`CAND-01 ShenNong TCM-KG`）

## 全局门禁

- 不把 GitHub/Hugging Face 公开可见等同于允许复制、派生或公开发布。
- 疾病、症状、证候、药材、饮片和方剂只按确定证据分类；类型不明时保留待审，不用名称后缀、编辑距离或 LLM 猜测自动归类。
- 只允许同类型、规范名一致或有可信标准标识支撑的确定性合并；跨类型、跨语言和模糊近似进入人工队列。
- 每条关系保留源、批次、原始行或记录定位；模型推断、共现和外部补充知识不得伪装成原始事实。
- 任一源出现许可、隐私或临床语义 `critical` 问题时保持 `publish: false`，不进入 public Parquet。

## 串行顺序

1. `CAND-01` ShenNong TCM-KG
2. `CAND-02` tcm-db
3. `CAND-03` DragonTCM
4. `CAND-04` TCM-MKG
5. `CAND-05` TCM-SD / ZY-BERT
6. `CAND-06` 至 `CAND-10` 按 `docs/architecture/data-sources.md` 的质量与许可结论逐个推进

每个源固定执行：`许可确认 -> 契约映射 -> 消歧门禁 -> 清洗 -> 测试 -> Neo4j smoke -> 质量结论 -> 独立提交`。

## 当前源：CAND-01 ShenNong TCM-KG

### 已确认事实

- 本地 `TCM-KG_triples.txt` 与 `michael-wzhu/ShenNong-TCM-LLM` 官方仓库 `src/TCM-KG_triples.txt` 的 SHA-256 相同。
- 文件共 123,358 行，每行是 `head<TAB>tail<TAB>relation`；无空端点、坏列或精确重复。
- 官方 README 指向 `ywjawmw/TCM_KG` 上游；两个仓库根目录当前都没有 `LICENSE`、`COPYING` 或 `NOTICE`。
- `symmap_chemical` 与 `chemical_MM` 共 67,481 行，不进入当前中医临床主域清洗结果。

### Tasks

- [x] 建立单一 active plan 和逐源执行顺序
- [x] 完成三路 Grok 许可、关系契约与实体消歧独立审查
- [x] 用 AnySearch 和官方一手来源核实上游、许可及疾病/证候术语边界
- [x] 决定症状到证候关系的最小共享契约，明确是否需要拆分 `病证`
- [x] 实现来源专用 parser/CLI；坏行、未知关系和类型冲突显式失败或进入拒绝统计
- [x] 为合并门禁、关系方向、属性化和排除关系补最小测试
- [x] 生成本地 `records.jsonl`、`stats.json` 和质量报告，不加入 public 发布
- [x] 运行 importer dry-run 与隔离 Neo4j smoke，验证无 dangling edge 和跨类型误合并
- [x] 更新 catalog/ledger、数据源清单、稳定架构与验收证据
- [ ] 独立提交 `CAND-01`，再把当前源切换为 `CAND-02`

### 当前实现证据

- 输出：19,066 records / 52,247 edges；3,278 个来源标注证候，12,687 个未分类临床概念
- 中性关联：`关联证候=35,444`、`关联药材=7,832`、`关联治法=2,606`
- 排除与隔离：化学关系 67,481，`TS_MS` 245，功能/临床类型冲突 337，证候自环 9
- 合并门禁：只在同类型内按规范名精确聚合；不使用编辑距离、跨语言映射或 LLM 猜测
- 发布门禁：两个上游仓库无许可证文件，ShenNong README 又限定仅供学术研究和禁止商业用途，固定 `publish: false`

## Verification

```bash
cd packages/data_ingestion
uv run --with pytest pytest tests/test_shennong_tcm_kg.py -q
uvx ruff check data_ingestion/shennong_tcm_kg.py \
  data_ingestion/cli/shennong_tcm_kg_clean.py tests/test_shennong_tcm_kg.py
uv run python -m data_ingestion.cli.shennong_tcm_kg_clean --help
uv run --with neo4j python -m data_ingestion.cli.import_dataset_neo4j \
  --records <processed/latest/records.jsonl> --dry-run
```

共享契约发生变化时，额外执行知识模型/API contract 测试、`pnpm --dir packages/shared typecheck` 和至少一条 web 消费检查。隔离 Neo4j smoke 必须使用无持久卷容器，不修改现有图库。

## 当前风险

- 原始 head 没有疾病、症状或证候类型，当前只能保留为 `未分类临床概念`；source-labeled syndrome 也只保留为 `来源标注证候`，同名异实需后续标准标识或人工证据才能拆分。
- 上游 `中药`、`治法`、`证候` 同时承担 tail label 和关系名，因此只映射为中性关联，不得作为治疗、诊断或因果事实。
- `TS_MS` 和功能/临床冲突已隔离但尚未人工逐条复核，不参与当前图谱合并。
- 许可不足以支持再发布；本地清洗结果和逐条派生关系不得进入 public dataset。

## Citations

1. [数据源与质量校验清单](../../architecture/data-sources.md)
2. [共享知识模型与数据采集边界](../../architecture/knowledge-model-and-ingestion.md)
3. [ShenNong-TCM-LLM](https://github.com/michael-wzhu/ShenNong-TCM-LLM)
4. [TCM_KG](https://github.com/ywjawmw/TCM_KG)
5. [OKF v0.1 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
