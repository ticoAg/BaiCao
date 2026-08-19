# VIEW · DragonTCM

本页数量来自 `processed/latest/stats.json`；全部内容为 `pending`，`publish: false`，不得进入 public Parquet。

## 处理状态

| 项 | 值 |
|---|---|
| 原始实体行 | 4,743 |
| 原始显式关系 | 28,735 |
| records | 11,598 |
| edges | 46,666 |
| batch_id | `2026-08-19-dragontcm-v1` |
| generated_at | `2026-08-19T10:54:03+00:00` |

## 节点类型

| 类型 | 数量 |
|---|---|
| 药材 | 1,027 |
| 方剂 | 2,574 |
| 病证 | 803 |
| 症状/临床表现 | 7,194 |

## 关系类型

| 类型 | 数量 | 方向 |
|---|---|---|
| 组成药材 | 14,608 | 方剂 -> 药材 |
| 关联药材 | 2,197 | 病证 -> 药材 |
| 关联症状 | 29,861 | 病证 -> 症状 |

没有生成 `治疗病证`、`使用方剂` 或 `关联证候`。来源的 `condition -> formula treats` 全部隔离，`condition -> herb treats` 只保留为中性 `关联药材`。

## condition 与 SNOMED 门禁

| 来源语义标签 | 数量 | 处理 |
|---|---|---|
| `disorder` | 803 | 映射为 `病证` |
| `finding` | 257 | 隔离 |
| `morphologic abnormality` | 40 | 隔离 |
| `observable entity` | 12 | 隔离 |
| `qualifier value` | 4 | 隔离 |
| `procedure` | 2 | 隔离 |
| 无合法标签 | 1 | 隔离 |

源中 306 个 condition 带唯一合法 SNOMED ID；入图的 disorder 中 227 个有 ID、576 个无 ID。无 ID 不生成、不猜测。

## 合并与隔离

| 决策 | 数量 | 处理 |
|---|---|---|
| herb/formula 跨类型同名 | 20 组 | 两种节点分别保留 |
| 药材表面重复 | 18 组 | 17 组合并；1 组属性冲突保持独立 |
| 方剂表面重复 | 6 组 | 6 组合并 |
| 非 disorder condition | 316 行 | 隔离 |
| 非 disorder 或被隔离端点关系 | 5,576 | 隔离 |
| disorder 到 formula `treats` | 6,354 | 隔离 |
| 截断 clinical manifestation | 45 | 隔离 |
| 空/缺失/坏 manifestation | 6 | 隔离 |
| 重复病证/症状边 | 7,281 | 确定性折叠 |

端点解析包含 14,564 次大小写归一化和 83 次表面变体重写；没有 alias-based 或 cross-language 自动合并。冲突组 `FUSHI` / `FU SHI` 在图中保持两个独立药材节点。

## 隔离 Neo4j smoke

无持久卷 `neo4j:5-community` 临时容器导入结果：

```text
created=11598
edges=46666
nodes=11598
relationships=46666
```

验收查询结果：三类关系端点类型错误均为 0；缺失 `证据定位=0`；节点/边 scope 错误均为 0；同标签同名重复为 0；非 `pending` 状态为 0；SNOMED 病证节点 227；跨类型同名 20 组；`治疗病证`、`使用方剂`、`关联证候` 均为 0。验证后容器已停止并自动删除。

## 筛选

```cypher
MATCH (n)
WHERE n.导入范围键 = 'huggingface:f-galkin/DragonTCM@57e19c6bb7aaf62feacbba97aa84d9baecd05582'
   OR 'huggingface:f-galkin/DragonTCM@57e19c6bb7aaf62feacbba97aa84d9baecd05582' IN coalesce(n.导入范围键列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '2026-08-19-dragontcm-v1'
   OR '2026-08-19-dragontcm-v1' IN coalesce(n.导入批次列表, [])
RETURN n
```
