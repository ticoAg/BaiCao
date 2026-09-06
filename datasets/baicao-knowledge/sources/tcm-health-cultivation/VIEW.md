# VIEW · tcm-health-cultivation

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 99 |
| units | 99 |
| batches | 1 |
| generated_at | 2026-08-20T08:01:20+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-08-20-tcm-health-cultivation-sample-v1` | 99 | 99 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 方剂 | 1 |
| 来源 | 3 |
| 治法 | 1 |
| 病证 | 40 |
| 药材 | 54 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 来源于 | 103 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = '中医养生样本'
   OR '中医养生样本' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `抱抱脸:中医养生样本`
