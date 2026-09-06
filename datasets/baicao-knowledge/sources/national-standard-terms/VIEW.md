# VIEW · national-standard-terms

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 5227 |
| units | 5227 |
| batches | 1 |
| generated_at | 2026-08-20T05:15:14+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-08-19-national-standard-terms-v1` | 5227 | 5227 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 方剂 | 1869 |
| 病证 | 3358 |

## 关系类型

| 类型 | 数量 |
|------|------|


## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = '国标临床术语与成方'
   OR '国标临床术语与成方' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `抱抱脸:国标临床术语与成方`
