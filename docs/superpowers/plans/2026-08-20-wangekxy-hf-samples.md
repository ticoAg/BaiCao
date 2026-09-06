---
type: Implementation Plan
title: wangekxy 13 源 roadmap 与剩余 HF 样本入图
description: 先登记 13 个 wangekxy Hugging Face 数据集的状态，再对剩余公开 sample 做章节适合性判定后清洗入本地图。
resource: docs/superpowers/plans/2026-08-20-wangekxy-hf-samples.md
tags: [data-sources, data-ingestion, huggingface, wangekxy]
timestamp: 2026-08-20T00:00:00+08:00
status: active
---

# wangekxy 13 源 roadmap 与剩余 HF 样本入图

**Goal:** 先列出 `wangekxy` 全部 13 个数据集的处理状态，再对剩余可下载的中医专题 sample 做章节适合性判定；判定 **go** 的才清洗并入本地 Neo4j。`publish` 保持 `false`。未购买的全量包不入图。

**Architecture:** 每源独立 `datasets/baicao-knowledge/sources/<source_id>/`。公开 sample 走与 `tcm-formulary` 相同的变换：`title`+`text` → `来源` 节点 + 现有词表最长匹配提及 + `来源于` 边。适配器不得发明 `NodeType` / `EdgeType`。catalog / `data-sources.md` / `graph_i18n.py` 由主代理统一合并。

**Status:** done（13 源 roadmap + 9 个 go sample 已清洗入本地图；NLP 与 unpaid 全量已跳过）

## 13 源状态

| HF id | 计划 source_id | 状态 | 说明 |
|---|---|---|---|
| `wangekxy/classical-tcm-canon` | `classical-tcm-canon` | already-imported | 115 部全量已入本地图 |
| `wangekxy/tcm-formulary` | `tcm-formulary` | already-imported | 3 部公开样本已入图；全量 91 部 unpaid / not held |
| `wangekxy/tcm-materia-medica` | `tcm-materia-medica` | imported | 本草/药性。读过石药尔雅、易牙遗意、药性歌括。705 records。全量 59 部 unpaid |
| `wangekxy/tcm-case-records` | `tcm-case-records` | imported | 古籍医案。读过一瓢医案、许氏医案、曹仁伯医案论。482 records。不建整书医案节点。全量 33 部 unpaid |
| `wangekxy/tcm-acupuncture-classics` | `tcm-acupuncture-classics` | imported | 针灸/经络。读过炙膏肓腧穴法、针经节要、黄庭内景五藏六府图。197 records。全量 33 部 unpaid |
| `wangekxy/tcm-diagnostics` | `tcm-diagnostics` | imported | 诊法。读过察舌辨症新法、脉象统类、咽喉脉证通论。410 records。不发明脉象/舌象节点。全量 42 部 unpaid |
| `wangekxy/tcm-gynecology-pediatrics` | `tcm-gynecology-pediatrics` | imported | 妇幼。读过鬻婴提要说、张氏妇科、颅囟经。435 records。全量 69 部 unpaid |
| `wangekxy/tcm-external-surgical` | `tcm-external-surgical` | imported | 外科。读过走马急疳真方、幼科种痘心法要旨、脏腑虚实标本用药式。432 records。全量 50 部 unpaid |
| `wangekxy/tcm-collected-works` | `tcm-collected-works` | imported | 医论。读过医学举要、上池杂说、三消论。411 records。不当事实。全量 171 部 unpaid |
| `wangekxy/tcm-health-cultivation` | `tcm-health-cultivation` | imported | 养生。读过万氏养生四要、养生肤语、陆地仙经。99 records。不发明导引类型。全量 18 部 unpaid |
| `wangekxy/tcm-reference-compendia` | `tcm-reference-compendia` | imported | 类书。读过医部全录肩/腋/懊憹门 3 卷切片。465 records。全量 14 部 unpaid |
| `wangekxy/classical-chinese-punctuation` | — | skip | 文言断句 SFT，不是图谱事实 |
| `wangekxy/classical-chinese-variant-collation` | — | skip | 异体/四库对照，不是图谱事实 |

未购买的商业全量（91 部方书、59 部本草等）一律 **unpaid-full-set-not-held**，不下载、不入图。

## 优先级

1. 本草 / 医案 / 针灸 sample
2. 诊法 / 妇幼 / 外科 / 医论 / 养生 / 类书
3. 跳过两个 NLP 集

## 适合性门禁

每个 remaining 源在发出 graph records 之前必须：

1. 下载本地 `sample.jsonl`
2. 读 `CONTENTS.md` 与至少一部正文切片
3. 写出 go/no-go：引用书名/切片，并说明能否映射到现有 `NodeType` / `EdgeType`
4. no-go 只记 skip，不写 cleaner

## 入图契约

- 判定 go 的源：DatasetRecord → `processed/latest` → catalog 登记 → 本地 Neo4j
- `publish: false`
- 节点/边类型只能用 `packages/knowledge_model` 已有枚举
- 默认变换：`来源` + 词表提及 + `来源于`

## 适合性判定（判定完成后回写）

书面结论在各源 `work/notes/suitability.md`。跳过总表：[`datasets/baicao-knowledge/tasks/wangekxy-skip.md`](../../../datasets/baicao-knowledge/tasks/wangekxy-skip.md)。

| source_id | 判定 | 抽样书名 | 映射 | 笔记 |
|---|---|---|---|---|
| `tcm-materia-medica` | go | 石药尔雅 / 易牙遗意 / 药性歌括四百味 | `来源` + 词表提及 + `来源于` | 易牙遗意是食经，不发明食谱类型 |
| `tcm-case-records` | go | 一瓢医案 / 许氏医案 / 曹仁伯医案论 | 同上 | 整书全文，不建 `医案` 节点 |
| `tcm-acupuncture-classics` | go | 炙膏肓腧穴法 / 针经节要 / 黄庭内景五藏六府图 | 同上，穴位/经脉走词表 | 不发明导引/内丹 |
| `tcm-diagnostics` | go | 察舌辨症新法 / 脉象统类 / 咽喉脉证通论 | 只抽可映射提及 | 不发明脉象/舌象节点 |
| `tcm-gynecology-pediatrics` | go | 鬻婴提要说 / 张氏妇科 / 颅囟经 | 病证/方剂/药材 | — |
| `tcm-external-surgical` | go | 走马急疳真方 / 幼科种痘心法要旨 / 脏腑虚实标本用药式 | 病证/方药/治法 | 不发明种痘法类型 |
| `tcm-collected-works` | go | 医学举要 / 上池杂说 / 三消论 | 方剂/药材/病证 | 医论保持 pending |
| `tcm-health-cultivation` | go | 万氏家传养生四要 / 养生肤语 / 陆地仙经 | 只抽可映射提及 | 不发明导引 |
| `tcm-reference-compendia` | go | 医部全录卷170 肩门 / 卷171 腋门 / 卷226 懊憹门 | 方剂/穴位/病证 | title 是卷切片；author 实为门类名 |

## 跳过记录

- `classical-chinese-punctuation`：断句任务，非图事实。
- `classical-chinese-variant-collation`：校勘对齐，非图事实。
- 各专题 unpaid 全量：HF 仅 sample.jsonl。详见 `datasets/baicao-knowledge/tasks/wangekxy-skip.md`。
