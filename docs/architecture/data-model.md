<!--
---
doc_kind: architecture
status: stable
tags: ["database", "knowledge-graph", "data-model", "multi-dimensional"]
summary: 完整数据模型设计（药材-成分-品种-工艺-性状）
audience: developer
---
-->

# 数据模型设计（完整版）

## 1. 概述

本项目采用**混合存储架构**：

| 数据库 | 职责 | 存储内容 |
|--------|------|----------|
| **PostgreSQL** | 事务型数据 + 验证工作流 | 用户、文献、验证申请、验证证据 |
| **Neo4j** | 图谱查询 + 知识网络 | 多维度实体、关系、验证状态 |

**设计理念**：
- **药材（Herb）** 作为核心基类
- **成分（Component）** 作为独立实体，有自己的功效
- **品种（Variant）** 描述同源不同种
- **工艺（Process）** 描述加工过程和影响
- **性状（Trait）** 描述可观察的特征
- **年份（Year）** 作为时间维度属性

---

## 2. Neo4j 节点类型

### 2.1 节点类型一览

```
(:Herb)         # 药材基类（如：陈皮、人参）
(:Component)    # 成分/副产品（如：挥发油、陈皮素）
(:Variant)      # 品种变种（如：大红皮、二红皮）
(:Process)      # 加工工艺（如：沉化、晒干）
(:Trait)        # 性状特征（如：油室、内囊）
(:Efficacy)     # 功效（如：去痰平喘）
(:Flavor)       # 性味（如：辛、苦）
(:Meridian)     # 归经（如：肺经、脾经）
(:Disease)       # 疾病（如：咳嗽、消化不良）
(:Source)        # 文献来源
(:TimePoint)    # 时间点（如：3年、5年、10年）
```

### 2.2 节点属性

#### Herb（药材）

```cypher
(:Herb {
  id: UUID,                    -- 唯一标识
  name: string,                 -- 基础名称（如"陈皮"）
  type: "base" | "byproduct", -- 类型：基类 or 副产品
  source: string,               -- 数据来源
  category: string,             -- 药材分类（如"理气药"）
  imported_at: datetime,        -- 导入时间
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null,
  verified_by: UUID | null,
  verified_at: datetime | null
})
```

#### Component（成分）

```cypher
(:Component {
  id: UUID,
  name: string,                 -- 成分名称（如"挥发油"、"陈皮素"）
  chemical_formula: string | null,  -- 化学式（可选）
  source: string,               -- 来源（如"陈皮提取"）
  imported_at: datetime,
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null,
  verified_by: UUID | null,
  verified_at: datetime | null
})
```

#### Variant（品种变种）

```cypher
(:Variant {
  id: UUID,
  name: string,                 -- 品种名称（如"大红皮"、"二红皮"）
  parent_herb: string,          -- 父级药材（如"陈皮"）
  description: string,            -- 品种描述
  imported_at: datetime,
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null,
  verified_by: UUID | null,
  verified_at: datetime | null
})
```

#### Process（加工工艺）

```cypher
(:Process {
  id: UUID,
  name: string,                 -- 工艺名称（如"沉化"、"晒干"）
  description: string,           -- 工艺描述
  min_duration: string | null,  -- 最短时间要求（如"3年"）
  conditions: string | null,     -- 条件要求（如"干皮晒干储存"）
  effect: string | null,        -- 对药材的影响
  imported_at: datetime,
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null,
  verified_by: UUID | null,
  verified_at: datetime | null
})
```

#### Trait（性状特征）

```cypher
(:Trait {
  id: UUID,
  name: string,                 -- 性状名称（如"油室"、"内囊"）
  category: "external" | "internal" | "chemical",  -- 类别
  description: string,           -- 描述
  observation_method: string | null,  -- 观察方法
  imported_at: datetime,
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null,
  verified_by: UUID | null,
  verified_at: datetime | null
})
```

#### TimePoint（时间点）

