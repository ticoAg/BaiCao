---
license: other
pretty_name: BaiCao Knowledge
configs:
  - config_name: records
    data_files:
      - split: train
        path: data/public/records.parquet
  - config_name: edges
    data_files:
      - split: train
        path: data/public/edges.parquet
  - config_name: restricted_records
    data_files:
      - split: train
        path: data/restricted/records.parquet
  - config_name: restricted_edges
    data_files:
      - split: train
        path: data/restricted/edges.parquet
---

# baicao-knowledge

白草自有中医药结构化知识数据集。HF id：[`ticoAg/baicao-knowledge`](https://huggingface.co/datasets/ticoAg/baicao-knowledge)（**private**）。图模型真源在仓库 `packages/knowledge_model/`，这里只放实例、统计、许可字段和溯源键。

原文、JSONL、`processed/latest`、`work/` 和 Neo4j 导出**不上 Hugging Face**。Parquet 保留入图用的 `evidence_text` 与边属性 `dosage` / `dosage_ratio` / `evidence_ref`，并从 `properties_json` 删除全书字段 `raw_text`、`source_text`、`content`、`text`。用这两套表可以重建与本地 JSONL 一致的折叠结果；**写入 Neo4j 默认丢掉 `来源于` 与原文片段**，走 `neo4j-admin database import`（见仓库 `docs/architecture/knowledge-dataset.md` §3.1）。

## 分层

| 目录 | HF config | 含义 |
|---|---|---|
| `data/public/` | `records` / `edges` | `release_tier=public`：脱敏结构化结果，许可允许作为派生数据保存 |
| `data/restricted/` | `restricted_records` / `restricted_edges` | `release_tier=restricted`：仅本 private 仓；上游许可不足或 NC/无再发布授权 |

每行带 `source_id`、`release_tier`、`license`、`license_status`。`publish: true` 只表示进入 `data/public/`，**不再表示整仓 public**。

筛选列：`source_id` · `batch_id` · `unit_id` · `node_type` · `prompt_hash` · `import_scope_key` · `release_tier` · `license_status`

当前苏子阳抽取契约：`prompt_hash = sha256:0d397619b867`（`EXTRACT_SUYANG.md` v3）。苏子阳全书不上 HF；public 层含结构化结果与证据短摘。

## public 源

| source_id | 许可 | license_status | 记录 | 说明 |
|---|---|---|---|---|
| `national-standard-2022-pharmacopoeia` | Apache-2.0 | `apache-2.0_upstream_redacted_structured_only` | 3431 | 13 run merge 后 entry_key 605/605。Neo4j 药典触达节点=3427 / 边=7548（4 个近重复词条已并入）。prompt_ |
| `daoyi-suyang` | other | `no_fulltext_grant_redacted_structured_only` | 1687 | v3 合并导入。药典同名只追加导入源列表/抽取契约哈希列表，不覆盖拉丁名。全图 4175 节点 / 12575 边（中文键 |

## restricted 源（许可说明）

这些源已清洗并入本地图，结构化结果进 private HF 的 `data/restricted/`。不得把该层当公开再发布授权。详细边界见各源 `SOURCE.md`。

| source_id | 许可 | license_status | 记录 | 说明 |
|---|---|---|---|---|
| `fengxi177-knowledge-graph-tcm` | unknown | `unlicensed_upstream` | 4996 | 结构清洗完成，全部记录为 pending |
| `shennong-tcm-kg` | other | `restricted_no_redistribution_grant` | 19066 | 保守结构清洗完成 |
| `tcm-db` | unknown | `mixed_unlicensed_upstreams` | 1715 | 只读消费 5 个实体表和 3 个显式关系表 |
| `dragontcm` | CC-BY-NC-4.0 | `restricted_noncommercial_upstream_rights_unverified` | 11598 | 只接受 SNOMED disorder 为病证 |
| `tcm-mkg` | CC-BY-NC-4.0 | `restricted_noncommercial_sharealike_no_derivatives_upstream_rights_unverified` | 19519 | 只消费 D1-D7 与 D18 主域表 |
| `tcm-sd` | CC-BY-NC-SA-4.0 | `cc_by_nc_sa_4_0_dataset_mit_code_residual_phi` | 54750 | 只提升 148 个证候术语。病例原文、病名节点、病-证共现和知识库定义全部隔离。CC-BY-NC-SA-4.0 且存在残留病历标识，禁止进入 public Pa |
| `tcm-ner` | unknown | `unverified_competition_mirror_unlicensed_repo` | 2961 | 竞赛镜像无许可证，官方包未持有。NER 跨度与 260 个跨类型同名全部隔离，不生成图节点或共现边。固定 publish=false。 |
| `tcm-ancient-books` | unknown | `unlicensed_upstream_digital_edition_unverified` | 9188 | 700 本编号书 + 李培生医论：来源 701、词表提及入图 merged 9188 / 来源于 464834。203 婴童类萃替换解码。publish 仍 f |
| `classical-tcm-canon` | other | `other_proprietary_commercial_pd_claim` | 4100 | 115 部全文隔离。Dataset Card 为 proprietary-commercial，固定 publish=false。 |
| `tcm-formulary` | other | `commercial_sample_only_full_set_not_held` | 494 | 全量 91 部未购买 |
| `tcm-materia-medica` | other | `commercial_sample_only_full_set_not_held` | 705 | 3 部公开样本（石药尔雅、易牙遗意、药性歌括） |
| `tcm-case-records` | other | `commercial_sample_only_full_set_not_held` | 482 | 3 部公开样本（一瓢医案、许氏医案、曹仁伯医案论） |
| `tcm-acupuncture-classics` | other | `commercial_sample_only_full_set_not_held` | 197 | 3 部公开样本（炙膏肓腧穴法、针经节要、黄庭内景五藏六府图） |
| `tcm-diagnostics` | other | `commercial_sample_only_full_set_not_held` | 410 | 3 部公开样本（察舌辨症新法、脉象统类、咽喉脉证通论） |
| `tcm-gynecology-pediatrics` | other | `commercial_sample_only_full_set_not_held` | 435 | 3 部公开样本（鬻婴提要说、张氏妇科、颅囟经） |
| `tcm-external-surgical` | other | `commercial_sample_only_full_set_not_held` | 432 | 3 部公开样本（走马急疳真方、幼科种痘心法要旨、脏腑虚实标本用药式） |
| `tcm-collected-works` | other | `commercial_sample_only_full_set_not_held` | 411 | 3 部公开样本（医学举要、上池杂说、三消论） |
| `tcm-health-cultivation` | other | `commercial_sample_only_full_set_not_held` | 99 | 3 部公开样本（万氏家传养生四要、养生肤语、陆地仙经） |
| `tcm-reference-compendia` | other | `commercial_sample_only_full_set_not_held` | 465 | 3 卷切片（医部全录肩/腋/懊憹门） |
| `sylvanl-tcm-pretrain` | Apache-2.0 | `apache-2.0_card_mixed_unstructured_content` | 4962 | 百科前缀条目：药材 3962、方剂 1000。注射用西药跳过。 |
| `zybert-pretrain-corpus` | unknown | `unverified_dropbox_archive_not_inherited_from_tcm_sd` | 11920 | 方剂索引 + 非索引行唯一词表提及。11920 records |
| `tcmchat-600k` | Apache-2.0 | `apache-2.0_dataset_filter_brand_and_pii` | 16894 | 整包盘点，0 条整包图记录。药典已入图。国标术语/成方、教材、医案、daiy、ChatMed、knowledge.json 已分源清洗。entity_extra |
| `national-standard-terms` | Apache-2.0 | `apache-2.0_dataset_filter_brand_and_pii` | 5227 | 疾病 1308、证候 2050、成方 1861。痞气两条按父类限定。不重复消费药典。 |
| `tcmchat-medical-cases` | Apache-2.0 | `apache-2.0_dataset_filter_brand_and_pii` | 28604 | 去姓氏、留性别年龄。医案 461 + 国标词表提及。agent 仍可补抽。 |
| `tcmchat-textbooks` | Apache-2.0 | `apache-2.0_dataset_filter_brand_and_pii` | 41419 | 7 本教材按章切分，国标词表最长匹配。agent 可补抽。 |
| `tcmchat-sft-knowledge` | Apache-2.0 | `apache-2.0_dataset_filter_brand_and_pii` | 7459 | 方剂 5906、药材 659、词表病证提及 894。注射剂名已丢。组成药材 50302、关联证候 10083、适用于 13069、关联药材 2495。不当已验证 |
| `tcmchat-web` | Apache-2.0 | `apache-2.0_dataset_filter_brand_and_pii` | 2290 | daiy 中医病名/病证名行。百度百科未整包入图。 |
| `tcmchat-chatmed` | Apache-2.0 | `apache-2.0_dataset_filter_brand_and_pii` | 1043 | 全量 535240 有效行唯一词表提及 1043 |

## 规模统计

口径：直接对 `data/public/` 与 `data/restricted/` 的 Parquet 统计，**记录数按行计，唯一数按 `node_name` 在层内去重计**；与 Neo4j 折叠后的节点/边数不是同一口径（同名节点跨行合并、跨层可能复用）。

节点记录 256959 行（public 5118 + restricted 251841），关系 1113843 条（public 11202 + restricted 1102641；restricted 另有 5 行全空占位未计入）。

### 节点类型

| node_type | public 行 / 唯一 | restricted 行 / 唯一 |
|---|---|---|
| 病证 | 1289 / 1237 | 79464 / 25191 |
| 药材 | 1099 / 695 | 56731 / 13328 |
| 医案 | 112 / 112 | 54613 / 54207 |
| 方剂 | 89 / 83 | 34215 / 16866 |
| 症状 | — | 10905 / 9652 |
| 饮片 | 509 / 482 | 6207 / 6207 |
| 治法 | 71 / 55 | 4857 / 1471 |
| 功效 | 649 / 633 | 2863 / 1819 |
| 来源 | 401 / 8 | 1722 / 1469 |
| 性味 | 45 / 33 | 230 / 121 |
| 归经 | 39 / 31 | 34 / 24 |
| 证据 | 725 / 725 | — |
| 穴位 | 48 / 41 | — |
| 工艺 | 42 / 29 | — |

public 的 `来源` 只有 8 个唯一值，因为按 `import_scope_key` 建节点，天然被源数限制。

### 关系类型

| edge_type | public | restricted |
|---|---|---|
| 来源于 | 1298 | 571304 |
| 关联证候 | — | 155879 |
| 组成药材 | 502 | 154787 |
| 适用于 | — | 86583 |
| 关联症状 | — | 30300 |
| 记载于医案 | 123 | 28143 |
| 相似于 | — | 21620 |
| 具有性味 | 751 | 17792 |
| 关联药材 | — | 12524 |
| 归于经脉 | 1097 | 10389 |
| 治疗病证 | 3188 | 3627 |
| 采用治法 | 70 | 4525 |
| 关联治法 | — | 2606 |
| 具有功效 | 1300 | 2562 |
| 由证据支持 | 2225 | — |
| 具有饮片 | 459 | — |
| 使用方剂 | 77 | — |
| 经过工艺 | 70 | — |
| 取用穴位 | 42 | — |

关系的起点类型分布很不均：全部 `来源于` 边中 87.1% 集中在 药材→来源（254797）与 病证→来源（243058）；`关联证候` 主体是 医案→证候（108301/155879）。`由证据支持` 只出现在 public 层，是药典与苏子阳抽取契约带出的证据链。

## Neo4j 筛选

图上标签、关系、属性键一律中文。

```cypher
MATCH (n)
WHERE n.导入源 = '道医苏子阳'
   OR '道医苏子阳' IN coalesce(n.导入源列表, [])
RETURN labels(n)[0], count(*)

MATCH ()-[r]->()
WHERE r.导入范围键 = '人工:白草知识:道医苏子阳'
RETURN type(r), count(*)
```

同名药材（如 `人参`、`桔梗`）复用药典节点：已有非空中文属性不覆盖，只追加 `导入源列表` 与 `抽取契约哈希列表`。
