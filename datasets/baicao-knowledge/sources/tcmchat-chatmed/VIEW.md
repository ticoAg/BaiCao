# VIEW · tcmchat-chatmed

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 1043 |
| units | 1043 |
| batches | 1 |
| generated_at | 2026-08-20T09:03:50+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-08-19-tcmchat-chatmed-v1` | 1043 | 1043 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 方剂 | 141 |
| 病证 | 902 |

## 关系类型

| 类型 | 数量 |
|------|------|


## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = 'TCMChat ChatMed'
   OR 'TCMChat ChatMed' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `抱抱脸:TCMChat-ChatMed`
