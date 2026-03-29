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

## 6. 相关文档

- [knowledge-model-and-ingestion.md](knowledge-model-and-ingestion.md) — 仓库级图模型与数据采集边界
- [data-model.md](data-model.md) — Neo4j 节点与关系模型
- `docs/superpowers/specs/2026-03-23-knowledge-model-and-data-ingestion-design.md` — 原始调研设计文档
