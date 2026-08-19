# VIEW · TCM-SD / ZY-BERT

本页数量来自 `processed/latest/stats.json`；全部内容为 `pending`，`publish: false`，不得进入 public Parquet。

## 处理状态

| 项 | 值 |
|---|---:|
| 消费文件 | `syndrome_vocab.txt`、train/dev/test.json |
| 标注行 | 54,152 |
| records | 148 |
| edges | 0 |
| batch_id | `2026-08-19-tcm-sd-v1` |
| generated_at | `2026-08-19T12:38:38+00:00` |

## 节点类型

| 类型 | 数量 |
|---|---:|
| 病证（来源标注证候） | 148 |

## 关系类型

| 类型 | 数量 | 方向 |
|---|---:|---|
| （无） | 0 | 本轮不提升病例标签边 |

`治疗病证=0`。病例上的病名-证候标注、知识库常见病/推荐方、主诉/现病史/四诊原文均未入图。

## 合并、修复与隔离

| 决策 | 数量 | 处理 |
|---|---:|---|
| 证候词表 | 148 | 入图，身份为规范名 |
| 病例病名 | 451 | 只统计，不生成节点 |
| 病名编码冲突 | 34 个多 ID 病名，6 个多病名编码 | 不合并 |
| 跨类型同名 | 1（`风寒湿痹证`） | 只保留证候节点 |
| 原始证候别名一对多 | 1（`脾虚证`） | 不把原始名当键 |
| 病-证共现对 | 2,023 | 隔离，不生成 `关联证候` |
| 知识库条目 | 1,027 | 隔离 |
| 临床自由文本行 | 59,638 | 不写入 records |
| 残留住院号 / 手机号 / 医院名 | 77 / 1 / 11,626 | 计入隐私门禁，不抽样原文 |
| 全文跨 split | 626 | 证明必须保持拆分，不得汇总当知识 |

## 隔离 Neo4j smoke

无持久卷 `neo4j:5-community` 临时容器导入结果：

```text
created=148
nodes=148
relationships=0
```

验收查询结果：全部为 `病证`；`中医类型=来源标注证候` 148；`治疗病证=0`；`关联证候=0`；节点 scope 错误 0；非 `待验证` 节点 0。验证后容器已停止并删除。

## 筛选

```cypher
MATCH (n)
WHERE n.导入范围键 = 'github:Borororo/ZY-BERT:TCM-SD'
   OR 'github:Borororo/ZY-BERT:TCM-SD' IN coalesce(n.导入范围键列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '2026-08-19-tcm-sd-v1'
   OR '2026-08-19-tcm-sd-v1' IN coalesce(n.导入批次列表, [])
RETURN n
```
