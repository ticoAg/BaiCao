---
license: other
pretty_name: BaiCao Knowledge
configs:
  - config_name: records
    data_files:
      - split: train
        path: data/records.parquet
  - config_name: edges
    data_files:
      - split: train
        path: data/edges.parquet
---

# baicao-knowledge

白草自有中医药结构化知识数据集（public）。HF id：[`ticoAg/baicao-knowledge`](https://huggingface.co/datasets/ticoAg/baicao-knowledge)。图模型真源在仓库 `packages/knowledge_model/`，这里只放实例、统计和溯源字段。

苏子阳原文未获转载授权，**不在本 repo 或 Hugging Face 发布全文**，只发布脱敏后的结构化记录。

## 发布状态

- 2026-08-19 已真实发布：12 个允许文件 + `.gitattributes`（第三源只发布 SOURCE/VIEW 元数据）
- `records`：5,118 行；`edges`：11,202 行
- 远端不含原文、JSONL、`processed/latest`、work 或 exports
- public Dataset Viewer 的 `/is-valid`、`/splits` 和两张表首行读取均返回 200
- public 导出会清空 `evidence_text`，并从 `properties_json` 删除 `raw_text`、`evidence_text`、`source_text`、`content`、`text`

## 筛选列

`source_id` · `batch_id` · `unit_id` · `node_type` · `prompt_hash` · `import_scope_key`

当前苏子阳抽取契约：`prompt_hash = sha256:0d397619b867`（`EXTRACT_SUYANG.md` v3）

## 当前源

| source_id | 状态 | 记录 | 说明 |
|-----------|------|------|------|
| `national-standard-2022-pharmacopoeia` | imported | 3431 / 605 条 | 药典 2022，entry_key 全成功 |
| `daoyi-suyang` | imported | 1687 / 389 章 | v3 宁缺毋滥；skip 262；已合并入 Neo4j |
| `fengxi177-knowledge-graph-tcm` | imported | 4996 / 11445 边 | 已入本地图；上游无许可证，`publish: false` |
| `shennong-tcm-kg` | imported | 19066 / 52247 边 | 已入本地图；许可限制，`publish: false` |
| `tcm-db` | imported | 1715 records / 654 edges | 已入本地图；混合上游许可不完整，`publish: false` |
| `dragontcm` | imported | 11598 records / 46666 edges | 已入本地图；非商业限制且上游权利链未闭合，`publish: false` |
| `tcm-mkg` | imported | 19519 records / 177672 edges | 已入本地图；聚合许可与 WHO 上游条款冲突，`publish: false` |
| `tcm-sd` | imported | 148 records / 0 edges | 已入本地图（证候术语）；CC-BY-NC-SA-4.0 且残留病历标识，`publish: false` |
| `tcm-ner` | imported | 2961 records | 说明书跨度已入本地图，`publish: false` |
| `tcm-ancient-books` | imported | 9188 records / 464834 边 | 700 本正文词表提及 + 李培生医论；`publish: false` |
| `classical-tcm-canon` | imported | 4100 records / 48602 边 | 115 部来源+词表提及已入本地图，`publish: false` |
| `sylvanl-tcm-pretrain` | imported | 4962 records / 0 edges | 已入本地图（可分源词条）；`publish: false` |
| `zybert-pretrain-corpus` | imported | 11920 records / 20441 边 | 方剂索引 + 非索引词表提及，`publish: false` |
| `tcmchat-600k` | imported | 16894 records / 21620 边 | 说明书抽取+相似药材+论文/百科提及，`publish: false` |
| `tcm-formulary` | imported | 494 records / 600 边 | HF 公开 3 部样本；全量 91 部未购买，`publish: false` |
| `national-standard-terms` | imported | 5227 records / 0 edges | 成方 TXT 1869 已解析；前言 2620 缺 751，`publish: false` |
| `tcmchat-medical-cases` | imported | 28604 records / 28143 边 | 扩词表补抽已入本地图，`publish: false` |
| `tcmchat-textbooks` | imported | 41419 records / 41187 边 | 扩词表补抽已入本地图，`publish: false` |
| `tcmchat-sft-knowledge` | imported | 7459 records / 75949 edges | 已入本地图（72682 边落地，3267 悬空）；不当事实，`publish: false` |
| `tcmchat-web` | imported | 2290 records | 已入本地图；daiy 病名行，`publish: false` |
| `tcmchat-chatmed` | imported | 1043 records | 全量对话词表提及，不当事实，`publish: false` |
| `tcm-materia-medica` | imported | 705 records / 790 边 | HF 公开 3 部本草样本；全量 59 部未购买，`publish: false` |
| `tcm-case-records` | imported | 482 records / 605 边 | HF 公开 3 部医案样本；不建整书医案节点，`publish: false` |
| `tcm-acupuncture-classics` | imported | 197 records / 231 边 | HF 公开 3 部针灸样本；全量 33 部未购买，`publish: false` |
| `tcm-diagnostics` | imported | 410 records / 449 边 | HF 公开 3 部诊法样本；不发明脉象节点，`publish: false` |
| `tcm-gynecology-pediatrics` | imported | 435 records / 512 边 | HF 公开 3 部妇幼样本；全量 69 部未购买，`publish: false` |
| `tcm-external-surgical` | imported | 432 records / 470 边 | HF 公开 3 部外科样本；全量 50 部未购买，`publish: false` |
| `tcm-collected-works` | imported | 411 records / 475 边 | HF 公开 3 部医论样本；不当事实，`publish: false` |
| `tcm-health-cultivation` | imported | 99 records / 103 边 | HF 公开 3 部养生样本；不发明导引，`publish: false` |
| `tcm-reference-compendia` | imported | 465 records / 645 边 | HF 公开 3 卷类书切片；全量 14 部未购买，`publish: false` |

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

同名药材（如 `人参`、`桔梗`）复用药典节点：`来源` / `拉丁名` 不覆盖，只追加 `导入源列表` 与 `抽取契约哈希列表`。

本仓库不包含苏子阳原文、切章、抽取中间态或 Neo4j 整库导出。
