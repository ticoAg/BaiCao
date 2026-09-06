# VIEW · tcm-diagnostics

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 410 |
| units | 410 |
| batches | 1 |
| generated_at | 2026-08-20T08:01:10+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-08-20-tcm-diagnostics-sample-v1` | 410 | 410 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 方剂 | 15 |
| 来源 | 3 |
| 治法 | 4 |
| 病证 | 206 |
| 药材 | 182 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 来源于 | 449 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = '中医诊法样本'
   OR '中医诊法样本' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `抱抱脸:中医诊法样本`
