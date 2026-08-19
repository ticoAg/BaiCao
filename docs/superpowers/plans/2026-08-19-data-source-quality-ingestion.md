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

**Status:** active（当前源：`CAND-02 tcm-db`）

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
- [x] 独立提交 `CAND-01`，再把当前源切换为 `CAND-02`

### 当前实现证据

- 输出：19,066 records / 52,247 edges；3,278 个来源标注证候，12,687 个未分类临床概念
- 中性关联：`关联证候=35,444`、`关联药材=7,832`、`关联治法=2,606`
- 排除与隔离：化学关系 67,481，`TS_MS` 245，功能/临床类型冲突 337，证候自环 9
- 合并门禁：只在同类型内按规范名精确聚合；不使用编辑距离、跨语言映射或 LLM 猜测
- 发布门禁：两个上游仓库无许可证文件，ShenNong README 又限定仅供学术研究和禁止商业用途，固定 `publish: false`

提交证据：`5188a09 feat: clean ShenNong TCM-KG source`

### CAND-01 残余风险

- 原始 head 没有疾病、症状或证候类型，当前只能保留为 `未分类临床概念`；source-labeled syndrome 也只保留为 `来源标注证候`，同名异实需后续标准标识或人工证据才能拆分。
- 上游 `中药`、`治法`、`证候` 同时承担 tail label 和关系名，因此只映射为中性关联，不得作为治疗、诊断或因果事实。
- `TS_MS` 和功能/临床冲突已隔离但尚未人工逐条复核，不参与当前图谱合并。
- 许可不足以支持再发布；本地清洗结果和逐条派生关系不得进入 public dataset。

## 当前源：CAND-02 tcm-db

### 已确认事实

- 本地仓库与远端 `main` 均固定在 commit `e29028be9a4b4a70a49a7adfaaf268e2f1b7999f`；SQLite SHA-256 为 `a9ff634e621ed47869c4ab2628e145b7da48afe922205bcf6f7983415a72966c`。
- 目标主域表为 472 药材、234 方剂、727 症状、194 证候、119 治法；显式关系为 `formula_herbs=196`、`formula_syndromes=19`、`syndrome_symptoms=440`，无悬空外键。
- `tcm-db` 本身和 6 个上游没有 GitHub 可识别许可证；仅 `9527qingfeng/hantang-nihaixia-follower` 为 MulanPSL-2.0，无法覆盖混合数据库中的其他来源。
- 29 个唯一方剂行命中描述句或多方合并 warning；药材“白芷”两行同名但属性冲突；症状与证候存在乳癌、肾衰竭、胰脏癌 3 个跨类型同名。
- 现有模型缺少独立 `症状` 节点；最小契约为新增 `症状` 与 `关联症状`，其余复用 `药材`、`方剂`、`病证`、`组成药材`、`关联证候`。

### Tasks

- [x] 用 AnySearch、GitHub 官方 API 和本地 commit 核实来源与许可链
- [x] 完成三路 Grok 许可、关系契约与实体消歧独立审查
- [x] 决定最小共享契约：新增 `症状` 节点和 `关联症状` 边
- [x] 决定消歧门禁：异常方剂和属性冲突同名药材隔离，症状/证候跨类型同名保持独立
- [x] 实现只读 SQLite parser/CLI，只消费主域实体和三张显式关系表
- [x] 为 schema 门禁、关系方向、隔离统计和跨类型不合并补测试
- [x] 生成本地 records/stats/质量报告，固定 `publish: false`
- [x] 运行 importer dry-run 与隔离 Neo4j smoke
- [x] 更新 catalog/ledger、数据源清单、稳定架构与验收证据
- [ ] 独立提交 `CAND-02`，再把当前源切换为 `CAND-03`

### 当前实现证据

- 输出：1,715 records / 654 edges；药材 470、方剂 205、症状 727、病证 194、治法 119
- 显式关系：`组成药材=196`、`关联证候=19`、`关联症状=439`
- 隔离：29 个异常方剂行、2 条冲突白芷和 1 条同名跨类型边
- 合并门禁：仅同类型规范名精确且非空属性无冲突时聚合；跨类型同名 3 组保持独立
- 溯源：每条节点和关系可定位到 `tcm_knowledge.db:<table>:<id/rowid>`
- 入图验收：1,715 节点 / 654 边；端点类型、同名边、治疗事实提升、缺失证据定位和 scope 错误均为 0
- 发布门禁：混合数据库许可链不完整，固定 `publish: false`

### CAND-02 残余风险

- 29 个异常方剂和两条冲突白芷仍需人工逐条裁定；当前隔离优先于猜测修复。
- `乳癌`、`肾衰竭`、`胰脏癌` 的症状表记录疑似类型误入，但除唯一同名边外仍保留源记录，等待专家确认。
- 方剂组成关系缺少剂量且角色全为“未知”；不能用于剂量或配伍角色推断。
- 医学内容仍为 `pending`，结构通过不等于疗效、主治、证候或治法已经验证。

### 当前风险

- 数据库是不可由现存脚本完整重建的权威产物，且缺少逐表/逐字段上游许可映射；不得发布整库或逐条派生 public 数据。
- `indication`、`composition`、`representative_formulas` 和 `related_*` 是长文本或列表字段，不得直接提升为治疗、组成、诊断或因果关系。
- `formula_herbs` 的 dosage 全空、role 全为“未知”；关系可保留成员事实，但不能伪造剂量或君臣佐使。
- 临床医案存在来源身份键问题且不在本轮中医药/疾病/症状显式关系范围内，保持排除。

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

## Citations

1. [数据源与质量校验清单](../../architecture/data-sources.md)
2. [共享知识模型与数据采集边界](../../architecture/knowledge-model-and-ingestion.md)
3. [ShenNong-TCM-LLM](https://github.com/michael-wzhu/ShenNong-TCM-LLM)
4. [TCM_KG](https://github.com/ywjawmw/TCM_KG)
5. [OKF v0.1 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
6. [tcm-db](https://github.com/xiaogege6697/tcm-db)
7. [MulanPSL-2.0](https://spdx.org/licenses/MulanPSL-2.0.html)
8. [中医临床诊疗术语国家标准索引](https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D7B2C0D3A7E05397BE0A0AB82A)
