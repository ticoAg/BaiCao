# VIEW · tcmchat-textbooks

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 41419 |
| units | 40879 |
| batches | 1 |
| generated_at | 2026-08-20T05:15:15+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-08-19-tcmchat-textbooks-v1` | 40879 | 41419 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 方剂 | 2767 |
| 来源 | 232 |
| 治法 | 1635 |
| 病证 | 20664 |
| 药材 | 16121 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 来源于 | 41187 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = 'TCMChat 教材'
   OR 'TCMChat 教材' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `抱抱脸:TCMChat教材`
