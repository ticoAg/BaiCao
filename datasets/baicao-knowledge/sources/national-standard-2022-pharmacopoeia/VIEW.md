# VIEW · national-standard-2022-pharmacopoeia

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 3431 |
| units | 1290 |
| batches | 8 |
| generated_at | 2026-08-17T04:18:33+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-04-19-pharmacopoeia-ark-retry-batch-100a-20260419` | 99 | 577 |
| `2026-04-19-pharmacopoeia-ark-retry-batch-100b-20260419` | 94 | 660 |
| `2026-04-19-pharmacopoeia-ark-retry-batch-50-20260419` | 50 | 291 |
| `2026-04-19-pharmacopoeia-ark-retry-final-62-20260419` | 61 | 579 |
| `2026-04-19-pharmacopoeia-ark-retry-sample-10` | 1 | 1 |
| `2026-04-19-pharmacopoeia-ark-retry-sample-10-v2` | 10 | 57 |
| `2026-04-19-pharmacopoeia-ark-smoke-real-v2` | 1 | 5 |
| `2026-04-19-pharmacopoeia-full-real-20260419` | 975 | 1261 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 功效 | 602 |
| 归经 | 26 |
| 性味 | 17 |
| 病证 | 1134 |
| 药材 | 593 |
| 证据 | 598 |
| 饮片 | 461 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 具有功效 | 1250 |
| 具有性味 | 723 |
| 具有饮片 | 453 |
| 归于经脉 | 1084 |
| 治疗病证 | 2892 |
| 由证据支持 | 1054 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = '2022年中药药典'
   OR '2022年中药药典' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `抱抱脸:中药药典2022`
