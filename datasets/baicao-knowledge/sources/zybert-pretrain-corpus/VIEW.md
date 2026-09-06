# VIEW · zybert-pretrain-corpus

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 11920 |
| units | 11920 |
| batches | 2 |
| generated_at | 2026-08-20T10:06:27+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|


## 节点类型

| 类型 | 数量 |
|------|------|
| 方剂 | 2516 |
| 来源 | 532 |
| 治法 | 99 |
| 病证 | 4802 |
| 药材 | 3971 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 来源于 | 11365 |
| 组成药材 | 9076 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = 'ZY-BERT 预训练语料'
   OR 'ZY-BERT 预训练语料' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `dropbox:zybert:tcm_pretrain_corpus_a.rar`
