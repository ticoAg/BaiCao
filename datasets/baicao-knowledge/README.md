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
| `fengxi177-knowledge-graph-tcm` | cleaned_local | 4996 / 19923 条关系 | 仅本地 records；上游无许可证，`publish: false` |
| `shennong-tcm-kg` | cleaned_local | 19066 / 123358 条三元组 | 仅本地 records；许可限制，`publish: false` |
| `tcm-db` | cleaned_local | 1715 records / 654 edges | 仅本地 records；混合上游许可不完整，`publish: false` |
| `dragontcm` | cleaned_local | 11598 records / 46666 edges | 仅本地 records；非商业限制且上游权利链未闭合，`publish: false` |
| `tcm-mkg` | cleaned_local | 19519 records / 177672 edges | 仅本地 records；聚合许可与 WHO 上游条款冲突，`publish: false` |
| `tcm-sd` | cleaned_local | 148 records / 0 edges | 仅本地证候词表；CC-BY-NC-SA-4.0 且残留病历标识，`publish: false` |
| `tcm-ner` | cleaned_local | 0 records / 0 edges | 仅本地审计；竞赛镜像无许可证，跨度不入图，`publish: false` |
| `tcm-ancient-books` | cleaned_local | 0 records / 0 edges | 仅书目审计；无许可证且全文不入图，`publish: false` |
| `classical-tcm-canon` | cleaned_local | 0 records / 0 edges | 115 部全文隔离；proprietary-commercial，`publish: false` |
| `sylvanl-tcm-pretrain` | cleaned_local | 0 records / 0 edges | 自由文本含串文；医案未持有，`publish: false` |
| `zybert-pretrain-corpus` | cleaned_local | 0 records / 0 edges | 只清单不解压，`publish: false` |
| `tcmchat-600k` | cleaned_local | 0 整包 records | Apache-2.0 整包盘点；除药典外待按子集清洗，`publish: false` |

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