```cypher
(:TimePoint {
  id: UUID,
  years: integer,               -- 年数（如：3、5、10）
  description: string | null,   -- 描述（如"新会陈皮三年陈"）
  quality_indicator: string | null,  -- 品质指标
  imported_at: datetime,
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null,
  verified_by: UUID | null,
  verified_at: datetime | null
})
```

#### Efficacy / Flavor / Meridian / Disease

```cypher
(:Efficacy {
  id: UUID,
  name: string,                 -- 功效名称（如"去痰平喘"）
  category: string | null,       -- 功效分类
  imported_at: datetime,
  status: "pending" | "verified" | "rejected",
  ...
})

(:Flavor {
  id: UUID,
  name: string,                 -- 性味名称（如"辛"、"苦"）
  nature: string | null,         -- 药性（如"温"、"凉"）
  ...
})

(:Meridian {
  id: UUID,
  name: string,                 -- 归经名称（如"肺经"、"脾经"）
  ...
})

(:Disease {
  id: UUID,
  name: string,                 -- 疾病名称
  tcm_type: string | null,      -- 中医证型
  ...
})
```

---

## 3. 关系类型

### 3.1 关系一览

```
药材-成分关系：
  (Herb)-[:CONTAINS {quantity, verification_id}]->(Component)
  (Component)-[:EXTRACTED_FROM]->(Herb)
  (Herb)-[:HAS_EFFICACY {verification_id}]->(Efficacy)

药材-品种关系：
  (Herb)-[:HAS_VARIANT]->(Variant)
  (Variant)-[:VARIANT_OF]->(Herb)
  (Variant)-[:HAS_TRAIT {value, observation}]->(Trait)

药材-工艺关系：
  (Herb)-[:PROCESSED_BY {duration, conditions}]->(Process)
  (Process)-[:APPLIES_TO]->(Herb)
  (Herb)-[:STORED_FOR {years, start_date}]->(TimePoint)

药材-性状关系：
  (Herb)-[:HAS_TRAIT {value, observation, year_range}]->(Trait)
  (Trait)-[:OBSERVED_IN]->(Herb)

药材-功效关系：
  (Herb)-[:HAS_EFFICACY]->(Efficacy)
  (Component)-[:HAS_EFFICACY]->(Efficacy)
  (Variant)-[:HAS_EFFICACY]->(Efficacy)

药材-性味关系：
  (Herb)-[:HAS_FLAVOR]->(Flavor)

药材-归经关系：
  (Herb)-[:ENTERS_MERIDIAN]->(Meridian)

药材-疾病关系：
  (Herb)-[:TREATS]->(Disease)
  (Component)-[:TREATS]->(Disease)

交叉关系：
  (Component)-[:INTERACTS_WITH]->(Component)
  (Efficacy)-[:SIMILAR_TO]->(Efficacy)
```

### 3.2 关系属性

所有知识关系都携带验证状态：

```cypher
(Herb)-[:CONTAINS {
  quantity: string | null,      -- 含量（如"约1-2%"）
  source: string,               -- 数据来源
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null,
  verified_by: UUID | null,
  verified_at: datetime | null
}]->(Component)

(Herb)-[:HAS_VARIANT {
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null
}]->(Variant)

(Herb)-[:PROCESSED_BY {
  duration: string,             -- 持续时间（如"3年以上"）
  conditions: string,          -- 条件（如"干皮晒干储存"）
  start_date: date | null,      -- 开始日期
  end_date: date | null,        -- 结束日期
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null
}]->(Process)

(Herb)-[:HAS_TRAIT {
  value: string,               -- 性状值（如"丰富"、"明显"）
  observation: string | null,  -- 观察描述
  year_range: string | null,    -- 适用年份（如"10年以上"）
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null
}]->(Trait)

(Herb)-[:STORED_FOR {
  years: integer,              -- 储存年数
  start_date: date,            -- 开始储存日期
  end_date: date | null,       -- 结束日期（可空表示至今）
  status: "pending" | "verified" | "rejected",
  verification_id: UUID | null
}]->(TimePoint)
```

---

## 4. 图模型示例：陈皮

