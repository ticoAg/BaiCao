# VIEW · TCM-NER / DeepNER

本页数量来自 `processed/latest/stats.json`；全部内容为 `pending`，`publish: false`，不得进入 public Parquet。

## 处理状态

| 项 | 值 |
|---|---:|
| 消费文件 | train.json、dev.json |
| 标注篇 | 1,000 |
| 标注跨度 | 17,757 |
| records | 0 |
| edges | 0 |
| batch_id | `2026-08-19-tcm-ner-v1` |
| generated_at | `2026-08-19T12:58:10+00:00` |

## 节点类型

本轮不入图。按类型计的表面词仅作隔离统计：

| 源标签 | 跨度 | 唯一表面 |
|---|---:|---:|
| SYMPTOM | 6,090 | 1,517 |
| DRUG_EFFICACY | 3,257 | 865 |
| PERSON_GROUP | 1,718 | 124 |
| SYNDROME | 1,206 | 311 |
| DRUG_TASTE | 1,133 | 106 |
| DISEASE | 1,104 | 218 |
| DRUG_DOSAGE | 1,016 | 72 |
| DRUG_INGREDIENT | 728 | 216 |
| FOOD_GROUP | 641 | 58 |
| DISEASE_GROUP | 623 | 149 |
| DRUG | 156 | 73 |
| FOOD | 71 | 25 |
| DRUG_GROUP | 14 | 12 |

## 关系类型

| 类型 | 数量 | 方向 |
|---|---:|---|
| （无） | 0 | 共现不提升为图关系 |

`治疗病证=0`。说明书原文、候选实体串和 stack 重复集均未入图。

## 合并、修复与隔离

| 决策 | 数量 | 处理 |
|---|---:|---|
| train∪dev | 1,000 | 只读审计 |
| stack 与 train∪dev | 精确相等 | 隔离，禁止双计数 |
| 无标签 test | 500 | 隔离 |
| 跨类型同名表面 | 260 | 不合并、不入图 |
| 说明书原文 | 1,500 篇 | 不写入 records |
| 药厂/公司名出现 | 904 / 1,000 标注篇 | 计入发布门禁 |

## 隔离 Neo4j smoke

无图记录，不启动临时图库。importer dry-run 对空 `records.jsonl` 不适用。

## 筛选

```cypher
MATCH (n)
WHERE n.导入范围键 = 'github:z814081807/DeepNER:data/raw_data'
   OR 'github:z814081807/DeepNER:data/raw_data' IN coalesce(n.导入范围键列表, [])
RETURN n
```

当前应返回 0 行。
