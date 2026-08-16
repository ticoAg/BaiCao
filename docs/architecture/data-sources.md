<!--
---
doc_kind: architecture
status: stable
tags: ["data-sources", "knowledge-graph", "data-ingestion"]
summary: 图谱数据候选源评估与分级整理（Hugging Face 数据集调研）
audience: developer, data-team
---
-->

# 图谱数据候选源

本文档整理从互联网（主要为 Hugging Face）调研到的与中药材 / 中医药知识图谱相关的候选数据源，并给出评估结论与落地建议。

> **背景**：2026-03-23 完成调研，结论是"可直接接入图谱的高质量结构化数据很少，更多是问答或训练语料"。本文档将这些调研发现整理为正式归档。

---

## 1. 数据源总览

| # | 数据集 | 定位 | 分级 | 建议用途 |
|---|--------|------|------|---------|
| 1 | `AIeathumberger/TCMKG` | 图谱型数据候选，含 Neo4j 存储文件 | 探索型图谱源 | 单独评估是否可导出为结构化图数据 |
| 2 | `ZJUFanLab/TCMChat-dataset-600k` | 大规模训练语料，含药典文本和知识 JSON | 优先辅助抽取源 | 从 `knowledge.json`、药典文本中抽实体与关系 |
| 3 | `michaelwzhu/ShenNong_TCM_Dataset` | 问答数据集，偏症状、证候、方剂推荐 | 训练 / 评测语料 | 问答侧补料，不作为图谱真源 |
| 4 | `xihao1/Traditional-Chinese-Medicine-Knowledge` | 对话结构知识数据 | 辅助问答语料 | 轻量知识补料，不作为图谱真源 |
| 5 | `TCMNER/TCMNER2025` | 命名实体识别训练集 | 抽取辅助数据 | 用于实体抽取质量提升或校验 |

---

## 2. 优先评估候选源

### 2.1 `AIeathumberger/TCMKG`

**链接**: <https://huggingface.co/datasets/AIeathumberger/TCMKG>

**定位判断**:
- 最接近"图谱型数据"的候选
- 数据仓库中直接包含大量 Neo4j 存储文件

**适配评估**:

| 维度 | 评估 |
|------|------|
| 潜在价值 | 高 — 可能已包含实体与关系网络 |
| 接入风险 | 高 — 公开形态更像 Neo4j store 目录打包，而非清晰导出的结构化图数据 |
| 字段说明 | 缺失 — 缺少明确字段、标签、关系说明 |
| 直接可用性 | 低 |

**结论**: 作为"高风险探索型候选源"，适合单独做一次导出可行性评估，不建议直接列为主真源。

**落地条件**: 需完成 Neo4j 导出可行性评估，判断能否转成 CSV / JSONL / Cypher。

---

### 2.2 `ZJUFanLab/TCMChat-dataset-600k`

**链接**: <https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k>

**定位判断**:
- 大规模中医药训练语料与任务数据集合
- 包含 `knowledge.json`、`recommend_herb.json`、`2022年中药药典.txt` 等文件

**与图谱结构重合度**:

| 已有结构 | 数据中对应内容 |
|----------|---------------|
| 药材 (Herb) | knowledge.json 中药材名称 |
| 成分 (Component) | 成分列表 |
| 功效 (Efficacy) | 功效主治 |
| 性味 (Flavor) | 性味归经 |
| 归经 (Meridian) | 性味归经 |
| 来源 (Source) | 药典文本 |

**适配评估**:

| 维度 | 评估 |
|------|------|
| 结构重合度 | 高 — 与本项目药材/成分/功效/性味/归经/来源结构明显重合 |
| 直接可用性 | 中 — 原始形式仍以 instruction/output 文本为主，不是可直接入图的结构化真源 |
| 抽取价值 | 高 — 适合进入规则 + agent 抽取链路 |

**结论**: 作为"优先辅助抽取源"，适合验证"规则 + agent -> 统一中间格式 -> 共享图模型"主链路。

