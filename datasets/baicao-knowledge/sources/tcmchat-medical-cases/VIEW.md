# VIEW · tcmchat-medical-cases

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 28604 |
| units | 20585 |
| batches | 1 |
| generated_at | 2026-08-20T05:15:14+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-08-19-tcmchat-cases-v1` | 20585 | 28604 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 医案 | 461 |
| 方剂 | 2037 |
| 治法 | 1076 |
| 病证 | 10363 |
| 药材 | 14667 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 记载于医案 | 28143 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = 'TCMChat 名医验案'
   OR 'TCMChat 名医验案' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `抱抱脸:TCMChat名医验案`
