---
license: other
pretty_name: BaiCao Knowledge
configs:
  - config_name: default
    data_files:
      - split: train
        path: data/records.parquet
---

# baicao-knowledge

白草自有中医药知识数据集（private）。HF id：[`ticoAg/baicao-knowledge`](https://huggingface.co/datasets/ticoAg/baicao-knowledge)。图模型真源在仓库 `packages/knowledge_model/`，这里只放实例、统计和溯源字段。

苏子阳原文未获转载授权，**不在本 repo 发布全文**，只发布结构化记录。

## 筛选列

`source_id` · `batch_id` · `unit_id` · `node_type` · `prompt_hash` · `import_scope_key`

当前苏子阳抽取契约：`prompt_hash = sha256:0d397619b867`（`EXTRACT_SUYANG.md` v3）

## 当前源

| source_id | 状态 | 记录 | 说明 |
|-----------|------|------|------|
| `national-standard-2022-pharmacopoeia` | imported | 3431 / 605 条 | 药典 2022，entry_key 全成功 |
| `daoyi-suyang` | imported | 1687 / 389 章 | v3 宁缺毋滥；skip 262；已合并入 Neo4j |

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