**落地条件**: 需走数据采集二级子项目的抽取流程，不建议直接导入。

---

## 3. 次优候选源

### 3.1 `michaelwzhu/ShenNong_TCM_Dataset`

**链接**: <https://huggingface.co/datasets/michaelwzhu/ShenNong_TCM_Dataset>

**定位判断**:
- 以 `query/response` 为主的问答数据
- 更偏中医症状、证候、方剂或中药推荐

**结论**: 适合作为问答训练或评测语料，不适合作为图谱主数据源。

---

### 3.2 `xihao1/Traditional-Chinese-Medicine-Knowledge`

**链接**: <https://huggingface.co/datasets/xihao1/Traditional-Chinese-Medicine-Knowledge>

**定位判断**:
- `conversation/system/input/output` 结构
- 包含一定中药知识问答内容

**结论**: 可作为轻量辅助抽取语料，结构稳定性与可溯源性不足，不宜直接入图。

---

## 4. 辅助能力型数据源

### 4.1 `TCMNER/TCMNER2025`

**链接**: <https://huggingface.co/datasets/TCMNER/TCMNER2025>

**定位判断**:
- 命名实体识别数据集
- 不是药材知识库，而是抽取能力训练数据

**结论**: 作为"抽取器训练 / 校验辅助数据"，服务于规则 + agent 的实体抽取流程，而不是直接入图。

---

## 5. 落地顺序建议

### 第一阶段：验证主链路

以 `ZJUFanLab/TCMChat-dataset-600k` 作为首个辅助抽取源，验证以下主链路：

```
原始语料
  → 规则 + agent 抽取
  → 统一中间格式（经过 packages/knowledge_model 校验）
  → 导入器写入 Neo4j
```

### 第二阶段：探索型评估

并行做一次 `AIeathumberger/TCMKG` 的导出可行性评估：

- 判断能否从 Neo4j store 打包格式中提取结构化数据
- 判断节点标签和关系类型是否与本项目图模型兼容
- 评估数据量和质量

### 第三阶段：辅助数据接入

在共享图模型稳定后，再决定是否把问答类语料纳入 RAG、评测或知识补全体系。

---

## 6. 白草自有数据集（进行中）

外部 HF 源只是输入。白草自己的发布面是 private dataset `ticoag/baicao-knowledge`，仓库 staging 在 `datasets/baicao-knowledge/`。

每份源固定三件套：`source/`、`processed/`、`VIEW.md`。任务计划量和完成量在 `tasks/ledger.json`。

| source_id | 状态 | 计划 | 完成（2026-08-16） |
|-----------|------|------|---------------------|
| `national-standard-2022-pharmacopoeia` | partial | 605 条 | ~595 条抽取（estimate，待 merge） |
| `daoyi-suyang` | collected | 389 章收源 | 原文已定位，未进 staging / 未抽取 |

苏子阳是叙事医案，不是药典字段；原文未授权公开转载，只进 private dataset。筛选入图数据用各源 `SOURCE.md` 的 `import_scope_key`。

任务定义与 Parquet 发布口径：`knowledge-dataset.md`。当前实施：`docs/superpowers/plans/2026-08-16-baicao-knowledge-dataset.md`。

## 7. 相关文档

- [knowledge-model-and-ingestion.md](knowledge-model-and-ingestion.md) — 仓库级图模型与数据采集边界
- [data-model.md](data-model.md) — Neo4j 节点与关系模型
- `datasets/baicao-knowledge/README.md` — 自有数据集台账
- `docs/superpowers/specs/2026-08-16-baicao-knowledge-dataset-design.md` — 数据集设计
- `docs/superpowers/specs/2026-03-23-knowledge-model-and-data-ingestion-design.md` — 原始调研设计文档

---

## 8. TCM 训练语料构建（TCMChat 数据体系，背景归档）

本章节整理中医药大语言模型训练语料的完整构建流程，涵盖数据来源、预处理方式及七类场景数据构造策略。

### 7.1 数据来源