```
                                ┌─────────────┐
                                │   Source    │
                                │  《本草纲目》│
                                └──────┬──────┘
                                       │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
            ┌───────────────┐                   ┌───────────────┐
            │   Efficacy    │                   │   Efficacy    │
            │  理气止痛     │◄──┌              │  燥湿化痰    │
            └───────────────┘   │              └───────────────┘
                    │           │                      │
                    │           │                      │
                    │           │                      │
┌───────────┐ ┌─────┴───────┐   │              ┌─────┴─────────┐
│  Flavor   │ │    Herb     │   │              │    Disease     │
│  辛、苦   │ │   陈皮      │───┘              │  咳嗽、消化不良│
└───────────┘ └─────┬───────┘                  └────────────────┘
                    │
    ┌───────────────┼───────────────┬───────────────┬───────────────┐
    │               │               │               │               │
    ▼               ▼               ▼               ▼               ▼
┌─────────┐  ┌─────────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│Component│  │  Variant    │  │  Process  │  │   Trait   │  │  TimePoint │
│挥发油   │  │  大红皮    │  │  沉化     │  │  油室     │  │   3年     │
└────┬────┘  └──────┬────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
     │               │              │              │              │
     │               │              │              │              │
     ▼               ▼              ▼              ▼              ▼
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│去痰平喘   │  │二红皮     │  │储存3年以上 │  │外皮呈黄褐 │  │外皮红棕色 │
│促进消化   │  │青柑皮     │  │干皮晒干   │  │内囊浮白   │  │内囊雪白   │
└───────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────┘
     │
     ▼
┌───────────┐
│Component │
│陈皮素    │
└────┬────┘
     │
     ▼
┌───────────┐
│调整肠胃   │
│抗炎      │
└───────────┘
     │
     ▼
┌───────────┐
│Component │
│橙皮苷    │
└────┬────┘
     │
     ▼
┌───────────┐
│抗炎抗病毒 │
│扩张冠状动 │
│脉降血压   │
└───────────┘
```

---

## 5. 查询示例

### 5.1 查询陈皮的所有成分

```cypher
MATCH (h:Herb {name: '陈皮'})-[r:CONTAINS]->(c:Component)
RETURN h.name, c.name, r.quantity, r.status
```

### 5.2 查询陈皮的品种分类

```cypher
MATCH (h:Herb {name: '陈皮'})-[r:HAS_VARIANT]->(v:Variant)
RETURN h.name, v.name, v.description
```

### 5.3 查询陈皮的加工工艺和年份

```cypher
MATCH (h:Herb {name: '陈皮'})-[r1:PROCESSED_BY]->(p:Process)
OPTIONAL MATCH (h)-[r2:STORED_FOR]->(t:TimePoint)
RETURN h.name, p.name as process, p.min_duration, t.years
```

### 5.4 查询陈皮的性状特征（按年份）

```cypher
MATCH (h:Herb {name: '陈皮'})-[r:HAS_TRAIT]->(t:Trait)
WHERE r.year_range IS NULL OR r.year_range CONTAINS '10'
RETURN h.name, t.name, r.value, r.observation
```

### 5.5 查询大红皮的完整信息

```cypher
MATCH (v:Variant {name: '大红皮'})-[:VARIANT_OF]->(h:Herb)
OPTIONAL MATCH (v)-[r1:HAS_TRAIT]->(t:Trait)
OPTIONAL MATCH (h)-[r2:HAS_EFFICACY]->(e:Efficacy)
RETURN v.name, h.name as base_herb, collect(DISTINCT t.name) as traits, collect(DISTINCT e.name) as efficacies
```

### 5.6 查询挥发油的功效和来源

```cypher
MATCH (c:Component {name: '挥发油'})<-[r:CONTAINS]-(h:Herb)
MATCH (c)-[r2:HAS_EFFICACY]->(e:Efficacy)
RETURN c.name, collect(DISTINCT h.name) as source_herbs, collect(DISTINCT e.name) as efficacies
```

---

## 6. PostgreSQL 模型

### 6.1 表结构（与 Phase 1 相同）

