# VIEW · tcm-ancient-books

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 9188 |
| units | 9188 |
| batches | 1 |
| generated_at | 2026-08-20T09:19:05+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|


## 节点类型

| 类型 | 数量 |
|------|------|
| 方剂 | 1593 |
| 来源 | 701 |
| 治法 | 94 |
| 病证 | 3889 |
| 药材 | 2911 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 来源于 | 464834 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = '中医古籍书目'
   OR '中医古籍书目' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `代码仓库:中医古籍书目`