| 来源 | 类型 | 规模 | 说明 |
|------|------|------|------|
| 图书（国家标准、医学教材、医学案例） | 结构化文本 | 4 项国家标准、7 部医学教材、18 个医学案例 | 通过 OCR 提取 PDF 文本，人工校对 |
| TCM-DaYi（<https://www.dayi.org.cn/>） | 疾病与证候数据 | 4214 条记录 | 中国医药信息查询平台 |
| ETCM（<http://www.tcmip.cn/ETCM2/front/>） | 中药与方剂数据 | 1852 味中药、8872 条方剂数据 | 中医药百科 |
| CNKI 文献摘要 | 文献 | 近 50 万篇摘要 | 关键词："Herb"、"Formula"、"Ingredient" |
| BaiduBaike | 百科 | — | 从 baby-llama2-chinese 代码库获取 |
| AliTianchi 平台 | 阅读理解 + NER | 18478 条阅读理解、2480 条实体识别 | TCM 阅读理解数据 + TCM-NER 数据集 |
| ZY-BERT（GitHub） | 辨证论治文献 | — | 文献支持的证候数据 |
| ShenNong_TCM_Dataset（HuggingFace） | 方剂/中药推荐 | 11 万条 | 药材或方剂推荐场景 |
| Herb2.0（<http://47.92.70.12/>） | TCM 分子数据 | 6893 条 TCM 数据、49259 条分子数据 | ADMET 预测场景 |
| PharmaBench（GitHub） | ADMET 数据 | LogD(14140)、AMES(9140)、BBB(8653)、PPB(1263)、CYP2C9(1000)、CYP2D6(4505)、CYP3A4(4506) | 分子属性预测 |

### 7.2 数据预处理

#### 7.2.1 无监督数据处理

主要处理对象：图书、BaiduBaike、TCM-DaYi、专业文献、ShenNong_TCM_Dataset。

- **图书**：使用 OCR 提取 PDF 文本，人工校对（纠正错别字、标点修正、段落格式化）
- **文献摘要**：去除 HTML 标签，修正符号错误
- **TCM-DaYi / ShenNong_TCM_Dataset**：简单分词处理

#### 7.2.2 有监督指令数据构建策略

构建方式分三类：

1. **人机交互指令创建**（Human-AI Interaction Instruction Creation）
2. **模板转换为文本格式**（Template Conversion to Text Format）
3. **开源数据集收集**（Open-source Dataset Collection）

最终通过人工验证过滤，生成七类核心场景数据。

### 7.3 七类场景数据构造

| 场景 | 数据内容 | 构建方式 |
|------|----------|----------|
| **TCM 知识库** | 药材的性味归经、功效主治、组成、配伍等 | 模板转换为文本格式 |
| **选择题** | 五选一选项 + 答案 + 分析描述 | 人机交互指令 + 模板转换 |
| **阅读理解** | 基于《黄帝内经》、名医百科、专利中药、慢性病保健等文献 | 模板转换为文本格式 |
| **实体抽取** | 13 类实体：药材、药物成分、疾病、症状等 | 模板转换为文本格式 |
| **医学案例诊断** | 主诉、疾病、证候、治法、中药/方剂建议 | TCM-SD 与 ETCM 映射构建 |
| **方剂/中药推荐** | 功效、靶点、证据、疾病等属性 | 公开数据库（ChatMed-TCM、ETCM、图书）整合 + 模板转换 |
| **ADMET 预测** | TCM SMILES 指令集、ADMET 回归/分类预测任务 | Herb2.0 + PharmaBench，模板转换 |

#### 场景详情

**医学案例诊断数据构造**：

- 数据源：TCM-SD（疾病、证候、症状）、ETCM（中药功效）
- 构建方式：通过证候与治法映射构建，输出字段包括：主诉、疾病、证候、治法、中药/方剂建议

**ADMET 预测数据构造**：

- TCM 分子 SMILES 指令集 ← Herb2.0
- ADMET 回归/分类预测任务 ← PharmaBench（LogD、AMES、BBB、PPB、CYP2C9、CYP2D6、CYP3A4）
