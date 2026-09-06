# VIEW · tcm-materia-medica

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 705 |
| units | 705 |
| batches | 1 |
| generated_at | 2026-08-20T08:00:51+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-08-20-tcm-materia-medica-sample-v1` | 705 | 705 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 方剂 | 11 |
| 来源 | 3 |
| 治法 | 15 |
| 病证 | 216 |
| 药材 | 460 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 来源于 | 790 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = '中医本草样本'
   OR '中医本草样本' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `抱抱脸:中医本草样本`
