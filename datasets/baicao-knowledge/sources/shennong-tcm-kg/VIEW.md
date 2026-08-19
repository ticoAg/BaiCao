# VIEW · shennong-tcm-kg

本页数量来自 `processed/latest/stats.json`；内容状态均为 `pending`，不得进入 public Parquet。

## 处理状态

| 项 | 值 |
|----|----|
| 原始行 | 123358 |
| records | 19066 |
| edges | 52247 |
| batches | 1 |
| batch_id | `2026-08-19-shennong-tcm-kg-v1` |
| generated_at | `2026-08-19T09:10:34+00:00` |

## 节点类型

| 类型 | 数量 |
|------|------|
| 药材 | 947 |
| 功效 | 846 |
| 性味 | 22 |
| 归经 | 12 |
| 病证 | 15965 |
| 治法 | 1274 |

`病证` 中有 3,278 个来源标注证候，12,687 个未分类临床概念；来源标注仍为 `pending`，当前不自动拆分疾病、症状或证候。

## 关系类型

| 类型 | 数量 |
|------|------|
| 具有功效 | 2180 |
| 具有性味 | 2231 |
| 归于经脉 | 1954 |
| 关联证候 | 35444 |
| 关联药材 | 7832 |
| 关联治法 | 2606 |

`decision_counts.mapped_edge=52,245` 按映射后的源三元组计数；上表 `52,247` 条边按多值拆分并去重后的物化关系计数，两者口径不同。

## 排除与隔离

| 决策 | 数量 | 处理 |
|------|------|------|
| `symmap_chemical` + `chemical_MM` | 67481 | 排除出当前主域 |
| `TS_MS` | 245 | 隔离，不作别名或实体合并 |
| 功能 / 临床概念冲突 | 337 | 隔离，不强制建成功效 |
| 证候自环 | 9 | 跳过 |
| 精确重复原始行 | 0 | 无 |

## 筛选

```cypher
MATCH (n)
WHERE n.导入范围键 = 'github:michael-wzhu/ShenNong-TCM-LLM:src/TCM-KG_triples.txt'
   OR 'github:michael-wzhu/ShenNong-TCM-LLM:src/TCM-KG_triples.txt' IN coalesce(n.导入范围键列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '2026-08-19-shennong-tcm-kg-v1'
   OR '2026-08-19-shennong-tcm-kg-v1' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `github:michael-wzhu/ShenNong-TCM-LLM:src/TCM-KG_triples.txt`
