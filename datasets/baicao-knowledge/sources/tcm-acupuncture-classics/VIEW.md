# VIEW · tcm-acupuncture-classics

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 197 |
| units | 197 |
| batches | 1 |
| generated_at | 2026-08-20T08:00:51+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-08-20-tcm-acupuncture-classics-sample-v1` | 197 | 197 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 方剂 | 1 |
| 来源 | 3 |
| 治法 | 3 |
| 病证 | 154 |
| 药材 | 36 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 来源于 | 231 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = '针灸古籍样本'
   OR '针灸古籍样本' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `抱抱脸:针灸古籍样本`