| 表 | 职责 |
|----|------|
| `users` | 用户账户、角色、专家领域 |
| `sources` | 文献来源（书名、ISBN、页码） |
| `verifications` | 验证申请记录 |
| `verification_evidences` | 验证证据 |

---

## 7. 数据导入说明

### 7.1 导入时默认状态

所有导入数据初始状态为 `status: "pending"`，表示待验证。

### 7.2 批量导入示例

```cypher
// 导入陈皮及其成分
CREATE (h:Herb {id: randomUUID(), name: '陈皮', type: 'base', source: '中国药典', status: 'pending', imported_at: datetime()})
CREATE (c1:Component {id: randomUUID(), name: '挥发油', source: '中国药典', status: 'pending', imported_at: datetime()})
CREATE (c2:Component {id: randomUUID(), name: '陈皮素', source: '中国药典', status: 'pending', imported_at: datetime()})
CREATE (c3:Component {id: randomUUID(), name: '橙皮苷', source: '中国药典', status: 'pending', imported_at: datetime()})
CREATE (v1:Variant {id: randomUUID(), name: '大红皮', parent_herb: '陈皮', status: 'pending', imported_at: datetime()})
CREATE (v2:Variant {id: randomUUID(), name: '二红皮', parent_herb: '陈皮', status: 'pending', imported_at: datetime()})
CREATE (v3:Variant {id: randomUUID(), name: '青柑皮', parent_herb: '陈皮', status: 'pending', imported_at: datetime()})
CREATE (p:Process {id: randomUUID(), name: '沉化', description: '干皮晒干储存后沉淀变化', min_duration: '3年', status: 'pending', imported_at: datetime()})
CREATE (t1:Trait {id: randomUUID(), name: '油室', category: 'external', description: '表皮下的油点', status: 'pending', imported_at: datetime()})
CREATE (t2:Trait {id: randomUUID(), name: '内囊', category: 'internal', description: '内层白色部分', status: 'pending', imported_at: datetime()})

// 创建关系
CREATE (h)-[:CONTAINS {quantity: '约1-2%', status: 'pending'}]->(c1)
CREATE (h)-[:CONTAINS {quantity: '约2-3%', status: 'pending'}]->(c2)
CREATE (h)-[:CONTAINS {quantity: '约5-10%', status: 'pending'}]->(c3)
CREATE (h)-[:HAS_VARIANT {status: 'pending'}]->(v1)
CREATE (h)-[:HAS_VARIANT {status: 'pending'}]->(v2)
CREATE (h)-[:HAS_VARIANT {status: 'pending'}]->(v3)
CREATE (h)-[:PROCESSED_BY {duration: '3年以上', conditions: '干皮晒干储存', status: 'pending'}]->(p)
CREATE (h)-[:HAS_TRAIT {value: '丰富', observation: '表皮可见明显油点', status: 'pending'}]->(t1)
CREATE (h)-[:HAS_TRAIT {value: '浮白', observation: '内囊白色海绵状', status: 'pending'}]->(t2)
```

---

## 8. 未来扩展

### 8.1 可扩展方向

- **产地（Origin）**：增加产地节点，描述不同产地对药材的影响
- **配伍（Compatibility）**：增加方剂节点，描述药材间的配伍关系
- **季节（Season）**：增加采收季节节点
- **等级（Grade）**：增加品质等级节点

### 8.2 扩展示例

```cypher
// 产地
(Herb)-[:GROWN_IN {province: '广东', county: '新会'}]->(Origin)
(Origin)-[:KNOWN_FOR {product: '新会陈皮'}]->(Herb)

// 配伍
(Herb)-[:COMPATIBLE_WITH {ratio: '1:1', effect: '协同增效'}]->(Herb)

// 方剂
(Formula)-[:CONTAINS_HERB {dose: '10g'}]->(Herb)
```

---

## 9. 相关文档

- [system-overview.md](system-overview.md) — 系统架构概览
- [IMPL_PLAN.md](../IMPL_PLAN.md) — 项目规划真源
