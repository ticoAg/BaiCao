# VIEW · fengxi177-knowledge-graph-tcm

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | 4996 |
| units | 4996 |
| batches | 1 |
| generated_at | 2026-08-19T06:51:10+00:00 |

## 批次

| batch_id | units | records |
|----------|-------|---------|
| `2026-08-19-kg-tcm-v1` | 4996 | 4996 |

## 节点类型

| 类型 | 数量 |
|------|------|
| 功效 | 224 |
| 归经 | 10 |
| 性味 | 12 |
| 方剂 | 742 |
| 来源 | 112 |
| 病证 | 2779 |
| 药材 | 1117 |

## 关系类型

| 类型 | 数量 |
|------|------|
| 具有功效 | 382 |
| 具有性味 | 336 |
| 归于经脉 | 143 |
| 来源于 | 436 |
| 治疗病证 | 3627 |
| 组成药材 | 6521 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = 'fengxi177-knowledge-graph-tcm'
   OR 'fengxi177-knowledge-graph-tcm' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `github:fengxi177/Knowlegde_Graph_TCM`
