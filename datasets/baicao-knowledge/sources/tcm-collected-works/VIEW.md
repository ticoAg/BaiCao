# VIEW · tcm-collected-works

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 411 |
| units | 411 |
| batches | 1 |
| generated_at | 2026-08-20T08:01:20+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-08-20-tcm-collected-works-sample-v1` | 411 | 411 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 方剂 | 26 |
| 来源 | 3 |
| 治法 | 9 |
| 病证 | 158 |
| 药材 | 215 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 来源于 | 475 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = '中医医论样本'
   OR '中医医论样本' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `抱抱脸:中医医论样本`
