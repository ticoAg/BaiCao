# VIEW · TCM-Ancient-Books

本页数量来自 `processed/latest/stats.json`；全部内容为 `pending`，`publish: false`，不得进入 public Parquet。

## 处理状态

| 项 | 值 |
|---|---:|
| 编号书 | 700 |
| 可解码 | 699，全部 GB18030 |
| records | 0 |
| edges | 0 |
| batch_id | `2026-08-19-tcm-ancient-books-v1` |
| generated_at | `2026-08-19T13:06:10+00:00` |
| 首书 / 末书 | 神农本草经 / 名老中医之路 |

## 节点类型

本轮不入图。

## 关系类型

`治疗病证=0`。全文不写入 records。

## 合并、修复与隔离

| 决策 | 数量 | 处理 |
|---|---:|---|
| 可解码编号书 | 699 | 只读书目统计 |
| `203-婴童类萃.txt` | 1 | 解码失败，隔离 |
| 未编号 `700.李培生老中医经验集.txt` | 1 | 隔离 |
| 百度云下载残留 | 2 | 隔离；不覆盖已存在的 `290-外科证治全书.txt` |
| 现代书名 | 5 | 保留在书目统计中，不单独提升 |

## 隔离 Neo4j smoke

无图记录，不启动临时图库。

## 筛选

```cypher
MATCH (n)
WHERE n.导入范围键 = 'github:xiaopangxia/TCM-Ancient-Books'
   OR 'github:xiaopangxia/TCM-Ancient-Books' IN coalesce(n.导入范围键列表, [])
RETURN n
```

当前应返回 0 行。
